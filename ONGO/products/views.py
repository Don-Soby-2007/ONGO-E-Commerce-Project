from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.db.models import Q
from django_extensions import settings

from adminpanel.models import Banner
from .models import Product, ProductVariant, ProductImage, Category
from cart.models import Cart
from accounts.models import Wishlist
from offers.models import ProductOffer, CategoryOffer
from order.models import ProductReview, Order

from django.contrib.auth.models import AnonymousUser

from django.db.models import Prefetch, Min, Case, When, DecimalField, Avg, Count
from django.db.models.functions import Coalesce
from django.db import transaction
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required

from django.contrib.auth.mixins import LoginRequiredMixin

from django.core.exceptions import ValidationError

from django.views import View

from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from decimal import Decimal

from .utils import calculate_discount

# from django.shortcuts import get_object_or_404

from django.core.mail import EmailMultiAlternatives
import re
import logging
import json
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)

# Create your views here.


def get_homepage_context(request):
    base_qs = Product.objects.filter(is_active=True, category__is_active=True).select_related('category')

    now = timezone.now()
    active_offer_filter = (
        Q(active=True) &
        Q(start_date__lte=now) &
        (Q(end_date__isnull=True) | Q(end_date__gte=now))
    )

    products_qs = base_qs.prefetch_related(
        Prefetch(
            'variants',
            queryset=ProductVariant.objects.prefetch_related(
                Prefetch(
                    'images',
                    queryset=ProductImage.objects.order_by('-is_primary', '-created_at')
                )
            )
        ),
        Prefetch(
            'offer',
            queryset=ProductOffer.objects.filter(active_offer_filter).order_by('-priority'),
            to_attr='prefetched_product_offers'
        ),
        Prefetch(
            'category__offer',
            queryset=CategoryOffer.objects.filter(active_offer_filter).order_by('-priority'),
            to_attr='prefetched_category_offers'
        )
    )

    new_arrivals_qs = products_qs.order_by('-created_at')[:8]
    trending_products_qs = products_qs.annotate(
        review_count=Count('reviews')
        ).order_by('-review_count', '-created_at')[:8]
    categories = Category.objects.filter(is_active=True)[:6]

    new_arrivals = list(new_arrivals_qs)
    trending_products = list(trending_products_qs)

    def attach_offer_and_wishlist(products):
        rep_variant_ids = []
        product_rep_map = {}

        for product in products:
            rep_variant = product.variants.first()
            if rep_variant:
                rep_variant_ids.append(rep_variant.id)
                product_rep_map[product.id] = rep_variant.id
            else:
                product_rep_map[product.id] = None

        for product in products:
            rep_id = product_rep_map[product.id]
            product.rep_variant_id = rep_id

            if not rep_id:
                product.offer_price = None
                product.offer_type = None
                product.offer_value = None
                product.primary_image = None
                product.base_price = None
                continue

            rep_variant = next((v for v in product.variants.all() if v.id == rep_id), None)

            if rep_variant and rep_variant.images.all():
                product.primary_image = rep_variant.images.all()[0].image_url
            else:
                product.primary_image = None

            base_price = Decimal(rep_variant.final_price) if rep_variant else Decimal('0.00')
            product.base_price = base_price
            best_discount = {'price': base_price, 'type': None, 'value': None}

            if product.prefetched_product_offers:
                offer = product.prefetched_product_offers[0]
                discounted = calculate_discount(base_price, offer)
                if discounted < best_discount['price']:
                    best_discount = {
                        'price': discounted,
                        'type': offer.discount_type,
                        'value': offer.value
                    }

            cat_offers = getattr(product.category, 'prefetched_category_offers', [])
            if cat_offers:
                offer = cat_offers[0]
                discounted = calculate_discount(base_price, offer)
                if discounted < best_discount['price']:
                    best_discount = {
                        'price': discounted,
                        'type': offer.discount_type,
                        'value': offer.value
                    }

            product.offer_price = best_discount['price'] if best_discount['price'] < base_price else None
            product.offer_type = best_discount['type']
            product.offer_value = best_discount['value']

    attach_offer_and_wishlist(new_arrivals)
    attach_offer_and_wishlist(trending_products)

    banners = Banner.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()).order_by('priority')

    return {
        'new_arrivals': new_arrivals,
        'trending_products': trending_products,
        'categories': categories,
        'banners': banners,
    }


@login_required
@never_cache
def HomeView(request):
    if request.user.is_authenticated and request.user.is_staff is False:
        context = get_homepage_context(request)
        return render(request, 'products/home.html', context)

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
            .prefetch_related(
                Prefetch(
                    'variants__images',
                    queryset=ProductImage.objects.order_by('-is_primary', '-created_at')
                )
            )
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

        now = timezone.now()
        active_offer_filter = (
            Q(active=True) &
            Q(start_date__lte=now) &
            (Q(end_date__isnull=True) | Q(end_date__gte=now))
        )

        queryset = queryset.prefetch_related(
            Prefetch(
                'offer',
                queryset=ProductOffer.objects.filter(active_offer_filter).order_by('-priority'),
                to_attr='prefetched_product_offers'
            ),
            Prefetch(
                'category__offer',
                queryset=CategoryOffer.objects.filter(active_offer_filter).order_by('-priority'),
                to_attr='prefetched_category_offers'
            )
        )

        return queryset.order_by(*ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        products = context['products']

        rep_variant_ids = []
        product_rep_map = {}

        for product in products:
            rep_variant = product.get_representative_variant()
            if rep_variant:
                rep_variant_ids.append(rep_variant.id)
                product_rep_map[product.id] = rep_variant.id
            else:
                product_rep_map[product.id] = None

        wishlist_variant_ids = set()
        if self.request.user.is_authenticated:
            wishlist_variant_ids = set(
                Wishlist.objects.filter(
                    user=self.request.user,
                    product_variant_id__in=rep_variant_ids
                ).values_list('product_variant_id', flat=True)
            )

        for product in products:
            rep_id = product_rep_map[product.id]
            product.rep_variant_id = rep_id
            product.in_wishlist = (rep_id in wishlist_variant_ids)

            if not rep_id:
                product.offer_price = None
                product.offer_type = None
                product.offer_value = None
                continue

            rep_variant = product.get_representative_variant()
            base_price = Decimal(rep_variant.final_price)
            best_discount = {'price': base_price, 'type': None, 'value': None}

            if product.prefetched_product_offers:
                offer = product.prefetched_product_offers[0]
                discounted = calculate_discount(base_price, offer)
                if discounted < best_discount['price']:
                    best_discount = {
                        'price': discounted,
                        'type': offer.discount_type,
                        'value': offer.value
                    }

            cat_offers = getattr(product.category, 'prefetched_category_offers', [])
            if cat_offers:
                offer = cat_offers[0]
                discounted = calculate_discount(base_price, offer)
                if discounted < best_discount['price']:
                    best_discount = {
                        'price': discounted,
                        'type': offer.discount_type,
                        'value': offer.value
                    }

            reviews = ProductReview.objects.filter(product=product).aggregate(avg_rating=Avg('star'),
                                                                              total_reviews=Count('id'))
            product.avg_rating_rounded = round(reviews['avg_rating']) if reviews['avg_rating'] else 0
            product.total_reviews = reviews['total_reviews']

            product.offer_price = best_discount['price']
            product.offer_type = best_discount['type']
            product.offer_value = best_discount['value']

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
    context = get_homepage_context(request)
    return render(request, 'products/landing.html', context)


class ProductDetailView(DetailView):
    model = Product
    template_name = "products/product-detail.html"
    context_object_name = 'product'
    pk_url_kwarg = 'pro_id'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        pro_id = self.kwargs.get(self.pk_url_kwarg)

        try:
            obj = queryset.get(pro_id=pro_id)  # Restore to pro_id field
        except Product.DoesNotExist:
            raise Http404('No Product matches the given query.')

        return obj

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        category = product.category
        request = self.request
        user = request.user if request else AnonymousUser()
        product_offer = (
                product.offer
                .filter(active=True)
                .order_by('-priority')
                .first()
            )
        category_offer = (
                category.offer
                .filter(active=True)
                .order_by('-priority')
                .first()
            )

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

        user_wishlist_variant_ids = set()
        if user.is_authenticated:
            user_wishlist_variant_ids = set(
                Wishlist.objects.filter(user=user, product_variant__product=product)
                .values_list('product_variant_id', flat=True)
            )

        # Build raw data structures (no UX decisions)
        variants_by_color = {}
        images_by_color = {}
        wishlist_status = {}  # Track wishlist per variant

        for variant in variants:
            color = variant.color

            # for offers
            variant_price = float(variant.final_price) if variant.final_price else None
            offer_price = variant_price
            offer_type = None
            offer_value = None
            has_offer = False
            original_price = variant_price

            if product_offer and product_offer.is_active_now():
                offer_type = product_offer.discount_type
                offer_value = float(product_offer.value)
                has_offer = True

                if offer_type == 'percent':
                    offer_price = variant_price * (1 - offer_value / 100)
                elif offer_type == 'fixed':
                    offer_price = max(0, variant_price - offer_value)

            if category_offer and category_offer.is_active_now():
                category_offer_price = None
                cat_offer_type = category_offer.discount_type
                cat_offer_value = float(category_offer.value)

                if cat_offer_type == 'percent':
                    category_offer_price = variant_price * (1 - cat_offer_value / 100)

                if category_offer_price < offer_price:
                    offer_price = category_offer_price

                    offer_type = category_offer.discount_type
                    offer_value = float(cat_offer_value)
                    has_offer = True

            in_wishlist = variant.id in user_wishlist_variant_ids
            wishlist_status[variant.id] = in_wishlist

            # Raw variant data (truth only)
            if color not in variants_by_color:
                variants_by_color[color] = []

            variants_by_color[color].append({
                'id': variant.id,
                'size': variant.size,
                'stock': variant.stock,
                'price': round(offer_price) if offer_price else None,
                'original_price': round(original_price, 2) if original_price else None,
                'offer_type': offer_type,
                'offer_value': offer_value,
                'in_wishlist': in_wishlist,
                'has_offer': has_offer,
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
            'wishlist_status_json': wishlist_status,
            'display_price': product.get_display_price(),
        })

        # Review section
        reviews_queryset = (
            ProductReview.objects
            .filter(product=product)
            .select_related('user')
            .order_by('-created_at')
        )
        reviews_to_show = reviews_queryset[:3]

        review_summary = reviews_queryset.aggregate(
            total_reviews=Count('id'),
            average_rating=Avg('star'),
        )
        total_reviews = review_summary['total_reviews'] or 0
        average_rating = float(review_summary['average_rating'] or 0)

        rating_distribution = {
            'five_star': 0,
            'four_star': 0,
            'three_star': 0,
            'two_star': 0,
            'one_star': 0,
        }
        star_key_map = {5: 'five_star', 4: 'four_star', 3: 'three_star', 2: 'two_star', 1: 'one_star'}
        for item in reviews_queryset.values('star').annotate(count=Count('id')):
            key = star_key_map.get(item['star'])
            if key:
                rating_distribution[key] += item['count']

        rating_percentages = {
            key: round((value / total_reviews) * 100) if total_reviews else 0
            for key, value in rating_distribution.items()
        }
        review_chart_data = [
            rating_distribution['five_star'],
            rating_distribution['four_star'],
            rating_distribution['three_star'],
            rating_distribution['two_star'],
            rating_distribution['one_star'],
        ]

        context['reviews'] = reviews_to_show
        context['avg_reviews'] = average_rating
        context['avg_rating_rounded'] = round(average_rating)
        context['total_reviews'] = total_reviews
        context['review_stats'] = rating_distribution
        context['review_percentages'] = rating_percentages
        context['review_chart_data'] = review_chart_data
        context['stat_of_reviews'] = rating_distribution
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

            try:
                deleted_count, _ = Wishlist.objects.filter(
                    user=request.user,
                    product_variant_id=variant_id
                ).delete()
            except Exception as e:
                logger.exception(
                    f"Failed to remove variant {variant_id} from wishlist for user {request.user.id} : {e}")
                raise

            cart_item, created = Cart.objects.get_or_create(
                user=request.user,
                product_variant=variant,
            )

            new_quantity = qty if created else cart_item.quantity + qty

            if new_quantity > variant.stock:
                return JsonResponse({
                    'success': False,
                    'message': 'Insuffcient stock, Please try again'
                })

            if qty < 1 or qty > 5:
                return JsonResponse({
                    'success': False,
                    'message': 'Quantity must be between 1 and 5.'
                })

            if new_quantity > 5:
                return JsonResponse({
                    'success': False,
                    'message': 'Maximum 5 items allowed per product in cart.'
                })

            cart_item.quantity = new_quantity
            cart_item.save()

            message = 'Product added to cart.' if created else f'{qty} more added to cart.'
            return JsonResponse({'success': True, 'message': message})

        except ProductVariant.DoesNotExist:
            logger.error(request, f'User tries to use non-existent variant in add to cart : {request.user}')
            return JsonResponse({'success': False, 'message': 'Invalid product'})

        except Exception as e:
            logger.error(request, f'Unexpected error occured when adding to cart: {e}')
            return JsonResponse({'success': False, 'message': 'Error adding to cart'})


class ToggleWishlistView(LoginRequiredMixin, View):

    def post(self, request, variant_id):
        try:
            variant_id = int(variant_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid variant ID format '{variant_id}' from user {request.user.id}")
            return JsonResponse({
                'success': False,
                'message': 'Invalid product identifier'
            }, status=400)

        try:
            variant = ProductVariant.objects.select_related('product').get(
                id=variant_id,
                product__is_active=True
            )
        except ProductVariant.DoesNotExist:
            logger.warning(
                f"User {request.user.id} attempted wishlist operation on "
                f"non-existent/inactive variant ID {variant_id}"
            )
            raise Http404("Product variant not found")

        try:
            cart = Cart.objects.filter(user=request.user, product_variant=variant)
            if cart:

                logger.warning(
                    f"On wishlist toggle Variant is allredy present in cart for user {request.user.id}, "
                    f"variant {variant_id}"
                )
                return JsonResponse({
                        'success': False,
                        'message': 'Product is already in Cart'
                    })

            with transaction.atomic():
                deleted_count, _ = Wishlist.objects.filter(
                    user=request.user,
                    product_variant=variant
                ).delete()

                if deleted_count:
                    action = 'removed'
                    message = 'Removed from wishlist'
                else:
                    wishlist_item = Wishlist(user=request.user, product_variant=variant)
                    wishlist_item.full_clean()
                    wishlist_item.save()
                    action = 'added'
                    message = 'Added to wishlist'

                wishlist_count = Wishlist.objects.filter(user=request.user).count()

        except ValidationError as e:
            logger.warning(
                f"Validation error during wishlist toggle for user {request.user.id}, "
                f"variant {variant_id}: {e}"
            )
            return JsonResponse({
                'success': False,
                'message': 'Invalid wishlist item data'
            }, status=400)
        except Exception as e:
            logger.exception(
                f"Unexpected error toggling wishlist for user {request.user.id}, "
                f"variant {variant_id}: {str(e)}"
            )
            return JsonResponse({
                'success': False,
                'message': 'Failed to update wishlist. Please try again.'
            }, status=500)

        return JsonResponse({
            'success': True,
            'action': action,
            'wishlist_count': wishlist_count,
            'message': message,
            'variant_id': variant_id
        })


def legal_view(request):
    return render(request, 'products/legal.html')


def about_view(request):
    return render(request, 'products/about.html')


class ContactView(View):
    def post(self, requesst):
        name = requesst.POST.get('name')
        email = requesst.POST.get('email')
        subject = requesst.POST.get('subject')
        message = requesst.POST.get('message')
        order_id = requesst.POST.get('order_id')
        attachments = requesst.FILES.getlist('attachments')

        if not all([name, email, subject, message]):
            return JsonResponse({'success': False, 'message': 'All fields are required.'}, status=400)

        if re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email) is None:
            return JsonResponse({'success': False, 'message': 'Invalid email format.'}, status=400)

        if len(message.strip()) < 50:
            return JsonResponse({'success': False, 'message': 'Message must be at least 50 characters long.'},
                                status=400)

        if order_id:
            try:
                _ = Order.objects.get(order_id=order_id, user=requesst.user).exist()
            except Order.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid order ID.'}, status=400)

        if attachments:
            if len(attachments) > 3:
                return JsonResponse({'success': False, 'message': 'You can upload a maximum of 3 attachments.'},
                                    status=400)
            for file in attachments:
                if file.size > 5 * 1024 * 1024:
                    return JsonResponse({'success': False, 'message': 'Each attachment must be under 5MB.'}, status=400)

                if file.content_type not in ['image/jpeg', 'image/png', 'image/svg']:
                    return JsonResponse({'success': False, 'message': 'Only JPEG, PNG and SVG files are allowed.'},
                                        status=400)

        subjects = f"Contacted Support Issue: {subject}"
        from_email = os.getenv("EMAIL_HOST_USER")
        to_email = ['info.ongo.styles@gmail.com']

        text_content = f"""
        Name: {name}
        Email: {email}
        Order ID: {order_id or 'N/A'}
        Category: {subject}

        Message:
        {message}"""

        msg = EmailMultiAlternatives(subjects, text_content, from_email, to_email)

        for f in attachments:
            msg.attach(f.name, f.read(), f.content_type)

        try:
            msg.send()
            return JsonResponse({
                'success': True,
                'message': 'Your message has been sent successfully!'
            }, status=200)

        except Exception as e:
            logger.exception("Failed to send contact email from user : " +
                             f"{requesst.user.id if requesst.user.is_authenticated else 'Anonymous'}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Failed to send email. Please try again later.',
                'error': str(e) if settings.DEBUG else None  # Hide details in production
            }, status=500)


class ReviewListView(LoginRequiredMixin, ListView):
    model = ProductReview
    template_name = "products/review_list.html"
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        product_id = self.kwargs.get('pro_id')
        product = get_object_or_404(Product, pro_id=product_id, is_active=True)
        return ProductReview.objects.filter(product=product).select_related('user').order_by('-created_at')
