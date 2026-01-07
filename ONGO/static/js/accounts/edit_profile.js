document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('edit-profile-form');
    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone');

    const usernameError = document.getElementById('username-error');
    const emailError = document.getElementById('email-error');
    const phoneError = document.getElementById('phone-error');

    // Validation Regex Patterns
    const usernameRegex = /^[a-zA-Z0-9_]{3,}$/;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const phoneRegex = /^\+?[\d\s-]{10,}$/;

    // Utility to show/hide errors
    const showError = (element, message) => {
        element.textContent = message;
        element.classList.remove('hidden');
        element.previousElementSibling.firstElementChild.classList.add('border-red-500');
        element.previousElementSibling.firstElementChild.classList.remove('border-gray-300');
    };

    const clearError = (element, input) => {
        element.textContent = '';
        element.classList.add('hidden');
        input.classList.remove('border-red-500');
        input.classList.add('border-gray-300');
    };

    // Real-time validation
    usernameInput.addEventListener('input', () => {
        if (!usernameRegex.test(usernameInput.value.trim())) {
            showError(usernameError, 'Username must be at least 3 characters (letters, numbers, underscore).');
        } else {
            clearError(usernameError, usernameInput);
        }
    });

    emailInput.addEventListener('input', () => {
        if (!emailRegex.test(emailInput.value.trim())) {
            showError(emailError, 'Please enter a valid email address.');
        } else {
            clearError(emailError, emailInput);
        }
    });

    phoneInput.addEventListener('input', () => {
        if (!phoneRegex.test(phoneInput.value.trim())) {
            showError(phoneError, 'Phone number is required and must be valid (at least 10 digits).');
        } else {
            clearError(phoneError, phoneInput);
        }
    });

    // Form Submission Validation
    form.addEventListener('submit', (e) => {
        let isValid = true;

        if (!usernameRegex.test(usernameInput.value.trim())) {
            showError(usernameError, 'Username must be at least 3 characters (letters, numbers, underscore).');
            isValid = false;
        }

        if (!emailRegex.test(emailInput.value.trim())) {
            showError(emailError, 'Please enter a valid email address.');
            isValid = false;
        }

        if (!phoneRegex.test(phoneInput.value.trim())) {
            showError(phoneError, 'Phone number is required and must be valid.');
            isValid = false;
        }

        if (!isValid) {
            e.preventDefault();
        }
    });
});
