document.addEventListener('DOMContentLoaded', () => {
    const placeOrderBtn = document.getElementById('place-order-btn');
    calculateOrderTotals()
    if (placeOrderBtn) {
        placeOrderBtn.addEventListener('click', () => {
            // Simulate order processing
            placeOrderBtn.innerHTML = '<i class="animate-spin mr-2" data-lucide="loader-2"></i> Processing...';
            placeOrderBtn.disabled = true;
            placeOrderBtn.classList.add('opacity-75', 'cursor-not-allowed');
            lucide.createIcons();

            setTimeout(() => {
                Swal.fire({
                    title: 'Order Placed!',
                    text: 'Thank you for your purchase. Your order #12345 has been confirmed.',
                    icon: 'success',
                    confirmButtonColor: '#DC2626',
                    confirmButtonText: 'Continue Shopping'
                }).then((result) => {
                    if (result.isConfirmed) {
                        window.location.href = '/products';
                    }
                });
            }, 2000);
        });
    }
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
