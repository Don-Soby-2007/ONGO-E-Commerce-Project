from django.shortcuts import render, redirect
from django.contrib import messages
# from django.views.generic import ListView
from .utils import get_cart_items_for_user
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.decorators.cache import never_cache

from django.utils.decorators import method_decorator

from django.views import View

from django.shortcuts import get_object_or_404

from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required

from accounts.utils import create_address_from_request

from decimal import Decimal
from django.db import transaction

from cart.models import Cart
from .models import Order, OrderItem
from products.models import ProductVariant
from accounts.models import Address

import logging


# Create your views here.

logger = logging.getLogger(__name__)


@method_decorator(never_cache, name='dispatch')
class CheckoutInformation(LoginRequiredMixin, View):
    template_name = 'checkout/information.html'

    def get(self, request):

        user = request.user

        address = Address.objects.filter(user=user)

        cart_items = get_cart_items_for_user(user)

        return render(request, self.template_name, {'addresses': address, 'cart_items': cart_items})

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

        cart_items = get_cart_items_for_user(user)

        return render(request, self.template_name, {'address': address, 'cart_items': cart_items})

    def post(self, request):
        payment_methode = request.POST.get('payment_method').strip()

        payment_methodes = ['cod', 'online', 'card', 'wallet']

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

        cart_items = get_cart_items_for_user(user)

        request.session["checkout_step"] = "confirmation"
        request.session.modified = True

        return render(request, self.template_name, {'address': address,
                                                    'cart_items': cart_items,
                                                    'payment_methode': payment_methode})


class PlaceOrder(LoginRequiredMixin, View):

    @transaction.atomic
    def post(self, request):

        checkout_information = request.session.get('checkout_information')

        address_id = checkout_information.get('address_id')
        payment_methode = checkout_information.get('payment_methode')
        user = request.user

        checkout_step = request.session.get('checkout_step')

        if not address_id or not payment_methode or not checkout_step == 'confirmation':
            return JsonResponse({
                'error': 'Incomplete checkout. Please go through all steps'
            }, status=400)

        address = get_object_or_404(Address, id=address_id, user=user)

        cart_items = Cart.objects.filter(user=request.user).select_related(
            'product_variant__product'
        ).prefetch_related(
            'product_variant__images'
        )

        if not cart_items.exists():
            return JsonResponse({
                'error': 'Your Cart is Empty'
            }, status=400)

        variant_ids = [item.product_variant_id for item in cart_items]

        locked_variants = {
            v.id: v for v in ProductVariant.objects.select_for_update().filter(id__in=variant_ids)
        }

        if len(variant_ids) != len(locked_variants):
            return JsonResponse({
                'error': 'One or more items are no longer available.'
            }, status=400)

        subtotal = Decimal('0.00')

        for cart_item in cart_items:

            variant = locked_variants[cart_item.product_variant_id]

            if variant.stock < cart_item.quantity:
                return JsonResponse({
                    'error': f'Insufficient stock for {variant.product.name} ({variant.size}/{variant.color})'
                }, status=400)

            subtotal += variant.final_price * cart_item.quantity

        if payment_methode == 'online':
            return JsonResponse({
                'initiate_razorpay': True,
                'amount': float(subtotal),  # Frontend will use this
                'currency': 'INR',
                'message': 'Redirecting to payment gateway...'
            })

        elif payment_methode == 'wallet':
            pass

        elif payment_methode == 'card':
            pass

        else:
            self._create_order_and_deduct_stock(
                user, address, cart_items, locked_variants, subtotal, payment_methode
            )

            request.session.pop('checkout_information')
            request.session.pop('checkout_step')

            return JsonResponse({
                'success': True,
                'order_placed': True,
                'redirect_url': '/checkout/order-success/'
            })

    def _create_order_and_deduct_stock(self, user, address, cart_items, locked_variants, sub_total, payment_method):

        for item in cart_items:
            variant = locked_variants[item.product_variant_id]
            variant.stock -= item.quantity
            variant.save(update_fields=['stock'])

        order = Order.objects.create(
            user=user,
            address=address,
            sub_total=sub_total,
            total_amount=sub_total,
            status='confirmed' if sub_total > 0 else 'pending',
            payment_method=payment_method
        )

        order_items = []

        for item in cart_items:
            variant = locked_variants[item.product_variant_id]
            image_obj = variant.images.filter(is_primary=True).first()

            if not image_obj:
                image_obj = variant.images.first()

            image_url = image_obj.image_url if image_obj else "https://via.placeholder.com/150?text=No+Image"

            order_items.append(
                OrderItem(
                    order=order,
                    product_variant=variant,
                    product_name=variant.product.name,
                    variant_options={'size': variant.size, 'color': variant.color},
                    image_url=image_url,
                    price_at_time_of_order=variant.final_price,
                    quantity=item.quantity,
                    total_price=variant.final_price*item.quantity,
                    status='confirmed'
                )
            )

        OrderItem.objects.bulk_create(order_items)

        cart_items.delete()


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
