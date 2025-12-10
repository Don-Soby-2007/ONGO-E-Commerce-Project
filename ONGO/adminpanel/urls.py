from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.AdminLoginView.as_view(), name='admin_login'),
    path('customers/', views.AdminCustomersView.as_view(), name='customers'),
    path('customers/delete-user/<int:user_id>/', views.delete_user_view, name='delete_user'),
    path('admin-logout/', views.admin_logout, name='admin_logout')
]
