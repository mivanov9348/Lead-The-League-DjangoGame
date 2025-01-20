function releasePlayer() {
    const releaseData = document.getElementById('release-data');
    const releaseURL = releaseData.dataset.url;
    const csrfToken = releaseData.dataset.csrfToken;

    if (!csrfToken) {
        console.error('CSRF token not found!');
        Swal.fire({
            icon: 'error',
            title: 'CSRF Token Missing',
            text: 'The action cannot be performed due to a missing CSRF token.',
        });
        return;
    }

    Swal.fire({
        title: 'Are you sure?',
        text: "You won't be able to undo this action!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Yes, release the player!',
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(releaseURL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    Swal.fire(
                        'Released!',
                        data.message || 'The player has been released successfully.',
                        'success'
                    ).then(() => {
                        window.location.reload();
                    });
                } else {
                    Swal.fire(
                        'Error!',
                        data.message || 'Something went wrong.',
                        'error'
                    );
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire(
                    'Error!',
                    'Something went wrong.',
                    'error'
                );
            });
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const releaseButton = document.getElementById('release-button');
    if (releaseButton) {
        releaseButton.addEventListener('click', releasePlayer);
    }
});
