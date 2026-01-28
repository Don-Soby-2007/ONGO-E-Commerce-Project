# from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
# from django.views.decorators.cache import never_cache

# from django.utils.decorators import method_decorator

from django.views import View

# from django.shortcuts import get_object_or_404

# from django.http import JsonResponse, FileResponse, Http404

# from order.models import Order, OrderItem
# Create your views here.


class ReturnOrderView(LoginRequiredMixin, View):

    def post(self, request, order_id):
        pass
