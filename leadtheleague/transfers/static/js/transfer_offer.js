document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("offer-modal");
    const errorModal = document.getElementById("error-modal");
    const errorMessage = document.getElementById("error-message");
    const closeErrorModal = errorModal.querySelector(".close-btn");
    const playerIdInput = document.getElementById("player-id");

    const showErrorModal = (message) => {
        errorMessage.textContent = message;
        errorModal.classList.remove("hidden");
    };

    closeErrorModal.addEventListener("click", () => {
        errorModal.classList.add("hidden");
    });

    document.querySelectorAll(".offer-btn").forEach(button => {
        button.addEventListener("click", () => {
            // Set values in the modal
            document.getElementById("player-image").src = button.dataset.playerImage;
            document.getElementById("player-name").textContent = button.dataset.playerName;
            document.getElementById("player-position").textContent = button.dataset.playerPosition;
            document.getElementById("player-price").textContent = button.dataset.playerPrice;
            playerIdInput.value = button.dataset.playerId;

            // Show modal
            modal.classList.remove("hidden");
        });
    });

    document.querySelector(".confirm-btn").addEventListener("click", (e) => {
        e.preventDefault();

        const playerId = playerIdInput.value;
        fetch("/transfers/check_balance/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
            },
            body: JSON.stringify({ player_id: playerId }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Submit the form if balance is sufficient
                modal.querySelector("form").submit();
            } else {
                // Show error modal
                showErrorModal(data.error);
                modal.classList.add("hidden");
            }
        })
        .catch(error => {
            console.error("Error:", error);
            showErrorModal("An unexpected error occurred. Please try again.");
        });
    });

    // Add event listener for the cancel button
    document.querySelector(".cancel-btn").addEventListener("click", () => {
        modal.classList.add("hidden");
    });

    // Add event listener for clicking outside the modal content
    modal.addEventListener("click", (e) => {
        if (e.target === modal) {
            modal.classList.add("hidden");
        }
    });
});