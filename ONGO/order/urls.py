from django.urls import path
from . import views

urlpatterns = [
    path('information/', views.CheckoutInformation.as_view(), name='checkout_information'),
    path('add-address/', views.add_address_in_checkout, name='add_address_in_checkout'),

    path('payment-methode/', views.PaymentMethode.as_view(), name='payment_methode'),
]
