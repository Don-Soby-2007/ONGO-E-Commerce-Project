/* Wishlist Interactions */

function addToCart(productId) {
    // Determine product name based on ID for a better message (simulation)
    let productName = "Product";
    const productCard = document.getElementById(productId);
    if (productCard) {
        productName = productCard.querySelector('h3').innerText;
    }

    alert(`Added "${productName}" to your cart!`);
    console.log(`Add to cart triggered for ${productId}`);
}

function removeFromWishlist(productId) {
    if (confirm('Are you sure you want to remove this item from your wishlist?')) {
        const card = document.getElementById(productId);
        if (card) {
            // Fade out effect
            card.style.transition = "all 0.5s ease";
            card.style.opacity = "0";
            card.style.transform = "scale(0.9)";

            setTimeout(() => {
                card.remove();
                // Check if empty (optional enhancement)
                const container = document.querySelector('.grid');
                if (container && container.children.length === 0) {
                    container.innerHTML = '<div class="col-span-full text-center py-20 text-gray-400">Your wishlist is empty.</div>';
                }
            }, 500);
        }
    }
}
