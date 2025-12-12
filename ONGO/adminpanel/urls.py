from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.AdminLoginView.as_view(), name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),

    path('customers/', views.AdminCustomersView.as_view(), name='customers'),
    path('customers/delete-user/<int:user_id>/', views.delete_user_view, name='delete_user'),

    path('categories/', views.AdminCategoryView.as_view(), name='categories'),
    path('categories/add', views.AddCategoryView.as_view(), name='add_category'),
    path('category/toggle/<int:category_id>/', views.ToggleUserStatusView.as_view(), name='delete_category')

]
