document.addEventListener('DOMContentLoaded', () => {
    const addressCards = document.querySelectorAll('.address-card');
    calculateOrderTotals()

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

function calculateOrderTotals() {
    let subtotal = 0;
    const cartItems = document.querySelectorAll('.flex.gap-3[data-price]');

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
    document.getElementById('subtotal').textContent = `₹${subtotal.toFixed(2)}`;
    document.getElementById('tax').textContent = `₹${tax.toFixed(2)}`;
    document.getElementById('total').textContent = `₹${total.toFixed(2)}`;

    // Optional: Update the "Including $12.00 in taxes" note
    const taxNote = document.getElementById('tax_not');
    if (taxNote) {
        taxNote.textContent = `Including ₹${tax.toFixed(2)} in taxes`;
    }
}