function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
}

email =  socument.getElementById('email');
emailError = document.getElementById('email-error');
email.addEventListener('focus', () => {
    email.classList.add('ring-2', 'ring-rose-500', 'border-rose-500');

});
email.addEventListener('blur', () => {
    email.classList.remove('ring-2', 'ring-rose-500', 'border-rose-500');

});
email.addEventListener('input', () => {
    if (email.value.trim() !== '') {
        email.classList.add('ring-2', 'ring-rose-500', 'border-rose-500');
        emailError.classList.add('hidden');
    } else {
        email.classList.remove('ring-2', 'ring-rose-500', 'border-rose-500');
        emailError.classList.remove('hidden');
    }
});

document.getElementById('reset-form').addEventListener('submit', function(event) {
    if (email.value.trim() === '') {
        event.preventDefault();
        emailError.classList.remove('hidden');
        email.classList.add('ring-2', 'ring-rose-500', 'border-rose-500');
    }
    if (!validateEmail(email.value.trim())) {
        event.preventDefault();
        emailError.classList.remove('hidden');
        email.classList.add('ring-2', 'ring-rose-500', 'border-rose-500');
    }
});
