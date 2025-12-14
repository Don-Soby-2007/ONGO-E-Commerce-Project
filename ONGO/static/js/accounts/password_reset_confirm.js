// Toggle password visibility
function togglePassword(inputId, button) {
    const input = document.getElementById(inputId);
    const svg = button.querySelector('svg');
    
    if (input.type === 'password') {
        input.type = 'text';
        svg.innerHTML = `
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
        `;
    } else {
        input.type = 'password';
        svg.innerHTML = `
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        `;
    }
}

function validPassword(password) {
    const minLength = 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSymbol = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    return password.length >= minLength && hasUpperCase && hasLowerCase && hasNumber && hasSymbol;
}

// Form submission handler
newPassword = document.getElementById('newPassword');
confirmPassword = document.getElementById('confirmPassword');
passwordMismatchError = document.getElementById('passwordMismatchError');
passwordError = document.getElementById('passwordError');
let valid = false;
newPassword.addEventListener('input', function() {
    if (validPassword(newPassword.value)) {
        passwordError.classList.add('hidden');
        valid = true;
    } else {
        passwordError.classList.remove('hidden');
        valid = false;
    }
});

confirmPassword.addEventListener('input', function() {
    if (newPassword.value === confirmPassword.value) {
        passwordMismatchError.classList.add('hidden');
        valid = true;
    } else {
        passwordMismatchError.classList.remove('hidden');
        valid = false;
    }
});

document.getElementById('passwordForm').addEventListener('submit', function(event) {
    if (!valid) {
        event.preventDefault();
    }
    if (newPassword.value !== confirmPassword.value) {
        event.preventDefault();
        passwordMismatchError.classList.remove('hidden');
    }else {
        passwordMismatchError.classList.add('hidden');
    }
    if (!validPassword(newPassword.value)) {
        event.preventDefault();
        passwordError.classList.remove('hidden');
    }else {
        passwordError.classList.add('hidden');
    }
});