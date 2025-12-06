from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login_view, name='admin_login'),
    path('customers/', views.admin_customer_view, name='customers')
]
