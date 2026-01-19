document.addEventListener('DOMContentLoaded', () => {
    const placeOrderBtn = document.getElementById('place-order-btn');

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
