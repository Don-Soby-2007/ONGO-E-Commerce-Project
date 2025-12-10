from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.db.models import Q
from django.views.generic import ListView
from django.contrib.auth import authenticate, login, logout
from accounts.models import User
from django.http import JsonResponse

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


# @method_decorator(never_cache, name='dispatch')
# class AdminCustomersView(ListView):
#     model = User
#     template_name = 'adminpanel/customers_panel.html'
#     context_object_name = 'users'
#     paginate_by = 6

    # def get(self, request):
    #     if request.user.is_authenticated and request.user.is_staff:

    #         user = User.objects.all().filter(is_staff=False)[::-1]

    #         users = {
    #             'users': user
    #         }
    #         return render(request, self.template_name, users)

    #     return redirect('admin_login')


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class AdminCustomersView(ListView):
    model = User
    template_name = 'adminpanel/customers_panel.html'
    context_object_name = 'users'
    paginate_by = 6

    def get_queryset(self):
        queryset = User.objects.all().order_by('-is_active')

        search_query = self.request.GET.get('search_query')
        if search_query:
            queryset = queryset.filter(Q(username__icontains=search_query) | Q(email__icontains=search_query))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search_query', '')
        return context


@login_required(login_url='admin_login')
@never_cache
def delete_user_view(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "You are not authorized to perform this action")
        return redirect('admin_login')

    try:
        # Get user and toggle activation status
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()

        if user.is_active:
            message = f"User '{user.username}' activated successfully."
            logger.info(f"Admin {request.user.username} activated user ID {user_id} ({user.username}).")
        else:
            message = f"User '{user.username}' deactivated successfully."
            logger.info(f"Admin {request.user.username} deactivated user ID {user_id} ({user.username}).")
        return JsonResponse({
            'success': True,
            'message': message,
            'new_status': 'Active' if user.is_active else 'Inactive'
        })

    except User.DoesNotExist:
        logger.warning(f"Admin {request.user.username} tried to toggle non-existent user ID {user_id}")
        return JsonResponse({
                'success': False,
                'message': "User not found."
        }, status=404)

    except DatabaseError as db_err:
        logger.error(f"Database error toggling user ID {user_id}: {db_err}")
        return JsonResponse({
                'success': False,
                'message': "Database error occurred while updating user. Please try again later."
        }, status=500)

    except Exception as e:
        logger.error(f"Unexpected error toggling user {user_id}: {e}")
        return JsonResponse({
                'success': False,
                'message': "An unexpected error occurred while updating the user"
        }, status=500)


@never_cache
def admin_logout(request):
    if request.user.is_authenticated and request.user.is_staff:
        logout(request)
        return redirect('admin_login')
