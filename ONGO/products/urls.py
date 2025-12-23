from django.urls import path
from . import views

urlpatterns = [
    path('', views.LandingView, name='landing'),
    path('home', views.HomeView, name='home'),
    path("product-listing", views.ProductListView.as_view(), name="product_list"),
    path("product-detail", views.ProductDetailView, name='product_detail'),

]
