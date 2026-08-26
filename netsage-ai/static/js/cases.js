/*
 * cases.js
 * Loads the case dataset from /api/cases, filters it, and shows full case
 * details (problem, topology, Cisco output, expected fault) in a side panel
 * with a one-click "Diagnose This Case" action.
 */
document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("cases-tbody");
  const resultCount = document.getElementById("result-count");
  const catFilter = document.getElementById("filter-category");
  const sevFilter = document.getElementById("filter-severity");
  const panel = document.getElementById("case-detail-panel");
  const overlay = document.getElementById("panel-overlay");
  const panelContent = document.getElementById("panel-content");

  function fetchCases() {
    const params = new URLSearchParams();
    if (catFilter.value) params.set("category", catFilter.value);
    if (sevFilter.value) params.set("severity", sevFilter.value);

    fetch(`/api/cases?${params.toString()}`)
      .then((r) => r.json())
      .then((data) => {
        const cases = data.cases || [];
        resultCount.textContent = `${data.count} case${data.count === 1 ? "" : "s"}`;
        renderTable(cases);
      });
  }

  function renderTable(cases) {
    if (!cases.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="empty-state">No cases match these filters.</td></tr>`;
      return;
    }
    tbody.innerHTML = cases.map((c) => `
      <tr class="clickable" data-case-id="${escapeHtml(c.case_id)}">
        <td><span class="tag">${escapeHtml(c.case_id)}</span></td>
        <td>${escapeHtml(c.title)}</td>
        <td>${escapeHtml(c.concept)}</td>
        <td><span class="badge ${severityBadgeClass(c.severity)}">${escapeHtml(c.severity)}</span></td>
      </tr>
    `).join("");

    tbody.querySelectorAll("tr[data-case-id]").forEach((row) => {
      row.addEventListener("click", () => openPanel(row.dataset.caseId));
    });
  }

  function openPanel(caseId) {
    const c = (allCases || []).find((x) => x.case_id === caseId);
    if (!c) return;
    panelContent.innerHTML = `
      <div class="eyebrow">${escapeHtml(c.concept)} · ${escapeHtml(c.osi_layer)}</div>
      <h2 style="margin-bottom:4px;">${escapeHtml(c.title)}</h2>
      <span class="badge ${severityBadgeClass(c.severity)}">${escapeHtml(c.severity)}</span>
      <span class="tag" style="margin-left:6px;">${escapeHtml(c.case_id)}</span>

      <div style="margin-top:20px;">
        <div class="diag-label">Problem</div>
        <p style="font-size:13.5px;">${escapeHtml(c.symptom)}</p>
      </div>
      <div>
        <div class="diag-label">Topology</div>
        <p style="font-size:13.5px;">${escapeHtml(c.topology_note)}</p>
      </div>
      <div>
        <div class="diag-label">Cisco Output</div>
        <div class="terminal">
          <div class="terminal-bar"><span class="terminal-dot"></span><span class="terminal-dot"></span><span class="terminal-dot"></span></div>
          <pre>${escapeHtml(c.show_output)}</pre>
        </div>
      </div>
      <div style="margin-top:16px;">
        <div class="diag-label">Expected Fault</div>
        <p style="font-size:13.5px;font-weight:600;color:var(--navy-900);margin:0;">${escapeHtml(c.expected_fault)}</p>
      </div>
      <a class="btn btn-primary btn-block" href="/diagnose?case=${encodeURIComponent(c.case_id)}&run=1">Diagnose This Case →</a>
    `;
    panel.classList.add("open");
    overlay.classList.add("open");
  }

  let allCases = [];

  function loadAll() {
    fetch("/api/cases")
      .then((r) => r.json())
      .then((data) => {
        allCases = data.cases || [];
        fetchCases();
      });
  }

  function closePanel() {
    panel.classList.remove("open");
    overlay.classList.remove("open");
  }

  document.getElementById("panel-close").addEventListener("click", closePanel);
  overlay.addEventListener("click", closePanel);
  [catFilter, sevFilter].forEach((el) => el.addEventListener("change", fetchCases));

  loadAll();
});