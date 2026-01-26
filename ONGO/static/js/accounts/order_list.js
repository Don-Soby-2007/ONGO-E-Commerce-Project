document.addEventListener('DOMContentLoaded', () => {
    // Auto-submit form when sort option changes
    const sortSelect = document.querySelector('select[name="sort"]');
    const filterForm = document.querySelector('.order-filters');

    if (sortSelect && filterForm) {
        sortSelect.addEventListener('change', () => {
            filterForm.submit();
        });
    }

    // Auto-submit form when status filter changes
    const statusSelect = document.querySelector('select[name="status"]');
    if (statusSelect && filterForm) {
        statusSelect.addEventListener('change', () => {
            filterForm.submit();
        });
    }
});
