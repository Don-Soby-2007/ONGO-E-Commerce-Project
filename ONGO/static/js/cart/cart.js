document.addEventListener('DOMContentLoaded', function () {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    if (document.querySelectorAll('.cart-item').length === 0) {
        document.querySelector('.cart-grid').innerHTML = `
                        <div class="col-span-full text-center py-20">
                            <h2 class="text-2xl font-bold mb-4">Your cart is empty</h2>
                            <a href="/product/listing" class="text-blue-600 hover:underline">Continue Shopping</a>
                        </div>
                    `;
    }

    //const cartItems = document.querySelectorAll('.cart-item');
    const subtotalEl = document.getElementById('subtotal');
    //const discountEl = document.getElementById('discount');
    const totalEl = document.getElementById('total');
    const itemCountEl = document.getElementById('item-count');


    // Initial calculation
    document.querySelectorAll('.cart-item').forEach(item => {
        updateRowTotal(item);
    });
    updateCartTotals();

    // Event Delegation for Quantity Buttons and Remove Buttons
    document.querySelector('.cart-items').addEventListener('click', async function (e) {
        // Increase Quantity
        if (e.target.closest('.qty-btn.plus')) {
            const row = e.target.closest('.cart-item');
            const cartId = row.dataset.cartId;
            await updateQuantity(cartId, 'increase', row);
            updateCartTotals();
            updateRowTotal(row)
        }

        // Decrease Quantity
        if (e.target.closest('.qty-btn.minus')) {
            const row = e.target.closest('.cart-item');
            const input = row.querySelector('.qty-input');
            let val = parseInt(input.value)
            const cartId = row.dataset.cartId;
            if (val > 1) {
                await updateQuantity(cartId, 'decrease', row);
                updateCartTotals();
                updateRowTotal(row)
            }
        }

        // Remove Item
        if (e.target.closest('.remove-btn')) {
            const row = e.target.closest('.cart-item');
            const cartId = row.dataset.cartId;

            Swal.fire({
                title: 'Are you sure?',
                text: "Do you really want to remove this item from your cart?",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Yes, remove it!'
            }).then(async (result) => {
                if (result.isConfirmed) {
                    await removeCart(cartId, row)
                    updateCartTotals();
                    updateRowTotal(row)
                    Swal.fire(
                        'Removed!',
                        'Item has been removed from your cart.',
                        'success'
                    )
                }
            })
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
        const price = parseFloat(row.dataset.price);
        const qty = parseInt(row.querySelector('.qty-input').value);
        let rowTotal = price * qty;

        const priceEl = row.querySelector('.item-price');
        if (priceEl) priceEl.textContent = `₹${rowTotal.toFixed(2)}`;
    }

    function updateCartTotals() {
        let subtotal = 0;
        let count = 0;

        document.querySelectorAll('.cart-item').forEach(item => {
            const price = parseFloat(item.dataset.price);
            const qty = parseInt(item.querySelector('.qty-input').value);
            subtotal += price * qty;
            count += qty
        });

        // Dummy discount logic (e.g., 10% if subtotal > 1000)
        // let discount = 0;
        // if (subtotal > 3000) {
        //     discount = subtotal * 0.1;
        // }

        let total = subtotal // - discount;

        // Update DOM
        if (subtotalEl) subtotalEl.textContent = `₹${subtotal.toFixed(2)}`;
        // if (discountEl) discountEl.textContent = `-₹${discount.toFixed(2)}`;
        if (totalEl) totalEl.textContent = `₹${total.toFixed(2)}`;
        if (itemCountEl) itemCountEl.textContent = `(${count} items)`;
    }

    async function updateQuantity(cartId, action, row) {
        const input = row.querySelector('.qty-input');
        const originalValue = input.value;

        try {
            const response = await fetch('/cart/update-quantity/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    cart_id: cartId,
                    action: action
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Update UI with new quantity
                input.value = data.new_quantity;
            } else {
                // Revert on error
                input.value = originalValue;
                alert(data.error || 'Failed to update quantity.');
            }
        } catch (error) {
            input.value = originalValue;
            console.error('AJAX error:', error);
            alert('Network error. Please try again.');
        }
    }

    async function removeCart(cartId, row) {
        try {
            const response = await fetch(`/cart/remove/${cartId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    cart_id: cartId,
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                row.remove();
                // Check if cart is empty
                if (document.querySelectorAll('.cart-item').length === 0) {
                    document.querySelector('.cart-grid').innerHTML = `
                        <div class="col-span-full text-center py-20">
                            <h2 class="text-2xl font-bold mb-4">Your cart is empty</h2>
                            <a href="/auth/product/listing/" class="text-blue-600 hover:underline">Continue Shopping</a>
                        </div>
                    `;
                }
            } else {
                // Revert on error
                input.value = originalValue;
                alert(data.error || 'Failed to update quantity.');
            }

        }
        catch (error) {
            console.error('AJAX error:', error);
            alert('Network error. Please try again.');
        }
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
