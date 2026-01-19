document.addEventListener('DOMContentLoaded', () => {
    const addressCards = document.querySelectorAll('.address-card');

    addressCards.forEach(card => {
        const radio = card.querySelector('input[type="radio"]');

        // Handle click on the card wrapper
        card.addEventListener('click', (e) => {
            // Uncheck all others style
            addressCards.forEach(c => {
                c.classList.remove('border-red-500', 'bg-red-50');
                c.classList.add('border-gray-200');
                const r = c.querySelector('input[type="radio"]');
                if (r) r.checked = false;
            });

            // Check current
            card.classList.remove('border-gray-200');
            card.classList.add('border-red-500', 'bg-red-50');
            if (radio) radio.checked = true;
        });
    });
});
