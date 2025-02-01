document.addEventListener('DOMContentLoaded', function() {
    const seasonList = document.getElementById('season-list');
    const calendarContent = document.getElementById('calendar-content');

    seasonList.addEventListener('click', function(event) {
        if (event.target.tagName === 'LI') {
            const seasonId = event.target.getAttribute('data-season-id');
            console.log('Selected Season ID:', seasonId); // Добавете това за да видите кой сезон е избран

            fetch(`/api/match-schedule/${seasonId}/`)
                .then(response => {
                    console.log('Response:', response); // Добавете това за да видите каква е отговора
                    return response.json();
                })
                .then(data => {
                    console.log('Data:', data); // Добавете това за да видите какви данни са върнати
                    renderCalendar(data);
                })
                .catch(error => {
                    console.error('Error fetching match schedule:', error); // Добавете това за да видите ако има грешка
                });
        }
    });

    function renderCalendar(matches) {
        let html = '<h2>Програма на мачовете</h2>';
        html += '<ul>';
        matches.forEach(match => {
            html += `<li>${match.date} - ${match.event_type}</li>`;
        });
        html += '</ul>';
        calendarContent.innerHTML = html;
    }
});