// Frontend validation functions for the hospital management system

// Function to validate email format
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Function to validate phone number format
function validatePhone(phone) {
    if (!phone || phone.length === 0) return true; // Phone is optional
    const phoneRegex = /^[+]?[0-9]{10,15}$/;
    return phoneRegex.test(phone);
}

// Function to validate password strength
function validatePassword(password) {
    if (!password) return false;
    // At least 8 characters, one uppercase, one lowercase, one digit
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    return passwordRegex.test(password);
}

// Function to validate name length
function validateName(name) {
    if (!name) return false;
    return name.length >= 2 && name.length <= 100;
}

// Function to validate username length
function validateUsername(username) {
    if (!username) return false;
    return username.length >= 3 && username.length <= 50;
}

// Function to show error message
function showError(elementId, message) {
    const errorElement = document.getElementById(elementId + '_error');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
}

// Function to hide error message
function hideError(elementId) {
    const errorElement = document.getElementById(elementId + '_error');
    if (errorElement) {
        errorElement.style.display = 'none';
    }
}

// Validation for login form
function validateLoginForm() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    
    let isValid = true;
    
    if (!validateUsername(username)) {
        showError('username', 'Username must be between 3 and 50 characters long.');
        isValid = false;
    } else {
        hideError('username');
    }
    
    if (!password || password.length < 8) {
        showError('password', 'Password must be at least 8 characters long.');
        isValid = false;
    } else {
        hideError('password');
    }
    
    return isValid;
}

// Validation for registration form
function validateRegisterForm() {
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const name = document.getElementById('name').value.trim();
    const phone = document.getElementById('phone').value.trim();
    
    let isValid = true;
    
    if (!validateUsername(username)) {
        showError('username', 'Username must be between 3 and 50 characters long.');
        isValid = false;
    } else {
        hideError('username');
    }
    
    if (!validateEmail(email)) {
        showError('email', 'Please enter a valid email address.');
        isValid = false;
    } else {
        hideError('email');
    }
    
    if (!validatePassword(password)) {
        showError('password', 'Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one digit.');
        isValid = false;
    } else {
        hideError('password');
    }
    
    if (!validateName(name)) {
        showError('name', 'Name must be between 2 and 100 characters long.');
        isValid = false;
    } else {
        hideError('name');
    }
    
    if (phone && !validatePhone(phone)) {
        showError('phone', 'Please enter a valid phone number (10-15 digits).');
        isValid = false;
    } else {
        hideError('phone');
    }
    
    return isValid;
}

// Validation for patient profile form
function validatePatientProfileForm() {
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const address = document.getElementById('address').value.trim();
    
    let isValid = true;
    
    if (!validateName(name)) {
        showError('name', 'Name must be between 2 and 100 characters long.');
        isValid = false;
    } else {
        hideError('name');
    }
    
    if (!validateEmail(email)) {
        showError('email', 'Please enter a valid email address.');
        isValid = false;
    } else {
        hideError('email');
    }
    
    if (phone && !validatePhone(phone)) {
        showError('phone', 'Please enter a valid phone number (10-15 digits).');
        isValid = false;
    } else {
        hideError('phone');
    }
    
    if (address.length > 500) {
        showError('address', 'Address must be less than 500 characters.');
        isValid = false;
    } else {
        hideError('address');
    }
    
    return isValid;
}

// Validation for add doctor form
function validateAddDoctorForm() {
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const name = document.getElementById('name').value.trim();
    const specialization = document.getElementById('specialization').value.trim();
    const phone = document.getElementById('phone').value.trim();
    
    let isValid = true;
    
    if (!validateUsername(username)) {
        showError('username', 'Username must be between 3 and 50 characters long.');
        isValid = false;
    } else {
        hideError('username');
    }
    
    if (!validateEmail(email)) {
        showError('email', 'Please enter a valid email address.');
        isValid = false;
    } else {
        hideError('email');
    }
    
    if (!validatePassword(password)) {
        showError('password', 'Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one digit.');
        isValid = false;
    } else {
        hideError('password');
    }
    
    if (!validateName(name)) {
        showError('name', 'Name must be between 2 and 100 characters long.');
        isValid = false;
    } else {
        hideError('name');
    }
    
    if (!validateName(specialization)) {
        showError('specialization', 'Specialization must be between 2 and 100 characters long.');
        isValid = false;
    } else {
        hideError('specialization');
    }
    
    if (phone && !validatePhone(phone)) {
        showError('phone', 'Please enter a valid phone number (10-15 digits).');
        isValid = false;
    } else {
        hideError('phone');
    }
    
    return isValid;
}

// Validation for edit doctor form
function validateEditDoctorForm() {
    const name = document.getElementById('name').value.trim();
    const specialization = document.getElementById('specialization').value.trim();
    const email = document.getElementById('email').value.trim();
    const phone = document.getElementById('phone').value.trim();
    
    let isValid = true;
    
    if (!validateName(name)) {
        showError('name', 'Name must be between 2 and 100 characters long.');
        isValid = false;
    } else {
        hideError('name');
    }
    
    if (!validateName(specialization)) {
        showError('specialization', 'Specialization must be between 2 and 100 characters long.');
        isValid = false;
    } else {
        hideError('specialization');
    }
    
    if (!validateEmail(email)) {
        showError('email', 'Please enter a valid email address.');
        isValid = false;
    } else {
        hideError('email');
    }
    
    if (phone && !validatePhone(phone)) {
        showError('phone', 'Please enter a valid phone number (10-15 digits).');
        isValid = false;
    } else {
        hideError('phone');
    }
    
    return isValid;
}

// Add event listeners when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add validation to login form
    const loginForm = document.querySelector('form[action="/login"]');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            if (!validateLoginForm()) {
                e.preventDefault();
            }
        });
    }
    
    // Add validation to registration form
    const registerForm = document.querySelector('form[action="/register"]');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            if (!validateRegisterForm()) {
                e.preventDefault();
            }
        });
    }
    
    // Add validation to patient profile form
    const patientProfileForm = document.querySelector('form[action="/patient/profile"]');
    if (patientProfileForm) {
        patientProfileForm.addEventListener('submit', function(e) {
            if (!validatePatientProfileForm()) {
                e.preventDefault();
            }
        });
    }
    
    // Add validation to add doctor form
    const addDoctorForm = document.querySelector('form[action="/admin/doctors/add"]');
    if (addDoctorForm) {
        addDoctorForm.addEventListener('submit', function(e) {
            if (!validateAddDoctorForm()) {
                e.preventDefault();
            }
        });
    }
    
    // Add validation to edit doctor form
    const editDoctorForm = document.querySelector('form[action="/admin/doctors/edit"]');
    if (editDoctorForm) {
        editDoctorForm.addEventListener('submit', function(e) {
            if (!validateEditDoctorForm()) {
                e.preventDefault();
            }
        });
    }
});