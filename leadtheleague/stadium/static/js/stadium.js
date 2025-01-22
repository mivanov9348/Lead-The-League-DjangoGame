document.addEventListener("DOMContentLoaded", () => {
    const tierList = document.querySelectorAll(".tier-item");
    const modal = document.getElementById("tier-modal");
    const modalClose = document.querySelector(".close-modal");
    const buyButton = document.getElementById("buy-button");

    let selectedTierId = null;

    tierList.forEach(item => {
        item.addEventListener("click", () => {
            const isPurchasable = item.dataset.purchasable === "true";

            if (!isPurchasable) return; // Пропускаме, ако тирът е вече купен

            const id = item.dataset.id;
            const name = item.dataset.name;
            const capacity = item.dataset.capacity;
            const ticketPrice = item.dataset.ticketPrice;
            const popularity = item.dataset.popularity;
            const cost = item.dataset.cost;

            selectedTierId = id;

            document.getElementById("modal-tier-name").textContent = name;
            document.getElementById("modal-capacity").textContent = capacity;
            document.getElementById("modal-price-multiplier").textContent = ticketPrice;
            document.getElementById("modal-bonus").textContent = popularity;
            document.getElementById("modal-cost").textContent = cost;

            buyButton.style.display = "block";
            buyButton.textContent = `Buy Tier ${name}`;

            modal.classList.remove("hidden");
        });
    });

    modalClose.addEventListener("click", () => {
        modal.classList.add("hidden");
        selectedTierId = null;
    });

    buyButton.addEventListener("click", () => {
        if (selectedTierId) {
            fetch("/stadium/purchase_tier/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken(),
                },
                body: JSON.stringify({ tier_id: selectedTierId }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire("Success", data.message, "success").then(() => location.reload());
                } else {
                    Swal.fire("Error", data.error, "error");
                }
            })
            .catch(error => console.error("Error purchasing tier:", error));
        }
    });

    function getCSRFToken() {
        return document.querySelector("[name=csrfmiddlewaretoken]").value;
    }
});
