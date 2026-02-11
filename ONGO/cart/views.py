# from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.db.models import Q, F, Count
from .models import Cart
from coupons.models import Coupon, CouponUsage
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.decorators.cache import never_cache

from django.utils.decorators import method_decorator

from django.views import View

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required

from .utils import get_cart_details, validate_and_apply_coupon  # Ensure utils.py exists
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal

import json

import logging


# Create your views here.

logger = logging.getLogger(__name__)


@method_decorator(never_cache, name='dispatch')
class CartView(LoginRequiredMixin, TemplateView):
    template_name = 'cart/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cart_items, summary = get_cart_details(self.request.user)

        context['summary'] = summary
        context['cart_items'] = cart_items

        return context


@method_decorator(csrf_exempt, name="dispatch")
class QtyChangeView(LoginRequiredMixin, View):

    def post(self, request):
        try:
            data = json.loads(request.body)
            cart_id = data.get('cart_id')
            action = data.get('action')

            cart_item = Cart.objects.get(id=cart_id, user=request.user)

            if action == 'increase':
                if cart_item.quantity < 5 and cart_item.product_variant.stock > cart_item.quantity:
                    cart_item.quantity += 1
                else:
                    return JsonResponse({
                        'error': 'Insufficient stock or ............. Max quantity reached'
                    }, status=400)
            elif action == 'decrease':
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                else:
                    return JsonResponse({
                        'error': 'Minimum quantity is 1.'
                    }, status=400)
            else:
                return JsonResponse({'error': 'Invalid action.'}, status=400)

            cart_item.save()

            # Return updated values
            return JsonResponse({
                'success': True,
                'new_quantity': cart_item.quantity,
            })

        except Cart.DoesNotExist:
            return JsonResponse({'error': 'Cart item not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@login_required
def DeleteCartView(request, pk):
    if request.method == "POST":
        try:
            cart = Cart.objects.get(pk=pk, user=request.user)
            cart.delete()
            return JsonResponse({'success': True})
        except Cart.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Cart item not found.'}, status=404)
        except Exception as e:
            logger.error(f"Error on deleting cart: {e}")
            return JsonResponse({'success': False, 'error': 'An error occurred while deleting the cart.'}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)


@method_decorator([never_cache, login_required], name='dispatch')
class ListCouponsView(View):
    """
    Returns coupons eligible for CURRENT USER (checks usage limits)
    Does NOT filter by min_order_amount (handled at apply time)
    """
    def get(self, request):
        now = timezone.now()
        eligible_coupons = []

        # Get coupons active in time window
        coupons = Coupon.objects.filter(
            active=True,
            start_date__lte=now
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        ).annotate(
            total_usage=Count('usage')
        ).filter(
            total_usage__lt=F('usage_limit')
        )

        # Filter by user's remaining usage
        for coupon in coupons:
            user_usage = CouponUsage.objects.filter(
                user=request.user,
                coupon=coupon
            ).count()

            if user_usage < coupon.per_user_limit:
                eligible_coupons.append({
                    'code': coupon.coupon_code,
                    'type': coupon.discount_type,
                    'value': float(coupon.value),
                    'min_order_amount': float(coupon.min_order_amount) if coupon.min_order_amount else None,
                    'description': (
                        f"{coupon.value}% OFF" if coupon.discount_type == 'percent'
                        else f"₹{coupon.value} OFF" if coupon.discount_type == 'fixed'
                        else "Free Shipping"
                    ),
                    'max_discount': float(coupon.max_discount) if coupon.max_discount else None
                })

        return JsonResponse({'coupons': eligible_coupons})


# ====== APPLY COUPON VIEW ======
@method_decorator([csrf_exempt, login_required, never_cache], name='dispatch')
class ApplyCouponView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            coupon_code = data.get('coupon_code', '').strip()

            if not coupon_code:
                return JsonResponse({'error': 'Coupon code is required'}, status=400)

            if request.session.applied_coupon:
                return JsonResponse({
                    'error': 'Coupon is alredy applied.. if you want to apply new coupon delete the applied coupon..'
                })

            # Get current cart state (matches CartView logic)
            base_total, current_shipping, _ = get_cart_base_total(request.user)

            # Validate and calculate discount
            is_valid, discount, free_shipping, error_msg = validate_and_apply_coupon(
                request.user,
                coupon_code,
                base_total
            )

            if not is_valid:
                return JsonResponse({'error': error_msg}, status=400)

            # Store in session (only coupon code - recalc on render for safety)
            request.session['applied_coupon'] = coupon_code.upper()
            request.session.modified = True

            # Calculate new totals for immediate frontend update
            new_base_total = base_total - discount
            new_shipping = Decimal('0.00') if free_shipping else current_shipping
            new_total = new_base_total + new_shipping

            return JsonResponse({
                'success': True,
                'discount_amount': float(discount),
                'new_base_total': float(new_base_total),
                'new_shipping': float(new_shipping),
                'new_total': float(new_total),
                'free_shipping_applied': free_shipping,
                'coupon_code': coupon_code.upper(),
                'message': 'Coupon applied successfully!'
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
        except Exception as e:
            logger.error(f"Coupon apply error: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Internal server error'}, status=500)


@require_http_methods(["POST"])
@login_required
@never_cache
def remove_coupon(request):
    if 'applied_coupon' in request.session:
        del request.session['applied_coupon']
        request.session.modified = True
    return JsonResponse({'success': True, 'message': 'Coupon removed'})
