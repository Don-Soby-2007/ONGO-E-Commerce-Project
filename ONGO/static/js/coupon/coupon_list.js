document.addEventListener('DOMContentLoaded', function () {
    // Initialize Lucide icons if not already done by base
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    const toggleButtons = document.querySelectorAll('.coupon-toggle-btn');
    const csrfToken = getCookie('csrftoken');

    toggleButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const couponId = this.dataset.couponId;
            const toggleUrl = this.dataset.toggleUrl;
            const currentStatus = this.dataset.currentStatus; // 'active' or 'inactive'

            const actionText = currentStatus === 'active' ? 'Deactivate' : 'Activate';
            const actionColor = currentStatus === 'active' ? '#d33' : '#3085d6';

            Swal.fire({
                title: 'Change Coupon Status?',
                text: `Are you sure you want to ${actionText.toLowerCase()} this coupon?`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: actionColor,
                cancelButtonColor: '#aaa',
                confirmButtonText: `Yes, ${actionText} it!`
            }).then((result) => {
                if (result.isConfirmed) {
                    performToggle(toggleUrl);
                }
            });
        });
    });

    function performToggle(url) {
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        title: 'Success!',
                        text: data.message,
                        icon: 'success',
                        timer: 1500,
                        showConfirmButton: false
                    }).then(() => {
                        window.location.reload();
                    });
                } else {
                    Swal.fire('Error!', data.message || 'Something went wrong', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire('Error!', 'Network error occurred.', 'error');
            });
    }

    // Helper to get cookie
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
});
