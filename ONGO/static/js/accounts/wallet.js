document.addEventListener('DOMContentLoaded', () => {
    // Animate Balance Counting Effect
    const balanceElement = document.querySelector('.balance-amount');
    if (balanceElement) {
        // Parse the float, ignoring commas if they existed, though Django's floatformat usually returns plain numbers
        const targetBalanceStr = balanceElement.getAttribute('data-balance') || '0';
        const targetBalance = parseFloat(targetBalanceStr.replace(/,/g, ''));

        if (!isNaN(targetBalance) && targetBalance > 0) {
            const duration = 1500; // ms
            const frameRate = 30; // ms per frame
            const totalFrames = Math.round(duration / frameRate);
            let currentFrame = 0;

            // Easing function (easeOutExpo)
            const easeOut = t => t === 1 ? 1 : 1 - Math.pow(2, -10 * t);

            const counter = setInterval(() => {
                currentFrame++;
                const progress = currentFrame / totalFrames;
                const currentVal = targetBalance * easeOut(progress);

                // Format to 2 decimal places with currency symbol and commas
                balanceElement.textContent = '₹' + currentVal.toLocaleString('en-IN', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });

                if (currentFrame >= totalFrames) {
                    clearInterval(counter);
                    // Final exact value
                    balanceElement.textContent = '₹' + targetBalance.toLocaleString('en-IN', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                }
            }, frameRate);
        } else {
            // Unchanged if NaN or zero, just format it
            if (!isNaN(targetBalance)) {
                balanceElement.textContent = '₹' + targetBalance.toLocaleString('en-IN', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
        }
    }

    // Animate Rows Fade-In
    const rows = document.querySelectorAll('.transaction-row');
    if (rows.length > 0) {
        const observerOptions = {
            root: null,
            rootMargin: '0px',
            threshold: 0.1
        };

        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Add staggered delay based on row's vertical position relative to others in the viewport
                    // For simplicity, we just use a small delay based on the index in the NodeList
                    const index = Array.from(rows).indexOf(entry.target);
                    const delay = index * 50; // 50ms per row delay

                    setTimeout(() => {
                        entry.target.classList.remove('opacity-0', 'translate-y-2');
                        entry.target.classList.add('opacity-100', 'translate-y-0');
                    }, delay);

                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        rows.forEach(row => {
            observer.observe(row);
            // Ensure transition property is set for smooth animations
            row.style.transition = 'opacity 0.4s ease-out, transform 0.4s ease-out, background-color 0.15s ease-in-out';
        });
    }
});
