const tableBody = document.getElementById('table-body');
const filterSelect = document.getElementById('filter-by-nation');
const nationId = filterSelect.value;

const sortTable = (colIndex) => {
  const rows = Array.from(tableBody.querySelectorAll('tr'));
  const isAscending = rows[1].children[colIndex].classList.contains('ascending');
  rows.sort((a, b) => {
    const valueA = a.children[colIndex].textContent.trim().toLowerCase();
    const valueB = b.children[colIndex].textContent.trim().toLowerCase();
    if (colIndex === 3) { // Sort balance numerically
      const numA = parseFloat(valueA.replace(',', ''));
      const numB = parseFloat(valueB.replace(',', ''));
      return isAscending ? numA - numB : numB - numA;
    } else {
      // Case-insensitive text sorting for other columns
      if (valueA < valueB) {
        return isAscending ? -1 : 1;
      } else if (valueA > valueB) {
        return isAscending ? 1 : -1;
      }
      return 0;
    }
  });
  tableBody.innerHTML = '';
  rows.forEach(row => tableBody.appendChild(row));
  rows[1].children[colIndex].classList.toggle('ascending');
};

const filterTable = (nationId) => {
  const rows = Array.from(tableBody.querySelectorAll('tr'));
  rows.forEach(row => {
  const nationCell = row.children[2];
  if (nationId === '' || nationCell.textContent.trim() === nationId) {
    row.style.display = ''; // Show row if nation matches or all nations selected
  } else {
    row.style.display = 'none'; // Hide row if nation doesn't match
  }
});
};



document.querySelectorAll('.sortable').forEach(header => {
  header.addEventListener('click', () => {
    const colIndex = header.cellIndex;
    sortTable(colIndex);
  });
});

filterSelect.addEventListener('change', () => {
  const nationId = filterSelect.value;
  filterTable(nationId);
});