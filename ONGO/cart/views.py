# from django.shortcuts import redirect
from django.views.generic import ListView
from .models import Cart
from offers.models import GlobalOffer
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

        summary = {}

        items_subtotal = 0
        total_payable = 0
        shipping = 100
        applied_global_offers = []

        from collections import defaultdict
        category_quantities = defaultdict(int)

        for cart_item in self.get_queryset():
            cat_id = cart_item.product_variant.product.category.id
            category_quantities[cat_id] += cart_item.quantity

        for cart_item in self.get_queryset():
            variant = cart_item.product_variant
            product = variant.product

            # for offer calculation
            variant_price = float(variant.final_price) if variant.final_price else None
            offer_price = variant_price
            offer_type = None
            offer_value = None
            offer_scope = None
            has_offer = False
            original_price = variant_price

            product_offer = (
                product.offer
                .filter(active=True)
                .order_by('-priority')
                .first()
            )
            category_offer = (
                    product.category.offer
                    .filter(active=True)
                    .order_by('-priority')
                    .first()
                )

            category_eligible = False
            if category_offer and category_offer.is_active_now():
                required_min = category_offer.min_items
                actual_in_cart = category_quantities.get(product.category.id, 0)
                if actual_in_cart >= required_min:
                    category_eligible = True

            if product_offer and product_offer.is_active_now():
                offer_type = product_offer.discount_type
                offer_value = float(product_offer.value)
                has_offer = True
                offer_scope = 'product'

                if offer_type == 'percent':
                    offer_price = variant_price * (1 - offer_value / 100)
                    offer_price = min(offer_price, product_offer.max_discount_amount)
                elif offer_type == 'fixed':
                    offer_price = max(0, variant_price - offer_value)

            if category_offer and category_offer.is_active_now():

                if category_eligible:
                    category_offer_type = category_offer.discount_type
                    if category_offer_type == 'percent':
                        category_offer_price = variant_price * (1 - offer_value / 100)
                    elif category_offer_type == 'fixed_per_item':
                        category_offer_price = max(0, variant_price - offer_value)

                    if category_offer_price < offer_price:
                        offer_price = category_offer_price

                        offer_type = category_offer_type
                        offer_value = float(category_offer.value)
                        has_offer = True
                        offer_scope = 'category'

            image_obj = variant.images.filter(is_primary=True).first()
            if not image_obj:
                image_obj = variant.images.first()
            image_url = image_obj.image_url if image_obj else "https://via.placeholder.com/150?text=No+Image"

            items_subtotal += round(original_price * cart_item.quantity, 2)
            total_payable += round(offer_price * cart_item.quantity, 2)

            cart_items.append({

                # Identity
                "cart_item_id": cart_item.id,
                "product_id": product.id,
                "variant_id": variant.id,

                # Display
                "product_name": product.name,
                "image_url": image_url,
                "color": variant.color,
                "size": variant.size,

                # Quantity & stock
                "quantity": cart_item.quantity,
                "max_qty_allowed": 5,
                "in_stock": variant.is_in_stock,

                # Pricing (unit-level)
                "unit_price": round(original_price, 2),
                "offer_price": round(offer_price, 2),
                "discount_per_unit": round(original_price - offer_price, 2),

                # Pricing (line-level)
                "line_subtotal": round(original_price * cart_item.quantity, 2),
                "total_discount": round(
                    (original_price - offer_price) * cart_item.quantity, 2
                ),
                "line_total": round(offer_price * cart_item.quantity, 2),

                # Applied offer
                "has_offer": has_offer,
                "applied_offer_scope": offer_scope,  # product / category
                "applied_offer_type": offer_type,  # percent / fixed
                "applied_offer_value": offer_value,
            })

        context['cart_items'] = cart_items

        global_offers = GlobalOffer.objects.filter(min_cart_value__lte=total_payable, active=True).order_by('-priority')

        for offer in global_offers:
            if not offer.is_active_now():
                continue

            offer_value = float(offer.value)

            if offer.discount_type == 'percent':
                discount_amount = round(
                    total_payable * (offer_value / 100), 2
                )

                if offer.max_discount:
                    discount_amount = min(discount_amount, offer.max_discount)

                total_payable -= discount_amount

                applied_global_offers.append({
                    "id": offer.id,
                    "name": f"Cart {offer_value}% OFF",
                    "type": "percent",
                    "value": offer_value,
                    "discount_amount": discount_amount
                })

            elif offer.discount_type == 'fixed':
                discount_amount = min(offer_value, total_payable)

                total_payable -= discount_amount

                applied_global_offers.append({
                    "id": offer.id,
                    "name": f"Cart ₹{offer_value} OFF",
                    "type": "fixed",
                    "value": offer_value,
                    "discount_amount": discount_amount
                })

        for offer in global_offers:
            if offer.discount_type == 'free_shipping' and offer.is_active_now():
                shipping = 0
                applied_global_offers.append({
                    "id": offer.id,
                    "name": "Free Shipping",
                    "type": "free_shipping",
                    "value": 0,
                    "discount_amount": shipping
                })
                break

        summary = {
            "items_subtotal": round(items_subtotal, 2),
            "cart_discount": round(items_subtotal-total_payable, 2),
            "shipping": shipping,
            "tax": 0,
            "total_payable": total_payable,
            "applied_global_offers": applied_global_offers,
        }

        context['summary'] = summary

        # for items in cart_items:
        #     print(items)
        # print('////////////////////////////////////////////////////////////////////////////////////////')
        # print(summary)

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
