from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from .models import Product, ProductVariant, ProductImage, Category
from cart.models import Cart
from django.db.models import Prefetch, Min, Case, When, DecimalField
from django.db.models.functions import Coalesce
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required

from django.contrib.auth.mixins import LoginRequiredMixin

from django.views import View

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import logging
import json

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
        queryset = (
            Product.objects
            .filter(is_active=True, category__is_active=True)
            .select_related('category')
            .prefetch_related('variants__images')
        )

        # Search Query
        q = self.request.GET.get('q')

        if q:
            queryset = queryset.filter(name__icontains=q)

        # Dynamic Category View
        category_name = self.request.GET.getlist('category')  # e.g. ['men', 'women']
        if category_name:
            queryset = queryset.filter(category__name__in=category_name)

        # ===== 2. PRICE FILTER =====
        min_price = self.request.GET.get('min')
        max_price = self.request.GET.get('max')

        queryset = queryset.annotate(
            display_price=Min(
                Case(
                    When(
                        variants__stock__gt=0,
                        then=Coalesce('variants__sale_price', 'variants__price')
                    ),
                    output_field=DecimalField()
                )
            )
        )

        if min_price:
            try:
                queryset = queryset.filter(display_price__gte=float(min_price))
            except (ValueError, TypeError):
                pass

        if max_price:
            try:
                queryset = queryset.filter(display_price__lte=float(max_price))
            except (ValueError, TypeError):
                pass

        # ===== 3. SORTING =====
        sort = self.request.GET.get('sort', 'latest')
        ordering = {
            'oldest': ['created_at'],
            'l-h': ['display_price', '-created_at'],
            'h-l': ['-display_price', '-created_at'],
            'a-z': ['name'],
            'z-a': ['-name'],
        }.get(sort, ['-created_at'])

        return queryset.order_by(*ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['categories'] = Category.objects.filter(is_active=True).order_by('name')

        # Preserve filters for pagination
        get_params = self.request.GET.copy()
        get_params.pop('page', None)
        context['filter_params'] = get_params.urlencode()

        # Current active filters (for UI state)
        context['selected_categories'] = self.request.GET.getlist('category')

        return context


# Landing Page
def LandingView(request):
    if request.user.is_authenticated:
        return redirect('home')
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


@method_decorator(csrf_exempt, name='dispatch')
class AddToCartView(LoginRequiredMixin, View):
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Login required'}, status=403)

        try:
            data = json.loads(request.body)
            variant_id = data['product_variant_id']
            qty = data['quantity']

            variant = ProductVariant.objects.get(id=variant_id, product__is_active=True)

            # ✅ Critical: Re-check live stock
            if qty > variant.stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Only {variant.stock} items left in stock.'
                })

            if qty < 1 or qty > 5:
                return JsonResponse({
                    'success': False,
                    'message': 'Quantity must be between 1 and 5.'
                })

            # Update or create cart item
            cart_item, created = Cart.objects.update_or_create(
                user=request.user,
                product_variant=variant,
                defaults={'quantity': qty}
            )

            return JsonResponse({'success': True, 'message': ''})

        except ProductVariant.DoesNotExist:
            logger.error(request, f'User tries to use non-existent variant in add to cart : {request.user}')
            return JsonResponse({'success': False, 'message': 'Invalid product'})

        except Exception as e:
            logger.error(request, f'Unexpected error occured when adding to cart: {e}')
            return JsonResponse({'success': False, 'message': 'Error adding to cart'})
