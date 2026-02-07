// Global Offer List JS

document.addEventListener('DOMContentLoaded', function () {
    if (window.lucide) {
        window.lucide.createIcons();
    }

    // Get CSRF Token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // Delete Confirmation
    const deleteButtons = document.querySelectorAll('.delete-offer-btn');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
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
                    Swal.fire('Not Implemented', 'Delete functionality is missing in backend.', 'info');
                }
            });
        });
    });

    // Toggle Status Logic
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.offer-toggle-btn');
        if (!btn) return;

        e.preventDefault();

        const offerId = btn.getAttribute('data-offer-id');
        const isActive = btn.getAttribute('data-status') === 'True';
        const toggleUrl = btn.getAttribute('data-toggle-url');

        Swal.fire({
            title: 'Change Offer Status?',
            text: isActive ? "This will deactivate the offer" : "This will activate the offer",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: isActive ? '#d33' : '#3085d6',
            cancelButtonColor: '#6c757d',
            confirmButtonText: isActive ? 'Yes, deactivate it!' : 'Yes, activate it!'
        }).then((result) => {
            if (result.isConfirmed) {
                fetch(toggleUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({})
                })
                    .then(response => response.json().then(data => ({ status: response.status, body: data })))
                    .then(obj => {
                        if (obj.body.success) {
                            Swal.fire({
                                title: 'Updated!',
                                text: obj.body.message,
                                icon: 'success',
                                confirmButtonText: 'OK'
                            }).then(() => {
                                window.location.reload();
                            });
                        } else {
                            Swal.fire({
                                title: 'Error!',
                                text: obj.body.message || "Failed to change offer status",
                                icon: 'error'
                            });
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        Swal.fire({
                            title: 'Error!',
                            text: "A network error occurred.",
                            icon: 'error'
                        });
                    });
            }
        });
    });
});
