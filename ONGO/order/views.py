from django.shortcuts import render, redirect
from django.contrib import messages
# from django.views.generic import ListView
from cart.models import Cart
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.decorators.cache import never_cache

from django.utils.decorators import method_decorator

from django.views import View

# from django.http import JsonResponse
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
            messages.success(request, message)
            return redirect('checkout_information')
        else:
            messages.error(request, message)
    return render(request, 'accounts/partials/add_address_form.html')
