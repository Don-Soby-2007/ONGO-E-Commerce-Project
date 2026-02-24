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

    const pdfBtn = document.getElementById('export-pdf-btn')

    if(pdfBtn){
        pdfBtn.addEventListener('click', function(){
            const params = getFilterParams();
            params.append('get_pdf', 'true')

            window.location.href = `/admin/analytics/?${params.toString()}`
        })
    }

    const excelBtn = document.getElementById('export-excel-btn')

    if (excelBtn){
        excelBtn.addEventListener('click', function(){

            const params = getFilterParams();
            params.append('get_excel', 'true')

            window.location.href = `/admin/analytics/?${params.toString()}`
        })
    }

    function getFilterParams() {
        const startDate = document.querySelector('input[name="start_date"]').value;
        const endDate = document.querySelector('input[name="end_date"]').value;
        
        return new URLSearchParams({
            'date_filter': dateFilter.value,
            'start_date': startDate,
            'end_date': endDate
        });
    }

    // 2. Chart.js Doughnut Chart for Payments
    const ctx = document.getElementById('paymentChart');
    if (ctx) {
        const paymentDataEl = document.getElementById('payment-data-json');
        if (paymentDataEl) {
            try {
                const paymentData = JSON.parse(paymentDataEl.textContent);

                const labels = Object.keys(paymentData).map(key => key.toUpperCase());
                const dataValues = Object.values(paymentData).map(item => item.amount);

                const colors = {
                    'cod': '#f59e0b',    // amber-500
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
            } catch (error) {
                console.error("Error parsing payment data for chart", error);
            }
        }
    }

    // 3. Progress Bar Animations
    const progressBars = document.querySelectorAll('.progress-bar-fill');
    setTimeout(() => {
        progressBars.forEach(bar => {
            const amount = parseFloat(bar.getAttribute('data-amount') || 0);
            const total = parseFloat(bar.getAttribute('data-total') || 0);
            const percentage = total > 0 ? (amount / total * 100).toFixed(1) : 0;
            // Prevent going over 100% just in case
            bar.style.width = Math.min(percentage, 100) + '%';
        });
    }, 300);

    const dataBars = document.querySelectorAll('.data-bar-fill');
    setTimeout(() => {
        dataBars.forEach(bar => {
            const percentage = parseFloat(bar.getAttribute('data-percentage') || 0);
            bar.style.width = Math.min(percentage, 100) + '%';
        });
    }, 400);

    // 4. Lucide Icons re-initialization (just in case)
    if (window.lucide) {
        window.lucide.createIcons();
    }
});
