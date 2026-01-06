// Mobile Menu Toggle Logic
const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
const sidebar = document.getElementById('sidebar');

if (mobileMenuToggle && sidebar) {
    mobileMenuToggle.addEventListener('click', () => {
        const isClosed = sidebar.classList.contains('-translate-x-full');
        if (isClosed) {
            sidebar.classList.remove('-translate-x-full');
        } else {
            sidebar.classList.add('-translate-x-full');
        }
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth < 768) { // md breakpoint
            if (!sidebar.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
                sidebar.classList.add('-translate-x-full');
            }
        }
    });
}

// Show/Hide Password Logic
document.querySelectorAll('.toggle-password').forEach(button => {
    button.addEventListener('click', () => {
        const targetId = button.getAttribute('data-target');
        const input = document.getElementById(targetId);
        const icon = button.querySelector('[data-lucide]');

        if (input && icon) {
            if (input.type === 'password') {
                input.type = 'text';
                icon.setAttribute('data-lucide', 'eye-off');
            } else {
                input.type = 'password';
                icon.setAttribute('data-lucide', 'eye');
            }
            lucide.createIcons();
        }
    });
});

// Form Logic
const passwordForm = document.getElementById('password-form');
const clearBtn = document.getElementById('clear-btn');
const oldPasswordInput = document.getElementById('old-password');
const newPasswordInput = document.getElementById('new-password');
const confirmPasswordInput = document.getElementById('confirm-password');

if (clearBtn) {
    clearBtn.addEventListener('click', () => {
        if (oldPasswordInput) oldPasswordInput.value = '';
        if (newPasswordInput) newPasswordInput.value = '';
        if (confirmPasswordInput) confirmPasswordInput.value = '';
    });
}

if (passwordForm) {
    passwordForm.addEventListener('submit', (e) => {
        e.preventDefault();

        // Basic Validation
        const oldPass = oldPasswordInput ? oldPasswordInput.value : '';
        const newPass = newPasswordInput ? newPasswordInput.value : '';
        const confirmPass = confirmPasswordInput ? confirmPasswordInput.value : '';

        if (!oldPass || !newPass || !confirmPass) {
            alert('Please fill in all fields.');
            return;
        }

        if (newPass !== confirmPass) {
            alert('New passwords do not match!');
            return;
        }

        if (newPass.length < 6) {
            alert('New password must be at least 6 characters long.');
            return;
        }

        // Mock Success
        alert('Password changed successfully!');
        // Reset form
        oldPasswordInput.value = '';
        newPasswordInput.value = '';
        confirmPasswordInput.value = '';
    });
}
