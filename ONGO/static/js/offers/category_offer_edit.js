// Category Offer Edit JS

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

    // Toggle Switch JS hook
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(el => {
        el.classList.add('toggle-checkbox');
    });

    // Initialize Flatpickr
    flatpickr("input#id_start_date", {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        time_24hr: true,
    });

    flatpickr("input#id_end_date", {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        time_24hr: true,
    });
});
