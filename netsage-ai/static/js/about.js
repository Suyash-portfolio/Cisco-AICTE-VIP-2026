/*
 * about.js
 * Fills in the AI mode description and renders the Responsible AI
 * correction log (the DEMO-* rows in the human review dataset).
 */
document.addEventListener("DOMContentLoaded", () => {
  fetch("/api/statistics")
    .then((r) => r.json())
    .then((stats) => {
      const el = document.getElementById("about-mode");
      if (stats.ai_mode === "live") {
        el.innerHTML = `<strong>Live AI Mode</strong> — using a real LLM API. The demo still
        works with predefined responses if the API is unavailable.`;
      } else {
        el.innerHTML = `<strong>Demo AI Mode</strong> — using predefined AI responses for reliable
        classroom demonstration. The whole project runs without an API key.`;
      }
    })
    .catch(() => {
      document.getElementById("about-mode").textContent = "AI mode information unavailable.";
    });

  fetch("/api/reviews")
    .then((r) => r.json())
    .then((data) => {
      const list = document.getElementById("correction-list");
      const demo = (data.reviews || []).filter((r) => (r.case_id || "").startsWith("DEMO-"));
      if (!demo.length) {
        list.innerHTML = `<p class="field-hint">No demo correction cases found.</p>`;
        return;
      }
      list.innerHTML = demo.map((r) => `
        <div class="correction-item">
          <div class="correction-head">
            <span class="tag">${escapeHtml(r.case_id)}</span>
            <span class="badge ${decisionBadge(r.human_decision)}">${escapeHtml(r.human_decision)}</span>
          </div>
          <div class="correction-ai"><b>AI:</b> ${escapeHtml(r.ai_result)}</div>
          <div class="correction-human"><b>Correct:</b> ${escapeHtml(r.corrected_diagnosis) || "—"}</div>
          <div class="correction-reason"><b>Reason:</b> ${escapeHtml(r.reviewer_comment) || "—"}</div>
        </div>`).join("");
    })
    .catch(() => {
      document.getElementById("correction-list").innerHTML =
        `<p class="field-hint">Could not load the correction log.</p>`;
    });

  function decisionBadge(decision) {
    if (decision === "Accepted") return "badge-low";
    if (decision === "Edited") return "badge-medium";
    if (decision === "Rejected") return "badge-high";
    return "badge-neutral";
  }
});