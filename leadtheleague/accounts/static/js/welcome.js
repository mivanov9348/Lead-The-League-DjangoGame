function showSignup() {
    document.getElementById("login-form").classList.add("d-none");
    document.getElementById("signup-form").classList.remove("d-none");
    document.getElementById("toggle-login").classList.add("d-none");
    document.getElementById("toggle-signup").classList.remove("d-none");

    // Change the title to "Sign Up"
    document.getElementById("card-title").textContent = "Sign Up";
}

function showLogin() {
    document.getElementById("signup-form").classList.add("d-none");
    document.getElementById("login-form").classList.remove("d-none");
    document.getElementById("toggle-signup").classList.add("d-none");
    document.getElementById("toggle-login").classList.remove("d-none");

    // Change the title back to "Lead The League"
    document.getElementById("card-title").textContent = "Sign In";
}
