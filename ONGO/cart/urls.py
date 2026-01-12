from django.urls import path
from . import views

urlpatterns = [
    path('', views.CartView.as_view(), name="cart"),
    path('update-quantity/', views.QtyAddView.as_view(), name="add_quantity"),
]
