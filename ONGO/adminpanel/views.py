from django.shortcuts import render


import logging

logger = logging.getLogger(__name__)

# Create your views here.


def admin_login_view(request):
    return render(request, 'adminpanel/admin-login.html')


def admin_customer_view(request):
    return render(request, 'adminpanel/customers_panel.html')