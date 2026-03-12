// dashboard.js
document.addEventListener('DOMContentLoaded', function() {
    
    Chart.defaults.font.family = 'Inter';
    Chart.defaults.color = '#6b7280';

    // Helper to extract JSON data safely
    function getJsonData(elementId) {
        const el = document.getElementById(elementId);
        if (el) {
            try {
                return JSON.parse(el.textContent);
            } catch (e) {
                console.error(`Error parsing JSON from ${elementId}:`, e);
                return [];
            }
        }
        return [];
    }

    // --- 1. SALES CHART ---
    const salesCtx = document.getElementById('salesChart');
    if (salesCtx) {
        let labels = getJsonData('chartDataLabels');
        let values = getJsonData('chartDataValues');

        new Chart(salesCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Revenue (₹)',
                    data: values,
                    borderColor: '#3b82f6', // Tailwind blue-500
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    pointBackgroundColor: '#ffffff',
                    pointBorderColor: '#3b82f6',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    fill: true,
                    tension: 0.3 // Smooth curves
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1f2937',
                        padding: 12,
                        titleFont: { size: 13, family: 'Inter' },
                        bodyFont: { size: 14, family: 'Inter', weight: 'bold' },
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return '₹ ' + context.parsed.y.toLocaleString('en-IN', {
                                    maximumFractionDigits: 2
                                });
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false, drawBorder: false },
                        ticks: { font: { family: 'Inter', size: 12 }, color: '#6b7280' }
                    },
                    y: {
                        grid: { color: '#f3f4f6', drawBorder: false },
                        ticks: {
                            font: { family: 'Inter', size: 12 },
                            color: '#6b7280',
                            callback: function(value) {
                                if (value >= 1000) {
                                    return '₹' + (value / 1000).toFixed(1) + 'k';
                                }
                                return '₹' + value;
                            }
                        },
                        beginAtZero: true
                    }
                },
                interaction: { intersect: false, mode: 'index' },
            }
        });
    }

    // --- 2. BEST SELLING PRODUCTS CHART ---
    const prodCtx = document.getElementById('productsChart');
    if (prodCtx) {
        let prodLabels = getJsonData('productDataLabels');
        let prodValues = getJsonData('productDataValues');

        new Chart(prodCtx, {
            type: 'bar', // OR 'doughnut'
            data: {
                labels: prodLabels,
                datasets: [{
                    label: 'Units Sold',
                    data: prodValues,
                    backgroundColor: 'rgba(139, 92, 246, 0.8)', // violet-500
                    borderColor: 'rgba(139, 92, 246, 1)',
                    borderWidth: 1,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y', // Makes it a horizontal bar chart
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1f2937',
                        padding: 12,
                        titleFont: { size: 13, family: 'Inter' },
                        bodyFont: { size: 14, family: 'Inter', weight: 'bold' },
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: '#f3f4f6', drawBorder: false },
                    },
                    y: {
                        grid: { display: false, drawBorder: false },
                        ticks: {
                            callback: function(value, index) {
                                // Truncate long labels
                                let label = this.getLabelForValue(value) || '';
                                if(label.length > 20){
                                    return label.substr(0, 20) + '...';
                                }
                                return label;
                            }
                        }
                    }
                }
            }
        });
    }

    // --- 3. BEST SELLING CATEGORIES CHART ---
    const catCtx = document.getElementById('categoriesChart');
    if (catCtx) {
        let catLabels = getJsonData('categoryDataLabels');
        let catValues = getJsonData('categoryDataValues');

        new Chart(catCtx, {
            type: 'doughnut',
            data: {
                labels: catLabels,
                datasets: [{
                    label: 'Units Sold',
                    data: catValues,
                    backgroundColor: [
                        '#3b82f6', // blue
                        '#10b981', // green
                        '#f59e0b', // yellow
                        '#ef4444', // red
                        '#8b5cf6', // purple
                        '#ec4899', // pink
                        '#14b8a6', // teal
                        '#f97316', // orange
                        '#06b6d4', // cyan
                        '#64748b'  // slate
                    ],
                    borderWidth: 2,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            padding: 20,
                            font: { family: 'Inter', size: 12 },
                            usePointStyle: true,
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1f2937',
                        padding: 12,
                        bodyFont: { size: 14, family: 'Inter', weight: 'bold' },
                    }
                },
                cutout: '65%' // Makes doughnut thinner
            }
        });
    }

});
