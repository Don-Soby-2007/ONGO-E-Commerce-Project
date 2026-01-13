# from django.shortcuts import redirect
from django.views.generic import ListView
from .models import Cart
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.decorators.cache import never_cache

from django.utils.decorators import method_decorator

from django.views import View

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required

import json

import logging


# Create your views here.

logger = logging.getLogger(__name__)


@method_decorator(never_cache, name='dispatch')
class CartView(LoginRequiredMixin, ListView):
    template_name = 'cart/cart.html'
    model = Cart
    context_object_name = 'cart_products'

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).select_related(
            'product_variant',
            'product_variant__product'
        ).prefetch_related(
            'product_variant__images'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_items = []

        for cart_item in self.get_queryset():
            variant = cart_item.product_variant
            product = variant.product

            image_obj = variant.images.filter(is_primary=True).first()
            if not image_obj:
                image_obj = variant.images.first()
            image_url = image_obj.image_url if image_obj else "https://via.placeholder.com/150?text=No+Image"

            cart_items.append({
                'id': cart_item.id,
                'product_name': product.name,
                'color': variant.color,
                'size': variant.size,
                'price': float(variant.final_price),
                'quantity': cart_item.quantity,
                'image_url': image_url,
                'in_stock': variant.is_in_stock,
            })

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
                        'error': 'Max quantity reached or insufficient stock.'
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
