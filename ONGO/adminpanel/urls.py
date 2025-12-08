from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.AdminLoginView.as_view(), name='admin_login'),
    path('customers/', views.admin_customer_view, name='customers'),
    path('admin-logout/', views.admin_logout, name='admin_logout')
]
