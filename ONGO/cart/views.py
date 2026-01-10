from django.shortcuts import render

# Create your views here.


def cartview(request):
    return render(request, 'cart/cart.html')
