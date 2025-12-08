from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.views import View
from django.contrib.auth import authenticate, login, logout
from accounts.models import User

from django.db import DatabaseError

import logging

logger = logging.getLogger(__name__)

# Create your views here.


@method_decorator(never_cache, name='dispatch')
class AdminLoginView(View):
    template_name = 'adminpanel/admin-login.html'

    def get(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('customers')
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email').strip()
        password = request.POST.get('password').strip()

        try:
            import re

            if re.match(r'', email) is False:
                messages.error(request, "Enter a valid email")
                return render(request, self.template_name)

            if re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password) is False:
                messages.error(request, "Password is wrong. Please Enter a valid Password")
                return render(request, self.template_name)

            user = authenticate(request, email=email, password=password)

            if user is None:
                raise User.DoesNotExist

            user_obj = User.objects.get(email=email)

            if user_obj.is_active and user_obj.is_staff:
                login(request, user)
                return redirect('customers')
            else:
                return render(request, self.template_name)

        except User.DoesNotExist:
            messages.error(request, "User doesn't exist please SignUp or check your details")
            logger.warning(f'Error when un-exist user tries to login user: {user}')
            return render(request, self.template_name)

        except DatabaseError as d:
            messages.error(request, "Database gone wrong. Please try again")
            logger.warning(f'Database error during user login {user}: {d}')
            return render(request, self.template_name)

        except Exception as e:
            messages.error(request, "Something went wrong. Please try again")
            logger.warning(f'Something went wrong during user login {user} : {e}')
            return render(request, self.template_name)


@never_cache
def admin_customer_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return render(request, 'adminpanel/customers_panel.html')

    return redirect('admin_login')


@never_cache
def admin_logout(request):
    if request.user.is_authenticated and request.user.is_staff:
        logout(request)
        return redirect('admin_login')
