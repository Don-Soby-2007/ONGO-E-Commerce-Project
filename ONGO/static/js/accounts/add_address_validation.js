document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    // Select inputs by ID
    const inputs = {
        fullName: document.getElementById('fullName'),
        streetAddress: document.getElementById('streetAddress'),
        phoneNumber: document.getElementById('phoneNumber'),
        city: document.getElementById('city'),
        state: document.getElementById('state'),
        postalCode: document.getElementById('postalCode'),
        country: document.getElementById('country')
    };

    // Strict Regex Patterns
    const patterns = {
        // Letters and spaces only, min 3 chars. No numbers or special chars.
        fullName: /^[a-zA-Z\s]{3,}$/,

        // Alphanumeric, spaces, comma, dot, dash, slash, hash. Min 5 chars.
        streetAddress: /^[a-zA-Z0-9\s,.\-/#]{5,}$/,

        // 10-15 digits, optional '+' prefix.
        phoneNumber: /^\+?[0-9]{10,15}$/,

        // Letters and spaces only.
        city: /^[a-zA-Z\s]+$/,

        // Letters and spaces only.
        state: /^[a-zA-Z\s]+$/,

        // Strict 5 or 6 digits.
        postalCode: /^[0-9]{5,6}$/,

        // Not empty
        country: /.+/
    };

    const messages = {
        fullName: "Name must contain only letters and spaces (min 3 chars).",
        streetAddress: "Address seems invalid. Use letters, numbers, and common symbols.",
        phoneNumber: "Enter a valid phone number (10-15 digits).",
        city: "City must contain only letters.",
        state: "State must contain only letters.",
        postalCode: "Postal code must be 5-6 digits.",
        country: "Please select a country."
    };

    // Utility: Show Error
    const showError = (input, msg) => {
        // Ensure error container exists
        let errorP = input.parentNode.querySelector('.error-msg');
        if (!errorP) {
            errorP = document.createElement('p');
            errorP.className = 'text-xs text-red-500 mt-1 hidden error-msg';
            input.parentNode.appendChild(errorP);
        }

        errorP.textContent = msg;
        errorP.classList.remove('hidden');
        input.classList.add('border-red-500', 'focus:ring-red-500');
        input.classList.remove('border-gray-200', 'focus:ring-brand-black');
    };

    // Utility: Clear Error
    const clearError = (input) => {
        const errorP = input.parentNode.querySelector('.error-msg');
        if (errorP) {
            errorP.classList.add('hidden');
        }
        input.classList.remove('border-red-500', 'focus:ring-red-500');
        input.classList.add('border-gray-200', 'focus:ring-brand-black');
    };

    // Validate Single Field
    const validateField = (input, fieldName) => {
        const value = input.value.trim();
        // Country is a select, so check value directly. Others check pattern.
        if (fieldName === 'country') {
            if (!value) {
                showError(input, messages[fieldName]);
                return false;
            }
        } else {
            if (!patterns[fieldName].test(value)) {
                showError(input, messages[fieldName]);
                // Special check for empty required fields to give "Required" message? 
                // Currently regex handles empty implicitly (e.g. + means 1 or more)
                if (value === '') showError(input, "This field is required.");
                return false;
            }
        }
        clearError(input);
        return true;
    };

    // Attach Input Listeners
    for (const [fieldName, inputElement] of Object.entries(inputs)) {
        if (inputElement) {
            inputElement.addEventListener('input', () => validateField(inputElement, fieldName));
            inputElement.addEventListener('blur', () => validateField(inputElement, fieldName));
        }
    }

    // Form Submit Listener
    if (form) {
        form.addEventListener('submit', (e) => {
            let isValid = true;
            for (const [fieldName, inputElement] of Object.entries(inputs)) {
                if (inputElement) {
                    if (!validateField(inputElement, fieldName)) {
                        isValid = false;
                    }
                }
            }

            if (!isValid) {
                e.preventDefault();
            }
        });
    }
});
