document.addEventListener('DOMContentLoaded', function () {
    const shortlistButton = document.getElementById('shortlist-button');

    if (shortlistButton) {
        shortlistButton.addEventListener('click', function () {
            const url = shortlistButton.getAttribute('data-url');
            const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'added') {
                        shortlistButton.textContent = 'Remove from Shortlist';
                        shortlistButton.classList.remove('btn-info');
                        shortlistButton.classList.add('btn-warning');
                    } else if (data.status === 'removed') {
                        shortlistButton.textContent = 'Add to Shortlist';
                        shortlistButton.classList.remove('btn-warning');
                        shortlistButton.classList.add('btn-info');
                    }
                    Swal.fire({
                        icon: 'success',
                        title: data.message,
                        showConfirmButton: false,
                        timer: 1500
                    });
                })
                .catch(error => {
                    console.error('Error:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Something went wrong!',
                        text: 'Please try again later.',
                        showConfirmButton: true
                    });
                });
        });
    }
});
