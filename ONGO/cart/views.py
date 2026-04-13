# from django.shortcuts import redirect
from django.views.generic import TemplateView
# from django.db.models import Q, F, Count
from .models import Cart
# from coupons.models import Coupon, CouponUsage
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.decorators.cache import never_cache

from django.utils.decorators import method_decorator

from django.views import View

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required

from .utils import get_cart_items_for_user
# from django.utils import timezone

import json

import logging


# Create your views here.

logger = logging.getLogger(__name__)


@method_decorator(never_cache, name='dispatch')
class CartView(LoginRequiredMixin, TemplateView):
    template_name = 'cart/cart.html'

    def get(self, request, *args, **kwargs):

        request.session.pop('checkout_information', None)
        request.session.pop('checkout_step', None)
        request.session.pop('applied_coupon', None)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cart_items, summary = get_cart_items_for_user(self.request, self.request.user)

        context['summary'] = summary
        context['cart_items'] = cart_items

        return context


@method_decorator(csrf_exempt, name="dispatch")
class QtyChangeView(LoginRequiredMixin, View):

    def patch(self, request):
        try:
            data = json.loads(request.body)
            cart_id = data.get('cart_id')
            action = data.get('action')

            cart_item = Cart.objects.get(id=cart_id, user=request.user)

            if action == 'increase':
                if cart_item.product_variant.stock <= cart_item.quantity:
                    return JsonResponse({
                        'error': 'Max quantity reached'
                    }, status=400)

                if cart_item.quantity < 5:
                    cart_item.quantity += 1
                else:
                    return JsonResponse({
                        'error': 'Max quantity reached'
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
            _, summary = get_cart_items_for_user(self.request, self.request.user)

            # Return updated values
            return JsonResponse({
                'success': True,
                'new_quantity': cart_item.quantity,
                'summary': summary,
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
