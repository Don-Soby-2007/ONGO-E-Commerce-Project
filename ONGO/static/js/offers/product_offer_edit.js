// Product Offer Edit JS

document.addEventListener('DOMContentLoaded', function () {
    // Apply Tailwind classes
    const inputs = document.querySelectorAll('input:not([type="checkbox"]):not([type="radio"]), select, textarea');
    inputs.forEach(el => {
        el.classList.add(
            'w-full', 'px-4', 'py-3', 'border', 'border-gray-200', 'rounded-lg',
            'focus:outline-none', 'focus:ring-2', 'focus:ring-blue-500/20',
            'focus:border-blue-500', 'transition-all', 'bg-gray-50', 'text-gray-800'
        );
    });

    // Toggle Switch JS hook: Add class to checkbox so CSS selector works
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(el => {
        el.classList.add('toggle-checkbox');
    });

    // Discount Toggle Logic
    const discountTypeSelect = document.querySelector('select[name="discount_type"]');
    const maxDiscountField = document.querySelector('input[name="max_discount_amount"]');
    const maxDiscountContainer = maxDiscountField ? maxDiscountField.closest('div.form-group') : null;

    function toggleFields() {
        if (!discountTypeSelect || !maxDiscountContainer) return;
        const type = discountTypeSelect.value;
        if (type === 'percent') {
            maxDiscountContainer.style.display = 'block';
        } else {
            maxDiscountContainer.style.display = 'none';
        }
    }

    if (discountTypeSelect) {
        discountTypeSelect.addEventListener('change', toggleFields);
        toggleFields(); // Init
    }

    // Initialize Flatpickr for Date Fields
    flatpickr("input#id_start_date", {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        time_24hr: true,
        // Edit page: default value comes from backend value="..." attribute, Flatpickr picks it up automatically
    });

    flatpickr("input#id_end_date", {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        time_24hr: true,
    });
});
