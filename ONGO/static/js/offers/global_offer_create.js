// Global Offer Create JS

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

    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(el => {
        el.classList.add(
            'w-5', 'h-5', 'text-blue-600', 'rounded', 'border-gray-300',
            'focus:ring-blue-500', 'transition'
        );
    });

    // Logic: Free Shipping hides Value; Percent shows Max Discount
    const discountTypeSelect = document.querySelector('select[name="discount_type"]');
    const valueField = document.querySelector('input[name="value"]');
    const maxDiscountField = document.querySelector('input[name="max_discount"]');

    const valueContainer = valueField ? valueField.closest('div.form-group') : null;
    const maxDiscountContainer = maxDiscountField ? maxDiscountField.closest('div.form-group') : null;

    function toggleFields() {
        if (!discountTypeSelect) return;

        const type = discountTypeSelect.value;

        // Handle Value Field (Hide for free_shipping)
        if (valueContainer) {
            if (type === 'free_shipping') {
                valueContainer.style.display = 'none';
            } else {
                valueContainer.style.display = 'block';
            }
        }

        // Handle Max Discount Field (Show only for percent)
        if (maxDiscountContainer) {
            if (type === 'percent') {
                maxDiscountContainer.style.display = 'block';
            } else {
                maxDiscountContainer.style.display = 'none';
            }
        }
    }

    if (discountTypeSelect) {
        discountTypeSelect.addEventListener('change', toggleFields);
        toggleFields();
    }

    // Initialize Flatpickr for Date Fields
    flatpickr("input#id_start_date", {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        time_24hr: true,
        defaultDate: new Date(),
        minDate: "today"
    });

    flatpickr("input#id_end_date", {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        time_24hr: true,
        minDate: "today"
    });
});
