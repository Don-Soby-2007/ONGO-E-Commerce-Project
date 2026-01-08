function confirmDelete(addressId) {
    Swal.fire({
        title: 'Are you sure?',
        text: "You won't be able to revert this!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444', // brand-red
        cancelButtonColor: '#000000',   // brand-black
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        if (result.isConfirmed) {
            // Create a form to submit POST request
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/auth/manage-address/delete/${addressId}/`;

            // Add CSRF token
            const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
            if (csrfToken) {
                const hiddenField = document.createElement('input');
                hiddenField.type = 'hidden';
                hiddenField.name = 'csrfmiddlewaretoken';
                hiddenField.value = csrfToken;
                form.appendChild(hiddenField);
            } else {
                // Fallback: Try get cookie or just warn (template should have csrf)
                console.error("CSRF token not found!");
            }

            document.body.appendChild(form);
            form.submit();
        }
    })
}
