from django.urls import path
from . import views

urlpatterns = [
    path('information/', views.orderInformation, name='checkout_information'),
    path('payment-methode/', views.paymentMethode, name='payment_methode')
]
