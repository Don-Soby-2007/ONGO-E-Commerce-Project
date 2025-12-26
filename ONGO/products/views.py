from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from .models import Product, ProductImage
from django.db.models import Prefetch
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required


import logging

logger = logging.getLogger(__name__)

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


# Landing Page
def LandingView(request):
    return render(request, 'products/landing.html')


class ProductDetailView(DetailView):
    model = Product
    template_name = "products/product-detail.html"
    context_object_name = 'product'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # Fetch all variants with images
        variants = product.variants.filter(
            stock__gte=0
        ).prefetch_related(
            Prefetch(
                'images',
                queryset=ProductImage.objects.order_by('-is_primary', '-created_at'),
                to_attr='prefetched_images'
            )
        )

        # Build raw data structures (no UX decisions)
        variants_by_color = {}
        images_by_color = {}

        for variant in variants:
            color = variant.color

            # Raw variant data (truth only)
            if color not in variants_by_color:
                variants_by_color[color] = []
            variants_by_color[color].append({
                'id': variant.id,
                'size': variant.size,
                'stock': variant.stock,
                'price': float(variant.price) if variant.price else None,
            })

            # All images for each color
            if color not in images_by_color:
                images_by_color[color] = set()
            for img in variant.prefetched_images:
                images_by_color[color].add(img.image_url)

        # Convert sets to lists
        for color in images_by_color:
            images_by_color[color] = list(images_by_color[color])

        # Context with raw data
        context.update({
            'product': product,
            'variants_by_color_json': variants_by_color,
            'images_by_color_json': images_by_color,
            'all_colors': list(variants_by_color.keys()),
            'display_price': product.get_display_price(),
        })

        return context
