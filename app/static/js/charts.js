(function () {
  const data = JSON.parse(document.getElementById("chart-data").textContent);
  const teal = "#0e7c7b", coral = "#c8453b", grey = "#b6c0cc";
  const palette = ["#0e7c7b", "#1b2a41", "#d9a300", "#c8453b", "#6b8fb5",
                   "#7aa874", "#8e6bb5", "#b57a6b", "#4f9fb0", "#999999"];

  // Income vs expense per month, with the forecast as one extra hatched bar.
  const labels = data.monthly.labels.slice();
  const income = data.monthly.income.slice();
  const expense = data.monthly.expense.slice();
  const forecast = labels.map(() => null);
  if (data.forecast) {
    labels.push(data.forecast.month + " (forecast)");
    income.push(null);
    expense.push(null);
    forecast.push(data.forecast.amount);
  }
  new Chart(document.getElementById("monthlyChart"), {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "Income", data: income, backgroundColor: teal },
        { label: "Spent", data: expense, backgroundColor: coral },
        { label: "Forecast", data: forecast, backgroundColor: grey },
      ],
    },
    options: { maintainAspectRatio: false, scales: { y: { beginAtZero: true } } },
  });

  const cats = Object.keys(data.byCategory);
  if (cats.length) {
    new Chart(document.getElementById("categoryChart"), {
      type: "doughnut",
      data: {
        labels: cats,
        datasets: [{ data: cats.map(c => data.byCategory[c]), backgroundColor: palette }],
      },
      options: { maintainAspectRatio: false, plugins: { legend: { position: "right" } } },
    });
  } else {
    const box = document.getElementById("categoryChart").parentElement;
    box.innerHTML = '<p class="muted m-3">No expenses this month yet.</p>';
  }
})();
