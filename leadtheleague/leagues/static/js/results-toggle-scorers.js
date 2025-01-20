document.querySelectorAll('.toggle-scorers').forEach(toggleScorersBtn => {
    toggleScorersBtn.addEventListener('click', function () {
        const scorersContainer = this.nextElementSibling;

        if (scorersContainer.classList.contains('show')) {
            scorersContainer.classList.remove('show');
            this.textContent = '🔽 View Scorers';
        } else {
            scorersContainer.classList.add('show');
            this.textContent = '🔼 Hide Scorers';
        }
    });
});
