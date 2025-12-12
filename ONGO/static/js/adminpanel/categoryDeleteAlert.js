document.querySelectorAll('[data-toggle-btn]').forEach(button => {

    button.addEventListener('click', function (event) {
        event.preventDefault();

        const objectId = this.dataset.id;
        const objectType = this.dataset.type; // user, category, product…
        const currentStatus = this.dataset.status;

        const action = currentStatus === 'Active' ? 'deactivate' : 'activate';
        const confirmText = `Yes, ${action} it!`;
        const successTitle = currentStatus === 'Active' ? 'Deactivated!' : 'Activated!';

        Swal.fire({
            title: "Are you sure?",
            text: `You want to ${action} this ${objectType}?`,
            icon: currentStatus === 'Active' ? "warning" : "success",
            showCancelButton: true,
            confirmButtonText: confirmText,
            cancelButtonText: "No, cancel!",
        }).then(result => {

            if (!result.isConfirmed) return;

            fetch(`/admin/${objectType}/toggle/${objectId}/`, {
                method: "POST",
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(res => res.json())
                .then(data => {

                    if (data.success) {
                        Swal.fire({
                            title: successTitle,
                            text: data.message,
                            icon: "success"
                        }).then(() => window.location.reload());
                    } else {
                        Swal.fire("Error", data.message, "error");
                    }

                })
                .catch(err => {
                    console.error(err);
                    Swal.fire("Error", "Server error occurred", "error");
                });

        });
    });

});
