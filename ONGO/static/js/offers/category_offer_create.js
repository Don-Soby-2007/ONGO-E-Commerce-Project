// Category Offer Create JS

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

    // Discount Logic
    const discountTypeSelect = document.querySelector('select[name="discount_type"]');
    // Category offer doesn't have max_discount in fields list provided in prompt details
    // It has value and min_items.
    // If logic needed for fixed_per_item vs percent?
    // User Instructions: "If discount_type = percent: Show max_discount field".
    // CategoryOffer doesn't have max_discount field in the provided list: ['name', ..., 'value', 'min_items']
    // So no toggle logic required for max_discount availability here.

    // However, we apply the styles.

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
