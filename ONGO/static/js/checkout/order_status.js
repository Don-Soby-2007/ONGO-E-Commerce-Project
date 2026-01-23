/* Order Status Page Logic */

document.addEventListener('DOMContentLoaded', () => {
    // Re-initialize icons just in case, though base template does it
    if (window.lucide) {
        window.lucide.createIcons();
    }

    // Copy Order ID functionality
    const copyButton = document.getElementById('copyOrderIdBtn');
    if (copyButton) {
        copyButton.addEventListener('click', () => {
            const orderId = copyButton.getAttribute('data-order-id');
            if (orderId) {
                navigator.clipboard.writeText(orderId).then(() => {
                    // Show tooltip or change icon temporarily
                    const originalIcon = copyButton.innerHTML;
                    copyButton.innerHTML = `<i data-lucide="check" class="w-4 h-4 text-green-600"></i><span class="ml-1 text-sm text-green-600">Copied</span>`;
                    if (window.lucide) window.lucide.createIcons();

                    setTimeout(() => {
                        copyButton.innerHTML = originalIcon;
                        if (window.lucide) window.lucide.createIcons();
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy text: ', err);
                });
            }
        });
    }

    // Optional: Add staggereed animation delay to timeline items
    const timelineItems = document.querySelectorAll('.order-timeline-step');
    timelineItems.forEach((item, index) => {
        item.style.animationDelay = `${index * 0.2}s`;
        item.style.opacity = '0';
        item.style.animation = `fadeUp 0.5s ease-out ${index * 0.2 + 0.5}s forwards`;
    });
});
