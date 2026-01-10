document.addEventListener('DOMContentLoaded', function () {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    const cartItems = document.querySelectorAll('.cart-item');
    const subtotalEl = document.getElementById('subtotal');
    const discountEl = document.getElementById('discount');
    const totalEl = document.getElementById('total');
    const itemCountEl = document.getElementById('item-count');

    // Initial calculation
    updateCartTotals();

    // Event Delegation for Quantity Buttons and Remove Buttons
    document.querySelector('.cart-items').addEventListener('click', function (e) {
        // Increase Quantity
        if (e.target.closest('.qty-btn.plus')) {
            const row = e.target.closest('.cart-item');
            const input = row.querySelector('.qty-input');
            let val = parseInt(input.value);
            input.value = val + 1;
            updateRowTotal(row);
            updateCartTotals();
        }

        // Decrease Quantity
        if (e.target.closest('.qty-btn.minus')) {
            const row = e.target.closest('.cart-item');
            const input = row.querySelector('.qty-input');
            let val = parseInt(input.value);
            if (val > 1) {
                input.value = val - 1;
                updateRowTotal(row);
                updateCartTotals();
            }
        }

        // Remove Item
        if (e.target.closest('.remove-btn')) {
            const row = e.target.closest('.cart-item');
            row.remove();
            updateCartTotals();

            // Check if cart is empty
            if (document.querySelectorAll('.cart-item').length === 0) {
                document.querySelector('.cart-grid').innerHTML = `
                    <div class="col-span-full text-center py-20">
                        <h2 class="text-2xl font-bold mb-4">Your cart is empty</h2>
                        <a href="#" class="text-blue-600 hover:underline">Continue Shopping</a>
                    </div>
                `;
            }
        }
    });

    // Handle Manual Input Change
    document.querySelectorAll('.qty-input').forEach(input => {
        input.addEventListener('change', function (e) {
            let val = parseInt(e.target.value);
            if (isNaN(val) || val < 1) {
                e.target.value = 1;
            }
            updateRowTotal(e.target.closest('.cart-item'));
            updateCartTotals();
        });
    });

    function updateRowTotal(row) {
        // In a real app, you might update a per-row total display here.
        // For this design, we just need to know the price * qty for the grand total.
    }

    function updateCartTotals() {
        let subtotal = 0;
        let count = 0;

        document.querySelectorAll('.cart-item').forEach(item => {
            const price = parseFloat(item.dataset.price);
            const qty = parseInt(item.querySelector('.qty-input').value);
            subtotal += price * qty;
            count += qty;
        });

        // Dummy discount logic (e.g., 10% if subtotal > 1000)
        let discount = 0;
        if (subtotal > 3000) {
            discount = subtotal * 0.1;
        }

        let total = subtotal - discount;

        // Update DOM
        if (subtotalEl) subtotalEl.textContent = `₹${subtotal.toFixed(2)}`;
        if (discountEl) discountEl.textContent = `-₹${discount.toFixed(2)}`;
        if (totalEl) totalEl.textContent = `₹${total.toFixed(2)}`;
        if (itemCountEl) itemCountEl.textContent = `(${count} items)`;
    }
});
