/**
 * Product Review List Functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Re-initialize Lucide icons if needed (though base template usually does it)
    if (window.lucide) {
        window.lucide.createIcons();
    }
});

/**
 * Open the image modal with the specified image source
 * @param {string} imgSrc - URL of the image to display
 */
function openImageModal(imgSrc) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    
    if (!modal || !modalImg) return;

    modalImg.src = imgSrc;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.classList.add('modal-open');

    // Immediate opacity zero for transition
    modal.style.opacity = '0';
    setTimeout(() => {
        modal.style.opacity = '1';
        modalImg.classList.remove('scale-95');
        modalImg.classList.add('scale-100');
    }, 10);
}

/**
 * Close the image modal
 */
function closeImageModal() {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    
    if (!modal || !modalImg) return;

    modal.style.opacity = '0';
    modalImg.classList.remove('scale-100');
    modalImg.classList.add('scale-95');

    setTimeout(() => {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        document.body.classList.remove('modal-open');
        modalImg.src = ''; // Clear source
    }, 300);
}

// Close modal on escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeImageModal();
    }
});

// Close modal on backdrop click
document.getElementById('imageModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        closeImageModal();
    }
});
