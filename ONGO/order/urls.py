from django.urls import path
from . import views

urlpatterns = [
    path('information/', views.orderInformation, name='checkout_information')
]
