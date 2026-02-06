// Global Offer List JS

document.addEventListener('DOMContentLoaded', function () {
    if (window.lucide) {
        window.lucide.createIcons();
    }

    // Delete Confirmation
    const deleteButtons = document.querySelectorAll('.delete-offer-btn');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const offerId = this.dataset.offerId;

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
