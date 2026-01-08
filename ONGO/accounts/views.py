from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views import View
from django.views.generic import ListView
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from django.utils.decorators import method_decorator


from django.db import DatabaseError

from .models import User, Address

from django.http import JsonResponse

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

        if re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password) is False:
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

            if re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password) is False:
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


def ProfileView(request):
    return render(request, 'accounts/profile_section.html',)


@method_decorator(login_required, name='dispatch')
class EditProfileView(View):
    template_name = 'accounts/edit_profile_section.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        user = request.user

        # 1. Regex Validation
        if not re.match(r'^[a-zA-Z0-9_]{3,}$', username):
            messages.error(request, "Username must be at least 3 characters alphanumeric/underscore.")
            return render(request, self.template_name)

        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            messages.error(request, "Please enter a valid email address.")
            return render(request, self.template_name)

        # Phone is mandatory
        if not phone or not re.match(r'^\+?[\d\s-]{10,}$', phone):
            messages.error(request, "Please enter a valid phone number (min 10 digits).")
            return render(request, self.template_name)

        # 2. Uniqueness Checks
        if User.objects.filter(username__iexact=username).exclude(pk=user.pk).exists():
            messages.error(request, "This username is already taken.")
            return render(request, self.template_name)

        if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            messages.error(request, "This email is already linked to another account.")
            return render(request, self.template_name)

        # 3. Save Changes
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


class AddressView(ListView):
    template_name = 'accounts/manage_address.html'
    model = Address
    context_object_name = 'addresses'

    def get_queryset(self):
        return Address.objects.all().order_by('-is_default')


class AddAddressView(View):

    template_name = 'accounts/add_address.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):

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

            Address.objects.create(
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

            messages.success(request, "Address added successfully!")
            return redirect('manage_address')

        except Exception as e:
            logger.error(f"Error saving address for user {user.id}: {e}")
            messages.error(request, "Something went wrong while saving the address.")
            return render(request, self.template_name)


class EditAddressView(View):
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
                messages.warning(request, f"Default address deleted. '{last_address.name}' is now your default address.")
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


def PasswordView(request):
    return render(request, 'accounts/manage_password.html',)
