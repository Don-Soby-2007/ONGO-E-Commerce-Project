// Product Offer List JS

document.addEventListener('DOMContentLoaded', function () {
    // Initialize Lucide icons if not already done by base
    if (window.lucide) {
        window.lucide.createIcons();
    }

    // Delete Confirmation
    const deleteButtons = document.querySelectorAll('.delete-offer-btn');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const offerId = this.dataset.offerId;
            // Placeholder for delete URL since it's missing in backend context
            // In a real scenario, this would be a form submission or fetch call

            Swal.fire({
                title: 'Are you sure?',
                text: "You won't be able to revert this!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Yes, delete it!'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Since backend URL for delete is missing, we show an alert
                    // If URL existed: document.getElementById('delete-form-' + offerId).submit();
                    Swal.fire(
                        'Not Implemented',
                        'Delete functionality is missing in backend.',
                        'info'
                    );
                }
            });
        });
    });

    // Toggle Status
    const toggleButtons = document.querySelectorAll('.toggle-status-btn');
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const offerId = this.dataset.offerId;
            const currentStatus = this.dataset.status;

            Swal.fire({
                title: 'Update Status?',
                text: `Are you sure you want to change status?`,
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Yes, change it!'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Placeholder for toggle URL
                    Swal.fire(
                        'Not Implemented',
                        'Status toggle functionality is missing in backend.',
                        'info'
                    );
                }
            });
        });
    });
});
