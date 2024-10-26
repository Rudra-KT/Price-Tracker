document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("register-form");
    const password = document.getElementById("password");
    const confirmPassword = document.getElementById("confirm-password");
    const passwordError = document.getElementById("password-error");
    const errorMessage = document.querySelector(".error-message"); // Select the error message element

    // Function to check if passwords match
    function checkPasswords() {
        if (password.value !== confirmPassword.value && confirmPassword.value !== '') {
            passwordError.style.display = 'block';
            return false; // Passwords don't match
        } else {
            passwordError.style.display = 'none';
            return true; // Passwords match
        }
    }

    // Clear inputs and error on page load
    window.addEventListener('load', function () {
        password.value = '';
        confirmPassword.value = '';
        passwordError.style.display = 'none';
    });

    // Real-time validation on confirm password input
    confirmPassword.addEventListener('input', checkPasswords);

    // Final form submission validation
    form.addEventListener('submit', function (event) {
        // Check if passwords match before submitting
        if (!checkPasswords()) {
            event.preventDefault(); // Prevent form submission if passwords don't match
        }
    });

    // Automatically hide the error message after a few seconds if it exists
    if (errorMessage) {
        setTimeout(() => {
            errorMessage.style.display = 'none'; // Hide error message after 5 seconds
        }, 5000); // Change 5000 to the desired duration in milliseconds
    }
});