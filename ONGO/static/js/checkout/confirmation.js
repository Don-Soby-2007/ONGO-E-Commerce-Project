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
                    body: JSON.stringify({}) // No payload needed — all in session
                });

                const data = await response.json();

                console.log(data)

                if (response.ok) {
                    if (data.initiate_razorpay) {
                        const options = {
                            "key": data.key_id,
                            "amount": data.amount,
                            "currency": data.currency,
                            "name": "ONGO E-Commerce",
                            "description": "Order Payment",
                            "image": "https://res.cloudinary.com/ddynxusw2/image/upload/v1766473856/Ongo_Logo_di7890.svg", // Replace with your logo path if available
                            "order_id": data.razorpay_order_id,
                            "handler": async function (response) {
                                // Payment succeeded, verifying...
                                placeOrderBtn.innerHTML = '<i class="animate-spin mr-2" data-lucide="loader-2"></i> Verifying Payment...';

                                try {
                                    const verifyResponse = await fetch('/checkout/payment-verify/', {
                                        method: 'POST',
                                        headers: {
                                            'X-CSRFToken': getCookie('csrftoken'),
                                            'Content-Type': 'application/json'
                                        },
                                        body: JSON.stringify({
                                            razorpay_payment_id: response.razorpay_payment_id,
                                            razorpay_order_id: response.razorpay_order_id,
                                            razorpay_signature: response.razorpay_signature
                                        })
                                    });

                                    const verifyData = await verifyResponse.json();

                                    if (verifyData.success) {
                                        window.location.href = verifyData.redirect_url;
                                    } else {
                                        Swal.fire({
                                            title: 'Payment Verification Failed',
                                            text: verifyData.error || 'Please try again or contact support.',
                                            icon: 'error'
                                        }).then(() => {
                                            window.location.href = verifyData.redirect_url || '/checkout/order-failed/';
                                        });
                                    }
                                } catch (err) {
                                    console.error('Verification error:', err);
                                    Swal.fire('Verification Error', 'Network error during verification.', 'error');
                                    resetButton();
                                }
                            },
                            "prefill": {
                                "name": "don", // Can be filled from address if available
                                "email": "don@gmail.com", // Can be filled from user email
                                "contact": "+918921390755" // Can be filled from address phone
                            },
                            "theme": {
                                "color": "#ff4242"
                            },
                            "modal": {
                                "ondismiss": function () {
                                    resetButton();
                                    Swal.fire('Payment Cancelled', 'You cancelled the payment.', 'info');
                                }
                            }
                        };
                        const rzp1 = new Razorpay(options);
                        rzp1.on('payment.failed', function (response) {
                            Swal.fire({
                                title: 'Payment Failed',
                                text: response.error.description,
                                icon: 'error'
                            });
                            resetButton();
                        });
                        rzp1.open();

                    } else if (data.success) {

                        window.location.href = data.redirect_url || '/checkout/order-success/';

                    }
                } else {
                    const errorMsg = data.error || 'Order placement failed.';
                    Swal.fire('Order Failed', errorMsg, 'error');
                    resetButton();
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

