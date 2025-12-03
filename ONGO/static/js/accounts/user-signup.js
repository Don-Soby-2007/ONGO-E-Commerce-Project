// ===============================================
// ONGO - User Signup Validation + UX
// Works 100% with your final HTML
// ===============================================

// Regex Patterns
const USERNAME_PATTERN = /^[A-Za-z]+( [A-Za-z]+)*$/;           // Letters + single spaces only
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;           // Basic email
const PHONE_PATTERN = /^\d{10}$/;                             // Exactly 10 digits
const PASSWORD_PATTERN = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
// Must contain: lowercase, uppercase, number, special char, 8+ length

// Helper: Show Error
function showError(input, errorElement, message) {
    input.classList.add('border-red-500');
    errorElement.textContent = message;
    errorElement.classList.remove('hidden');
}

// Helper: Clear Error
function clearError(input, errorElement) {
    input.classList.remove('border-red-500');
    errorElement.classList.add('hidden');
}

// 1. Validate Username
function checkUsername() {
    const input = document.getElementById('username');
    const error = document.getElementById('usernameError');
    const value = input.value.trim();

    if (value === '') {
        showError(input, error, 'Username is required');
        return false;
    }
    if (value.length < 3 || value.length > 20) {
        showError(input, error, 'Username must be 3–20 characters');
        return false;
    }
    if (!USERNAME_PATTERN.test(value)) {
        showError(input, error, 'Only letters and single spaces allowed');
        return false;
    }

    clearError(input, error);
    return true;
}

// 2. Validate Email
function checkEmail() {
    const input = document.getElementById('email');
    const error = document.getElementById('emailError');
    const value = input.value.trim();

    if (value === '') {
        showError(input, error, 'Email is required');
        return false;
    }
    if (!EMAIL_PATTERN.test(value)) {
        showError(input, error, 'Enter a valid email address');
        return false;
    }

    clearError(input, error);
    return true;
}

// 3. Validate Phone
function checkPhone() {
    const input = document.getElementById('phone');
    const error = document.getElementById('phoneError');
    const value = input.value.replace(/\D/g, ''); // Remove non-digits

    if (value === '') {
        showError(input, error, 'Phone number is required');
        return false;
    }
    if (!PHONE_PATTERN.test(value)) {
        showError(input, error, 'Enter a valid 10-digit phone number');
        return false;
    }

    clearError(input, error);
    return true;
}

// 4. Validate Password
function checkPassword() {
    const input = document.getElementById('password');
    const error = document.getElementById('passwordError');
    const value = input.value;

    if (value === '') {
        showError(input, error, 'Password is required');
        return false;
    }
    if (!PASSWORD_PATTERN.test(value)) {
        showError(input, error, '8+ chars: A-Z, a-z, 0-9, and @#$!%*?&');
        return false;
    }

    clearError(input, error);
    return true;
}

// 5. Confirm Password Match
function checkConfirmPassword() {
    const password = document.getElementById('password').value;
    const confirmInput = document.getElementById('confirmPassword');
    const error = document.getElementById('confirmPasswordError');
    const confirmValue = confirmInput.value.trim();

    if (confirmValue === '') {
        showError(confirmInput, error, 'Please confirm your password');
        return false;
    }
    if (password !== confirmValue) {
        showError(confirmInput, error, 'Passwords do not match');
        return false;
    }

    clearError(confirmInput, error);
    return true;
}

// 6. Update Submit Button State
function updateSubmitButton() {
    const isValid =
        checkUsername() &&
        checkEmail() &&
        checkPhone() &&
        checkPassword() &&
        checkConfirmPassword();

    const button = document.getElementById('createAccountBtn');
    button.disabled = !isValid;

    // Visual feedback
    if (isValid) {
        button.classList.remove('bg-gray-400', 'cursor-not-allowed');
        button.classList.add('bg-red-600', 'hover:bg-red-700');
    } else {
        button.classList.remove('bg-red-600', 'hover:bg-red-700');
        button.classList.add('bg-gray-400', 'cursor-not-allowed');
    }
}

// 7. Password Visibility Toggle
function setupPasswordToggles() {
    const togglePassword = document.getElementById('togglePassword');
    const toggleConfirm = document.getElementById('toggleConfirmPassword');

    if (togglePassword) {
        togglePassword.addEventListener('click', () => {
            const input = document.getElementById('password');
            const icon = togglePassword.querySelector('svg');
            if (input.type === 'password') {
                input.type = 'text';
                icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>`;
            } else {
                input.type = 'password';
                icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />`;
            }
        });
    }

    if (toggleConfirm) {
        toggleConfirm.addEventListener('click', () => {
            const input = document.getElementById('confirmPassword');
            input.type = input.type === 'password' ? 'text' : 'password';
        });
    }
}

// 8. Attach Real-Time Listeners
document.addEventListener('DOMContentLoaded', () => {
    const fields = ['username', 'email', 'phone', 'password', 'confirmPassword'];
    fields.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', updateSubmitButton);
            el.addEventListener('blur', updateSubmitButton);
        }
    });

    // Initial check
    // updateSubmitButton();
    setupPasswordToggles();

});