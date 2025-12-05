const PASSWORD_PATTERN = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;


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


// Validation Functions
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


function setupPasswordToggles() {
    const togglePassword = document.getElementById('togglePassword');

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
}

document.addEventListener('DOMContentLoaded', () => {
    const fields = ['username', 'password'];
    fields.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', updateSubmitButton);
            el.addEventListener('blur', updateSubmitButton);
        }
    });

    // Initial check
    setupPasswordToggles();
}
);

// Update Submit Button State
function updateSubmitButton() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    const isValid = username.length > 0 && password.length >= 6;

    const button = document.getElementById('loginButton');

    if (isValid) {
        button.classList.remove('bg-gray-400', 'cursor-not-allowed');
        button.classList.add('bg-red-600', 'hover:bg-red-700');
    } else {
        button.classList.remove('bg-red-600', 'hover:bg-red-700');
        button.classList.add('bg-gray-400', 'cursor-not-allowed');
    }

    button.disabled = !isValid;

    // Visual feedback
    
}
function updateSubmitButton() {
    const isValid =
        checkEmail() &&
        checkPassword();

    const button = document.getElementById('loginBtn');
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
