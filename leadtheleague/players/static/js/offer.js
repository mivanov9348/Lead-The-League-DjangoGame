function toggleOfferInput() {
    const offerInput = document.getElementById('offer-input');
    offerInput.style.display = offerInput.style.display === 'none' ? 'block' : 'none';
}

function sendOffer() {
    const offerData = document.getElementById('offer-data');
    const offerURL = offerData.dataset.url;
    const csrfToken = offerData.dataset.csrfToken;
    const offerAmount = document.getElementById('offerAmount').value;

    if (!offerAmount || parseFloat(offerAmount) <= 0) {
        Swal.fire({
            icon: 'warning',
            title: 'Invalid Offer Amount',
            text: 'Please enter a valid offer amount.',
        });
        return;
    }

    fetch(offerURL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ offer_amount: parseFloat(offerAmount) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'error') {
            Swal.fire({
                icon: 'error',
                title: 'Error!',
                text: data.message || 'Something went wrong.',
            });
        } else {
            Swal.fire({
                icon: 'success',
                title: 'Success!',
                text: data.message || 'Offer sent successfully!',
            }).then(() => {
                window.location.reload();
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error!',
            text: 'Something went wrong.',
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const sendOfferButton = document.getElementById('sendOfferButton');
    if (sendOfferButton) {
        sendOfferButton.addEventListener('click', sendOffer);
    }
});
