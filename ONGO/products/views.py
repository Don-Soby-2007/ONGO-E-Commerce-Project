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

        # 🔁 Fetch & process data
        try:
            variants = product.variants.filter(
                stock__gte=0
            ).prefetch_related(
                Prefetch(
                    'images',
                    queryset=ProductImage.objects.order_by('-is_primary', '-created_at'),
                    to_attr='image_list'  # efficient access
                )
            )

            # --- Build data structures ---
            color_variants = {}      # for Django template loops (full objects)
            js_variants = {}         # for JS: only primitives
            images_by_color = {}     # for Django & JS (URLs only)

            for variant in variants:
                color = variant.color

                # 1. Group full variants (for {% for %} in template)
                color_variants.setdefault(color, []).append(variant)

                # 2. Build JS-safe variant data (id, size, stock)
                if color not in js_variants:
                    js_variants[color] = []
                js_variants[color].append({
                    'id': variant.id,
                    'size': variant.size,
                    'stock': variant.stock,
                    # Add more if needed: 'price': float(variant.price), etc.
                })

                # 3. Collect image URLs (deduplicated)
                if color not in images_by_color:
                    images_by_color[color] = set()
                for img in variant.image_list:
                    images_by_color[color].add(img.image_url)

            # Convert sets → lists (preserve primary-first order if needed)
            for color in images_by_color:
                # Optional: sort to put is_primary first — but we already ordered in DB
                images_by_color[color] = list(images_by_color[color])

            # Default selection
            default_color = next(iter(color_variants), None)
            default_images = images_by_color.get(default_color, [
                "https://via.placeholder.com/400x500?text=No+Image  "
            ])

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error building product detail context for pk={product.pk}: {e}", exc_info=True)
            js_variants = {}
            images_by_color = {}
            default_color = None
            default_images = ["https://via.placeholder.com/400x500?text=Error  "]

        # ✅ Inject into context
        context.update({
            # For Django template loops (we'll reconstruct minimal variant data)
            'color_variants': self._build_template_variants(js_variants),
            # For JavaScript
            'variants_by_color_json': js_variants,
            'images_by_color': images_by_color,
            'default_color': default_color,
            'default_images': default_images,
            'display_price': product.get_display_price(),
        })

        return context

    def _build_template_variants(self, js_variants):
        """
        Reconstruct minimal variant-like objects for template rendering.
        Returns dict: {color: [{'size': ..., 'is_in_stock': ...}, ...]}
        """
        if js_variants is None:
            return {}

        template_variants = {}
        for color, variants in js_variants.items():
            template_variants[color] = [
                {
                    'size': v['size'],
                    'is_in_stock': v['stock'] > 0,
                    'id': v['id'],
                    'stock': v['stock'],
                }
                for v in variants
            ]
        return template_variants
