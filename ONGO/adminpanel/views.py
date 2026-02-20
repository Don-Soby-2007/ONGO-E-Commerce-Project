from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.db.models import Q, Count, Case, When, Value, IntegerField, Sum
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from accounts.models import User
from products.models import Category, Product, ProductVariant, ProductImage
from order.models import Order, OrderItem
from returns.models import Return, ReturnItem
from offers.models import ProductOffer, CategoryOffer, GlobalOffer
from coupons.models import Coupon

from django.http import JsonResponse

from django.db import DatabaseError
from django.db import transaction
from django.conf import settings
from django.core.exceptions import ValidationError

from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

import uuid

import re

import logging
from cloudinary.uploader import upload as cloudinary_upload
from cloudinary.uploader import destroy as cloudinary_destroy

logger = logging.getLogger(__name__)

# Create your views here.


@method_decorator(never_cache, name='dispatch')
class AdminLoginView(View):
    template_name = 'adminpanel/admin-login.html'

    def get(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('customers')
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email').strip()
        password = request.POST.get('password').strip()

        try:

            if re.match(r'', email) is False:
                messages.error(request, "Enter a valid email")
                return render(request, self.template_name)

            if re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password) is False:
                messages.error(request, "Password is wrong. Please Enter a valid Password")
                return render(request, self.template_name)

            user = authenticate(request, email=email, password=password)

            if user is None:
                raise User.DoesNotExist

            user_obj = User.objects.get(email=email)

            if user_obj.is_active and user_obj.is_staff:
                login(request, user)
                messages.success(request, 'Admin logined successfully')
                return redirect('customers')
            else:
                return render(request, self.template_name)

        except User.DoesNotExist:
            messages.error(request, "User doesn't exist please SignUp or check your details")
            logger.warning(f'Error when un-exist user tries to login user: {user}')
            return render(request, self.template_name)

        except DatabaseError as d:
            messages.error(request, "Database gone wrong. Please try again")
            logger.warning(f'Database error during user login {user}: {d}')
            return render(request, self.template_name)

        except Exception as e:
            messages.error(request, "Something went wrong. Please try again")
            logger.warning(f'Something went wrong during user login {user} : {e}')
            return render(request, self.template_name)


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class AdminCustomersView(ListView):
    model = User
    template_name = 'adminpanel/customers_panel.html'
    context_object_name = 'users'
    paginate_by = 8

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = User.objects.filter(is_staff=False)

        # SEARCH
        search_query = self.request.GET.get('search_query')
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query)
            )

        # STATUS FILTER
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'blocked':
            queryset = queryset.filter(is_active=False)

        # SORTING
        sort = self.request.GET.get('sort', 'latest')

        if sort == 'oldest':
            queryset = queryset.order_by('date_joined')
        elif sort == 'active_first':
            queryset = queryset.order_by('-is_active')
        else:  # latest
            queryset = queryset.order_by('-date_joined')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search_query', '')
        return context


@never_cache
def admin_logout(request):
    if request.user.is_authenticated and request.user.is_staff:
        logout(request)
        messages.info(request, 'Admin logout successfully')
        return redirect('admin_login')


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class AdminCategoryView(ListView):
    model = Category
    template_name = 'adminpanel/category_panel.html'
    context_object_name = 'category_list'
    paginate_by = 8

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Category.objects.all()

        # SEARCH
        search_query = self.request.GET.get('search_query')
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query))

        # STATUS FILTER
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'blocked':
            queryset = queryset.filter(is_active=False)

        # SORTING
        sort = self.request.GET.get('sort', 'latest')

        if sort == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort == 'active-first':
            queryset = queryset.order_by('-is_active')
        elif sort == 'latest':  # latest
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-updated_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search_query', '')
        return context


@method_decorator(never_cache, name='dispatch')
class AddCategoryView(View, LoginRequiredMixin):

    login_url = 'admin_login'

    template_name = 'adminpanel/add_category.html'

    def get(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            return render(request, self.template_name)
        return redirect('admin_login')

    def post(self, request):
        name = request.POST.get('category_name')
        description = request.POST.get('category_description')
        is_active = 'category_status' in request.POST

        try:

            if len(name) >= 15:
                messages.error(request, 'name is too long')
                return render(request, self.template_name)

            if len(description) > 400:
                messages.error(request, 'description is too long')
                return render(request, self.template_name)

            category = Category.objects.filter(name__iexact=name).first()

            if category:
                messages.error(request, 'category name alredy existed, please give other name')
                return render(request, self.template_name)

            Category.objects.create(name=name, description=description, is_active=is_active)

            messages.success(request, f'New category {name} created successfully')

            return redirect('categories')

        except DatabaseError as d:
            messages.error(request, 'Database error occured. :(')
            logger.error(f'Some thing happend in database side : {d}')
            return redirect('categories')

        except Exception as e:
            messages.error(request, 'Something went wrong during category creation')
            logger.error(f'something went wrong during category creation : {e}')
            return redirect('categories')


@method_decorator(never_cache, name='dispatch')
class ToggleCategoryStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'admin_login'

    def test_func(self):
        # Only admin can toggle categories
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "You are not authorized")
        return redirect('login')

    def post(self, request, category_id):

        try:
            category = Category.objects.get(id=category_id)

            # Toggle status
            category.is_active = not category.is_active
            category.save()

            new_status = "Active" if category.is_active else "Inactive"

            logger.info(
                f"Admin {request.user.username} changed "
                f"category {category.name} to {new_status}"
            )

            return JsonResponse({
                "success": True,
                "message": f"Category '{category.name}' {new_status.lower()} successfully.",
                "new_status": new_status
            })

        except Category.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "Category not found."
            }, status=404)

        except DatabaseError:
            return JsonResponse({
                "success": False,
                "message": "Database error occurred."
            }, status=500)

        except Exception as e:
            logger.error(f"Unexpected error toggling category {category_id}: {e}")
            return JsonResponse({
                "success": False,
                "message": "Unexpected server error occurred."
            }, status=500)


@method_decorator(never_cache, name='dispatch')
class ToggleUserStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'admin_login'

    def test_func(self):
        # Only admin can toggle categories
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "You are not authorized")
        return redirect('login')

    def post(self, request, user_id):

        try:
            user = User.objects.get(id=user_id)

            # Toggle status
            user.is_active = not user.is_active
            user.save()

            new_status = "Active" if user.is_active else "Inactive"

            logger.info(
                f"Admin {request.user.username} changed "
                f"user {user.username} to {new_status}"
            )

            return JsonResponse({
                "success": True,
                "message": f"User '{user.username}' {new_status.lower()} successfully.",
                "new_status": new_status
            })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "User not found."
            }, status=404)

        except DatabaseError:
            return JsonResponse({
                "success": False,
                "message": "Database error occurred."
            }, status=500)

        except Exception as e:
            logger.error(f"Unexpected error toggling user {user_id}: {e}")
            return JsonResponse({
                "success": False,
                "message": "Unexpected server error occurred."
            }, status=500)


class EditCategoryView(View, LoginRequiredMixin):

    login_url = 'admin_login'

    template_name = 'adminpanel/edit_category.html'

    def get(self, request, category_id):

        if request.user.is_authenticated and request.user.is_staff:

            category = Category.objects.get(id=category_id)

            if category is None:
                messages.error(request, 'Category not found. Please try to add new category')
                logger.warning('Admin tries to edit no-excisting category')
                return redirect('categories')

            context = {
                'category': category
            }

            return render(request, self.template_name, context)

        return redirect('login')

    def post(self, request, category_id):

        name = request.POST.get('category_name')
        description = request.POST.get('category_description')
        is_active = 'category_status' in request.POST

        try:

            if len(name) >= 15:
                messages.error(request, 'name is too long')
                return render(request, self.template_name)

            if len(description) > 400:
                messages.error(request, 'description is too long')
                return render(request, self.template_name)

            category = Category.objects.get(id=category_id)

            if category is None:
                raise Category.DoesNotExist

            category.name = name
            category.description = description
            category.is_active = is_active

            category.save()

            messages.success(request, f'Category {name} is edited succesfully')

            return redirect('categories')

        except Category.DoesNotExist:
            messages.error(request, 'Category not found. :(')
            logger.error(f'Admin tries to edit un-excisting category : {category_id}')
            return redirect('categories')

        except DatabaseError as d:
            messages.error(request, 'Database error occured. :(')
            logger.error(f'Some thing happend iin database side : {d}')
            return redirect('categories')

        except Exception as e:
            messages.error(request, 'Something went wrong during editing category')
            logger.error(f'something went wrong during editing category : {e}')
            return redirect('categories')


@method_decorator(never_cache, name='dispatch')
class AdminProductsView(ListView, LoginRequiredMixin):

    model = Product
    template_name = 'adminpanel/products_panel.html'
    login_url = 'admin_login'
    context_object_name = 'products'
    paginate_by = 8

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Product.objects.annotate(variant_count=Count("variants")).prefetch_related("variants__images")

        # SEARCH
        search_query = self.request.GET.get('search_query')
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query))

        # STATUS FILTER
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'blocked':
            queryset = queryset.filter(is_active=False)

        # SORTING
        sort = self.request.GET.get('sort', 'latest')

        if sort == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort == 'active-first':
            queryset = queryset.order_by('-is_active')
        elif sort == 'latest':  # latest
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-updated_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search_query', '')
        return context


ALLOWED_IMAGE_TYPES = ["image/png", "image/jpeg", "image/webp"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


def validate_product_fields(data):
    NAME_REGEX = re.compile(r'^[A-Za-z\s]+$')
    DESCRIPTION_REGEX = re.compile(r'^[A-Za-z\s.,-]+$')

    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    category = data.get("category")

    if not name or not NAME_REGEX.match(name):
        raise ValidationError("Product name must contain only alphabets")

    if not Category.objects.filter(id=category, is_active=True).exists():
        raise ValidationError("Invalid category selected")

    if not description or not DESCRIPTION_REGEX.match(description):
        raise ValidationError(
            "Description must contain only alphabets, comma, dot, or hyphen"
        )

    return {
        "name": name,
        "description": description,
        "category_id": category,
    }


def validate_variant_fields(data):
    COLOR_REGEX = re.compile(r'^[A-Za-z\s]+$')
    SKU_REGEX = re.compile(r'^[A-Za-z]+-[0-9]+$')

    price = data.get("price")
    stock = data.get("stock")

    sku = (data.get("SKU") or "").strip()
    color = (data.get("color") or "").strip()
    size = data.get("size")

    try:
        price = float(price)
        if price <= 0:
            raise ValueError
    except Exception:
        raise ValidationError("Price must be a positive number")

    try:
        stock = int(stock)
        if stock <= 0:
            raise ValueError
    except Exception:
        raise ValidationError("Stock must be a positive number")

    if not SKU_REGEX.match(sku):
        raise ValidationError("SKU format must be like ABC-123")

    if not COLOR_REGEX.match(color):
        raise ValidationError("Color must contain only alphabets")

    if not size or "Select" in size:
        raise ValidationError("Size is required")

    return {
        "price": price,
        "stock": stock,
        "sku": sku,
        "color": color,
        "size": size,
    }


def validate_images(uploaded_images, *, existing_count=0, mode="create"):

    total_images = existing_count + len(uploaded_images)

    if mode == "create" and total_images < 3:
        raise ValidationError("At least 3 images are required")

    if mode == "edit" and total_images < 1:
        raise ValidationError("At least 1 image is required")

    for img in uploaded_images:
        if img.size > MAX_IMAGE_SIZE:
            raise ValidationError("Image size must be under 5MB")

        if img.content_type not in ALLOWED_IMAGE_TYPES:
            raise ValidationError("Invalid image format. Use PNG, JPG, or WEBP.")


class ProductCreateView(View):

    template_name = "adminpanel/add_product.html"

    def get(self, request):

        if request.user.is_authenticated and request.user.is_staff:
            return render(request, self.template_name, {
                "categories": Category.objects.filter(is_active=True)
            })

        return redirect('admin_login')

    @transaction.atomic
    def post(self, request):
        try:

            product_data = validate_product_fields(request.POST)

            if Product.objects.filter(name__iexact=request.POST.get('name', "").strip()).exists():
                raise ValidationError("Product with this name already exists")

            product = Product.objects.create(**product_data)

            variant_indexes = set()

            for key in request.POST.keys():
                if key.startswith("variants["):
                    idx = key.split("[")[1].split("]")[0]
                    variant_indexes.add(idx)

            if not variant_indexes:
                raise ValidationError("At least one variant is required")

            for idx in sorted(variant_indexes, key=int):
                raw_variant_data = {
                    "price": request.POST.get(f"variants[{idx}][price]"),
                    "SKU": request.POST.get(f'variants[{idx}][SKU]'),
                    "color": request.POST.get(f'variants[{idx}][color]'),
                    "size": request.POST.get(f'variants[{idx}][size]'),
                    "stock": request.POST.get(f'variants[{idx}][stock]')
                }

                variant_data = validate_variant_fields(raw_variant_data)

                if ProductVariant.objects.filter(sku__iexact=raw_variant_data.get('SKU')).exists():
                    raise ValidationError("SKU already exists")

                variant = ProductVariant.objects.create(
                    product=product,
                    **variant_data
                )

                images = request.FILES.getlist(f"variants[{idx}][images][]")
                validate_images(images, existing_count=0, mode="create")

                for i, img in enumerate(images):
                    upload = cloudinary_upload(
                        img,
                        folder="products/variants",
                        public_id=f"variant_{variant.id}_{uuid.uuid4().hex[:8]}",
                        resource_type="image"
                    )

                    ProductImage.objects.create(
                        product_variant=variant,
                        image_url=upload["secure_url"],
                        public_id=upload["public_id"],
                        is_primary=(i == 0)
                    )

            messages.success(request, "Product created successfully")
            return redirect("products")

        except ValidationError as e:
            transaction.set_rollback(True)
            messages.error(request, str(e))
            logger.error(f"Validation error during Product creation {e}")
            return redirect("add_product")

        except Exception as e:
            transaction.set_rollback(True)
            messages.error(request, "Something went wrong while creating product")
            logger.error(f"Unexpecated error during Product creation {e}")
            return redirect("add_product")


@method_decorator(never_cache, name='dispatch')
class ToggleProductStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'admin_login'

    def test_func(self):
        # Only admin can toggle products
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "You are not authorized")
        return redirect('login')

    def post(self, request, product_id):

        try:
            product = Product.objects.get(id=product_id)

            # Toggle status
            product.is_active = not product.is_active
            product.save()

            new_status = "Active" if product.is_active else "Inactive"

            logger.info(
                f"Admin {request.user.username} changed "
                f"product {product.name} to {new_status}"
            )

            return JsonResponse({
                "success": True,
                "message": f"product '{product.name}' {new_status.lower()} successfully.",
                "new_status": new_status
            })

        except Product.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "product not found."
            }, status=404)

        except DatabaseError:
            return JsonResponse({
                "success": False,
                "message": "Database error occurred."
            }, status=500)

        except Exception as e:
            logger.error(f"Unexpected error toggling product {product_id}: {e}")
            return JsonResponse({
                "success": False,
                "message": "Unexpected server error occurred."
            }, status=500)


class ProductEditView(View):

    template_name = "adminpanel/edit_product.html"

    def get(self, request, pk):

        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('admin_login')

        product = get_object_or_404(Product, pk=pk)
        variants = product.variants.prefetch_related("images")

        return render(request, self.template_name, {
            "product": product,
            "variants": variants,
            "size": ["S", "M", "L", "XL", "XXL"],
            "categories": Category.objects.filter(is_active=True)
        })

    @transaction.atomic
    def post(self, request, pk):
        try:
            # Validate product data first
            product_data = validate_product_fields(request.POST)

            # Fetch product within transaction to ensure consistency
            product = get_object_or_404(Product, pk=pk)

            # Fetch and validate category
            category = get_object_or_404(Category, id=product_data['category_id'], is_active=True)

            # Update product
            product.category = category
            product.name = product_data['name']
            product.description = product_data['description']
            product.save()

            # ===== Collect variant indices =====
            variant_indexes = set()
            for key in request.POST.keys():
                if key.startswith("variants["):
                    try:
                        idx = key.split("[")[1].split("]")[0]
                        # Validate that idx is a valid integer
                        int(idx)  # This will raise ValueError if not an integer
                        variant_indexes.add(idx)
                    except (IndexError, ValueError):
                        continue

            # Filter valid indexes
            valid_indexes = []
            for idx in variant_indexes:
                price = request.POST.get(f"variants[{idx}][price]")
                sku = request.POST.get(f"variants[{idx}][SKU]")
                if price and sku:
                    valid_indexes.append(idx)
                else:
                    logger.debug(f"Skipping variant idx={idx} (missing price/SKU)")
            variant_indexes = sorted(valid_indexes, key=int)

            if not variant_indexes:
                raise ValidationError("At least one variant is required")

            # ===== DELETE VARIANTS =====
            # Handle explicitly deleted variants
            deleted_ids_str = request.POST.get("deleted_variants", "")
            deleted_ids = []
            if deleted_ids_str:
                for vid_str in deleted_ids_str.split(","):
                    vid_str = vid_str.strip()
                    if vid_str:
                        try:
                            # Validate ID as integer (since models use default AutoField)
                            deleted_ids.append(int(vid_str))
                        except ValueError:
                            logger.warning(f"Invalid variant ID in deleted_variants: {vid_str}")
                            continue

            if deleted_ids:
                # Only delete variants belonging to this product
                ProductVariant.objects.filter(
                    id__in=deleted_ids,
                    product=product
                ).delete()

            # Get all submitted variant IDs to identify which ones to keep
            submitted_variant_ids = set()
            for idx in variant_indexes:
                variant_id = request.POST.get(f"variants[{idx}][id]")
                if variant_id:
                    try:
                        # Validate ID as integer
                        int(variant_id)
                        submitted_variant_ids.add(variant_id)
                    except ValueError:
                        logger.warning(f"Invalid variant ID in submission: {variant_id}")
                        continue

            # Delete variants that are not submitted (cleanup)
            variants_to_delete = ProductVariant.objects.filter(product=product).exclude(id__in=submitted_variant_ids)
            for variant in variants_to_delete:
                # Delete associated images
                for img in variant.images.all():
                    try:
                        cloudinary_destroy(img.public_id)
                    except Exception as e:
                        logger.warning(f"Cloudinary delete failed for {img.public_id}: {e}")
                    img.delete()
                variant.delete()

            # ===== UPDATE/CREATE VARIANTS =====
            for idx in variant_indexes:
                variant_id = request.POST.get(f"variants[{idx}][id]")
                raw_variant_data = {
                    "price": request.POST.get(f"variants[{idx}][price]"),
                    "SKU": request.POST.get(f"variants[{idx}][SKU]"),
                    "color": request.POST.get(f"variants[{idx}][color]"),
                    "size": request.POST.get(f"variants[{idx}][size]"),
                    "stock": request.POST.get(f"variants[{idx}][stock]"),
                }

                variant_data = validate_variant_fields(raw_variant_data)

                if variant_id:
                    # Update existing variant - ensure it belongs to this product
                    variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
                    variant.price = variant_data["price"]
                    variant.sku = variant_data["sku"]
                    variant.color = variant_data["color"]
                    variant.size = variant_data["size"]
                    variant.stock = variant_data["stock"]
                    variant.save()
                else:
                    # Create new variant
                    variant = ProductVariant.objects.create(
                        product=product,
                        price=variant_data["price"],
                        sku=variant_data["sku"],
                        color=variant_data["color"],
                        size=variant_data["size"],
                        stock=variant_data["stock"],
                    )

                # ===== IMAGE HANDLING =====
                # Get all existing images for this variant
                all_existing_images = {str(img.id): img for img in variant.images.all()}

                # Get IDs of images to keep
                submitted_image_ids = set(request.POST.getlist(f"variants[{idx}][existing_images][]"))

                # Process image deletions
                for img_id, img in all_existing_images.items():
                    if img_id not in submitted_image_ids:
                        # Delete image from both DB and Cloudinary
                        try:
                            cloudinary_destroy(img.public_id)
                        except Exception as e:
                            logger.warning(f"Cloudinary destroy failed: {e}")
                        img.delete()

                # Process image replacements (if any)
                # This is where we handle edited images
                for key in request.POST.keys():
                    if key.startswith("replaced_image_"):
                        # Extract image ID from key
                        img_id_str = key.replace("replaced_image_", "")
                        try:
                            img_id = int(img_id_str)
                            # Get the replacement file
                            replacement_files = request.FILES.getlist(key)
                            if replacement_files:
                                replacement_file = replacement_files[0]  # Take first file if multiple

                                # Validate the replacement file
                                validate_images([replacement_file], existing_count=0, mode="edit")

                                # Find the existing image to replace
                                existing_img = all_existing_images.get(str(img_id))
                                if existing_img:
                                    # Upload new file to Cloudinary
                                    upload = cloudinary_upload(
                                        replacement_file,
                                        folder="products/variants",
                                        public_id=existing_img.public_id,  # Reuse the same public ID
                                        resource_type="image"
                                    )

                                    # Update the existing image record with new file details
                                    existing_img.image_url = upload["secure_url"]
                                    existing_img.public_id = upload["public_id"]
                                    existing_img.save()
                                else:
                                    # If the image ID doesn't exist, skip this replacement
                                    logger.warning(f"Replacement image ID {img_id} not found for variant {variant.id}")
                        except ValueError:
                            logger.warning(f"Invalid image ID in replaced_image key: {key}")

                # Handle new image uploads
                new_images = request.FILES.getlist(f"variants[{idx}][images][]")
                if new_images:
                    # Count current existing images to validate total count
                    current_existing_count = len(submitted_image_ids)
                    validate_images(new_images, existing_count=current_existing_count, mode="edit")
                    for img_file in new_images:
                        upload = cloudinary_upload(
                            img_file,
                            folder="products/variants",
                            public_id=f"variant_{variant.id}_{uuid.uuid4().hex[:8]}",
                            resource_type="image"
                        )
                        ProductImage.objects.create(
                            product_variant=variant,
                            image_url=upload["secure_url"],
                            public_id=upload["public_id"],
                        )

                # Handle primary image selection
                primary_image_id = request.POST.get(f"variants[{idx}][primary_image_id]")
                if primary_image_id:
                    # Validate that the primary image ID is among the current images
                    current_images = variant.images.all()
                    primary_img = None
                    for img in current_images:
                        if str(img.id) == primary_image_id:
                            primary_img = img
                            break

                    if primary_img:
                        # Reset all images to non-primary
                        variant.images.update(is_primary=False)
                        # Set the selected image as primary
                        primary_img.is_primary = True
                        primary_img.save(update_fields=['is_primary'])
                    else:
                        # If primary image ID is invalid, just skip setting primary
                        pass
                else:
                    # If no primary image was explicitly selected, maintain existing primary status
                    # If no primary exists and there are images, set the first one as primary
                    current_images = list(variant.images.all())
                    if current_images and not any(img.is_primary for img in current_images):
                        current_images[0].is_primary = True
                        current_images[0].save(update_fields=['is_primary'])

            messages.success(request, "Product updated successfully")
            return redirect("products")

        except ValidationError as e:
            transaction.set_rollback(True)
            messages.error(request, str(e))
            logger.error(f"Validation error during Product update: {e}")
            return redirect("edit_product", pk=pk)

        except Exception as e:
            transaction.set_rollback(True)
            messages.error(request, "Something went wrong while updating product")
            logger.error(f"Unexpected error during Product update: {e}", exc_info=True)
            return redirect("edit_product", pk=pk)


@method_decorator(never_cache, name='dispatch')
class AdminOrderListView(LoginRequiredMixin, ListView):

    model = Order
    template_name = 'adminpanel/orders_panel.html'
    context_object_name = 'orders'
    paginate_by = 8

    def get_queryset(self):

        queryset = Order.objects.all()

        q = self.request.GET.get('q')

        if q:
            queryset = queryset.filter(order_id__icontains=q)

        status = self.request.GET.get('status')

        if status:
            queryset = queryset.filter(status=status)

        sort = self.request.GET.get('sort')

        if sort == 'oldest':
            queryset = queryset.order_by('created_at')
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context


@method_decorator(never_cache, name='dispatch')
class AdminOrderDetailView(LoginRequiredMixin, DetailView):

    model = Order
    template_name = 'adminpanel/admin_order_detail.html'
    context_object_name = 'order'
    slug_field = 'order_id'
    slug_url_kwarg = 'order_id'

    def get_queryset(self):
        queryset = Order.objects.all().select_related('address').prefetch_related('items')
        return queryset


@method_decorator(never_cache, name='dispatch')
class ToggleOrderStatusView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, order_id):
        order = get_object_or_404(Order, order_id=order_id)
        new_status = request.POST.get('status')

        allowed_statuses = dict(Order.ORDER_STATUS_CHOICES).keys()
        if new_status not in allowed_statuses:
            return JsonResponse({'error': 'Invalid status'}, status=400)

        if not self._is_valid_transition(order.status, new_status):
            return JsonResponse({'error': 'Invalid status transition'}, status=400)

        if new_status == 'cancelled':

            order.items.filter(status__in=['pending', 'confirmed', 'shipped']).update(
                status='cancelled',
                cancel_reason='Cancelled via order-level action',
                cancelled_at=timezone.now()
            )
        elif new_status == 'delivered':
            order.items.exclude(status='cancelled').update(status='delivered')
        elif new_status == 'shipped':
            order.items.exclude(status='cancelled').update(status='shipped')

        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])

        return JsonResponse({'success': True, 'new_status': new_status})

    def _is_valid_transition(self, old, new):
        ALLOWED_TRANSITIONS = {
            'pending':      ['confirmed', 'cancelled'],
            'confirmed':    ['shipped', 'cancelled'],
            'shipped':      ['delivered'],
            'delivered':    [],
            'cancelled':    [],
        }

        return new in ALLOWED_TRANSITIONS.get(old, [])


@method_decorator(never_cache, name='dispatch')
class ToggleOrderItemStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, order_id, item_id):
        order = get_object_or_404(Order, order_id=order_id)
        item = get_object_or_404(OrderItem, id=item_id, order=order)

        new_status = request.POST.get('status')
        allowed_statuses = dict(OrderItem.ITEM_STATUS_CHOICES).keys()

        if new_status not in allowed_statuses:
            return JsonResponse({'error': 'Invalid item status'}, status=400)

        if not self._is_valid_transition(item.status, new_status):
            return JsonResponse({'error': 'Invalid status transition'}, status=400)

        if item.status == 'delivered' and new_status == 'pending':
            return JsonResponse({'error': 'Cannot revert delivered item'}, status=400)

        if new_status == 'cancelled':
            variant = item.product_variant
            variant.stock += item.quantity
            variant.save(update_fields=['stock'])

            order.sub_total -= item.total_price
            order.total_amount -= item.total_price
            order.save(update_fields=['sub_total', 'total_amount'])

        item.status = new_status
        item.save(update_fields=['status'])

        self._update_order_status_if_needed(order)

        return JsonResponse({'success': True, 'new_status': new_status})

    def _update_order_status_if_needed(self, order):
        item_statuses = set(order.items.values_list('status', flat=True))
        if item_statuses == {'delivered'}:
            order.status = 'delivered'
            order.save(update_fields=['status'])
        elif 'cancelled' in item_statuses and not item_statuses - {'cancelled'}:
            order.status = 'cancelled'
            order.save(update_fields=['status'])

    def _is_valid_transition(self, old, new):
        ALLOWED_TRANSITIONS = {
            'pending':      ['confirmed', 'cancelled'],
            'confirmed':    ['shipped', 'cancelled'],
            'shipped':      ['delivered'],
            'delivered':    [],
            'cancelled':    [],
        }

        return new in ALLOWED_TRANSITIONS.get(old, [])


@method_decorator(never_cache, name='dispatch')
class ReturnListView(LoginRequiredMixin, UserPassesTestMixin, ListView):

    def test_func(self):
        return self.request.user.is_staff

    template_name = 'adminpanel/return_list.html'
    model = Return
    paginate_by = 6
    context_object_name = 'returns_list'

    def get_queryset(self):
        queryset = Return.objects.select_related(
            'user',
            'order'
        ).prefetch_related(
            'return_items'
        ).all()

        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status')

        if q:
            queryset = queryset.filter(
                Q(user__email__icontains=q) |
                Q(order__order_id__icontains=q.replace('-', '').replace(' ', ''))
            )

        if status and status in dict(Return.RETURN_STATUS_CHOICES):
            queryset = queryset.filter(status=status)

        queryset = queryset.annotate(
            pending_priority=Case(
                When(status='pending', then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by('pending_priority', '-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['status_choices'] = Return.RETURN_STATUS_CHOICES
        return context


@method_decorator(never_cache, name='dispatch')
class ReturnDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):

    def test_func(self):
        return self.request.user.is_staff

    template_name = 'adminpanel/return_detail.html'

    model = Return
    context_object_name = 'returns_list'
    slug_field = 'id'
    slug_url_kwarg = 'return_id'


@method_decorator(never_cache, name='dispatch')
class ReturnStatusToggleView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return self.request.user.is_authenticated

    def post(self, request, return_id):
        new_status = request.POST.get('status')
        allowed_statuses = [choice[0] for choice in Return.RETURN_STATUS_CHOICES]

        if new_status not in allowed_statuses:
            return JsonResponse({'error': 'Invalid status value'}, status=400)

        try:
            with transaction.atomic():
                returns = get_object_or_404(
                    Return.objects.select_for_update(),
                    id=return_id
                )
                current_status = returns.status

                if current_status in ['accepted', 'rejected']:
                    return JsonResponse({
                        'error': 'Status cannot be changed',
                        'details': f'This return has already been {current_status}.'
                    }, status=403)

                if current_status == new_status:
                    return JsonResponse({
                        'success': True,
                        'message': 'Status unchanged',
                        'current_status': current_status
                    }, status=200)

                if new_status in ['accepted', 'rejected']:
                    returns.processed_at = timezone.now()
                else:
                    returns.processed_at = None

                if new_status == 'rejected':
                    admin_notes = request.POST.get('admin_notes', '').strip()
                    returns.admin_notes = admin_notes if admin_notes else 'Rejected by admin'

                if current_status == 'pending' and new_status == 'accepted':
                    for item in returns.return_items.select_related('order_item__product_variant'):
                        variant = item.order_item.product_variant
                        original_stock = variant.stock
                        variant.stock += item.quantity
                        variant.save(update_fields=['stock'])
                        logger.info(
                            f"Stock increased: Variant {variant.sku} | "
                            f"+{item.quantity} (Return #{returns.id}) | "
                            f"Old: {original_stock} → New: {variant.stock}"
                        )

                returns.status = new_status
                returns.save(update_fields=['status', 'processed_at', 'admin_notes'])

                if new_status == 'accepted':
                    order = returns.order
                    fully_returned_items = []

                    for return_item in returns.return_items.select_related('order_item'):
                        order_item = return_item.order_item

                        total_returned = ReturnItem.objects.filter(
                            order_item=order_item,
                            return_request__status='accepted'
                        ).aggregate(total=Sum('quantity'))['total'] or 0

                        if total_returned >= order_item.quantity and order_item.status != 'returned':
                            order_item.status = 'returned'
                            order_item.save(update_fields=['status'])
                            fully_returned_items.append(order_item)
                            logger.info(
                                f"OrderItem #{order_item.id} marked as 'returned' | "
                                f"Total returned: {total_returned}/{order_item.quantity}"
                            )

                    if fully_returned_items:
                        total_order_items = order.items.count()
                        returned_order_items = order.items.filter(status='returned').count()

                        if total_order_items == returned_order_items and order.status != 'returned':
                            old_order_status = order.status
                            order.status = 'returned'
                            order.save(update_fields=['status'])
                            logger.info(
                                f"Order #{order.id} status updated: {old_order_status} → 'returned' | "
                                f"All {total_order_items} items returned"
                            )

            return JsonResponse({
                'success': True,
                'new_status': new_status,
                'processed_at': returns.processed_at.isoformat() if returns.processed_at else None,
                'message': f'Return status updated to "{new_status}"',
                'is_final': new_status in ['accepted', 'rejected']
            })

        except Exception as e:
            logger.error(f"Error processing return #{return_id}: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': 'Internal server error',
                'details': str(e) if settings.DEBUG else 'An error occurred during processing'
            }, status=500)


class ProductOfferList(LoginRequiredMixin, UserPassesTestMixin, ListView):

    def test_func(self):
        return self.request.user.is_staff

    template_name = 'offers/product_offerlist.html'
    model = ProductOffer
    context_object_name = 'product_offers'
    paginate_by = 6

    def get_queryset(self):
        queryset = ProductOffer.objects.all()

        # SEARCH
        search_query = self.request.GET.get('search_query')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(product__name__icontains=search_query)
            )

        # STATUS FILTER
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(active=True)
        elif status == 'inactive':
            queryset = queryset.filter(active=False)

        # SORTING
        sort = self.request.GET.get('sort', 'start-date')

        if sort == 'end-date':
            queryset = queryset.order_by('end_date')
        elif sort == 'active-first':
            queryset = queryset.order_by('-active')
        else:  # start-date
            queryset = queryset.order_by('-start_date')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search_query', '')
        return context


class CategoryOfferList(LoginRequiredMixin, UserPassesTestMixin, ListView):

    def test_func(self):
        return self.request.user.is_staff

    template_name = 'offers/category_offerlist.html'
    model = CategoryOffer
    context_object_name = 'category_offers'
    paginate_by = 6

    def get_queryset(self):
        queryset = CategoryOffer.objects.all()

        # SEARCH
        search_query = self.request.GET.get('search_query')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )

        # STATUS FILTER
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(active=True)
        elif status == 'inactive':
            queryset = queryset.filter(active=False)

        # SORTING
        sort = self.request.GET.get('sort', 'start-date')

        if sort == 'end-date':
            queryset = queryset.order_by('end_date')
        elif sort == 'active-first':
            queryset = queryset.order_by('-active')
        else:  # start-date
            queryset = queryset.order_by('-start_date')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search_query', '')
        return context


class GlobalOfferList(LoginRequiredMixin, UserPassesTestMixin, ListView):

    def test_func(self):
        return self.request.user.is_staff

    template_name = 'offers/global_offerlist.html'
    model = GlobalOffer
    context_object_name = 'global_offers'
    paginate_by = 6

    def get_queryset(self):
        queryset = GlobalOffer.objects.all()

        # SEARCH
        search_query = self.request.GET.get('search_query')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
            )

        # STATUS FILTER
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(active=True)
        elif status == 'inactive':
            queryset = queryset.filter(active=False)

        # SORTING
        sort = self.request.GET.get('sort', 'start-date')

        if sort == 'end-date':
            queryset = queryset.order_by('end_date')
        elif sort == 'active-first':
            queryset = queryset.order_by('-active')
        else:  # start-date
            queryset = queryset.order_by('-start_date')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search_query', '')
        return context


@method_decorator(never_cache, name='dispatch')
class ProductOfferCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):

    def test_func(self):
        return self.request.user.is_staff

    model = ProductOffer
    fields = [
        'name', 'start_date', 'end_date', 'priority',
        'product', 'discount_type', 'value', 'max_discount_amount'
    ]
    template_name = 'offers/product_offer_create.html'
    success_url = reverse_lazy('produc_offer_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['product'].queryset = Product.objects.filter(is_active=True)
        return form

    @transaction.atomic
    def form_valid(self, form):

        ProductOffer.objects.filter(
            product=form.cleaned_data['product'],
            active=True
        ).update(active=False)

        form.instance.active = True

        response = super().form_valid(form)

        messages.success(
            self.request,
            f"✅ Product offer '{form.instance.name}' activated for '{form.instance.product.name}'. "
            f"All previous active offers deactivated."
        )
        return response

    def get_initial(self):
        return {'start_date': timezone.now(), 'priority': 10}


@method_decorator(never_cache, name='dispatch')
class CategoryOfferCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):

    def test_func(self):
        return self.request.user.is_staff

    model = CategoryOffer
    fields = [
        'name', 'start_date', 'end_date', 'priority',
        'category', 'discount_type', 'value', 'min_items'
    ]
    template_name = 'offers/category_offer_create.html'
    success_url = reverse_lazy('catego_offer_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['category'].queryset = Category.objects.filter(is_active=True)
        return form

    @transaction.atomic
    def form_valid(self, form):

        CategoryOffer.objects.filter(
            category=form.cleaned_data['category'],
            active=True
        ).update(active=False)

        form.instance.active = True
        response = super().form_valid(form)

        messages.success(
            self.request,
            f"✅ Category offer '{form.instance.name}' activated for '{form.instance.category.name}'. "
            f"All previous active offers deactivated."
        )
        return response

    def get_initial(self):
        return {'start_date': timezone.now(), 'priority': 10, 'min_items': 1}


@method_decorator(never_cache, name='dispatch')
class GlobalOfferCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):

    def test_func(self):
        return self.request.user.is_staff

    model = GlobalOffer
    fields = [
        'name', 'active', 'start_date', 'end_date', 'priority',
        'discount_type', 'value', 'min_cart_value', 'max_discount'
    ]
    template_name = 'offers/global_offer_create.html'
    success_url = reverse_lazy('global_offer_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"✅ Global offer '{form.instance.name}' created.")
        return response

    def get_initial(self):
        return {'start_date': timezone.now(), 'priority': 10, 'min_cart_value': 0}


@method_decorator(never_cache, name='dispatch')
class ProductOfferUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):

    def test_func(self):
        return self.request.user.is_staff

    model = ProductOffer
    fields = [
        'name', 'active', 'start_date', 'end_date', 'priority',
        'product', 'discount_type', 'value', 'max_discount_amount'
    ]
    template_name = 'offers/product_offer_edit.html'
    success_url = reverse_lazy('produc_offer_list')
    pk_url_kwarg = 'pk'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        if self.object.product_id:
            form.fields['product'].queryset = Product.objects.filter(
                Q(is_active=True) | Q(pk=self.object.product_id)
            )
        else:
            form.fields['product'].queryset = Product.objects.filter(is_active=True)
        return form

    @transaction.atomic
    def form_valid(self, form):
        current_offer = self.get_object()

        new_product = form.cleaned_data['product']
        new_active = form.cleaned_data['active']

        if new_active:
            ProductOffer.objects.filter(
                product=new_product,
                active=True
            ).exclude(pk=current_offer.pk).update(active=False)

        response = super().form_valid(form)

        messages.success(
            self.request,
            f"✅ Product offer '{form.instance.name}' updated successfully."
        )
        return response


@method_decorator(never_cache, name='dispatch')
class CategoryOfferUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):

    def test_func(self):
        return self.request.user.is_staff

    model = CategoryOffer
    fields = [
        'name', 'active', 'start_date', 'end_date', 'priority',
        'category', 'discount_type', 'value', 'min_items'
    ]
    template_name = 'offers/category_offer_edit.html'
    success_url = reverse_lazy('catego_offer_list')
    pk_url_kwarg = 'pk'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        if self.object.category_id:
            form.fields['category'].queryset = Category.objects.filter(
                Q(is_active=True) | Q(pk=self.object.category_id)
            )
        else:
            form.fields['category'].queryset = Category.objects.filter(is_active=True)
        return form

    @transaction.atomic
    def form_valid(self, form):
        current_offer = self.get_object()

        new_category = form.cleaned_data['category']
        new_active = form.cleaned_data['active']

        if new_active:
            CategoryOffer.objects.filter(
                category=new_category,
                active=True
            ).exclude(pk=current_offer.pk).update(active=False)

        response = super().form_valid(form)

        messages.success(
            self.request,
            f"✅ Category offer '{form.instance.name}' updated successfully."
        )
        return response


@method_decorator(never_cache, name='dispatch')
class GlobalOfferUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):

    def test_func(self):
        return self.request.user.is_staff

    model = GlobalOffer
    fields = [
        'name', 'active', 'start_date', 'end_date', 'priority',
        'discount_type', 'value', 'min_cart_value', 'max_discount'
    ]
    template_name = 'offers/global_offer_edit.html'
    success_url = reverse_lazy('global_offer_list')
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"✅ Global offer '{form.instance.name}' updated successfully."
        )
        return response


class ToggleProductOfferStatus(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return self.request.user.is_staff

    @transaction.atomic
    def post(self, request, offer_id):

        try:
            offer = get_object_or_404(ProductOffer, id=offer_id)

            new_status = not offer.active

            if new_status:
                ProductOffer.objects.filter(product=offer.product, active=True).exclude(
                    id=offer_id
                ).update(active=False)

            offer.active = new_status

            offer.save(update_fields=["active"])

            return JsonResponse({
                'success': True,
                'message': 'Status changed Succesfully',
                'status': 'Active' if offer.active else 'Inactive'
            })

        except DatabaseError as e:
            logger.error(request, f'Some database error occurd while toggling Product offer status : {e}')
            return JsonResponse({
                'success': False,
                'message': 'Database Error occured ..'
            })

        except Exception as e:
            logger.error(request, f'Something went wrong while toggling Product Offer Status {offer_id}: {e}')
            return JsonResponse({
                'success': False,
                'message': 'Something went wrong while changing the offer status ...'
            })


class ToggleCategoryOfferStatus(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return self.request.user.is_staff

    @transaction.atomic
    def post(self, request, offer_id):

        try:
            offer = get_object_or_404(CategoryOffer, id=offer_id)

            new_status = not offer.active

            if new_status:
                CategoryOffer.objects.filter(category=offer.category, active=True).exclude(
                    id=offer_id
                ).update(active=False)

            offer.active = new_status

            offer.save(update_fields=["active"])

            return JsonResponse({
                'success': True,
                'message': 'Status changed Succesfully',
                'status': 'Active' if offer.active else 'Inactive'
            })

        except DatabaseError as e:
            logger.error(request, f'Some database error occurd while toggling Category offer status : {e}')
            return JsonResponse({
                'success': False,
                'message': 'Database Error occured ..'
            })

        except Exception as e:
            logger.error(request, f'Something went wrong while toggling Category Offer Status {offer_id}: {e}')
            return JsonResponse({
                'success': False,
                'message': 'Something went wrong while changing the offer status ...'
            })


class ToggleGlobalOfferStatus(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return self.request.user.is_staff

    @transaction.atomic
    def post(self, request, offer_id):

        try:
            offer = get_object_or_404(GlobalOffer, id=offer_id)

            offer.active = not offer.active

            offer.save(update_fields=["active"])

            return JsonResponse({
                'success': True,
                'message': 'Status changed Succesfully',
                'status': 'Active' if offer.active else 'Inactive'
            })

        except DatabaseError as e:
            logger.error(request, f'Some database error occurd while toggling Global offer status : {e}')
            return JsonResponse({
                'success': False,
                'message': 'Database Error occured ..'
            })

        except Exception as e:
            logger.error(request, f'Something went wrong while toggling Global Offer Status {offer_id}: {e}')
            return JsonResponse({
                'success': False,
                'message': 'Something went wrong while changing the offer status ...'
            })


class CouponListView(LoginRequiredMixin, UserPassesTestMixin, ListView):

    def test_func(self):
        return self.request.user.is_staff

    template_name = 'coupon/coupon_list.html'

    model = Coupon
    context_object_name = 'coupon_list'
    paginate_by = 6

    def get_queryset(self):
        queryset = Coupon.objects.all()

        # SEARCH
        search_query = self.request.GET.get('search_query')
        if search_query:
            queryset = queryset.filter(
                Q(coupon_code__icontains=search_query)
            )

        # STATUS FILTER
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(active=True)
        elif status == 'inactive':
            queryset = queryset.filter(active=False)

        queryset = queryset.order_by('-active')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search_query', '')
        return context


@method_decorator(never_cache, name='dispatch')
class CouponCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):

    def test_func(self):
        return self.request.user.is_staff

    model = Coupon
    template_name = 'coupon/coupon_create.html'
    success_url = reverse_lazy('coupon_list')

    fields = [
        "coupon_code",
        "discount_type",
        "value",
        "max_discount",
        "min_order_amount",
        "usage_limit",
        "per_user_limit",
        "active",
        "start_date",
        "end_date",
    ]

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(self.request, f'Coupon created Successfully..{form.instance.coupon_code}')

        return response

    def get_initial(self):
        initial = super().get_initial()
        initial['start_date'] = timezone.now()
        return initial


class CouponEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):

    def test_func(self):
        return self.request.user.is_staff

    model = Coupon
    template_name = 'coupon/coupon_edit.html'
    success_url = reverse_lazy('coupon_list')
    pk_url_kwarg = 'coupon_id'

    fields = [
        "coupon_code",
        "discount_type",
        "value",
        "max_discount",
        "min_order_amount",
        "usage_limit",
        "per_user_limit",
        "active",
        "start_date",
        "end_date",
    ]

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(self.request, f'Coupon Edited Successfully..{form.instance.coupon_code}')

        return response


class ToggleCouponStatusView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, coupon_id):

        try:
            coupon = get_object_or_404(Coupon, id=coupon_id)

            new_status = not coupon.active

            coupon.active = new_status
            coupon.save(update_fields=['active'])

            status = 'Active' if coupon.active else 'Inactive'

            return JsonResponse({
                'success': True,
                'message': f"{coupon.coupon_code} is now {status}",
                'status': status
            })

        except DatabaseError as e:

            logger.error(f'Database error occured while coupon status changeing: {e}')
            return JsonResponse({
                'success': False,
                'message': f'Database error occured while changing status of {coupon.coupon_code}'
            })

        except Exception as e:
            logger.error(f'Something went wrong while changing status of coupon{coupon.id} : {e}')
            return JsonResponse({
                'success': False,
                'message': f'Something went wrong while changing status of {coupon.coupon_code}'
            })


@method_decorator(never_cache, name='dispatch')
class AnalyticstView(LoginRequiredMixin, UserPassesTestMixin, ListView):

    def test_func(self):
        return self.request.user.is_staff

    template_name = 'adminpanel/sales_report.html'
    model = Order
    paginate_by = 6
    context_object_name = "orders"

    def get_queryset(self):
        queryset = Order.objects.filter(status='delivered')

        # date filter

        date_filter = self.request.GET.get('date_filter', 'all')
        start_date = self.request.GET.get('start_date', '')
        end_date = self.request.GET.get('end_date', '')

        today = timezone.now().date()

        if date_filter == 'today':
            queryset = queryset.filter(created_at__date=today)
        elif date_filter == 'week':
            start_of_week = today - timedelta(days=today.weekday())
            queryset = queryset.filter(created_at__date__gte=start_of_week)
        elif date_filter == 'month':
            queryset = queryset.filter(created_at__year=today.year, created_at__month=today.month)
        elif date_filter == 'year':
            queryset = queryset.fileter(created_at__year=today.year)
        elif date_filter == 'custom' and start_date and end_date:
            queryset = queryset.filter(created_at__date__gte=start_date, created_at__date_lte=end_date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        base_orders = self.get_queryset()

        context['current_filters'] = {
            'date_filter': self.request.GET.get('date_filter', 'all'),
            'start_date': self.request.GET.get('start_date', ''),
            'end_date': self.request.GET.get('end_date', ''),
            'status_filter': self.request.GET.get('status_filter', 'all'),
            'payment_filter': self.request.GET.get('payment_filter', 'all'),
        }

        # KPI

        order_stats = base_orders.aggregate(
            total_orders=Count('id'),
            gross_revenue=Sum('sub_total'),
            discount_amount=Sum('discount_amount'),
            coupon_discount_amount=Sum('coupon_discount_amount'),
            )

        def safe_decimal(value):
            """Convert None to Decimal(0) for safe math"""
            return value if value is not None else Decimal('0')

        context['total_orders'] = safe_decimal(order_stats['total_orders'])
        context['gross_revenue'] = safe_decimal(order_stats['gross_revenue'])
        context['discount_amount'] = safe_decimal(order_stats['discount_amount'])
        context['coupon_discount_amount'] = safe_decimal(order_stats['coupon_discount_amount'])
        context['overall_discount'] = context['discount_amount'] + context['coupon_discount_amount']
        context['net_revenue'] = context['gross_revenue'] - context['overall_discount']

        # payment distribution

        payment_stats = base_orders.values('payment_method').annotate(
            total_amount=Sum('total_amount'),
            order_count=Count('id')
        ).order_by('-total_amount')

        context['payment_distribution'] = {
            item['payment_method']: {
                'amount': safe_decimal(item['total_amount']),
                'count': safe_decimal(item['order_count'])
            } for item in payment_stats
        }

        # Calculate total for percentage calculation in template
        context['payment_total'] = sum(p['amount'] for p in context['payment_distribution'].values())

        return context
