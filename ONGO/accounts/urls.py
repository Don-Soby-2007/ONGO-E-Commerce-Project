from django.urls import path
from . import views

urlpatterns = [
    path('admin/login/', views.admin_login_view, name='admin_login'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),

    path('', views.user_login_view, name='user_login'),
    path('signup/', views.user_signup_view, name='user_signup'),
]
