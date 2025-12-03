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