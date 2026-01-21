from django.shortcuts import render, redirect
from django.contrib import messages
# from django.views.generic import ListView
from cart.models import Cart
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.decorators.cache import never_cache

from django.utils.decorators import method_decorator

from django.views import View

from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required

from accounts.utils import create_address_from_request

# import json

from accounts.models import Address

import logging


# Create your views here.

logger = logging.getLogger(__name__)


@method_decorator(never_cache, name='dispatch')
class OrderInformation(LoginRequiredMixin, View):
    template_name = 'checkout/information.html'

    def get(self, request):

        user = request.user

        address = Address.objects.filter(user=user)

        cart_items = []
        cart = Cart.objects.filter(user=user).select_related(
            'product_variant',
            'product_variant__product'
        ).prefetch_related(
            'product_variant__images'
        )

        for item in cart:
            variant = item.product_variant
            product = variant.product

            image_obj = variant.images.filter(is_primary=True).first()
            if not image_obj:
                image_obj = variant.images.first()
            image_url = image_obj.image_url if image_obj else "https://via.placeholder.com/150?text=No+Image"

            cart_items.append({
                'id': item.id,
                'product_name': product.name,
                'price': float(variant.final_price),
                'quantity': item.quantity,
                'image_url': image_url,
                'in_stock': variant.is_in_stock,
            })

        return render(request, self.template_name, {'addresses': address, 'cart_items': cart_items})


@login_required
def paymentMethode(request):

    if not request.user.is_authenticated:
        return redirect('login')

    return render(request, 'checkout/payment.html')


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
