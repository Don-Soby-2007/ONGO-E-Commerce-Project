document.addEventListener('DOMContentLoaded', function () {
    // 1. Date Filter Logic
    const dateFilter = document.getElementById('date_filter');
    const customDateRange = document.getElementById('custom-date-range');

    if (dateFilter && customDateRange) {
        function toggleCustomDates() {
            if (dateFilter.value === 'custom') {
                customDateRange.classList.remove('hidden');
                customDateRange.classList.add('flex');
            } else {
                customDateRange.classList.add('hidden');
                customDateRange.classList.remove('flex');
            }
        }

        dateFilter.addEventListener('change', toggleCustomDates);
        toggleCustomDates(); // Initial check
    }

    // 2. Chart.js Doughnut Chart
    const ctx = document.getElementById('paymentChart');
    if (ctx) {
        const paymentData = JSON.parse(document.getElementById('payment-data-json').textContent);

        const labels = Object.keys(paymentData).map(key => key.toUpperCase());
        const dataValues = Object.values(paymentData).map(item => item.amount);

        const colors = {
            'cod': '#f97316',    // orange-500
            'online': '#3b82f6', // blue-500
            'wallet': '#a855f7'  // purple-500
        };

        const backgroundColors = Object.keys(paymentData).map(key => colors[key.toLowerCase()] || '#94a3b8');

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: dataValues,
                    backgroundColor: backgroundColors,
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                let label = context.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed !== null) {
                                    label += new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(context.parsed);
                                }
                                return label;
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }

    // 3. Progress Bar Animations
    const progressBars = document.querySelectorAll('.progress-bar-fill');
    setTimeout(() => {
        progressBars.forEach(bar => {
            const amount = parseFloat(bar.getAttribute('data-amount'));
            const total = parseFloat(bar.getAttribute('data-total'));
            const percentage = total > 0 ? (amount / total * 100).toFixed(1) : 0;
            bar.style.width = percentage + '%';
        });
    }, 300);

    // 4. Lucide Icons re-initialization (just in case)
    if (window.lucide) {
        window.lucide.createIcons();
    }
});
