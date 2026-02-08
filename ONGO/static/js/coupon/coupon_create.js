document.addEventListener('DOMContentLoaded', function () {
    const typeSelect = document.getElementById('id_discount_type');
    const valueFieldContainer = document.getElementById('valueField');
    const maxDiscountContainer = document.getElementById('maxDiscountField');
    const valuePrefix = document.getElementById('valuePrefix');
    const valueSuffix = document.getElementById('valueSuffix');
    const statusCheckbox = document.getElementById('id_active');
    const statusLabel = document.getElementById('statusLabel');

    function updateFormState() {
        const type = typeSelect.value;

        // Handle Value Field visibility and hints
        if (type === 'free_shipping') {
            valueFieldContainer.style.display = 'none';
        } else {
            valueFieldContainer.style.display = 'block';
            if (type === 'percent') {
                valuePrefix.textContent = '';
                valueSuffix.textContent = '%';
            } else {
                valuePrefix.textContent = '₹';
                valueSuffix.textContent = '';
            }
        }

        // Handle Max Discount visibility
        if (type === 'percent') {
            maxDiscountContainer.style.display = 'block';
        } else {
            maxDiscountContainer.style.display = 'none';
        }
    }

    // Status label updater
    function updateStatusLabel() {
        if (statusCheckbox.checked) {
            statusLabel.textContent = 'Active';
            statusLabel.className = 'ml-3 text-sm font-medium text-green-600';
        } else {
            statusLabel.textContent = 'Inactive';
            statusLabel.className = 'ml-3 text-sm font-medium text-gray-500';
        }
    }

    // Attach listeners
    if (typeSelect) {
        typeSelect.addEventListener('change', updateFormState);
        // Initial call
        updateFormState();
    }

    if (statusCheckbox) {
        statusCheckbox.addEventListener('change', updateStatusLabel);
        updateStatusLabel();
    }
});
