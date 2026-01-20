from django.shortcuts import render, redirect
from django.contrib import messages
# from django.views.generic import ListView
# from .models import Cart
# from django.contrib.auth.mixins import LoginRequiredMixin

# from django.views.decorators.cache import never_cache

# from django.utils.decorators import method_decorator

# from django.views import View

# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required

from accounts.utils import create_address_from_request

# import json

import logging


# Create your views here.

logger = logging.getLogger(__name__)


@login_required
def orderInformation(request):

    if not request.user.is_authenticated:
        return redirect('login')

    return render(request, 'checkout/information.html')


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
