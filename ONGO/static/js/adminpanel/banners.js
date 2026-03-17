document.addEventListener('DOMContentLoaded', () => {
    const toggles = document.querySelectorAll('.status-toggle');

    toggles.forEach(toggle => {
        toggle.addEventListener('click', async (e) => {
            e.preventDefault();

            const url = toggle.dataset.url;
            if (!url) return;
            
            // CSRF Token setup
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

            const result = await Swal.fire({
                title: 'Change banner status?',
                text: "Are you sure you want to change the status of this banner?",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Yes, change it!'
            });

            if (result.isConfirmed) {
                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrftoken,
                            'Content-Type': 'application/json',
                        },
                    });

                    if (response.ok) {
                        const data = await response.json().catch(() => ({}));
                        Swal.fire({
                            title: 'Success!',
                            text: data.message || 'Banner status updated successfully.',
                            icon: 'success',
                            confirmButtonColor: '#3085d6'
                        }).then(() => {
                            window.location.reload();
                        });
                    } else {
                        const data = await response.json().catch(() => ({}));
                        Swal.fire(
                            'Error!',
                            data.message || 'Failed to update the status.',
                            'error'
                        );
                    }
                } catch (error) {
                    console.error("Status toggle error:", error);
                    Swal.fire(
                        'Error!',
                        'A network error occurred while updating the status.',
                        'error'
                    );
                }
            }
        });
    });
});
