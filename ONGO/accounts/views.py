from django.shortcuts import render, redirect

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required

from .utils import create_address_from_request


from django.views import View
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.decorators.cache import never_cache

from django.core.mail import send_mail

from django.utils.decorators import method_decorator

from django.db import DatabaseError, transaction

from django.http import JsonResponse

from django.contrib.auth.mixins import LoginRequiredMixin

from .models import User, Address, Wishlist
from order.models import Order, OrderItem
from products.models import ProductVariant
from cart.models import Cart

from django.shortcuts import get_object_or_404
from django.utils import timezone

import re
import logging


# Create your views here.

logger = logging.getLogger(__name__)


def user_login_view(request):
    return render(request, 'accounts/user-login.html')


@method_decorator(never_cache, name='dispatch')
class SignupView(View):
    template_name = 'accounts/user-sigup.html'

    def get(self, request):
        if request.user.is_authenticated and request.user.is_staff is False:
            return redirect('home')
        return render(request, self.template_name)

    def post(self, request):

        username = request.POST.get('username').strip()
        email = request.POST.get('email').strip().lower()
        phone = request.POST.get('phone').strip()
        password = request.POST.get('password').strip()
        confirm_password = request.POST.get('confirm_password').strip()

        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password):
            messages.error(request, "Password must be at least 8 characters long "
                           "and include uppercase,lowercase, number, and special character.")
            return render(request, self.template_name)

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, self.template_name)

        # Check for existing user
        existing_user = User.objects.filter(email=email).first()

        if existing_user:
            if existing_user.is_verified:
                messages.error(request, "Email is already registered.")
                return render(request, self.template_name)
            else:
                otp = existing_user.generate_otp()
                logger.info(f"OTP for user {existing_user.email}")

                send_mail(
                    'Your OTP Verification Code',
                    f'Your OTP code is: {otp}. It is valid for 5 minutes.',
                    None,
                    [existing_user.email],
                    fail_silently=False,
                )
                request.session['pending_user_id'] = existing_user.id
                return redirect("otp_verify")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, self.template_name)

        user = User.objects.create_user(
            username=username,
            email=email,
            phone_number=phone,
        )
        user.set_password(password)
        user.is_verified = False
        user.is_active = False
        user.save()

        otp = user.generate_otp()
        logger.info(f"OTP for user {user.email}: {otp}")

        send_mail(
            'Your OTP Verification Code',
            f'Your OTP code is: {otp}. It is valid for 5 minutes. Please do not share it anyone',
            None,
            [user.email],
            fail_silently=False,
        )

        request.session['pending_user_id'] = user.id
        return redirect("otp_verify")


@method_decorator(never_cache, name='dispatch')
class OtpVerificationView(View):
    template_name = 'accounts/otp-verification.html'

    def get(self, request):
        if not request.session.get('pending_user_id'):
            return redirect("login")
        return render(request, self.template_name)

    def post(self, request):
        user_id = request.session.get('pending_user_id')
        otp_input = request.POST.get('otp')

        if not user_id:
            messages.error(request, "No pending OTP verification found.")
            return redirect("signup")

        if not otp_input or not otp_input.isdigit() or len(otp_input) != 6:
            messages.error(request, "Please enter a valid 6-digit OTP.")
            return render(request, self.template_name)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            logger.warning(f"OTP verification attempted for non-existent user ID: {user_id}")
            messages.error(request, "User not found. Please sign up again.")
            return redirect("signup")

        except DatabaseError as e:
            logger.error(f"Database error during OTP verification for user {user_id}: {e}")
            messages.error(request, "A database error occurred. Please try again later.")
            return render(request, self.template_name)

        if user.verify_otp(otp_input):
            request.session.pop('pending_user_id', None)
            request.session['verified_user_id'] = user.id
            messages.success(request, "OTP verified successfully. Your account is now active.")
            return redirect("user_confirmed")
        else:
            messages.error(request, "Invalid or expired OTP. Please try again.")
            return render(request, self.template_name)


@never_cache
def userConfirmedView(request):
    if request.user.is_authenticated:
        return redirect('home')

    user_id = request.session.get('verified_user_id')
    if not user_id:
        return redirect("login")

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning(f"User confirmed view accessed for non-existent user ID: {user_id}")
        messages.error(request, "User not found. Please sign up again.")
        return redirect("signup")

    except DatabaseError as e:
        logger.error(f"Database error accessing user confirmed view for user {user_id}: {e}")
        messages.error(request, "A database error occurred. Please try again later.")
        return redirect("signup")

    return render(request, 'accounts/user-confirmed.html', {'user': user.username, 'email': user.email})


@never_cache
def resend_otp_view(request):
    if request.method != 'POST':
        return redirect('signup')

    try:
        user_id = request.session.get('pending_user_id')

        if not user_id:
            return JsonResponse({'success': False, 'message': "No pending OTP verification found."})

        user = User.objects.get(pk=user_id)

        if user:
            otp = user.generate_otp()
            logger.info(f"New OTP (resend otp) for user {user.email}: {otp}")

            send_mail(
                'Your New OTP Verification Code',
                f'Your OTP code is: {otp}. It is valid for 5 minutes. Please do not share it anyone',
                None,
                [user.email],
                fail_silently=False,
            )
            return JsonResponse({'success': True, 'message': "OTP Resended Successfully"})
        else:
            raise User.DoesNotExist

    except User.DoesNotExist:
        logger.warning(f"Resend OTP attempted for non-existing user ID: {user_id}")
        return JsonResponse({'success': False, 'message': "User doesn't exists"})

    except Exception as e:
        logger.error(f"Error Resending OTP {user_id} : {e}")
        return JsonResponse({'success': False, 'message': "Something Went Wrong. Please Try Again"})


@method_decorator(never_cache, name='dispatch')
class LoginView(View):
    template_name = "accounts/user-login.html"

    def get(self, request):
        if request.user.is_authenticated and request.user.is_staff is False:
            return redirect('home')
        if request.session.get('verified_user_id'):
            request.session.pop('verified_user_id', None)

        return render(request, self.template_name)

    def post(self, request):

        email = request.POST.get('email').strip()
        password = request.POST.get('password').strip()

        try:
            import re

            if re.match(r'', email) is False:
                messages.error(request, "Enter a valid email")
                return render(request, self.template_name)

            if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password):
                messages.error(request, "Password is wrong. Please Enter a valid Password")
                return render(request, self.template_name)

            user = authenticate(request, email=email, password=password)
            user_obj = User.objects.get(email=email)

            if not user_obj.is_active and user_obj.is_verified:
                messages.error(request, "You are blocked, Plese contact admin for further updation")
                return render(request, self.template_name)

            if user is None:
                raise User.DoesNotExist

            if user_obj.is_active and user_obj.is_verified and user_obj.is_blocked is False:
                login(request, user)
                return redirect('home')
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


@login_required
@never_cache
def userLogoutView(request):
    logout(request)
    return redirect('login')


@login_required
def ProfileView(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'accounts/profile_section.html',)


@method_decorator(never_cache, name='dispatch')
class EditProfileView(LoginRequiredMixin, View):
    template_name = 'accounts/edit_profile_section.html'
    otp_verification_template = 'accounts/otp_verification_profile.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        user = request.user

        original_email = user.email

        if not re.match(r'^[a-zA-Z ]{3,}$', username):
            messages.error(request, "Username must be at least 3 characters only alphabets.")
            return render(request, self.template_name)

        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            messages.error(request, "Please enter a valid email address.")
            return render(request, self.template_name)

        if not phone or not re.match(r'^\+?[\d\s-]{10,}$', phone):
            messages.error(request, "Please enter a valid phone number (min 10 digits).")
            return render(request, self.template_name)

        if email.lower() != original_email.lower():
            if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                messages.error(request, "This email is already linked to another account.")
                return render(request, self.template_name)

            temp_email = email

            otp = user.generate_otp()
            logger.info(f"Email change OTP for user {user.email} -> {temp_email}: {otp}")

            send_mail(
                'Verify Your New Email Address',
                f'Your OTP to verify new email address is: {otp}. It is valid for 5 minutes.',
                None,
                [temp_email],
                fail_silently=False,
            )

            # Session: for profilechanges
            request.session['temp_email_change'] = {
                'user_id': user.id,
                'new_email': temp_email,
                'username': username,
                'phone': phone
            }

            return render(request, self.otp_verification_template, {
                'new_email': temp_email
            })
        else:
            # Email not changed
            return self._update_profile(user, username, email, phone, request)

    # Private methode for helping to update the profile

    def _update_profile(self, user, username, email, phone, request):

        try:
            user.username = username
            user.email = email
            user.phone_number = phone
            user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
        except Exception as e:
            logger.error(f"Error updating profile for user {user.id}: {e}")
            messages.error(request, "Something went wrong while updating your profile.")
            return render(request, self.template_name)


@method_decorator(never_cache, name='dispatch')
class UpdateProfilePhotoView(LoginRequiredMixin, View):

    def post(self, request):

        profile_photo = request.FILES.get('profile_photo')

        if not profile_photo:
            messages.error(request, "No image file provided.")
            return redirect('profile')

        allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
        if profile_photo.content_type not in allowed_types:
            messages.error(request, "Invalid file type. Please use PNG, JPG, or WEBP.")
            return redirect('profile')

        if profile_photo.size > 5 * 1024 * 1024:
            messages.error(request, "Image too large. Maximum size is 5MB.")
            return redirect('profile')

        try:
            success = request.user.upload_profile_picture(profile_photo)
            if success:
                messages.success(request, "Profile photo updated successfully!")
            else:
                messages.error(request, "Failed to upload image. Please try again.")
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Error uploading profile photo for user {request.user.id}: {e}")
            messages.error(request, "An error occurred while uploading your photo. Please try again.")

        return redirect('profile')


@method_decorator(never_cache, name='dispatch')
class EmailChangeOtpVerificationView(LoginRequiredMixin, View):

    template_name = 'accounts/otp_verification_profile.html'

    def get(self, request):
        temp_data = request.session.get('temp_email_change')
        if not temp_data:
            messages.error(request, "No pending email change found.")
            return redirect('edit-profile')

        return render(request, self.template_name, {
            'new_email': temp_data['new_email']
        })

    def post(self, request):
        otp_input = request.POST.get('otp')
        temp_data = request.session.get('temp_email_change')

        if not temp_data or not otp_input:
            messages.error(request, "No pending email change or OTP found.")
            return redirect('edit-profile')

        try:
            user = User.objects.get(pk=temp_data['user_id'])
        except User.DoesNotExist:
            messages.error(request, "User not found. Please try changing your email again.")
            request.session.pop('temp_email_change', None)
            return redirect('edit-profile')

        if user.verify_otp(otp_input):
            self._update_profile_with_new_email(user, temp_data, request)
            request.session.pop('temp_email_change', None)
            messages.success(request, "Email changed successfully! Profile updated.")
            return redirect('profile')
        else:
            messages.error(request, "Invalid or expired OTP. Please try again.")
            return render(request, self.template_name, {
                'new_email': temp_data['new_email']
            })

    def _update_profile_with_new_email(self, user, temp_data, request):
        try:
            user.username = temp_data['username']
            user.email = temp_data['new_email']
            user.phone_number = temp_data['phone']
            user.is_verified = True
            user.save()
        except Exception as e:
            logger.error(f"Error updating profile with new email for user {user.id}: {e}")
            messages.error(request, "Failed to update profile. Please try again.")


@login_required
def cancel_email_change(request):
    if request.method == 'POST':
        request.session.pop('temp_email_change', None)
        messages.info(request, "Email change cancelled. No changes were made to your email.")
    return redirect('profile')


@login_required
def resend_email_change_otp(request):
    if request.method != 'POST':
        return redirect('edit-profile')

    temp_data = request.session.get('temp_email_change')
    if not temp_data:
        return JsonResponse({'success': False, 'message': "No pending email change found."})

    try:
        user = User.objects.get(pk=temp_data['user_id'])
        new_email = temp_data['new_email']

        otp = user.generate_otp()
        logger.info(f"Resent email change OTP for {user.email} -> {new_email}: {otp}")

        send_mail(
            'Your New Email Verification Code',
            f'Your OTP to verify new email address is: {otp}. It is valid for 5 minutes.',
            None,
            [new_email],
            fail_silently=False,
        )

        return JsonResponse({'success': True, 'message': "OTP sent successfully"})

    except User.DoesNotExist:
        logger.warning("Resend OTP attempted for non-existing user during email change")
        request.session.pop('temp_email_change', None)
        return JsonResponse({'success': False, 'message': "User not found"})

    except Exception as e:
        logger.error(f"Error resending OTP for email change: {e}")
        return JsonResponse({'success': False, 'message': "Failed to send OTP"})


@method_decorator(never_cache, name='dispatch')
class AddressView(LoginRequiredMixin, ListView):
    template_name = 'accounts/manage_address.html'
    model = Address
    context_object_name = 'addresses'

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).order_by('-is_default')


@method_decorator(never_cache, name='dispatch')
class AddAddressView(LoginRequiredMixin, View):

    template_name = 'accounts/add_address.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):

        success, message, redirect_url = create_address_from_request(request)
        if success:
            messages.success(request, message)
            return redirect(redirect_url)
        else:
            messages.error(request, message)
            return render(request, self.template_name)


@method_decorator(never_cache, name='dispatch')
class EditAddressView(LoginRequiredMixin, View):
    template_name = 'accounts/edit_address.html'

    def get(self, request, address_id):
        address = Address.objects.get(id=address_id)
        return render(request, self.template_name, {'address': address})

    def post(self, request, address_id):
        full_name = request.POST.get('fullName', '').strip()
        street_address = request.POST.get('streetAddress', '').strip()
        phone_number = request.POST.get('phoneNumber', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postalCode', '').strip()
        country = request.POST.get('country', '').strip()
        is_default = request.POST.get('defaultAddress') == 'on'

        user = request.user

        if not re.match(r'^[a-zA-Z\s]{3,}$', full_name):
            messages.error(request, "Name must contain only letters and spaces (min 3 chars).")
            return render(request, self.template_name)

        if not re.match(r'^[a-zA-Z0-9\s,.\-/#]{5,}$', street_address):
            messages.error(request, "Address seems invalid. Use letters, numbers, and common symbols.")
            return render(request, self.template_name)

        if not re.match(r'^\+?[0-9]{10,15}$', phone_number):
            messages.error(request, "Enter a valid phone number (10-15 digits).")
            return render(request, self.template_name)

        if not re.match(r'^[a-zA-Z\s]+$', city):
            messages.error(request, "City must contain only letters.")
            return render(request, self.template_name)

        if not re.match(r'^[a-zA-Z\s]+$', state):
            messages.error(request, "State must contain only letters.")
            return render(request, self.template_name)

        if not re.match(r'^[0-9]{5,6}$', postal_code):
            messages.error(request, "Postal code must be 5-6 digits.")
            return render(request, self.template_name)

        if not country:
            messages.error(request, "Please select a country.")
            return render(request, self.template_name)

        try:
            if is_default:
                Address.objects.filter(user=user, is_default=True).update(is_default=False)

            if not Address.objects.filter(user=user).exists():
                is_default = True

            Address.objects.filter(id=address_id).update(
                user=user,
                name=full_name,
                street_address=street_address,
                phone=phone_number,
                city=city,
                state=state,
                country=country,
                postal_code=postal_code,
                is_default=is_default
            )

            messages.success(request, "Address edited successfully!")
            return redirect('manage_address')

        except Exception as e:
            logger.error(f"Error saving address for user {user.id}: {e}")
            messages.error(request, "Something went wrong while saving the address.")
            return render(request, self.template_name)


@login_required
def DeleteAddressView(request, pk):

    if request.method != "POST":
        return redirect('manage_address')

    try:
        address = Address.objects.get(pk=pk, user=request.user)
        is_default = address.is_default
        address.delete()

        # If deleted address was default, set the last updated address as default
        if is_default:
            last_address = Address.objects.filter(user=request.user).order_by('-updated_at').first()
            if last_address:
                last_address.is_default = True
                last_address.save()
                messages.warning(request,
                                 f"Default address deleted. '{last_address.name}' is now your default address.")
            else:
                messages.success(request, "Address deleted successfully.")
        else:
            messages.success(request, "Address deleted successfully.")

    except Address.DoesNotExist:
        messages.error(request, "Address not found.")
    except Exception as e:
        logger.error(f"Error deleting address: {e}")
        messages.error(request, "An error occurred while deleting the address.")

    return redirect('manage_address')


@method_decorator(never_cache, name='dispatch')
class PasswordView(LoginRequiredMixin, View):

    template_name = 'accounts/manage_password.html'

    def get(self, request):
        return render(request, self.template_name,)

    def post(self, request):
        old_password = request.POST.get('old_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        user = request.user

        if not old_password:
            messages.error(request, "Please enter your current password.")
            return render(request, self.template_name)

        if not new_password:
            messages.error(request, "Please enter a new password.")
            return render(request, self.template_name)

        if not confirm_password:
            messages.error(request, "Please confirm your new password.")
            return render(request, self.template_name)

        if not user.check_password(old_password):
            messages.error(request, "The old password is incorrect.")
            return render(request, self.template_name)

        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', new_password):
            messages.error(request, "Password does not meet requirements. Must contain uppercase, lowercase, number,"
                                    "and special character.")
            return render(request, self.template_name)

        if old_password == new_password:
            messages.error(request, "The new password must be different from your current password.")
            return render(request, self.template_name)

        if new_password != confirm_password:
            messages.error(request, "The new password and confirmation do not match.")
            return render(request, self.template_name)

        try:
            user.set_password(new_password)
            user.save()

            update_session_auth_hash(request, user)

            messages.success(request, "Your password has been changed successfully.")
            return redirect('profile')
        except Exception as e:
            messages.error(request, "Something went wrong while updating your password.")
            logger.error(f"Unexpected error occurred when updating password for user {user}: {e}")
            return render(request, self.template_name)


class OrderListView(LoginRequiredMixin, ListView):

    model = Order
    template_name = 'accounts/order_list.html'
    context_object_name = 'orders'
    paginate_by = 3

    def get_queryset(self):

        queryset = Order.objects.filter(user=self.request.user)

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
class OrderDetailView(LoginRequiredMixin, DetailView):

    model = Order
    template_name = 'accounts/order_detail.html'
    context_object_name = 'order'
    slug_field = 'order_id'
    slug_url_kwarg = 'order_id'

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user).select_related('address').prefetch_related('items')
        return queryset


@method_decorator(never_cache, name='dispatch')
class OrderCancelView(LoginRequiredMixin, View):

    def post(self, request, order_id):

        order = get_object_or_404(Order, order_id=order_id, user=request.user)

        if order.status not in ['pending', 'confirmed']:
            return JsonResponse({
                'error': 'Cannot cancell This Order. Current Status: ' + order.status
            }, status=400)

        reason = request.POST.get('cancel_reason', 'Cancelled by User')

        for item in order.items.all():
            if item.status in ['pending', 'confirmed']:
                item.status = 'cancelled'
                item.cancel_reason = reason
                item.cancelled_at = timezone.now()
                item.save()
                variant = item.product_variant
                variant.stock += item.quantity
                variant.save(update_fields=['stock'])

        order.status = 'cancelled'
        order.save()

        return JsonResponse({'message': 'Order cancelled successfully.'})


@method_decorator(never_cache, name='dispatch')
class OrderItemCancelView(LoginRequiredMixin, View):
    def post(self, request, order_id, item_id):
        order = get_object_or_404(Order, order_id=order_id, user=request.user)
        item = get_object_or_404(OrderItem, id=item_id, order=order)

        if item.status not in ['pending', 'confirmed']:
            return JsonResponse({
                'error': 'Cannot cancel this item. Current status: ' + item.status
            }, status=400)

        reason = request.POST.get('reason', 'Cancelled by user')
        item.status = 'cancelled'
        item.cancel_reason = reason
        item.cancelled_at = timezone.now()
        item.save()

        order.sub_total -= item.total_price
        order.total_amount -= item.total_price
        order.save(update_fields=['sub_total', 'total_amount'])

        variant = item.product_variant
        variant.stock += item.quantity
        variant.save(update_fields=['stock'])

        if not order.items.exclude(status='cancelled').exists():
            order.status = 'cancelled'
            order.save()

        return JsonResponse({'message': 'Item cancelled successfully.'})


@method_decorator(never_cache, name='dispatch')
class WishlistView(LoginRequiredMixin, ListView):

    model = Wishlist
    template_name = 'accounts/wishlist.html'
    context_object_name = 'wishlist_items'
    paginate_by = 6

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)


class DeleteWishlistItem(LoginRequiredMixin, View):

    def post(self, request, variant_id):

        try:
            # Validate variant_id is an integer
            try:
                variant_id = int(variant_id)
            except (ValueError, TypeError):
                logger.warning(f'User {request.user.id} provided invalid variant_id: {variant_id}')
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid product identifier'
                }, status=400)

            # Get the variant (404 if not found or inactive)
            try:
                variant = get_object_or_404(ProductVariant, id=variant_id, product__is_active=True)
            except ProductVariant.DoesNotExist:
                logger.warning(f'User {request.user.id} attempted to delete non-existent variant {variant_id}')
                return JsonResponse({
                        'success': False,
                        'message': 'Variant is not found in Product'
                    }, status=404)

            # Delete the wishlist item
            with transaction.atomic():
                deleted_count, _ = Wishlist.objects.filter(
                    user=request.user,
                    product_variant=variant
                ).delete()

                if deleted_count == 0:
                    logger.warning(
                        f'User {request.user.id} tried to delete non-existent wishlist item for variant {variant_id}')
                    return JsonResponse({
                        'success': False,
                        'message': 'Item not found in your wishlist'
                    }, status=404)

            logger.info(f'User {request.user.id} deleted variant {variant_id} from wishlist')

            return JsonResponse({
                'success': True,
                'message': 'Removed from wishlist',
            }, status=200)

        except Exception as e:
            logger.exception(
                f'Unexpected error deleting wishlist item for user{request.user.id}, variant {variant_id}: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': 'Something went wrong while deleting wishlist item. Please try again later.'
            }, status=500)


class AddtoCartWishlistItem(LoginRequiredMixin, View):

    def post(self, request, variant_id):

        try:
            try:
                variant_id = int(variant_id)
            except (ValueError, TypeError):
                logger.warning(f'User {request.user.id} provided invalid variant_id: {variant_id}')
                messages.error(request, 'Invalid product identifier')
                return redirect('wishlist')

            try:
                variant = get_object_or_404(ProductVariant, id=variant_id, product__is_active=True)
            except ProductVariant.DoesNotExist:
                logger.warning(f'User {request.user.id} attempted to delete non-existent variant {variant_id}')
                messages.error(request, 'Variant is not found in Product')
                return redirect('wishlist')

            with transaction.atomic():
                deleted_count, _ = Wishlist.objects.filter(
                    user=request.user,
                    product_variant=variant
                ).delete()

                if deleted_count == 0:
                    logger.warning(
                        f'User {request.user.id} tried to delete non-existent wishlist item for variant {variant_id}')
                    messages.error(request, 'please tries to add existing wishlist item')
                    return redirect('wishlist')

                logger.info(f'User {request.user.id} deleted variant {variant_id} from wishlist for add to cart')

                qty = 1

                cart_item, created = Cart.objects.get_or_create(
                    user=request.user,
                    product_variant=variant,
                )

                new_quantity = qty if created else cart_item.quantity + qty

                if new_quantity > variant.stock:
                    messages.error(request, 'Insuffcient stock, Please try again')
                    return redirect('wishlist')

                if new_quantity > 5:
                    messages.error(request, 'Maximum 5 items allowed per product in cart.')
                    return redirect('wishlist')

                cart_item.quantity = new_quantity
                cart_item.save()

            logger.info(f'User {request.user.id} added variant {variant_id} from wishlist to Cart')

            messages.success(request, 'Added to cart')
            return redirect('wishlist')

        except Exception as e:
            logger.exception(
                f'Unexpected error deleting wishlist item for user{request.user.id}, variant {variant_id}: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': 'Something went wrong while deleting wishlist item. Please try again later.'
            }, status=500)
