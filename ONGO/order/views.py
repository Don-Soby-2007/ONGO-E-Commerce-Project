# from django.shortcuts import redirect
from django.shortcuts import render, redirect
# from django.views.generic import ListView
# from .models import Cart
# from django.contrib.auth.mixins import LoginRequiredMixin

# from django.views.decorators.cache import never_cache

# from django.utils.decorators import method_decorator

# from django.views import View

# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required

# import json

import logging


# Create your views here.

logger = logging.getLogger(__name__)


@login_required
def orderInformation(request):

    if not request.user.is_authenticated:
        return redirect('login')

    return render(request, 'checkout/information.html')
