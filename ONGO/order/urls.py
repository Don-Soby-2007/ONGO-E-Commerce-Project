from django.urls import path
from . import views

urlpatterns = [
    path('information/', views.CheckoutInformation.as_view(), name='checkout_information'),
    path('apply-coupon/', views.ApplyCouponView.as_view(), name='apply_coupon'),
    path('add-address/', views.add_address_in_checkout, name='add_address_in_checkout'),

    path('payment-methode/', views.PaymentMethode.as_view(), name='payment_methode'),

    path('order-confiramtion/', views.OrderConfirmation.as_view(), name='order_confirmation'),

    path('place-order/', views.PlaceOrder.as_view(), name='place_order'),

    path('order-success/', views.OrderSuccess.as_view(), name='order-success'),
    path('order-failed/', views.orderFailed, name='order-failed'),
    path('invoice/<uuid:order_id>/', views.download_invoice, name='download_invoice'),
]
