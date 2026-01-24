document.addEventListener('DOMContentLoaded', () => {
    const placeOrderBtn = document.getElementById('place-order-btn');
    calculateOrderTotals();

    if (placeOrderBtn) {
        placeOrderBtn.addEventListener('click', async () => {
            placeOrderBtn.innerHTML = '<i class="animate-spin mr-2" data-lucide="loader-2"></i> Processing...';
            placeOrderBtn.disabled = true;
            placeOrderBtn.classList.add('opacity-75', 'cursor-not-allowed');
            lucide.createIcons();

            try {
                const response = await fetch('/checkout/place-order/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({}) // No payload needed — all in session
                });

                const data = await response.json();

                console.log(data)

                if (response.ok) {
                    if (data.initiate_razorpay) {
                        // 🚧 Phase 1: Just show alert (replace later with Razorpay SDK)
                        Swal.fire({
                            title: 'Payment Required',
                            text: `Please complete payment of ₹${data.amount.toFixed(2)} via Razorpay.`,
                            icon: 'info',
                            confirmButtonColor: '#3b82f6',
                            confirmButtonText: 'Proceed to Payment'
                        }).then((result) => {
                            if (result.isConfirmed) {
                                // In future: open Razorpay checkout here
                                alert('Razorpay integration placeholder. Redirecting...');
                                window.location.href = '/checkout/success/'; // temporary
                            }
                        });
                    } else if (data.success) {
                        
                        window.location.href = data.redirect_url || '/checkout/order-success/';

                    }
                } else {
                    window.location.href = '/checkout/order-failed'
                }
            } catch (error) {
                console.error('Order error:', error);
                Swal.fire('Network Error', 'Please try again.', 'error');
                resetButton();
            }
        });
    }

    function resetButton() {
        placeOrderBtn.innerHTML = 'Place Order';
        placeOrderBtn.disabled = false;
        placeOrderBtn.classList.remove('opacity-75', 'cursor-not-allowed');
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
