from django.shortcuts import render, redirect
from django.contrib import messages
# from django.views.generic import ListView
from cart.utils import get_cart_items_for_user
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.decorators.cache import never_cache

from django.utils.decorators import method_decorator

from django.views import View

from django.shortcuts import get_object_or_404

from django.http import JsonResponse, FileResponse, Http404
# from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required

from accounts.utils import create_address_from_request

from decimal import Decimal
from decimal import ROUND_HALF_UP

from django.db import transaction
from django.db.models import Q, F, Count
from django.utils import timezone
from django.conf import settings

from cart.models import Cart
from .models import Order, OrderItem
from products.models import ProductVariant
from accounts.models import Address
from coupons.models import Coupon, CouponUsage

from .utils import validate_and_apply_coupon, create_razorpay_order, verify_razorpay_signature

import logging
import json
from uuid import UUID


# Create your views here.

logger = logging.getLogger(__name__)


@method_decorator(never_cache, name='dispatch')
class CheckoutInformation(LoginRequiredMixin, View):
    template_name = 'checkout/information.html'

    def get(self, request):

        user = request.user

        address = Address.objects.filter(user=user)

        cart_items, cart_summary = get_cart_items_for_user(request, user)

        for item in cart_items:
            if item.get('stock') < item.get('quantity'):
                messages.error(request, f'Insufficient Stock for {item.get('product_name')}')
                return redirect('cart')

        total_payable = cart_summary['total_payable']
        now = timezone.now()

        coupons = Coupon.objects.filter(
                active=True,
                start_date__lte=now
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=now)
            ).annotate(
                total_usage=Count('usage')
            ).filter(
                total_usage__lt=F('usage_limit'),
                min_order_amount__lte=total_payable
            )

        return render(request, self.template_name, {'addresses': address,
                                                    'cart_items': cart_items,
                                                    'cart_summary': cart_summary,
                                                    'coupons': coupons})

    def post(self, request):

        address = request.POST.get('shipping_address')

        if address is None or not Address.objects.filter(id=address).exists():
            messages.error(request, 'Please select a valid address')
            return render(request, self.template_name)

        request.session["checkout_information"] = {
            "address_id": int(address),
        }

        request.session["checkout_step"] = "information"
        request.session.modified = True

        return redirect('payment_methode')


@never_cache
@login_required
def add_address_in_checkout(request):
    if request.method == 'POST':
        success, message, _ = create_address_from_request(request)
        if success:
            # Fetch the newly created address to return it
            new_address = Address.objects.filter(user=request.user).order_by('-id').first()
            return JsonResponse({
                'success': True,
                'message': message,
                'address': {
                    'id': new_address.id,
                    'name': new_address.name,
                    'street_address': new_address.street_address,
                    'city': new_address.city,
                    'state': new_address.state,
                    'postal_code': new_address.postal_code,
                    'country': new_address.country,
                    'phone': new_address.phone,
                    'is_default': new_address.is_default
                }
            })
        else:
            return JsonResponse({'success': False, 'message': message})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@method_decorator(never_cache, name='dispatch')
class PaymentMethode(LoginRequiredMixin, View):

    template_name = 'checkout/payment.html'

    def get(self, request):

        user = request.user
        checkout_information = request.session.get('checkout_information')

        if checkout_information is None:
            return redirect('checkout_information')

        address_id = checkout_information.get('address_id')

        address = Address.objects.get(user=user, id=address_id)

        cart_items, cart_summary = get_cart_items_for_user(request, user)

        for item in cart_items:
            if item.get('stock') < item.get('quantity'):
                messages.error(request, f'Insufficient Stock for {item.get('product_name')}')
                return redirect('cart')

        return render(request, self.template_name, {'address': address, 'cart_items': cart_items,
                                                    'cart_summary': cart_summary})

    def post(self, request):
        payment_methode = request.POST.get('payment_method', '').strip()

        payment_methodes = ['cod', 'online', 'wallet']

        if payment_methode not in payment_methodes:
            messages.error(request, 'Select correct Payment methode')
            return render(request, self.template_name)

        checkout_information = request.session.get('checkout_information')

        checkout_information["payment_methode"] = payment_methode

        request.session["checkout_step"] = "payment_methode"
        request.session.modified = True

        return redirect('order_confirmation')


@method_decorator(never_cache, name='dispatch')
class OrderConfirmation(LoginRequiredMixin, View):

    template_name = 'checkout/confirmation.html'

    def get(self, request):

        user = request.user
        checkout_information = request.session.get('checkout_information')

        if checkout_information is None:
            return redirect('checkout_information')

        address_id = checkout_information.get('address_id')
        payment_methode = checkout_information.get('payment_methode')

        address = Address.objects.get(user=user, id=address_id)

        cart_items, cart_summary = get_cart_items_for_user(request, user)

        for item in cart_items:
            if item.get('stock') < item.get('quantity'):
                messages.error(request, f'Insufficient Stock for {item.get('product_name')}')
                return redirect('cart')

        request.session["checkout_step"] = "confirmation"
        request.session.modified = True

        return render(request, self.template_name, {'address': address,
                                                    'cart_items': cart_items,
                                                    'payment_methode': payment_methode,
                                                    'cart_summary': cart_summary})


class PlaceOrder(LoginRequiredMixin, View):

    @transaction.atomic
    def post(self, request):
        checkout_information = request.session.get('checkout_information', {})
        address_id = checkout_information.get('address_id')
        payment_methode = checkout_information.get('payment_methode')
        user = request.user
        checkout_step = request.session.get('checkout_step')

        if not address_id or not payment_methode or checkout_step != 'confirmation':
            return JsonResponse({
                'error': 'Incomplete checkout. Please go through all steps'
            }, status=400)

        address = get_object_or_404(Address, id=address_id, user=user)

        cart_list, summary = get_cart_items_for_user(request, user)

        if not cart_list:
            return JsonResponse({'error': 'Your Cart is Empty'}, status=400)

        variant_ids = [item['variant_id'] for item in cart_list]
        locked_variants = {
            v.id: v for v in ProductVariant.objects.select_for_update().filter(id__in=variant_ids)
        }

        for item in cart_list:
            variant = locked_variants.get(item['variant_id'])
            if not variant:
                return JsonResponse({'error': f"Item {item['product_name']} is no longer available."}, status=400)

            if variant.stock < item['quantity']:
                return JsonResponse({
                    'error': f"Insufficient stock for {item['product_name']} ({item['size']}/{item['color']})"
                }, status=400)

        total_payable = Decimal(str(summary['total_payable']))
        items_subtotal = Decimal(str(summary['items_subtotal']))
        discount_amount = Decimal(str(summary['cart_discount']))
        shipping = Decimal(str(summary['shipping']))
        coupon_code = summary.get('applied_coupon', {}).get('coupon_code', '')
        coupon_discount_amount = summary.get('applied_coupon', {}).get('discount_amount', 0)
        print(coupon_code)

        coupon = None

        if coupon_code:
            try:
                coupon = Coupon.objects.get(
                    coupon_code__iexact=coupon_code,
                    coupon_code__isnull=False,
                    active=True
                )
            except Coupon.DoesNotExist:
                return JsonResponse({
                    'error': 'Applied coupon is no longer valid. Please re-apply and try again.'
                }, status=400)

        if payment_methode == 'online':
            try:
                rzp_order = create_razorpay_order(total_payable)
                print('DEBUG: rzp_order: ', rzp_order)

                order = self._create_order_and_deduct_stock(
                    user, address, cart_list, locked_variants,
                    items_subtotal, total_payable, discount_amount,
                    payment_methode, coupon, coupon_discount_amount, shipping,
                    razorpay_order_id=rzp_order['id']
                )

                amount_in_paisa = int((total_payable * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
                print(amount_in_paisa, '----', type(amount_in_paisa))

                return JsonResponse({
                    'initilaize_razorpay': True,
                    'razorpay_order_id': rzp_order['id'],
                    'amount_paisa': amount_in_paisa,
                    'amount_inr': float(total_payable),
                    'currency': 'INR',
                    'key_id': settings.RAZORPAY_KEY_ID,
                    'internal_order_id': order.order_id,
                    'message': 'procceding to secure payment gateway',
                    "username": user.username,
                    "email": user.email,
                    "contact": '+91'+user.phone_number,
                })

            except Exception as e:
                transaction.set_rollback(True)
                logger.exception(f"Razorpay order creation failed: {e}")
                return JsonResponse({
                    'error': 'Payment gateway unavailable. Please try COD.'
                }, status=500)

        _ = self._create_order_and_deduct_stock(
            user, address, cart_list, locked_variants,
            items_subtotal, total_payable, discount_amount,
            payment_methode, coupon, coupon_discount_amount, shipping
        )

        request.session.pop('checkout_information', None)
        request.session.pop('checkout_step', None)
        request.session.pop('applied_coupon', None)
        print('Cart Session cleared...!!!!!')

        return JsonResponse({
            'success': True,
            'order_placed': True,
            'redirect_url': '/checkout/order-success/'
        })

    def _create_order_and_deduct_stock(self, user, address, cart_list, locked_variants,
                                       sub_total, total_amount, discount, payment_method,
                                       coupon, coupon_discount_amount, shipping, razorpay_order_id=None):

        order = Order.objects.create(
            user=user,
            address=address,
            sub_total=sub_total,
            promotional_discount=discount,
            total_amount=total_amount,
            status='confirmed' if payment_method != 'online' else 'pending',
            payment_method=payment_method,
            coupon=coupon,
            coupon_discount=coupon_discount_amount,
            shipping=shipping,
            razorpay_order_id=razorpay_order_id
        )

        if coupon and payment_method != 'online':
            CouponUsage.objects.create(
                coupon=coupon,
                user=user,
                order=order,
            )

        order_items = []

        for item in cart_list:
            variant = locked_variants[item['variant_id']]

            if payment_method != 'online':
                variant.stock -= item['quantity']
                variant.save(update_fields=['stock'])

            order_items.append(
                OrderItem(
                    order=order,
                    product_variant=variant,
                    product_name=item['product_name'],
                    variant_options={'size': item['size'], 'color': item['color']},
                    image_url=item['image_url'],
                    price_at_purchase=Decimal(str(item['unit_price'])),
                    quantity=item['quantity'],
                    line_discount=Decimal(str(item['total_discount'])),
                    final_line_price=Decimal(str(item['line_total'])),
                    status='confirmed' if payment_method != 'online' else 'pending'
                )
            )

        OrderItem.objects.bulk_create(order_items)

        if payment_method != 'online':
            Cart.objects.filter(user=user).delete()

        return order


@method_decorator(never_cache, name='dispatch')
class VerifyRazorpayPayment(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request):
        try:
            # Parse JSON body instead of using request.POST
            data = json.loads(request.body)
            rzp_order_id = data.get('razorpay_order_id')
            rzp_payment_id = data.get('razorpay_payment_id')
            rzp_signature = data.get('razorpay_signature')
            internal_order_id = data.get('internal_order_id')
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

        if not all([rzp_order_id, rzp_payment_id, rzp_signature, internal_order_id]):
            return JsonResponse({'error': 'Missing payment parameters'}, status=400)

        try:
            internal_order_id = UUID(str(internal_order_id))
        except (ValueError, TypeError, AttributeError):
            return JsonResponse({'error': 'Invalid order ID'}, status=400)

        try:
            order = Order.objects.select_for_update().get(
                order_id=internal_order_id,
                user=request.user,
                status='pending',
                payment_status='pending',
                razorpay_order_id=rzp_order_id
            )
        except Order.DoesNotExist:
            logger.warning(f"Invalid verification attempt for order {internal_order_id}")
            return JsonResponse({'error': 'Invalid payment session'}, status=400)

        # Verify signature

        params = {
            'razorpay_order_id': rzp_order_id,
            'razorpay_payment_id': rzp_payment_id,
            'razorpay_signature': rzp_signature
        }
        if not verify_razorpay_signature(params):
            order.status = 'failed'
            order.payment_status = 'failed'
            order.save(update_fields=['status', 'payment_status'])
            return JsonResponse({'error': 'Payment verification failed'}, status=400)

        # stock validation & deduction
        try:
            order_items = list(order.items.select_related('product_variant'))
            variant_ids = [item.product_variant_id for item in order_items]
            locked_variants = {
                variant.id: variant
                for variant in ProductVariant.objects.select_for_update().filter(id__in=variant_ids)
            }

            for item in order_items:
                variant = locked_variants.get(item.product_variant_id)
                if not variant:
                    raise Exception(f"Product variant missing for {item.product_name}")
                if variant.stock < item.quantity:
                    raise Exception(f"Insufficient stock for {item.product_name}")
                variant.stock -= item.quantity
                variant.save(update_fields=['stock'])
        except Exception as e:
            order.status = 'failed'
            order.payment_status = 'failed'
            order.save(update_fields=['status', 'payment_status'])
            logger.error(f"Stock deduction failed: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

        # Finalize order
        order.status = 'confirmed'
        order.payment_status = 'paid'
        order.razorpay_payment_id = rzp_payment_id
        order.razorpay_signature = rzp_signature
        order.save(update_fields=[
            'status', 'payment_status',
            'razorpay_payment_id', 'razorpay_signature'
        ])

        # Apply coupon usage successful payment
        if order.coupon_id:
            CouponUsage.objects.get_or_create(
                coupon=order.coupon,
                user=request.user,
                order=order
            )

        # Cleanup
        Cart.objects.filter(user=request.user).delete()
        request.session.pop('checkout_information', None)
        request.session.pop('checkout_step', None)
        request.session.pop('applied_coupon', None)
        print('Cart session Cleared..!!!')

        return JsonResponse({
            'success': True,
            'redirect_url': '/checkout/order-success/'
        })


@method_decorator(never_cache, name='dispatch')
class OrderSuccess(LoginRequiredMixin, View):
    template_name = 'checkout/order_success.html'

    def get(self, request):

        user = request.user

        order = Order.objects.filter(user=user).order_by('-created_at').first()

        if not order:
            return redirect('order-failed')

        address = order.address

        order_items = order.items.all()

        return render(request, self.template_name, {'address': address, 'order': order, 'order_items': order_items})


def orderFailed(request):

    return render(request, 'checkout/order_failed.html')


@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    if request.user != order.user and not request.user.is_staff:
        raise Http404("Order not found")

    if not hasattr(order, 'invoice'):
        # Just in case signals failed or old order, try generating it if delivered
        if order.status == 'delivered':
            from .utils import generate_invoice_pdf
            generate_invoice_pdf(order)
            order.refresh_from_db()
        else:
            raise Http404("Invoice not available yet")
    try:
        return FileResponse(order.invoice.pdf_file.open('rb'), content_type='application/pdf')
    except FileNotFoundError:
        raise Http404("Invoice file missing")


class ApplyCouponView(LoginRequiredMixin, View):

    def post(self, request):

        coupon_code = request.POST.get('coupon_code')

        if not coupon_code:
            messages.error(request, 'Enter a coupon code...')
            return redirect('checkout_information')

        if 'applied_coupon' in request.session:
            messages.error(request, 'Coupon is alredy applied')
            return redirect('checkout_information')

        _, summary = get_cart_items_for_user(request, request.user)

        min_order_amount = summary['total_payable']

        is_valid, discount, free_shipping, error_msg = validate_and_apply_coupon(
                request.user,
                coupon_code,
                Decimal(str(min_order_amount))
            )

        if not is_valid:
            messages.error(request, error_msg)
            return redirect('checkout_information')

        if (
            free_shipping and
            any(global_offer['name'] == 'Free Shipping' for global_offer in summary['applied_global_offers'])
        ):
            messages.error(request,
                           "Free shiping global offer alredy existing.. so you can't apply free shipping coupon")
            return redirect('checkout_information')

        request.session['applied_coupon'] = {
            'coupon_code': coupon_code.upper(),
            'discount_amount': str(discount),
            'free_shipping': free_shipping,
        }
        request.session.modified = True

        messages.success(request, 'Coupon applied successfully..')
        return redirect('checkout_information')
