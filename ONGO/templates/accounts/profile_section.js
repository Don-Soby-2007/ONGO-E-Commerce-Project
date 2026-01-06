document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide Icons
    lucide.createIcons();

    // Navigation Handling
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));

            // Add active class to clicked link
            e.currentTarget.classList.add('active');

            // On mobile, auto-close sidebar when a link is clicked
            if (window.innerWidth < 768) {
                const sidebar = document.getElementById('sidebar');
                if (sidebar) {
                    sidebar.classList.add('-translate-x-full');
                }
            }
        });
    });

    // Mobile Sidebar Toggle
    const toggleBtn = document.getElementById('mobile-menu-toggle');
    const sidebar = document.getElementById('sidebar');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            // Toggle the translate class to show/hide
            sidebar.classList.toggle('-translate-x-full');
        });

        // Optional: Close sidebar when clicking outside (on main content)
        document.addEventListener('click', (e) => {
            if (window.innerWidth < 768 &&
                !sidebar.contains(e.target) &&
                !toggleBtn.contains(e.target) &&
                !sidebar.classList.contains('-translate-x-full')) {
                sidebar.classList.add('-translate-x-full');
            }
        });
    }

    // Edit Button Interaction
    const editBtn = document.querySelector('#edit-profile-btn');
    if (editBtn) {
        editBtn.addEventListener('click', () => {
            // Mock Edit Mode
            alert('Edit Profile feature coming soon!');
        });
    }
});
