document.addEventListener('DOMContentLoaded', function () {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Check for empty cart on load
    checkEmptyCart();

    // Event Delegation for Quantity Buttons and Remove Buttons
    const cartItemsContainer = document.querySelector('.cart-items');
    if (cartItemsContainer) {
        cartItemsContainer.addEventListener('click', async function (e) {

            // Quantity Increase
            if (e.target.closest('.qty-btn.plus')) {
                const btn = e.target.closest('.qty-btn.plus');
                if (btn.disabled) return;

                const row = btn.closest('.cart-item');
                const cartId = row.dataset.cartId;
                const updateUrl = cartItemsContainer.dataset.updateUrl;

                await updateQuantity(updateUrl, cartId, 'increase');
            }

            // Quantity Decrease
            if (e.target.closest('.qty-btn.minus')) {
                const btn = e.target.closest('.qty-btn.minus');
                if (btn.disabled) return;

                const row = btn.closest('.cart-item');
                const cartId = row.dataset.cartId;
                const updateUrl = cartItemsContainer.dataset.updateUrl;

                await updateQuantity(updateUrl, cartId, 'decrease');
            }

            // Remove Item
            if (e.target.closest('.remove-btn')) {
                const btn = e.target.closest('.remove-btn');
                const removeUrl = btn.dataset.removeUrl;

                confirmRemove(removeUrl);
            }
        });
    }

    async function updateQuantity(url, cartId, action) {
        try {
            const response = await fetch(url, {
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
                // Reload to update totals and UI from backend
                window.location.reload();
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Oops...',
                    text: data.error || 'Cannot update quantity',
                    toast: true,
                    position: 'top-end',
                    showConfirmButton: false,
                    timer: 3000
                });
            }
        } catch (error) {
            console.error('AJAX error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Network Error',
                text: 'Please try again later.',
            });
        }
    }

    function confirmRemove(url) {
        Swal.fire({
            title: 'Are you sure?',
            text: "Do you really want to remove this item?",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Yes, remove it!'
        }).then(async (result) => {
            if (result.isConfirmed) {
                await removeCartItem(url);
            }
        });
    }

    async function removeCartItem(url) {
        try {
            const response = await fetch(url, {
                method: 'POST', // The view likely expects POST for deletion safety
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({})
            });

            const data = await response.json();

            if (response.ok && data.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Removed!',
                    text: 'Item has been removed.',
                    timer: 1500,
                    showConfirmButton: false
                }).then(() => {
                    window.location.reload();
                });
            } else {
                Swal.fire('Error', data.error || 'Failed to remove item.', 'error');
            }

        } catch (error) {
            console.error('AJAX error:', error);
            Swal.fire('Error', 'Network error. Please try again.', 'error');
        }
    }

    function checkEmptyCart() {
        if (document.querySelectorAll('.cart-item').length === 0) {
            const grid = document.querySelector('.cart-grid');
            if (grid) {
                grid.innerHTML = `
                    <div class="col-span-full text-center py-20">
                        <h2 class="text-2xl font-bold mb-4 text-gray-800">Your cart is empty</h2>
                        <a href="/product/listing" class="text-blue-600 hover:text-blue-800 font-medium inline-flex items-center gap-2">
                             Start Shopping
                        </a>
                    </div>
                `;
            }
            // Hide order summary if cart is empty (optional, but good UX)
            const summary = document.querySelector('.order-summary-container');
            if (summary) summary.style.display = 'none';
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
