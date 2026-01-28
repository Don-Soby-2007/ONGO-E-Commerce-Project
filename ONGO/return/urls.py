from django.urls import path
from . import views

urlpatterns = [
    path('order/<uuid:order_id>', views.ReturnOrderView.as_view(), name='return_order'),
]
