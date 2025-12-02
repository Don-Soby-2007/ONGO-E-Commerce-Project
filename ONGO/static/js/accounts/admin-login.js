function checkUsername() {
    const usernameInput = document.getElementById('username');
    const username = usernameInput.value;
    const trimusername = usernameInput.value.trim();
    const usernamePattern =  /^[A-Za-z]+( [A-Za-z]+)*$/; // Alphabets and spaces, 3-20 characters

    if (usernamePattern.test(username) && !(username.length < 3 || username.length > 20) && trimusername.length != 0) {
        usernameInput.classList.remove('border-red-500');
        document.getElementById('usernameError').classList.add('hidden');
        return true;
    }else {
        usernameInput.classList.add('border-red-500');
        document.getElementById('usernameError').classList.remove('hidden');
        return false;
    }
}

function checkPassword() {
    const passwordInput = document.getElementById('password');
    const password = passwordInput.value;
    const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;

    if (!passwordPattern.test(password)) {
        passwordInput.classList.add('border-red-500');
        document.getElementById('passwordError').classList.remove('hidden');
        return false;
    } else {
        passwordInput.classList.remove('border-red-500');
        document.getElementById('passwordError').classList.add('hidden');
        return true;
    }
}

document.getElementById('username').addEventListener('input', function() {
    checkUsername();
    updateLoginButton();
});

document.getElementById('password').addEventListener('input', function() {
    checkPassword();
    updateLoginButton();
});

function updateLoginButton() {
    const isValid = checkUsername() && checkPassword();
    document.getElementById('loginBtn').disabled = !isValid;
}