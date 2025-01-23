document.addEventListener("DOMContentLoaded", function () {
    const tierItems = document.querySelectorAll(".tier-item");
    const modal = document.getElementById("tier-modal");
    const modalTierName = document.getElementById("modal-tier-name");
    const modalCapacity = document.getElementById("modal-capacity");
    const modalPriceMultiplier = document.getElementById("modal-price-multiplier");
    const modalBonus = document.getElementById("modal-bonus");
    const modalCost = document.getElementById("modal-cost");
    const buyButton = document.getElementById("buy-button");
    const cancelButton = document.getElementById("cancel-button");
    const closeModal = document.querySelector(".close-modal");

    // Проверка дали елементите съществуват
    if (!modal || !modalTierName || !modalCapacity || !modalPriceMultiplier || !modalBonus || !modalCost || !buyButton || !cancelButton || !closeModal) {
        console.error("One or more required elements are missing from the DOM.");
        return;
    }

    // Проверка при клик на tier елементи
    tierItems.forEach((tier) => {
        if (!tier) {
            console.warn("A tier item is missing.");
            return;
        }
        tier.addEventListener("click", function () {
            // Проверка за налични данни
            const isPurchasable = tier.dataset.purchasable === "true";
            const tierName = tier.dataset.name || "Unknown Tier";
            const capacityBoost = tier.dataset.capacity || "N/A";
            const priceMultiplier = tier.dataset.ticketPrice || "N/A";
            const popularityBonus = tier.dataset.popularity || "N/A";
            const upgradeCost = tier.dataset.cost || "N/A";

            modalTierName.textContent = tierName;
            modalCapacity.textContent = capacityBoost;
            modalPriceMultiplier.textContent = priceMultiplier;
            modalBonus.textContent = popularityBonus;
            modalCost.textContent = upgradeCost;

            // Проверка за отключване на бутон
            if (isPurchasable) {
                buyButton.classList.remove("hidden");
                buyButton.dataset.id = tier.dataset.id; // ID на tier-а
            } else {
                buyButton.classList.add("hidden");
            }

            modal.classList.remove("hidden");
        });
    });

    // Затваряне на модала
    closeModal.addEventListener("click", function () {
        if (modal.classList.contains("hidden")) {
            console.warn("Modal is already hidden.");
        } else {
            modal.classList.add("hidden");
        }
    });

    cancelButton.addEventListener("click", function () {
        if (modal.classList.contains("hidden")) {
            console.warn("Modal is already hidden.");
        } else {
            modal.classList.add("hidden");
        }
    });

    buyButton.addEventListener("click", function () {
        // Проверка за наличен ID преди изпращане на заявката
        const tierId = buyButton.dataset.id;
        if (!tierId) {
            console.error("Tier ID is missing or invalid.");
            Swal.fire("Error!", "Tier ID is missing.", "error");
            return;
        }

        fetch(`/stadium/buy_tier/${tierId}/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector("meta[name='csrf-token']")?.getAttribute("content") || getCookie("csrftoken"),
            },
        })
            .then((response) => {
                if (!response.ok) {
                    console.error("Server responded with an error status:", response.status);
                    throw new Error("Network response was not ok.");
                }
                return response.json();
            })
            .then((data) => {
                if (data.success) {
                    Swal.fire("Success!", "Tier upgraded successfully!", "success");
                    location.reload();
                } else {
                    console.error("Server error:", data.message);
                    Swal.fire("Error!", data.message, "error");
                }
            })
            .catch((error) => {
                console.error("Fetch error:", error);
                Swal.fire("Error!", "Something went wrong.", "error");
            });
    });

    // Функция за получаване на CSRF токен
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
