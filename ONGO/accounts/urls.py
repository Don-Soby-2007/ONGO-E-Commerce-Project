from django.urls import path
from . import views

urlpatterns = [
    path('admin/login', views.admin_login_view, name='admin_login')
]
