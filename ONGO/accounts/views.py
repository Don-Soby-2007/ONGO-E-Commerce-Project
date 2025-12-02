from django.shortcuts import render
# Create your views here.


def admin_login_view(request):
    return render(request, 'accounts/admin-login.html')


def admin_dashboard_view(request):
    return render(request, 'accounts/admin-dashboard.html')


def user_login_view(request):
    return render(request, 'accounts/user-login.html')


def user_signup_view(request):
    return render(request, 'accounts/user-sigup.html')
