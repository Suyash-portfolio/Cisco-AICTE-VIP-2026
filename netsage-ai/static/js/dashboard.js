/*
 * dashboard.js
 * Fetches /api/statistics and renders the metric tiles plus three Chart.js
 * charts (category, review decisions, severity). All values come from the
 * stored case + review data - nothing here is hardcoded.
 */
document.addEventListener("DOMContentLoaded", () => {
  const palette = ["#274670", "#0E7C86", "#159AA6", "#9A6B00", "#B3261E", "#1C7C4C", "#7A1220", "#8493A3"];

  fetch("/api/statistics")
    .then((r) => r.json())
    .then((stats) => {
      const decisions = stats.review_decision_counts || {};

      document.getElementById("metric-total-cases").textContent = stats.total_cases;
      document.getElementById("metric-reviewed").textContent = stats.reviewed_total;
      document.getElementById("metric-agreement").textContent = stats.reviewed_total ? `${stats.ai_agreement_rate}%` : "—";
      document.getElementById("metric-accepted").textContent = decisions.Accepted || 0;
      document.getElementById("metric-edited").textContent = decisions.Edited || 0;
      document.getElementById("metric-rejected").textContent = decisions.Rejected || 0;

      renderBarChart("chart-categories", stats.category_counts, "Cases", palette);
      renderBarChart("chart-severity", stats.severity_counts, "Cases", ["#1C7C4C", "#9A6B00", "#B3261E", "#7A1220"]);
      renderDoughnut("chart-decisions", decisions);

      document.getElementById("ai-mode-detail").innerHTML =
        `<strong>${escapeHtml(stats.ai_mode_label || "Demo AI Mode")}</strong><br>` +
        (stats.ai_mode === "live"
          ? "Using a live LLM API."
          : "Using predefined AI responses for reliable classroom demonstration.");

      const summary = document.getElementById("corrections-summary");
      const tiles = [
        { label: "Accepted", value: decisions.Accepted || 0, color: "var(--success)" },
        { label: "Edited", value: decisions.Edited || 0, color: "var(--warning)" },
        { label: "Rejected", value: decisions.Rejected || 0, color: "var(--danger)" },
      ];
      summary.innerHTML = `
        <div class="mini-tiles">${tiles.map((t) => `
          <div style="text-align:center;">
            <div style="font-family:var(--font-mono);font-size:22px;font-weight:600;color:${t.color};">${t.value}</div>
            <div style="font-size:12px;color:var(--text-400);text-transform:uppercase;">${t.label}</div>
          </div>`).join("")}</div>`;
    })
    .catch(() => {
      document.getElementById("metric-total-cases").textContent = "—";
    });

  function renderBarChart(canvasId, dataObj, label, colors) {
    const ctx = document.getElementById(canvasId).getContext("2d");
    const labels = Object.keys(dataObj || {});
    const values = Object.values(dataObj || {});
    new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label,
          data: values,
          backgroundColor: colors || palette,
          borderRadius: 4,
          maxBarThickness: 42,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#EEF1F5" } },
          x: { grid: { display: false } },
        },
      },
    });
  }

  function renderDoughnut(canvasId, dataObj) {
    const ctx = document.getElementById(canvasId).getContext("2d");
    const labels = Object.keys(dataObj || {});
    const values = Object.values(dataObj || {});
    new Chart(ctx, {
      type: "doughnut",
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: ["#1C7C4C", "#9A6B00", "#B3261E"],
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom", labels: { boxWidth: 12, font: { size: 11 } } } },
        cutout: "65%",
      },
    });
  }
});