// Function to check if passwords match
function checkPasswords() {
    var password = document.getElementById('password').value;
    var confirmPassword = document.getElementById('confirm-password').value;
    var errorElement = document.getElementById('password-error');

    if (password !== confirmPassword && confirmPassword !== '') {
        errorElement.style.display = 'block';
        return false;
    } else {
        errorElement.style.display = 'none';
        return true;
    }
}

// Form submission check
document.getElementById('register-form').addEventListener('submit', function(event) {
    if (!checkPasswords()) {
        event.preventDefault(); // Prevent form submission
    }
});

// Real-time validation
document.getElementById('confirm-password').addEventListener('input', checkPasswords);

// Clear error message on page load
window.addEventListener('load', function() {
    document.getElementById('password-error').style.display = 'none';
    document.getElementById('password').value = '';
    document.getElementById('confirm-password').value = '';
});