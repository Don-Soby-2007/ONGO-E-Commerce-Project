from django.shortcuts import render

# Create your views here.


def admin_login_view(request):
    return render(request, 'accounts/admin-login.html')
