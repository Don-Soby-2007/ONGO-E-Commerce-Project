from django.urls import path
from . import views

urlpatterns = [
    path('', views.CartView.as_view(), name="cart"),
    path('update-quantity/', views.QtyChangeView.as_view(), name="add_quantity"),
    path('remove/<int:pk>', views.DeleteCartView, name="delete_cart"),

    path('coupons/list/', views.ListCouponsView.as_view(), name='list_coupons'),
    path('coupons/apply/', views.ApplyCouponView.as_view(), name='apply_coupon'),
    path('coupons/remove/', views.remove_coupon, name='remove_coupon'),
]
