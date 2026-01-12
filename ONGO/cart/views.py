from django.shortcuts import render
from django.views.generic import ListView
from .models import Cart
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.decorators.cache import never_cache

from django.utils.decorators import method_decorator
# Create your views here.


@method_decorator(never_cache, name='dispatch')
class CartView(LoginRequiredMixin, ListView):
    template_name = 'cart/cart.html'
    model = Cart
    context_object_name = 'cart_products'

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).select_related(
            'product_variant',
            'product_variant__product'
        ).prefetch_related(
            'product_variant__images'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_items = []

        for cart_item in self.get_queryset():
            variant = cart_item.product_variant
            product = variant.product

            image_obj = variant.images.filter(is_primary=True).first()
            if not image_obj:
                image_obj = variant.images.first()
            image_url = image_obj.image_url if image_obj else "https://via.placeholder.com/150?text=No+Image"

            cart_items.append({
                'id': cart_item.id,
                'product_name': product.name,
                'color': variant.color,
                'size': variant.size,
                'price': float(variant.final_price),
                'quantity': cart_item.quantity,
                'image_url': image_url,
                'in_stock': variant.is_in_stock,
            })

        context['cart_items'] = cart_items
        return context
