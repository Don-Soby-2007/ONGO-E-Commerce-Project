// Mobile Menu Toggle Logic
const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
const sidebar = document.getElementById('sidebar');

if (mobileMenuToggle && sidebar) {
    mobileMenuToggle.addEventListener('click', () => {
        const isClosed = sidebar.classList.contains('-translate-x-full');
        if (isClosed) {
            sidebar.classList.remove('-translate-x-full');
        } else {
            sidebar.classList.add('-translate-x-full');
        }
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth < 768) { // md breakpoint
            if (!sidebar.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
                sidebar.classList.add('-translate-x-full');
            }
        }
    });
}

// Show/Hide Password Logic
document.querySelectorAll('.toggle-password').forEach(button => {
    button.addEventListener('click', () => {
        const targetId = button.getAttribute('data-target');
        const input = document.getElementById(targetId);
        const icon = button.querySelector('[data-lucide]');

        if (input && icon) {
            if (input.type === 'password') {
                input.type = 'text';
                icon.setAttribute('data-lucide', 'eye-off');
            } else {
                input.type = 'password';
                icon.setAttribute('data-lucide', 'eye');
            }
            lucide.createIcons();
        }
    });
});

// Password Validation Functions
const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;

function validatePasswordStrength(password) {
    const requirements = {
        length: password.length >= 8,
        lowercase: /[a-z]/.test(password),
        uppercase: /[A-Z]/.test(password),
        number: /\d/.test(password),
        special: /[@$!%*?&]/.test(password)
    };

    return {
        isValid: PASSWORD_REGEX.test(password),
        requirements: requirements
    };
}

function updateRequirementUI(requirementId, isMet) {
    const element = document.getElementById(requirementId);
    if (!element) return;

    const icon = element.querySelector('[data-lucide]');

    if (isMet) {
        element.classList.remove('text-gray-500');
        element.classList.add('text-green-600');
        if (icon) {
            icon.setAttribute('data-lucide', 'check-circle');
        }
    } else {
        element.classList.remove('text-green-600');
        element.classList.add('text-gray-500');
        if (icon) {
            icon.setAttribute('data-lucide', 'circle');
        }
    }

    lucide.createIcons();
}

function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
        errorElement.classList.add('text-red-500');
    }
}

function hideError(elementId) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = '';
        errorElement.classList.add('hidden');
    }
}

// Form Elements
const passwordForm = document.getElementById('password-form');
const clearBtn = document.getElementById('clear-btn');
const oldPasswordInput = document.getElementById('old-password');
const newPasswordInput = document.getElementById('new-password');
const confirmPasswordInput = document.getElementById('confirm-password');
const passwordRequirements = document.getElementById('password-requirements');

// Live Validation for New Password
if (newPasswordInput) {
    newPasswordInput.addEventListener('focus', () => {
        if (passwordRequirements) {
            passwordRequirements.classList.remove('hidden');
        }
    });

    newPasswordInput.addEventListener('input', () => {
        const password = newPasswordInput.value;

        if (password.length === 0) {
            hideError('new-password-error');
            if (passwordRequirements) {
                passwordRequirements.classList.add('hidden');
            }
            return;
        }

        if (passwordRequirements) {
            passwordRequirements.classList.remove('hidden');
        }

        const validation = validatePasswordStrength(password);

        // Update requirement indicators
        updateRequirementUI('req-length', validation.requirements.length);
        updateRequirementUI('req-lowercase', validation.requirements.lowercase);
        updateRequirementUI('req-uppercase', validation.requirements.uppercase);
        updateRequirementUI('req-number', validation.requirements.number);
        updateRequirementUI('req-special', validation.requirements.special);

        // Show error if password is invalid
        if (!validation.isValid && password.length > 0) {
            showError('new-password-error', 'Password does not meet all requirements');
        } else {
            hideError('new-password-error');
        }

        // Also validate confirm password if it has value
        if (confirmPasswordInput && confirmPasswordInput.value) {
            validateConfirmPassword();
        }
    });

    newPasswordInput.addEventListener('blur', () => {
        const password = newPasswordInput.value;
        if (password.length === 0 && passwordRequirements) {
            passwordRequirements.classList.add('hidden');
        }
    });
}

// Live Validation for Confirm Password
function validateConfirmPassword() {
    const newPass = newPasswordInput ? newPasswordInput.value : '';
    const confirmPass = confirmPasswordInput ? confirmPasswordInput.value : '';

    if (confirmPass.length === 0) {
        hideError('confirm-password-error');
        return true;
    }

    if (newPass !== confirmPass) {
        showError('confirm-password-error', 'Passwords do not match');
        return false;
    } else {
        hideError('confirm-password-error');
        return true;
    }
}

if (confirmPasswordInput) {
    confirmPasswordInput.addEventListener('input', validateConfirmPassword);
}

// Clear Button
if (clearBtn) {
    clearBtn.addEventListener('click', () => {
        if (oldPasswordInput) {
            oldPasswordInput.value = '';
            hideError('old-password-error');
        }
        if (newPasswordInput) {
            newPasswordInput.value = '';
            hideError('new-password-error');
            if (passwordRequirements) {
                passwordRequirements.classList.add('hidden');
            }
        }
        if (confirmPasswordInput) {
            confirmPasswordInput.value = '';
            hideError('confirm-password-error');
        }
    });
}

// Form Submission with Validation
if (passwordForm) {
    passwordForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const oldPass = oldPasswordInput ? oldPasswordInput.value.trim() : '';
        const newPass = newPasswordInput ? newPasswordInput.value.trim() : '';
        const confirmPass = confirmPasswordInput ? confirmPasswordInput.value.trim() : '';

        let isValid = true;

        // Validate old password
        if (!oldPass) {
            showError('old-password-error', 'Please enter your current password');
            isValid = false;
        } else {
            hideError('old-password-error');
        }

        // Validate new password
        if (!newPass) {
            showError('new-password-error', 'Please enter a new password');
            isValid = false;
        } else {
            const validation = validatePasswordStrength(newPass);
            if (!validation.isValid) {
                showError('new-password-error', 'Password does not meet all requirements');
                isValid = false;
            } else {
                hideError('new-password-error');
            }
        }

        // Validate confirm password
        if (!confirmPass) {
            showError('confirm-password-error', 'Please confirm your new password');
            isValid = false;
        } else if (newPass !== confirmPass) {
            showError('confirm-password-error', 'Passwords do not match');
            isValid = false;
        } else {
            hideError('confirm-password-error');
        }

        if (!isValid) {
            return;
        }

        // If all validations pass, submit the form
        passwordForm.submit();
    });
}
