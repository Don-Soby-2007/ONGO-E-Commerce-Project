from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.db.models import Q
from django.views.generic import ListView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from accounts.models import User
from products.models import Category, Product, ProductVariant, ProductImage

from django.http import JsonResponse

from django.db import DatabaseError

from django.db import transaction
from django.core.exceptions import ValidationError

import cloudinary.uploader
import uuid

import re

import logging

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
        queryset = Product.objects.all().prefetch_related('variants__images')

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


# def ProductCreateView(request):
#     if request.user.is_authenticated:
#         return render(request, "adminpanel/add_product.html")


ALLOWED_IMAGE_TYPES = ["image/png", "image/jpeg", "image/webp"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


def validate_product_fields(data):
    NAME_REGEX = re.compile(r'^[A-Za-z\s]+$')
    DESCRIPTION_REGEX = re.compile(r'^[A-Za-z\s.,-]+$')
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    category = data.get("category")

    if not name or not NAME_REGEX.match(name):
        raise ValidationError("Product name must contain only alphabets")

    if Product.objects.filter(name__iexact=name).exists():
        raise ValidationError("Product with this name already exists")

    if not category:
        raise ValidationError("Category is required")

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
    sku = data.get("SKU", "").strip()
    color = data.get("color", "").strip()
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


def validate_images(images):
    if not images:
        raise ValidationError("At least one product image is required")

    for img in images:
        if img.content_type not in ALLOWED_IMAGE_TYPES:
            raise ValidationError("Only PNG, JPG, WEBP images are allowed")

        if img.size > MAX_IMAGE_SIZE:
            raise ValidationError("Each image must be under 5MB")


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

            product = Product.objects.create(**product_data)

            variant_data = validate_variant_fields(request.POST)

            variant = ProductVariant.objects.create(
                product=product,
                **variant_data
            )

            images = request.FILES.getlist("variant_images[]")
            validate_images(images)

            for img in images:
                upload = cloudinary.uploader.upload(
                    img,
                    folder="products/variants",
                    public_id=f"variant_{variant.id}_{uuid.uuid4().hex[:8]}",
                    resource_type="image"
                )

                ProductImage.objects.create(
                    product_variant=variant,
                    image_url=upload["secure_url"],
                    public_id=upload["public_id"],
                )

            messages.success(request, "Product created successfully")
            return redirect("products")

        except ValidationError as e:
            transaction.set_rollback(True)
            messages.error(request, str(e))
            return redirect("add_product")

        except Exception as e:
            transaction.set_rollback(True)
            messages.error(request, "Something went wrong while creating product")
            print(e)
            return redirect("add_product")


@method_decorator(never_cache, name='dispatch')
class ToggleProductStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'admin_login'

    def test_func(self):
        # Only admin can toggle categories
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
