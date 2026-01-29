// Admin Return Detail Page JavaScript

// Get CSRF token from cookie
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

document.addEventListener('DOMContentLoaded', function () {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Accept Return Button
    const acceptBtn = document.getElementById('acceptReturnBtn');
    if (acceptBtn) {
        acceptBtn.addEventListener('click', function () {
            const returnId = this.dataset.returnId;

            Swal.fire({
                title: 'Accept This Return?',
                html: '<p class="text-gray-700">This action will:</p>' +
                    '<ul class="text-left text-sm text-gray-600 mt-2 space-y-1">' +
                    '<li>• Update stock levels for returned items</li>' +
                    '<li>• Mark items as "Returned"</li>' +
                    '<li>• Set status to "Accepted"</li>' +
                    '</ul>',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#10B981',
                cancelButtonColor: '#6B7280',
                confirmButtonText: 'Yes, Accept Return',
                cancelButtonText: 'Cancel',
                customClass: {
                    popup: 'rounded-lg',
                    confirmButton: 'font-semibold',
                    cancelButton: 'font-semibold'
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    acceptReturn(returnId);
                }
            });
        });
    }

    // Reject Return Button
    const rejectBtn = document.getElementById('rejectReturnBtn');
    if (rejectBtn) {
        rejectBtn.addEventListener('click', function () {
            const returnId = this.dataset.returnId;

            Swal.fire({
                title: 'Reject This Return?',
                html: '<p class="text-gray-700 mb-3">Please provide a reason for rejection:</p>' +
                    '<textarea id="adminNotesInput" class="swal2-textarea w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500" ' +
                    'placeholder="Enter admin notes (required)" rows="4"></textarea>',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#EF4444',
                cancelButtonColor: '#6B7280',
                confirmButtonText: 'Yes, Reject Return',
                cancelButtonText: 'Cancel',
                customClass: {
                    popup: 'rounded-lg',
                    confirmButton: 'font-semibold',
                    cancelButton: 'font-semibold'
                },
                preConfirm: () => {
                    const adminNotes = document.getElementById('adminNotesInput').value.trim();
                    if (!adminNotes) {
                        Swal.showValidationMessage('Admin notes are required for rejection');
                        return false;
                    }
                    return adminNotes;
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    rejectReturn(returnId, result.value);
                }
            });
        });
    }
});

// Accept Return Function
function acceptReturn(returnId) {
    const url = `/admin/returns/${returnId}/action`;

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken
        },
        body: new URLSearchParams({
            'status': 'accepted'
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success || data.new_status === 'accepted') {
                Swal.fire({
                    icon: 'success',
                    title: 'Return Accepted!',
                    text: data.message || 'Return has been accepted and stock updated.',
                    timer: 2000,
                    showConfirmButton: false,
                    customClass: {
                        popup: 'rounded-lg'
                    }
                }).then(() => {
                    location.reload();
                });
            } else {
                throw new Error(data.error || data.message || 'Failed to accept return');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: error.message || 'Failed to accept return. Please try again.',
                customClass: {
                    popup: 'rounded-lg'
                }
            });
        });
}

// Reject Return Function
function rejectReturn(returnId, adminNotes) {
    const url = `/admin/returns/${returnId}/action`;

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken
        },
        body: new URLSearchParams({
            'status': 'rejected',
            'admin_notes': adminNotes
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success || data.new_status === 'rejected') {
                Swal.fire({
                    icon: 'success',
                    title: 'Return Rejected',
                    text: data.message || 'Return has been rejected.',
                    timer: 2000,
                    showConfirmButton: false,
                    customClass: {
                        popup: 'rounded-lg'
                    }
                }).then(() => {
                    location.reload();
                });
            } else {
                throw new Error(data.error || data.message || 'Failed to reject return');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: error.message || 'Failed to reject return. Please try again.',
                customClass: {
                    popup: 'rounded-lg'
                }
            });
        });
}
