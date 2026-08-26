/*
 * main.js - shared behavior across all NetSage AI pages:
 * mobile sidebar toggle and the "AI MODE" indicator pill.
 */
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
    document.addEventListener("click", (e) => {
      if (window.innerWidth <= 900 && sidebar.classList.contains("open")
          && !sidebar.contains(e.target) && e.target !== toggle) {
        sidebar.classList.remove("open");
      }
    });
  }

  const modePill = document.getElementById("ai-mode-pill");
  if (modePill) {
    fetch("/api/statistics")
      .then((r) => r.json())
      .then((data) => {
        const mode = (data.ai_mode || "demo").toUpperCase();
        modePill.textContent = `AI MODE: ${mode}`;
      })
      .catch(() => {
        modePill.textContent = "AI MODE: DEMO";
      });
  }

  const homeBadge = document.getElementById("home-mode-badge");
  if (homeBadge) {
    fetch("/api/statistics")
      .then((r) => r.json())
      .then((data) => {
        homeBadge.textContent = data.ai_mode === "live"
          ? "Live AI Mode — using a live LLM API."
          : "Demo AI Mode — Using predefined AI responses for reliable classroom demonstration.";
      })
      .catch(() => {
        homeBadge.textContent = "Demo AI Mode — Using predefined AI responses for reliable classroom demonstration.";
      });
  }
});

/* Small shared helper: map a severity string to a badge CSS class. */
function severityBadgeClass(sev) {
  const s = (sev || "").toLowerCase();
  if (s === "critical") return "badge-critical";
  if (s === "high") return "badge-high";
  if (s === "medium") return "badge-medium";
  if (s === "low") return "badge-low";
  return "badge-neutral";
}

/* Small shared helper: escape text before injecting into innerHTML. */
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}
