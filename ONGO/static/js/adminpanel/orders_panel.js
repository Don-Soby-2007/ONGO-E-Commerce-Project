/**
 * Admin Panel Orders - Main Logic
 * Handles status updates via AJAX
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons if not already done by base template
    if (window.lucide) {
        window.lucide.createIcons();
    }

    setupStatusDropdowns();
});

/**
 * Setup event listeners for all status dropdowns (Order level & Item level)
 */
function setupStatusDropdowns() {
    const statusSelects = document.querySelectorAll('.js-status-select');

    statusSelects.forEach(select => {
        // Store initial value to revert if needed
        select.dataset.originalStatus = select.value;

        select.addEventListener('change', async (e) => {
            const selectEl = e.target;
            const newStatus = selectEl.value;
            const originalStatus = selectEl.dataset.originalStatus;

            // Data attributes
            const orderId = selectEl.dataset.orderId;
            const itemId = selectEl.dataset.itemId; // Optional, exists only for items
            const type = selectEl.dataset.type; // 'order' or 'item'

            // Confirm action (especially for irreversible actions like cancel)
            if (['cancelled', 'returned'].includes(newStatus)) {
                const confirmed = await showConfirmationDialog(newStatus);
                if (!confirmed) {
                    selectEl.value = originalStatus;
                    return;
                }
            }

            // Disable during request
            selectEl.disabled = true;

            try {
                let success = false;
                if (type === 'order') {
                    success = await updateOrderStatus(orderId, newStatus);
                } else if (type === 'item') {
                    success = await updateItemStatus(orderId, itemId, newStatus);
                }

                if (success) {
                    // Update original status on success
                    selectEl.dataset.originalStatus = newStatus;
                    showToast('Status updated successfully', 'success');

                    // If order status changed, we might want to reload to reflect strict backend transitions for items/order
                    // Or update the badge dynamically. For now, dynamic badge update:
                    updateStatusBadge(selectEl, newStatus);
      
                    setTimeout(() => window.location.reload(), 1000); 
                } else {
                    // Revert on failure (logic handled in update functions usually)
                    selectEl.value = originalStatus;
                }
            } catch (error) {
                console.error('Update failed', error);
                selectEl.value = originalStatus;
                showToast('Failed to update status', 'error');
            } finally {
                selectEl.disabled = false;
            }
        });
    });
}

/**
 * Update Order Status
 */
async function updateOrderStatus(orderId, newStatus) {
    const url = `/admin/orders/status/${orderId}/`; // POST to ToggleOrderStatusView

    // Get CSRF token
    const csrfToken = getCookie('csrftoken');

    try {
        const formData = new FormData();
        formData.append('status', newStatus);

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
            return true;
        } else {
            showToast(data.error || 'Error updating order status', 'error');
            return false;
        }
    } catch (error) {
        showToast('Network error occurred', 'error');
        throw error;
    }
}

/**
 * Update Item Status
 */
async function updateItemStatus(orderId, itemId, newStatus) {
    const url = `/admin/orders/${orderId}/${itemId}`; // POST to ToggleOrderItemStatusView

    const csrfToken = getCookie('csrftoken');

    try {
        const formData = new FormData();
        formData.append('status', newStatus);

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Check if backend implicitly updated order status?
            // The backend returns {success: true, new_status: ...}
            // Ideally we should reload if the order status changed, but for now we just return success.
            return true;
        } else {
            showToast(data.error || 'Error updating item status', 'error');
            return false;
        }
    } catch (error) {
        showToast('Network error occurred', 'error');
        throw error;
    }
}

/**
 * Helper: Update badge UI next to select if it exists
 */
function updateStatusBadge(selectEl, newStatus) {
    // Attempt to find a badge container related to this select
    // Assumes structure: <div wrapper> <badge> <select> </div>
    const wrapper = selectEl.closest('.status-wrapper');
    if (wrapper) {
        const badge = wrapper.querySelector('.status-badge');
        if (badge) {
            // Remove old classes
            badge.className = 'status-badge';
            // Add new class
            badge.classList.add(`status-${newStatus.toLowerCase()}`);
            badge.textContent = newStatus;
        }
    }
}

/**
 * Helper: Confirmation Dialog using SweetAlert2
 */
async function showConfirmationDialog(status) {
    if (typeof Swal !== 'undefined') {
        const result = await Swal.fire({
            title: 'Are you sure?',
            text: `You are about to mark this as ${status}. This action may be irreversible.`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#EF4444',
            cancelButtonColor: '#3B82F6',
            confirmButtonText: 'Yes, proceed'
        });
        return result.isConfirmed;
    } else {
        return confirm(`Are you sure you want to change status to ${status}?`);
    }
}

/**
 * Helper: Get Cookie
 */
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

/**
 * Helper: Show Toast (using existing toast system or fallback)
 */
function showToast(message, type = 'success') {
    // Check if custom toast function exists (from base template)
    // If not, use SweetAlert toast or simple alert
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            toast: true,
            position: 'top-end',
            icon: type,
            title: message,
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });
    } else {
        alert(message);
    }
}
