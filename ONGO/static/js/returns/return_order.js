document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('return-form');
    const submitBtn = document.getElementById('submit-return-btn');
    const returnReasonTextarea = document.getElementById('return_reason');
    const itemCheckboxes = document.querySelectorAll('.item-checkbox');

    // Toggle quantity and reason inputs when checkbox is checked
    itemCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            const itemId = this.dataset.itemId;
            const reasonWrapper = document.getElementById(`reason-wrapper-${itemId}`);

            if (this.checked) {
                reasonWrapper.classList.add('active');
            } else {
                reasonWrapper.classList.remove('active');
            }

            validateForm();
        });
    });

    // Validate return reason on input
    if (returnReasonTextarea) {
        returnReasonTextarea.addEventListener('input', validateForm);
    }

    // Form validation function
    function validateForm() {
        let isValid = true;
        const returnReason = returnReasonTextarea.value.trim();
        const returnReasonError = document.getElementById('return-reason-error');

        // Check if at least one item is selected
        const anyItemSelected = Array.from(itemCheckboxes).some(cb => cb.checked);

        // Validate return reason
        if (!returnReason) {
            isValid = false;
            if (returnReasonError) {
                returnReasonError.textContent = 'Please provide a reason for the return.';
                returnReasonError.classList.add('active');
                returnReasonTextarea.classList.add('error');
            }
        } else {
            if (returnReasonError) {
                returnReasonError.classList.remove('active');
                returnReasonTextarea.classList.remove('error');
            }
        }

        // Validate selected items
        if (!anyItemSelected) {
            isValid = false;
        }

        // Enable/disable submit button
        if (submitBtn) {
            submitBtn.disabled = !isValid;
        }

        return isValid;
    }

    // Form submission validation
    if (form) {
        form.addEventListener('submit', function (e) {
            if (!validateForm()) {
                e.preventDefault();

                // Show error message
                Swal.fire({
                    icon: 'error',
                    title: 'Validation Error',
                    text: 'Please fill in all required fields and select at least one item to return.',
                    confirmButtonColor: '#dc2626'
                });
            }
        });
    }

    // Initial validation on page load
    validateForm();
});
