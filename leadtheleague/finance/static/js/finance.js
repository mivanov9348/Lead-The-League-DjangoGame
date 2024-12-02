document.addEventListener('DOMContentLoaded', () => {
    const teamFinanceBtn = document.getElementById('team-finance-btn');
    const globalFinanceBtn = document.getElementById('global-finance-btn');
    const teamFinanceSection = document.getElementById('team-finance-section');
    const globalFinanceSection = document.getElementById('global-finance-section');

    // Event listeners for buttons
    teamFinanceBtn.addEventListener('click', () => {
        teamFinanceSection.style.display = 'block';
        globalFinanceSection.style.display = 'none';
        teamFinanceBtn.classList.add('active');
        globalFinanceBtn.classList.remove('active');
    });

    globalFinanceBtn.addEventListener('click', () => {
        globalFinanceSection.style.display = 'block';
        teamFinanceSection.style.display = 'none';
        globalFinanceBtn.classList.add('active');
        teamFinanceBtn.classList.remove('active');
    });

    // Default view
    teamFinanceBtn.click();
});
