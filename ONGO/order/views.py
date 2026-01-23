from django.shortcuts import render, redirect
from django.contrib import messages
# from django.views.generic import ListView
from .utils import get_cart_items_for_user
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

        return render(request, self.template_name, {'address': address,
                                                    'cart_items': cart_items,
                                                    'payment_methode': payment_methode})
