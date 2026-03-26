const API_BASE_URL = '';

// Simple auth check
function checkAuth() {
    const isLoggedIn = localStorage.getItem('lokkartavya_loggedIn');
    if (!isLoggedIn && !window.location.pathname.endsWith('login.html') && !window.location.pathname.endsWith('register.html')) {
        window.location.href = 'login.html';
    }
}

// Function to handle logout
function logout() {
    localStorage.removeItem('lokkartavya_loggedIn');
    window.location.href = 'login.html';
}

// Add event listener to handle basic logic on load
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});
