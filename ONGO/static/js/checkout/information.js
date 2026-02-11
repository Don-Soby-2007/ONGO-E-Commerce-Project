document.addEventListener('DOMContentLoaded', () => {
    // Initial setup
    setupAddressSelection();
    setupModal();
    setupCheckoutValidation();
});

// Expose these for potential cross-function usage if needed, or keep scoped.
// Using a shared validation checker function.
let checkCheckoutFormValidity = () => { };

function setupAddressSelection() {
    const addressList = document.getElementById('address-list');

    // Use event delegation for address cards
    addressList.addEventListener('click', (e) => {
        const card = e.target.closest('.address-card');
        if (!card) return;

        // Deselect all others
        document.querySelectorAll('.address-card').forEach(c => {
            c.classList.remove('border-red-500', 'bg-red-50');
            c.classList.add('border-gray-200');
        });

        // Select clicked
        card.classList.remove('border-gray-200');
        card.classList.add('border-red-500', 'bg-red-50');

        // Check the radio input
        const radio = card.querySelector('input[type="radio"]');
        if (radio) {
            radio.checked = true;
            // Trigger validation check on selection change
            checkCheckoutFormValidity();
        }
    });

    // Initial visual state for checked inputs
    document.querySelectorAll('.address-card input[checked]').forEach(input => {
        const card = input.closest('.address-card');
        if (card) {
            card.classList.remove('border-gray-200');
            card.classList.add('border-red-500', 'bg-red-50');
        }
    });
}

function setupCheckoutValidation() {
    const continueButtons = document.querySelectorAll('.continue-payment-trigger');

    const isAddressSelected = () => {
        return document.querySelector('input[name="shipping_address"]:checked') !== null;
    };

    // UI Helpers
    const showFieldError = (input, errorEl, msg) => {
        input.classList.add('border-red-500', 'focus:ring-red-500');
        input.classList.remove('border-gray-300');
        if (errorEl) {
            errorEl.textContent = msg;
            errorEl.classList.remove('hidden');
        }
    };

    const clearFieldError = (input, errorEl) => {
        input.classList.remove('border-red-500', 'focus:ring-red-500');
        input.classList.add('border-gray-300');
        if (errorEl) {
            errorEl.classList.add('hidden');
            errorEl.textContent = '';
        }
    };

    // Update Button State
    checkCheckoutFormValidity = () => {
        const addressSelected = isAddressSelected();

        const isFormValid = addressSelected;

        continueButtons.forEach(btn => {
            if (isFormValid) {
                // Enable
                btn.classList.remove('opacity-50', 'cursor-not-allowed', 'pointer-events-none');
                btn.classList.add('hover:bg-red-700'); // Restore hover
            } else {
                // Disable
                btn.classList.add('opacity-50', 'cursor-not-allowed', 'pointer-events-none');
                btn.classList.remove('hover:bg-red-700');
            }
        });

        return isFormValid;
    };


    // Button Click Interception (Extra safety, though pointer-events-none handles most)
    continueButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (!checkCheckoutFormValidity()) {
                e.preventDefault();

                // Address error?
                if (!isAddressSelected()) {
                    const list = document.getElementById('address-list');
                    list.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    });

    // Initial check
    checkCheckoutFormValidity();
}

function setupModal() {
    const modal = document.getElementById('address-modal');
    const openBtn = document.getElementById('open-address-modal');
    const closeBtn = document.getElementById('close-modal-btn');
    const cancelBtn = document.getElementById('cancel-modal-btn');
    const form = document.getElementById('add-address-form');
    const errorContainer = document.getElementById('modal-error-message');

    if (!modal || !openBtn) return;

    // Open
    openBtn.addEventListener('click', (e) => {
        e.preventDefault();
        modal.classList.remove('hidden');
    });

    // Close functions
    const closeModal = () => {
        modal.classList.add('hidden');
        form.reset();
        clearAllErrors();
        errorContainer.classList.add('hidden');
        errorContainer.textContent = '';
    };

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    // Validation Logic
    form.setAttribute('novalidate', true);

    const rules = {
        fullName: {
            test: (value) => /^[a-zA-Z\s]{3,}$/.test(value.trim()),
            message: 'Please enter a valid name (letters only, min 3 chars)'
        },
        phoneNumber: {
            test: (value) => /^\d{10}$/.test(value.trim()),
            message: 'Enter a valid 10-digit phone number'
        },
        streetAddress: {
            test: (value) => /[a-zA-Z]/.test(value) && value.trim().length > 5,
            message: 'Address must contain letters and be descriptive'
        },
        city: {
            test: (value) => /^[a-zA-Z\s]+$/.test(value.trim()),
            message: 'City must contain only letters'
        },
        state: {
            test: (value) => /^[a-zA-Z\s]+$/.test(value.trim()),
            message: 'State must contain only letters'
        },
        postalCode: {
            test: (value) => /^\d{5,8}$/.test(value.trim()),
            message: 'Enter a valid pincode (5-8 digits)'
        },
        country: {
            test: (value) => value.trim() !== '',
            message: 'Please select a country'
        }
    };

    const validateField = (input) => {
        const name = input.name;
        const rule = rules[name];
        if (!rule) return true;

        const isValid = rule.test(input.value);
        if (!isValid) {
            showError(input, rule.message);
        } else {
            clearError(input);
        }
        return isValid;
    };

    const showError = (input, msg) => {
        // Remove existing error if any
        clearError(input);

        // Style input
        input.classList.add('border-red-500', 'focus:ring-red-500');
        input.classList.remove('border-gray-300', 'focus:ring-black');

        // Create error message
        const errorDiv = document.createElement('p');
        errorDiv.className = 'text-red-500 text-xs mt-1 ml-1 field-error';
        errorDiv.textContent = msg;
        input.parentNode.appendChild(errorDiv);
    };

    const clearError = (input) => {
        input.classList.remove('border-red-500', 'focus:ring-red-500');
        input.classList.add('border-gray-300', 'focus:ring-black');
        const error = input.parentNode.querySelector('.field-error');
        if (error) {
            error.remove();
        }
    };

    const clearAllErrors = () => {
        form.querySelectorAll('.field-error').forEach(e => e.remove());
        form.querySelectorAll('input, select').forEach(input => {
            input.classList.remove('border-red-500', 'focus:ring-red-500');
            input.classList.add('border-gray-300', 'focus:ring-black');
        });
    };

    // Real-time validation
    form.querySelectorAll('input, select').forEach(input => {
        input.addEventListener('input', () => {

            validateField(input);
        });

        input.addEventListener('blur', () => {
            validateField(input);
        });
    });

    // Form Submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Validate all
        let isFormValid = true;
        let firstInvalidInput = null;

        form.querySelectorAll('input, select').forEach(input => {
            if (rules[input.name]) {
                if (!validateField(input)) {
                    isFormValid = false;
                    if (!firstInvalidInput) firstInvalidInput = input;
                }
            }
        });

        if (!isFormValid) {
            if (firstInvalidInput) firstInvalidInput.focus();
            return;
        }

        const formData = new FormData(form);
        const url = form.getAttribute('action');

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {

                closeModal();
                window.location.reload();

                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        toast: true,
                        animation: true,
                        position: 'top-end',
                        icon: 'success',
                        title: 'Saved successfully!',
                        showConfirmButton: false,
                        timer: 2000,
                        timerProgressBar: true,
                        didOpen: (toast) => {
                            toast.addEventListener('mouseenter', Swal.stopTimer);
                            toast.addEventListener('mouseleave', Swal.resumeTimer);
                        }
                    });
                }
            } else {
                // Backend Error
                errorContainer.textContent = data.message || 'An error occurred. Please try again.';
                errorContainer.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Error:', error);
            errorContainer.textContent = 'Network error. Please try again.';
            errorContainer.classList.remove('hidden');
        }
    });
}
