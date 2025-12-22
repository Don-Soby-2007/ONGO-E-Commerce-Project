from django.urls import path
from . import views

urlpatterns = [
    path('', views.homeView, name='home'),
    path("product-listing", views.ProductListView.as_view(), name="product_list")

]
