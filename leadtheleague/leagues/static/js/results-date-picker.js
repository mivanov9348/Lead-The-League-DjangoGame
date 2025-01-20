document.getElementById('date-picker').addEventListener('change', function () {
    const selectedDate = this.value;
    window.location.href = `?date=${selectedDate}`;
});
