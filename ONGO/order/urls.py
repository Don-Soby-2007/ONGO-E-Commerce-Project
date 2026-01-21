from django.urls import path
from . import views

urlpatterns = [
    path('information/', views.OrderInformation.as_view(), name='checkout_information'),
    path('payment-methode/', views.paymentMethode, name='payment_methode')
]
