// Product Offer Create JS

document.addEventListener('DOMContentLoaded', function () {
    // Apply Tailwind classes to Django widgets
    const inputs = document.querySelectorAll('input:not([type="checkbox"]):not([type="radio"]), select, textarea');
    inputs.forEach(el => {
        el.classList.add(
            'w-full', 'px-4', 'py-3', 'border', 'border-gray-200', 'rounded-lg',
            'focus:outline-none', 'focus:ring-2', 'focus:ring-blue-500/20',
            'focus:border-blue-500', 'transition-all', 'bg-gray-50', 'text-gray-800'
        );
    });

    // Specific styling for checkboxes if any (ProductOffer doesn't have active, but just in case)
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(el => {
        el.classList.add(
            'w-5', 'h-5', 'text-blue-600', 'rounded', 'border-gray-300',
            'focus:ring-blue-500', 'transition'
        );
    });

    // Logic for Discount Type Toggle
    const discountTypeSelect = document.querySelector('select[name="discount_type"]');
    const maxDiscountField = document.querySelector('input[name="max_discount_amount"]');

    // Find containers to hide/show entire group
    // Assuming structure: div > label + input
    const maxDiscountContainer = maxDiscountField ? maxDiscountField.closest('div.form-group') : null;

    function toggleFields() {
        if (!discountTypeSelect || !maxDiscountContainer) return;

        const type = discountTypeSelect.value;

        // Show max_discount only for 'percent'
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
    flatpickr("input[name*='date']", {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        time_24hr: true,
        allowInput: true,
        altInput: true,
        altFormat: "F j, Y at H:i",
        minDate: "today"
    });
});
