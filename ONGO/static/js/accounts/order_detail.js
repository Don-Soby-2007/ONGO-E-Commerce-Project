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

/* ================== REVIEW LOGIC ================== */

let cropper = null;
let currentFile = null;
let reviewImages = []; // Stores objects {id: optional_db_id, url: string, file: optional_File_object}
let deletedImageIds = []; // Stores db ids of removed pre-existing images

function updateImageUI() {
    const container = document.getElementById('reviewImagesContainer');
    const badge = document.getElementById('imageCountBadge');
    const addBtn = document.getElementById('addPhotoBtn');
    
    container.innerHTML = '';
    reviewImages.forEach((img, index) => {
        const div = document.createElement('div');
        div.className = 'w-20 h-20 rounded border border-gray-300 relative bg-gray-50 flex items-center justify-center';
        div.innerHTML = `
            <img src="${img.url}" class="w-full h-full object-cover rounded" alt="Review Image">
            <button type="button" class="absolute -top-2 -right-2 bg-white rounded-full p-1 shadow-sm border" onclick="removeReviewImage(event, ${index})">
                <i data-lucide="x" class="w-3 h-3 text-red-500"></i>
            </button>
        `;
        container.appendChild(div);
    });
    
    lucide.createIcons();
    
    badge.textContent = `${reviewImages.length}/5 images`;
    
    if (reviewImages.length >= 5) {
        addBtn.disabled = true;
    } else {
        addBtn.disabled = false;
    }
}

function openReviewModal(mode, productId, variantId, reviewId = null, star = 0, text = '', existingImages = []) {
    const modal = document.getElementById('reviewModal');
    
    document.getElementById('reviewMode').value = mode;
    document.getElementById('reviewProductId').value = productId;
    document.getElementById('reviewVariantId').value = variantId;
    document.getElementById('reviewId').value = reviewId || '';
    
    const title = document.getElementById('reviewModalTitle');
    const deleteBtn = document.getElementById('deleteReviewBtn');
    
    reviewImages = [];
    deletedImageIds = [];
    
    if (mode === 'edit') {
        title.textContent = 'Edit Your Review';
        deleteBtn.style.display = 'block';
        setRating(star);
        document.getElementById('reviewText').value = text;
        
        if (existingImages && existingImages.length > 0) {
            reviewImages = existingImages.map(img => ({ id: img.id, url: img.url, file: null }));
        }
    } else {
        title.textContent = 'Write a Review';
        deleteBtn.style.display = 'none';
        setRating(0);
        document.getElementById('reviewText').value = '';
    }
    
    updateImageUI();
    modal.classList.add('active');
}

function closeReviewModal() {
    const modal = document.getElementById('reviewModal');
    if (modal) {
        modal.classList.remove('active');
        document.getElementById('reviewForm').reset();
        reviewImages = [];
        deletedImageIds = [];
        updateImageUI();
        setRating(0);
        
        document.getElementById('starError').classList.add('hidden');
        document.getElementById('textError').classList.add('hidden');
    }
}

function setRating(rating) {
    document.getElementById('reviewStar').value = rating;
    const stars = document.querySelectorAll('#starRatingContainer .star-btn');
    
    stars.forEach((btn, index) => {
        // Lucide renders SVG inside the button, so query for svg instead or let tailwind handle colors
        const icon = btn.querySelector('svg') || btn.querySelector('i');
        
        if (index < rating) {
            btn.classList.add('text-yellow-500');
            btn.classList.remove('text-gray-300');
            if (icon) icon.setAttribute('fill', 'currentColor');
        } else {
            btn.classList.remove('text-yellow-500');
            btn.classList.add('text-gray-300');
            if (icon) {
                icon.setAttribute('fill', 'none');
                icon.setAttribute('stroke', 'currentColor');
            }
        }
    });
}

function handleImageSelect(event) {
    if (reviewImages.length >= 5) {
        Swal.fire({icon: 'error', title: 'Limit Reached', text: 'You can only upload up to 5 images.', toast: true, position: 'top-right'});
        return;
    }

    const file = event.target.files[0];
    if (!file) return;

    if (!file.type.match('image.*')) {
        Swal.fire({icon: 'error', title: 'Invalid File', text: 'Please select an image file (JPG, PNG, SVG).', toast: true, position: 'top-right'});
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        Swal.fire({icon: 'error', title: 'File Too Large', text: 'Maximum allowed image size is 5MB.', toast: true, position: 'top-right'});
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        const cropperImage = document.getElementById('cropperImage');
        cropperImage.src = e.target.result;
        
        document.getElementById('cropperModal').classList.add('active');
        
        if (cropper) {
            cropper.destroy();
        }
        
        cropper = new Cropper(cropperImage, {
            aspectRatio: 1,
            viewMode: 1,
            autoCropArea: 1,
        });
    };
    reader.readAsDataURL(file);
    // Reset file input so same file can be selected again if cancelled
    event.target.value = '';
}

function closeCropperModal() {
    document.getElementById('cropperModal').classList.remove('active');
    if (cropper) {
        cropper.destroy();
        cropper = null;
    }
}

function cropImage() {
    if (!cropper) return;
    
    if (reviewImages.length >= 5) {
        closeCropperModal();
        return;
    }
    
    cropper.getCroppedCanvas({
        width: 500,
        height: 500
    }).toBlob((blob) => {
        const uniqueName = `cropped_${Date.now()}.jpg`;
        const newFile = new File([blob], uniqueName, { type: 'image/jpeg' });
        
        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            reviewImages.push({
                id: null, // No ID yet, it's new
                url: e.target.result,
                file: newFile
            });
            updateImageUI();
        };
        reader.readAsDataURL(newFile);
        
        closeCropperModal();
    }, 'image/jpeg');
}

function removeReviewImage(event, index) {
    event.stopPropagation();
    const removed = reviewImages.splice(index, 1)[0];
    if (removed.id) {
        deletedImageIds.push(removed.id);
    }
    updateImageUI();
}

async function submitReview(event) {
    event.preventDefault();
    
    const starInput = document.getElementById('reviewStar').value;
    const textInput = document.getElementById('reviewText').value.trim();
    
    let hasError = false;
    
    if (!starInput || starInput == 0) {
        document.getElementById('starError').classList.remove('hidden');
        hasError = true;
    } else {
        document.getElementById('starError').classList.add('hidden');
    }
    
    if (textInput.length < 20) {
        document.getElementById('textError').classList.remove('hidden');
        hasError = true;
    } else {
        document.getElementById('textError').classList.add('hidden');
    }
    
    if (hasError) return;
    
    const mode = document.getElementById('reviewMode').value;
    const productId = document.getElementById('reviewProductId').value;
    const variantId = document.getElementById('reviewVariantId').value;
    const reviewId = document.getElementById('reviewId').value;
    
    const url = mode === 'add' ? `/auth/add-review/${productId}/` : `/auth/edit-review/${reviewId}/`;
    
    const formData = new FormData();
    formData.append('star', starInput);
    formData.append('review', textInput);
    if (mode === 'add') {
        formData.append('variant_id', variantId);
    }
    
    // Append deleted image IDs for edit mode
    deletedImageIds.forEach(id => {
        formData.append('deleted_images', id);
    });
    
    // Append new cropped files
    reviewImages.forEach(img => {
        if (img.file) {
            formData.append('images', img.file);
        }
    });
    
    const submitBtn = document.getElementById('submitReviewBtn');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Saving...';
    submitBtn.disabled = true;
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Success',
                text: data.message,
                toast: true,
                position: 'top-right',
                timer: 2000
            }).then(() => {
                window.location.reload();
            });
            closeReviewModal();
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.message || 'Failed to save review.',
                toast: true,
                position: 'top-right'
            });
        }
    } catch (error) {
        console.error('Submit review error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'An unexpected error occurred.',
            toast: true,
            position: 'top-right'
        });
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

async function deleteReview() {
    const reviewId = document.getElementById('reviewId').value;
    if (!reviewId) return;
    
    const confirmation = await Swal.fire({
        title: 'Delete Review?',
        text: "You won't be able to revert this!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#6b7280',
        confirmButtonText: 'Yes, delete it!'
    });
    
    if (confirmation.isConfirmed) {
        const deleteBtn = document.getElementById('deleteReviewBtn');
        const originalText = deleteBtn.textContent;
        deleteBtn.textContent = 'Deleting...';
        deleteBtn.disabled = true;
        
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        try {
            const response = await fetch(`/order/delete-review/${reviewId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Deleted!',
                    text: data.message,
                    toast: true,
                    position: 'top-right',
                    timer: 2000
                }).then(() => {
                    window.location.reload();
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: data.message || 'Failed to delete review.',
                    toast: true,
                    position: 'top-right'
                });
            }
        } catch (error) {
            console.error('Delete review error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'An unexpected error occurred.',
                toast: true,
                position: 'top-right'
            });
        } finally {
            deleteBtn.textContent = originalText;
            deleteBtn.disabled = false;
        }
    }
}
