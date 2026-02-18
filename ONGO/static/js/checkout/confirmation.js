document.addEventListener('DOMContentLoaded', () => {
    const placeOrderBtn = document.getElementById('place-order-btn');

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
                    body: JSON.stringify({})
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Something went wrong');
                }

                if (data.initilaize_razorpay) {
                    console.log("called razorpay");

                    loadRazorpayScript().then(() => {
                        openRazorpayCheckout(data);
                    });
                }
                else if (data.success) {
                    window.location.href = data.redirect_url;
                }
            } catch (error) {
                console.error('Order error:', error);
                Swal.fire('Network Error', error.message || 'Please try again.', 'error');
                resetButton();
            }
        });
    }

    function openRazorpayCheckout(data) {
        console.log(typeof(data.amount_paisa));
        
        let options = {
            'key': data.key_id,
            'amount': String(data.amount_paisa),
            'currency': data.currency,
            'name': 'Ongo Store',
            'description': 'Order Payment',
            "image": "https://res.cloudinary.com/ddynxusw2/image/upload/v1766473856/Ongo_Logo_di7890.svg",
            'order_id': data.razorpay_order_id,
            'handler': function (response) {
                verifyPayment({
                    "razorpay_order_id": response.razorpay_order_id,
                    "razorpay_payment_id": response.razorpay_payment_id,
                    "razorpay_signature": response.razorpay_signature,
                    "internal_order_id": data.internal_order_id
                });
            },
            'prefill': {
                'name': data.username || '',
                'email': data.email || '',
                'contact': data.contact || ''
            },
            'theme': {
                color: '#ff4d4d'
            },
            'modal': {
                'ondismiss': function () {
                    Swal.fire('Cancelled', 'Payment was cancelled.', 'info');
                    resetButton();
                }
            }
        };

        const rzp = new Razorpay(options);
        rzp.open();
        console.log("razorpay opend");
    }

    async function verifyPayment(paymentData) {
        try {
            const response = await fetch('/checkout/verify-payment/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(paymentData)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                window.location.href = data.redirect_url;
            } else {
                throw new Error(data.error || 'Verification failed');
            }

        } catch (error) {
            console.error('Verification error:', error);
            Swal.fire('Payment Failed', error.message, 'error');
            resetButton();
        }
    }

    function loadRazorpayScript() {
        return new Promise((resolve) => {
            if (window.Razorpay) {
                resolve();
                return;
            }
            const script = document.createElement('script');
            script.src = 'https://checkout.razorpay.com/v1/checkout.js';
            script.onload = resolve;
            document.body.appendChild(script);
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

