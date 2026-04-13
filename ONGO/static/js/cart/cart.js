document.addEventListener('DOMContentLoaded', function () {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Check for empty cart on load
    checkEmptyCart();
    renderAppliedOffers(getInitialAppliedOffers());

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
                method: 'PATCH',
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
                const row = document.querySelector(`.cart-item[data-cart-id="${cartId}"]`);
                if (row) {
                    const qtyInput = row.querySelector('.qty-input');
                    const subtotalEL = document.getElementById('subtotal');
                    const totalEL = document.getElementById('total');
                    const discountEL = document.getElementById('discount');

                    if (qtyInput) qtyInput.value = data.new_quantity;
                    if (subtotalEL) subtotalEL.textContent = data.summary.items_subtotal;
                    if (totalEL) totalEL.textContent = data.summary.total_payable;
                    if (discountEL) discountEL.textContent = data.summary.cart_discount;

                    renderAppliedOffers(data.summary.applied_global_offers);
                }
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

    function getInitialAppliedOffers() {
        const offersDataEl = document.getElementById('applied-offers-data');
        if (!offersDataEl) return [];

        try {
            return JSON.parse(offersDataEl.textContent) || [];
        } catch (error) {
            console.error('Applied offers parse error:', error);
            return [];
        }
    }

    function renderAppliedOffers(offers) {
        const container = document.getElementById('applied-offers-container');
        if (!container) return;

        container.innerHTML = '';

        if (!Array.isArray(offers) || offers.length === 0) {
            return;
        }

        const wrapper = document.createElement('div');
        wrapper.className = 'mt-4 border-t pt-4';

        const title = document.createElement('h3');
        title.className = 'text-sm font-semibold text-gray-700 mb-2';
        title.textContent = 'Applied Offers:';

        const badges = document.createElement('div');
        badges.className = 'flex flex-wrap gap-2';

        offers.forEach((offer) => {
            const badge = document.createElement('span');
            badge.className = 'px-2 py-1 text-xs font-semibold rounded bg-purple-100 text-purple-800 border border-purple-200';
            badge.textContent = offer.name;
            badges.appendChild(badge);
        });

        wrapper.appendChild(title);
        wrapper.appendChild(badges);
        container.appendChild(wrapper);
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
                    location.reload();
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
