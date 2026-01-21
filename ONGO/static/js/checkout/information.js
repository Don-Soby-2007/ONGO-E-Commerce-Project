document.addEventListener('DOMContentLoaded', () => {
    // Initial setup
    calculateOrderTotals();
    setupAddressSelection();
    setupModal();
});

function setupAddressSelection() {
    const addressList = document.getElementById('address-list');

    // Use event delegation for address cards
    addressList.addEventListener('click', (e) => {
        const card = e.target.closest('.address-card');
        if (!card) return;

        // Deselect all others
        document.querySelectorAll('.address-card').forEach(c => {
            c.classList.remove('border-red-500', 'bg-red-50');
            c.classList.add('border-gray-200');
        });

        // Select clicked
        card.classList.remove('border-gray-200');
        card.classList.add('border-red-500', 'bg-red-50');

        // Check the radio input
        const radio = card.querySelector('input[type="radio"]');
        if (radio) radio.checked = true;
    });

    // Initial visual state for checked inputs
    document.querySelectorAll('.address-card input[checked]').forEach(input => {
        const card = input.closest('.address-card');
        if (card) {
            card.classList.remove('border-gray-200');
            card.classList.add('border-red-500', 'bg-red-50');
        }
    });
}

function setupModal() {
    const modal = document.getElementById('address-modal');
    const openBtn = document.getElementById('open-address-modal');
    const closeBtn = document.getElementById('close-modal-btn');
    const cancelBtn = document.getElementById('cancel-modal-btn');
    const form = document.getElementById('add-address-form');
    const errorContainer = document.getElementById('modal-error-message');

    if (!modal || !openBtn) return;

    // Open
    openBtn.addEventListener('click', (e) => {
        e.preventDefault();
        modal.classList.remove('hidden');
    });

    // Close functions
    const closeModal = () => {
        modal.classList.add('hidden');
        form.reset();
        errorContainer.classList.add('hidden');
        errorContainer.textContent = '';
    };

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    // Form Submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const url = form.getAttribute('action');

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                // Success
                addNewAddressToDOM(data.address);
                closeModal();
            } else {
                // Error
                errorContainer.textContent = data.message || 'An error occurred. Please try again.';
                errorContainer.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Error:', error);
            errorContainer.textContent = 'Network error. Please try again.';
            errorContainer.classList.remove('hidden');
        }
    });
}

function addNewAddressToDOM(address) {
    const addressList = document.getElementById('address-list');

    // Create the HTML structure
    const label = document.createElement('label');
    label.className = 'block relative border-2 border-red-500 rounded-lg p-4 cursor-pointer bg-red-50 transition-all address-card';

    label.innerHTML = `
        <input type="radio" name="shipping_address" value="${address.id}"
            class="absolute top-4 right-4 text-red-600 focus:ring-red-500" checked>
        <div class="pr-8">
            <p class="font-bold text-gray-900 text-lg">${address.name}
                ${address.is_default ? '<span class="text-sm font-normal text-gray-500 ml-2">(Default)</span>' : ''}
            </p>
            <p class="text-base text-gray-600 mt-1">${address.street_address}</p>
            <p class="text-base text-gray-600">${address.city}, ${address.state} ${address.postal_code}, ${address.country}</p>
            <p class="text-base text-gray-600 mt-1">Phone: ${address.phone}</p>
        </div>
    `;

    // Deselect all existing cards visually
    document.querySelectorAll('.address-card').forEach(c => {
        c.classList.remove('border-red-500', 'bg-red-50');
        c.classList.add('border-gray-200');
        const r = c.querySelector('input[type="radio"]');
        if (r) r.checked = false;
    });

    // Add new card to the top
    addressList.insertBefore(label, addressList.firstChild);
}

function calculateOrderTotals() {
    let subtotal = 0;
    const cartItems = document.querySelectorAll('.flex.gap-3[data-price]');

    cartItems.forEach(item => {
        const price = parseFloat(item.getAttribute('data-price')) || 0;
        const quantity = parseInt(item.getAttribute('data-quantity')) || 0;
        subtotal += price * quantity;
    });

    subtotal = Math.round(subtotal * 100) / 100;

    const taxRate = 0.02;
    const tax = subtotal > 0 ? subtotal * taxRate : 0;
    const shipping = 0;
    const total = subtotal + tax + shipping;

    // Update DOM
    const subtotalEl = document.getElementById('subtotal');
    const taxEl = document.getElementById('tax');
    const totalEl = document.getElementById('total');
    const taxNote = document.getElementById('tax_not');

    if (subtotalEl) subtotalEl.textContent = `₹${subtotal.toFixed(2)}`;
    if (taxEl) taxEl.textContent = `₹${tax.toFixed(2)}`;
    if (totalEl) totalEl.textContent = `₹${total.toFixed(2)}`;
    if (taxNote) taxNote.textContent = `Including ₹${tax.toFixed(2)} in taxes`;
}