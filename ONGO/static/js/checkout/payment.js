document.addEventListener('DOMContentLoaded', () => {
    const paymentCards = document.querySelectorAll('.payment-card');
    const submitButton = document.getElementById('review-order-btn');
    const paymentRadios = document.querySelectorAll('input[name="payment_method"]');

    calculateOrderTotals();

    // Function to update button state
    function updateSubmitButton() {
        const isChecked = Array.from(paymentRadios).some(radio => radio.checked);
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

    // Initialize button state
    updateSubmitButton();

    // Re-check whenever a radio is clicked
    paymentRadios.forEach(radio => {
        radio.addEventListener('change', updateSubmitButton);
    });

    // Optional: Also handle card click (though change event should suffice)
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

            if (cardDetails) {
                cardDetails.classList.remove('hidden');
            }

            // Update button after selection
            updateSubmitButton();
        });

        if (cardDetails) {
            cardDetails.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }
    });
});

function calculateOrderTotals() {
    let subtotal = 0;
    const cartItems = document.querySelectorAll('.cart-items[data-price]');
    
    cartItems.forEach(item => {
        const price = parseFloat(item.getAttribute('data-price')) || 0;
        const quantity = parseInt(item.getAttribute('data-quantity')) || 0;
        subtotal += price * quantity;
    });

    subtotal = Math.round(subtotal * 100) / 100;

    const taxRate = 0.02;
    const tax = subtotal > 0 ? subtotal * taxRate : 0;
    const shipping = 0;
    const total = subtotal + tax + shipping;

    // Update DOM
    const subtotalEl = document.getElementById('subtotal');
    const taxEl = document.getElementById('tax');
    const totalEl = document.getElementById('total');

    if (subtotalEl) subtotalEl.textContent = `₹${subtotal.toFixed(2)}`;
    if (taxEl) taxEl.textContent = `₹${tax.toFixed(2)}`;
    if (totalEl) totalEl.textContent = `₹${total.toFixed(2)}`;
    
}