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

function selectAvatar(avatarUrl) {
    document.getElementById("selected-avatar").value = avatarUrl;
    let images = document.querySelectorAll(".avatar-img");
    images.forEach(img => img.classList.remove("selected-avatar"));
    event.target.classList.add("selected-avatar");
}