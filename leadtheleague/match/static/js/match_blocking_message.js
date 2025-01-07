function checkGameState() {
    fetch('/get_game_state/')
        .then(response => response.json())
        .then(data => {
            const overlay = document.getElementById('blocking-overlay');
            if (data.is_playing_matches) {
                overlay.style.display = 'block'; // Показва блокиращия екран
            } else {
                overlay.style.display = 'none'; // Скрива блокиращия екран
            }
        })
        .catch(error => console.error('Error fetching game state:', error));
}

// Извикваме checkGameState при зареждане на страницата и след това на всеки 5 секунди.
document.addEventListener('DOMContentLoaded', () => {
    checkGameState(); // Първоначална проверка
    setInterval(checkGameState, 5000); // Проверява на всеки 5 секунди
});
