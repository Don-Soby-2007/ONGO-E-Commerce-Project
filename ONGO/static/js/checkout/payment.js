document.addEventListener('DOMContentLoaded', () => {
    const paymentCards = document.querySelectorAll('.payment-card');
    const submitButton = document.getElementById('review-order-btn');
    const paymentRadios = document.querySelectorAll('input[name="payment_method"]');

    function syncCardStyles() {
        paymentCards.forEach(card => {
            const radio = card.querySelector('input[type="radio"]');
            if (!radio) {
                return;
            }

            if (radio.checked) {
                card.classList.remove('border-gray-200');
                card.classList.add('border-red-500', 'bg-red-50');
            } else {
                card.classList.remove('border-red-500', 'bg-red-50');
                card.classList.add('border-gray-200');
            }
        });
    }

    function updateSubmitButton() {
        const isChecked = Array.from(paymentRadios).some(radio => radio.checked && !radio.disabled);
        if (isChecked) {
            submitButton.disabled = false;
            submitButton.classList.remove('opacity-50', 'cursor-not-allowed');
            submitButton.classList.add('bg-red-600', 'hover:bg-red-700');
        } else {
            submitButton.disabled = true;
            submitButton.classList.add('opacity-50', 'cursor-not-allowed');
            submitButton.classList.remove('bg-red-600', 'hover:bg-red-700');
        }
    }

    function syncUI() {
        syncCardStyles();
        updateSubmitButton();
    }

    updateSubmitButton();
    syncCardStyles();

    paymentRadios.forEach(radio => {
        radio.addEventListener('change', syncUI);
    });

    paymentCards.forEach(card => {
        const radio = card.querySelector('input[type="radio"]');
        if (!radio) {
            return;
        }

        card.addEventListener('click', () => {
            if (radio.disabled) {
                return;
            }

            radio.checked = true;
            radio.dispatchEvent(new Event('change', { bubbles: true }));
        });
    });

    syncUI();
});
