// JavaScript for OTP input navigation
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
document.addEventListener("DOMContentLoaded", function() {
    updateTimerDisplay();
    startResendTimer(); // Start the countdown immediately
});

// Handle resend link click
document.getElementById("resendLink").addEventListener("click", function(e) {
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
    
    // Make the API call to resend OTP
    fetch('/resend-otp/', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.CSRF_TOKEN,  // Django CSRF token
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            // Use the level provided by the backend, default to 'info' or 'error'
            const level = data.level || (data.success ? 'success' : 'error');
            window.showToast(data.message, level);
        }
        if (data.success) {
            // Reset the countdown
            countdown = 30;
            startResendTimer();
            console.log('OTP has been resent successfully!');
        } else {
            // Handle error
            console.log(data.message || 'Failed to resend OTP. Please try again.');
            // Re-enable the link if request failed
            isResendDisabled = false;
            document.getElementById('resendLink').classList.remove('text-gray-500', 'cursor-not-allowed');
            document.getElementById('resendLink').classList.add('text-gray-900', 'hover:text-gray-700', 'cursor-pointer');
        }
    })
    .catch(error => {
        console.error('Error resending OTP:', error);
        console.log('An error occurred. Please try again.');
        // Re-enable the link if request failed
        isResendDisabled = false;
        document.getElementById('resendLink').classList.remove('text-gray-500', 'cursor-not-allowed');
        document.getElementById('resendLink').classList.add('text-gray-900', 'hover:text-gray-700', 'cursor-pointer');
    });
}