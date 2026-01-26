function openCancelModal(actionUrl, typeLabel) {
    const modal = document.getElementById('cancelModal');
    const modalTitle = document.getElementById('modalTitle');
    const cancelForm = document.getElementById('cancelForm');

    if (modal && cancelForm) {
        modal.classList.add('active');
        // Update title to 'Cancel Order' or 'Cancel Item'
        modalTitle.textContent = `Cancel ${typeLabel}`;

        // Store the action URL on the form dataset to use in AJAX
        cancelForm.dataset.actionUrl = actionUrl;
    }
}

function closeCancelModal() {
    const modal = document.getElementById('cancelModal');
    const cancelForm = document.getElementById('cancelForm');

    if (modal) {
        modal.classList.remove('active');
    }

    if (cancelForm) {
        cancelForm.reset();
        delete cancelForm.dataset.actionUrl;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const cancelForm = document.getElementById('cancelForm');

    // Close modal when clicking outside
    const modal = document.getElementById('cancelModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeCancelModal();
            }
        });
    }

    if (cancelForm) {
        cancelForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const actionUrl = cancelForm.dataset.actionUrl;
            const reason = document.getElementById('cancelReason').value;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            if (!actionUrl) {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Cancellation URL not found.',
                    toast: true,
                    position: 'top-right',
                    timer: 3000
                });
                return;
            }

            // Show loading state
            const submitBtn = cancelForm.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.textContent;
            submitBtn.textContent = 'Processing...';
            submitBtn.disabled = true;

            try {
                const formData = new FormData();
                formData.append('cancel_reason', reason);
                // Also append 'reason' for item cancel if backend expects 'reason' instead of 'cancel_reason'
                // View checklist: OrderCancelView uses 'cancel_reason'. OrderItemCancelView uses 'reason'.
                // I should send both or just send both keys with same value to be safe.
                formData.append('reason', reason);

                const response = await fetch(actionUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken
                    },
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Cancelled',
                        text: data.message || 'Cancelled successfully',
                        toast: true,
                        position: 'top-right',
                        timer: 2000
                    }).then(() => {
                        window.location.reload();
                    });
                    closeCancelModal();
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Failed',
                        text: data.error || 'Cancellation failed',
                        toast: true,
                        position: 'top-right',
                    });
                }
            } catch (error) {
                console.error('Error:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Something went wrong. Please try again.',
                    toast: true,
                    position: 'top-right',
                });
            } finally {
                submitBtn.textContent = originalBtnText;
                submitBtn.disabled = false;
            }
        });
    }
});
