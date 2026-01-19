document.addEventListener('DOMContentLoaded', () => {
    const paymentCards = document.querySelectorAll('.payment-card');

    paymentCards.forEach(card => {
        const radio = card.querySelector('input[type="radio"]');
        const cardDetails = card.querySelector('.card-details');

        card.addEventListener('click', (e) => {
            // Unselect all
            paymentCards.forEach(c => {
                c.classList.remove('border-red-500', 'bg-red-50');
                c.classList.add('border-gray-200');
                const r = c.querySelector('input[type="radio"]');
                const details = c.querySelector('.card-details');
                if (r) r.checked = false;
                if (details) details.classList.add('hidden');
            });

            // Select current
            card.classList.remove('border-gray-200');
            card.classList.add('border-red-500', 'bg-red-50');
            if (radio) radio.checked = true;

            // Show details if needed (avoiding event bubbling issues by checking target)
            // But since input is inside label, redundant click might happen, but logic handles it
            if (cardDetails) {
                cardDetails.classList.remove('hidden');
            }
        });

        // Prevent click on input fields from triggering card click handler excessively
        // (though label triggers click anyway, we just want to ensure focus works)
        if (cardDetails) {
            cardDetails.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }
    });
});
