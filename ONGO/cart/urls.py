from django.urls import path
from . import views

urlpatterns = [
    path('', views.CartView.as_view(), name="cart"),
    path('update-quantity/', views.QtyChangeView.as_view(), name="add_quantity"),
    path('remove/<int:pk>', views.DeleteCartView, name="delete_cart")
]
