// JavaScript for OTP input navigation in profile email change
function moveNext(current, nextId) {
    if (current.value.length === 1) {
        document.getElementById(nextId).focus();
    }
}

function moveBack(current, prevId) {
    if (current.value.length === 0 && event.key === "Backspace") {
        document.getElementById(prevId).focus();
    }
}

document.getElementById("otpForm").addEventListener("submit", function () {
    const otp =
        document.getElementById("otp1").value +
        document.getElementById("otp2").value +
        document.getElementById("otp3").value +
        document.getElementById("otp4").value +
        document.getElementById("otp5").value +
        document.getElementById("otp6").value;

    document.getElementById("otp").value = otp;
});

// JavaScript for Resend OTP timer
let timer;
let countdown = 30; // 30 seconds
let isResendDisabled = true; // Start disabled

// Initialize the timer on page load
document.addEventListener("DOMContentLoaded", function () {
    updateTimerDisplay();
    startResendTimer(); // Start the countdown immediately
});

// Handle resend link click
document.getElementById("resendLink").addEventListener("click", function (e) {
    e.preventDefault(); // Prevent default anchor behavior

    if (!isResendDisabled) {
        // Call your resend OTP endpoint
        resendOTP();
    }
});

function startResendTimer() {
    // Start the countdown
    isResendDisabled = true;
    timer = setInterval(updateTimer, 1000);
}

function updateTimer() {
    const timerElement = document.getElementById('resendLink');

    if (countdown > 0) {
        // Show countdown
        const seconds = (countdown % 60).toString().padStart(2, '0');
        timerElement.textContent = `Resend OTP in 00:${seconds}`;
        timerElement.classList.add('text-gray-500', 'cursor-not-allowed');
        timerElement.classList.remove('hover:text-gray-700', 'cursor-pointer');
        isResendDisabled = true;
        countdown--;
    } else {
        // Enable the link when countdown finishes
        timerElement.textContent = 'Resend OTP';
        timerElement.classList.remove('text-gray-500', 'cursor-not-allowed');
        timerElement.classList.add('text-gray-900', 'hover:text-gray-700', 'cursor-pointer');
        isResendDisabled = false;

        // Clear the timer
        clearInterval(timer);
    }
}

function updateTimerDisplay() {
    const timerElement = document.getElementById('resendLink');
    const seconds = (countdown % 60).toString().padStart(2, '0');
    timerElement.textContent = `Resend OTP in 00:${seconds}`;
}

function resendOTP() {
    // Disable the link immediately
    isResendDisabled = true;
    document.getElementById('resendLink').classList.add('text-gray-500', 'cursor-not-allowed');
    document.getElementById('resendLink').classList.remove('hover:text-gray-700', 'cursor-pointer');

    // Get the resend URL from data attribute
    const resendUrl = document.getElementById('resendLink').getAttribute('data-resend-url');

    // Make the API call to resend OTP
    fetch(resendUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),  // Django CSRF token
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reset the countdown
                countdown = 30;
                startResendTimer();

                // Show success message using SweetAlert
                Swal.fire({
                    toast: true,
                    icon: 'success',
                    title: data.message || 'OTP sent successfully!',
                    position: 'top-right',
                    showConfirmButton: false,
                    timer: 3500,
                    timerProgressBar: true,
                });
            } else {
                // Handle error
                Swal.fire({
                    toast: true,
                    icon: 'error',
                    title: data.message || 'Failed to resend OTP',
                    position: 'top-right',
                    showConfirmButton: false,
                    timer: 3500,
                    timerProgressBar: true,
                });

                // Re-enable the link if request failed
                isResendDisabled = false;
                document.getElementById('resendLink').classList.remove('text-gray-500', 'cursor-not-allowed');
                document.getElementById('resendLink').classList.add('text-gray-900', 'hover:text-gray-700', 'cursor-pointer');
            }
        })
        .catch(error => {
            console.error('Error resending OTP:', error);

            Swal.fire({
                toast: true,
                icon: 'error',
                title: 'An error occurred. Please try again.',
                position: 'top-right',
                showConfirmButton: false,
                timer: 3500,
                timerProgressBar: true,
            });

            // Re-enable the link if request failed
            isResendDisabled = false;
            document.getElementById('resendLink').classList.remove('text-gray-500', 'cursor-not-allowed');
            document.getElementById('resendLink').classList.add('text-gray-900', 'hover:text-gray-700', 'cursor-pointer');
        });
}

// Helper function to get CSRF token (Django specific)
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

// Handle cancel email change button with SweetAlert
document.addEventListener("DOMContentLoaded", function () {
    const cancelButton = document.getElementById('cancelEmailChange');

    if (cancelButton) {
        cancelButton.addEventListener('click', function (e) {
            e.preventDefault();
            const cancelUrl = this.getAttribute('data-cancel-url');

            Swal.fire({
                title: 'Cancel Email Change?',
                text: "Are you sure you want to cancel the email change? No changes will be made to your email.",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#ef4444',
                cancelButtonColor: '#6b7280',
                confirmButtonText: 'Yes, cancel it',
                cancelButtonText: 'No, keep it'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Create a form and submit it to cancel the email change
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = cancelUrl;

                    // Add CSRF token
                    const csrfInput = document.createElement('input');
                    csrfInput.type = 'hidden';
                    csrfInput.name = 'csrfmiddlewaretoken';
                    csrfInput.value = getCookie('csrftoken');
                    form.appendChild(csrfInput);

                    document.body.appendChild(form);
                    form.submit();
                }
            });
        });
    }
});
