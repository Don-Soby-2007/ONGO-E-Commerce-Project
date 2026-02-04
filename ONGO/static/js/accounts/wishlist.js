/* Wishlist Interactions */

async function removeFromWishlist(productId) {
    // 1. SweetAlert confirmation (replaces native confirm)
    const result = await Swal.fire({
        title: 'Remove from Wishlist?',
        text: "This item will be permanently removed from your wishlist",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc2626',
        cancelButtonColor: '#6b7280',
        confirmButtonText: 'Yes, remove it!',
        cancelButtonText: 'Cancel',
        reverseButtons: true,
        focusCancel: true
    });

    if (!result.isConfirmed) return;

    const card = document.getElementById(productId);
    if (!card) {
        Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'error',
            title: 'Item not found',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });
        return;
    }

    // 2. Get URL from button's data-url (MUST be fixed in template - see note below)
    const deleteButton = card.querySelector('button[data-url]');
    const url = deleteButton?.getAttribute('data-url') || `/wishlist/delete/${productId}/`;

    // 3. AJAX request with CSRF token
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.CSRF_TOKEN || getCookie('csrftoken'), // Fallback to cookie
                'Accept': 'application/json'
            }
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.message || 'Failed to remove item');
        }

        // 4. PRESERVE YOUR EXACT FADE-OUT EFFECT (unchanged)
        card.style.transition = "all 0.5s ease";
        card.style.opacity = "0";
        card.style.transform = "scale(0.9)";

        setTimeout(() => {
            card.remove();
            // Check if container is empty
            const container = document.querySelector('.grid');
            if (container && container.children.length === 0) {
                container.innerHTML = '<div class="col-span-full text-center py-20 text-gray-400">Your wishlist is empty.</div>';
            }
        }, 500);

        // 5. Success toast
        Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'success',
            title: data.message || 'Removed from wishlist',
            showConfirmButton: false,
            timer: 2500,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer);
                toast.addEventListener('mouseleave', Swal.resumeTimer);
            }
        });

    } catch (error) {
        console.error('Wishlist delete error:', error);
        // Revert visual state
        if (card) {
            card.style.opacity = "1";
            card.style.transform = "scale(1)";
        }
        
        // Error toast
        Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'error',
            title: error.message || 'Failed to remove item. Please try again.',
            showConfirmButton: false,
            timer: 3500,
            timerProgressBar: true
        });
    }
}

// Fallback CSRF token getter (if window.CSRF_TOKEN not set)
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
