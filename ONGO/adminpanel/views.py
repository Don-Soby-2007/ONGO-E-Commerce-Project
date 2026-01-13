from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.db.models import Q, Count
from django.views.generic import ListView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from accounts.models import User
from products.models import Category, Product, ProductVariant, ProductImage

from django.http import JsonResponse

from django.db import DatabaseError

from django.db import transaction
from django.core.exceptions import ValidationError


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

            category = Category.objects.filter(name=name).first()

            if category:
                messages.error(request, 'category name alredy existed, please give other name')
                return render(request, self.template_name)

            Category.objects.create(name=name, description=description, is_active=is_active)

            messages.success(request, f'New category {name} created successfully')

            return redirect('categories')

        except DatabaseError as d:
            messages.error(request, 'Database error occured. :(')
            logger.error(f'Some thing happend iin database side : {d}')
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
