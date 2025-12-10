// In your template's JavaScript section
document.querySelectorAll('[id^="deleteCustomerBtn"]').forEach(button => {
    button.addEventListener('click', function(event) {
        event.preventDefault();
        
        // Get user ID and current status from data attributes
        const userId = this.getAttribute('data-user-id');
        const currentStatus = this.getAttribute('data-status');
        
        // Determine action text based on current status
        const actionText = currentStatus === 'Active' ? 'deactivate' : 'activate';
        const confirmText = `Yes, ${actionText} it!`;
        const titleText = currentStatus === 'Active' ? 'Deactivated!' : 'Activated!';
        const icon = currentStatus === 'Active' ? 'warning' : 'success';
        
        // Show confirmation dialog
        const swalWithBootstrapButtons = Swal.mixin({
            customClass: {
                cancelButton: "block w-full mb-4 bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-4 rounded-lg text-center transition-colors duration-200",
                confirmButton: "block w-full bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-4 rounded-lg text-center transition-colors duration-200"
            },
            buttonsStyling: false
        });
        
        swalWithBootstrapButtons.fire({
            title: `Are you sure?`,
            text: `You want to ${actionText} this user!`,
            icon: icon,
            showCancelButton: true,
            confirmButtonText: confirmText,
            cancelButtonText: "No, cancel!",
            reverseButtons: true
        }).then((result) => {
            if (result.isConfirmed) {
                // Perform the toggle request - FIXED ENDPOINT
                fetch(`delete-user/${userId}/`, {  // Fixed: correct endpoint
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    }
                })
                .then(response => response.json())  // Fixed: expect JSON response
                .then(data => {
                    if (data.success) {
                        // Show success alert
                        Swal.fire({
                            title: titleText,
                            text: data.message,  // Use message from backend
                            icon: 'success',
                            confirmButtonText: 'OK'
                        }).then(() => {
                            // Reload the page to reflect changes
                            window.location.reload();
                        });
                    } else {
                        // Show error message
                        Swal.fire("Error", data.message, "error");
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    // Show error message
                    Swal.fire("Error", "Could not update user status", "error");
                });
            } else if (result.dismiss === Swal.DismissReason.cancel) {
                swalWithBootstrapButtons.fire({
                    title: "Cancelled",
                    text: "User status is unchanged :)",
                    icon: "error"
                });
            }
        });
    });
});