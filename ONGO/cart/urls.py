from django.urls import path
from . import views

urlpatterns = [
    path('', views.CartView.as_view(), name="cart"),
    path('update-quantity/', views.QtyChangeView.as_view(), name="add_quantity"),
    path('remove/<int:pk>', views.DeleteCartView, name="delete_cart"),

    path('api/coupons/list/', views.ListCouponsView.as_view(), name='list_coupons'),
    path('api/coupons/apply/', views.ApplyCouponView.as_view(), name='apply_coupon'),
    path('api/coupons/remove/', views.remove_coupon, name='remove_coupon'),
]
