from django.shortcuts import render, redirect
from django.views.generic import ListView
from .models import Product
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required

# Create your views here.


@login_required
@never_cache
def HomeView(request):
    if request.user.is_authenticated and request.user.is_staff is False:
        return render(request, 'products/home.html')

    return redirect('login')


class ProductListView(ListView):

    template_name = "products/productlist.html"
    model = Product
    context_object_name = 'products'
    paginate_by = 8

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True, category__is_active=True).prefetch_related("variants__images")
        )


def LandingView(request):
    return render(request, 'products/landing.html')


def ProductDetailView(request):
    return render(request, 'products/product-detail.html')
