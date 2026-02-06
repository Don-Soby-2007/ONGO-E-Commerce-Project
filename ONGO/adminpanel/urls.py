from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.AdminLoginView.as_view(), name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),

    path('customers/', views.AdminCustomersView.as_view(), name='customers'),
    path('customer/toggle/<int:user_id>/', views.ToggleUserStatusView.as_view(), name='delete_user'),

    path('categories/', views.AdminCategoryView.as_view(), name='categories'),
    path('categories/add', views.AddCategoryView.as_view(), name='add_category'),
    path('categories/edit/<int:category_id>/', views.EditCategoryView.as_view(), name='edit_category'),
    path('category/toggle/<int:category_id>/', views.ToggleCategoryStatusView.as_view(), name='delete_category'),

    path('products/', views.AdminProductsView.as_view(), name='products'),
    path('products/add', views.ProductCreateView.as_view(), name='add_product'),
    path('product/edit/<int:pk>', views.ProductEditView.as_view(), name='edit_product'),
    path('product/toggle/<int:product_id>/', views.ToggleProductStatusView.as_view(), name='delete_product'),

    path('orders/', views.AdminOrderListView.as_view(), name='admin_orders'),
    path('orders/<uuid:order_id>/', views.AdminOrderDetailView.as_view(), name='admin_order_detail'),
    path('orders/status/<uuid:order_id>/', views.ToggleOrderStatusView.as_view(), name='toggle_order_status'),
    path('orders/<uuid:order_id>/<int:item_id>',
         views.ToggleOrderItemStatusView.as_view(),
         name='toggle_orderitem_status'),

    path('returns/', views.ReturnListView.as_view(), name='returns_list'),
    path('returns/<int:return_id>', views.ReturnDetailView.as_view(), name='returs_detail'),
    path('returns/<int:return_id>/action', views.ReturnStatusToggleView.as_view(), name='returns_status_toggle'),

    # offers

    path('offers/', views.ProductOfferList.as_view(), name='produc_offer_list'),
    path('offers/category-offers/', views.CategoryOfferList.as_view(), name='catego_offer_list'),
    path('offers/global-offers/', views.GlobalOfferList.as_view(), name='global_offer_list'),
    path('offers/create', views.ProductOfferCreateView.as_view(), name='produc_offer_create'),
    path('offers/category-offers/create', views.CategoryOfferCreateView.as_view(), name='catego_offer_create'),
    path('offers/global-offers/create', views.GlobalOfferCreateView.as_view(), name='global_offer_create'),

]
