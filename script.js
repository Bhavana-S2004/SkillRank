/* filepath: c:\Users\sahuk\OneDrive\Desktop\SkillRank\static\script.js */
document.addEventListener('DOMContentLoaded', function() {
    const queryForm = document.getElementById('query-form');
    const queryInput = document.getElementById('query-input');
    const queryResults = document.getElementById('query-results');
    const chartCanvas = document.getElementById('myChart').getContext('2d');
    let myChart; // Chart instance

    queryForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const query = queryInput.value;

        // Fetch query results
        fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: 'query=' + encodeURIComponent(query)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                queryResults.innerHTML = '<p class="error">Error: ' + data.error + '</p>';
            } else {
                // Display results in a table
                let resultsHTML = '<h3>Results:</h3><table><thead><tr>';
                if (data.results && data.results.length > 0) {
                    const columns = data.results[0];
                    columns.forEach(column => {
                        resultsHTML += `<th>${column}</th>`;
                    });
                    resultsHTML += '</tr></thead><tbody>';

                    for (let i = 1; i < data.results.length; i++) {
                        resultsHTML += '<tr>';
                        data.results[i].forEach(value => {
                            resultsHTML += `<td>${value}</td>`;
                        });
                        resultsHTML += '</tr>';
                    }
                    resultsHTML += '</tbody></table>';
                } else {
                    resultsHTML = '<p>No results found.</p>';
                }
                resultsHTML += '<h3>SQL Query:</h3><pre>' + data.sql + '</pre>';
                queryResults.innerHTML = resultsHTML;
            }
        })
        .catch(error => {
            queryResults.innerHTML = '<p class="error">Network error: ' + error + '</p>';
        });

        // Fetch chart data
        fetch('/chart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: 'query=' + encodeURIComponent(query)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Chart error:', data.error);
            } else {
                // Generate chart
                if (myChart) {
                    myChart.destroy(); // Destroy existing chart
                }
                myChart = new Chart(chartCanvas, {
                    type: data.chart_type,
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: query,
                            data: data.values,
                            backgroundColor: 'rgba(54, 162, 235, 0.5)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
        })
        .catch(error => {
            console.error('Chart fetch error:', error);
        });
    });
});