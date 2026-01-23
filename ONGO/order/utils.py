from cart.models import Cart


def get_cart_items_for_user(user):
    cart_items = []
    cart = Cart.objects.filter(user=user).select_related(
        'product_variant__product'
    ).prefetch_related('product_variant__images')

    for item in cart:
        variant = item.product_variant
        product = variant.product
        image_obj = variant.images.filter(is_primary=True).first() or variant.images.first()
        image_url = image_obj.image_url if image_obj else "https://via.placeholder.com/150?text=No+Image"
        cart_items.append({
            'id': item.id,
            'product_name': product.name,
            'price': float(variant.final_price),
            'quantity': item.quantity,
            'image_url': image_url,
            'size': variant.size,
            'color': variant.color,
            'in_stock': variant.is_in_stock,
        })
    return cart_items
