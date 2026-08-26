/*
 * diagnose.js
 * Drives the full Diagnose page:
 *   1. Case selection  -> 2. Evidence preview -> 3. Diagnose (rule checker +
 *      AI, server side) -> 4. Human review (Accept / Edit / Reject) -> status.
 */
document.addEventListener("DOMContentLoaded", () => {
  const caseSelect = document.getElementById("case-select");
  const casePreview = document.getElementById("case-preview");
  const caseDiagnoseBtn = document.getElementById("case-diagnose-btn");
  const manualBtn = document.getElementById("manual-diagnose-btn");
  const symptomEl = document.getElementById("symptom");
  const topologyEl = document.getElementById("topology");
  const showOutputEl = document.getElementById("show-output");
  const resultsColumn = document.getElementById("results-column");
  const formHint = document.getElementById("form-hint");

  let allCases = [];
  let selectedCase = null;

  // ---- Load the case list ------------------------------------------------
  fetch("/api/cases")
    .then((r) => r.json())
    .then((data) => {
      allCases = data.cases || [];
      caseSelect.innerHTML =
        '<option value="">Select a case...</option>' +
        allCases
          .map((c) => {
            const cat = escapeHtml(c.concept || "");
            const sev = escapeHtml(c.severity || "");
            return `<option value="${escapeHtml(c.case_id)}">${escapeHtml(c.case_id)} — ${escapeHtml(c.title)} (${cat}, ${sev})</option>`;
          })
          .join("");

      // Auto-open a demo case via ?case=CASE-001&run=1
      const params = new URLSearchParams(window.location.search);
      const autoCase = params.get("case");
      if (autoCase) {
        caseSelect.value = autoCase;
        showPreviewFor(autoCase);
        if (params.get("run") === "1") {
          runCaseDiagnosis(autoCase);
        }
      }
    })
    .catch(() => {
      caseSelect.innerHTML = '<option value="">Failed to load cases.</option>';
    });

  function showPreviewFor(caseId) {
    const c = allCases.find((x) => x.case_id === caseId);
    if (!c) {
      casePreview.style.display = "none";
      caseDiagnoseBtn.disabled = true;
      return;
    }
    selectedCase = c;
    casePreview.style.display = "block";
    document.getElementById("cv-title").textContent = `${c.case_id} — ${c.title}`;
    document.getElementById("cv-problem").textContent = c.symptom;
    document.getElementById("cv-topology").textContent = c.topology_note;
    document.getElementById("cv-output").textContent = c.show_output;
    caseDiagnoseBtn.disabled = false;
  }

  caseSelect.addEventListener("change", () => {
    if (caseSelect.value) {
      showPreviewFor(caseSelect.value);
    } else {
      casePreview.style.display = "none";
      caseDiagnoseBtn.disabled = true;
    }
  });

  caseDiagnoseBtn.addEventListener("click", () => {
    if (caseSelect.value) runCaseDiagnosis(caseSelect.value);
  });

  function runCaseDiagnosis(caseId) {
    if (!caseId) return;
    postDiagnosis({ case_id: caseId }, `Diagnosing ${caseId}...`);
  }

  // ---- Manual diagnosis ---------------------------------------------------
  manualBtn.addEventListener("click", () => {
    const symptom = symptomEl.value.trim();
    const topology = topologyEl.value.trim();
    const showOutput = showOutputEl.value.trim();

    formHint.innerHTML = "";
    if (!symptom) {
      showFormError("Please enter a network symptom.");
      return;
    }
    if (!showOutput) {
      showFormWarning("Command output is recommended for evidence-based diagnosis.");
    }
    postDiagnosis({ symptom, topology_note: topology, show_output: showOutput }, "Analyzing your problem...");
  });

  function showFormError(msg) {
    formHint.innerHTML = `<p style="color:var(--danger);font-size:13px;margin:10px 0 0;">${escapeHtml(msg)}</p>`;
  }
  function showFormWarning(msg) {
    formHint.innerHTML = `<p style="color:var(--warning);font-size:12.5px;margin:10px 0 0;">${escapeHtml(msg)}</p>`;
  }

  // ---- Common diagnosis request ------------------------------------------
  async function postDiagnosis(payload, loadingText) {
    resultsColumn.innerHTML = `
      <div class="card">
        <div class="loading-row"><div class="spinner"></div> ${loadingText}</div>
      </div>`;
    resultsColumn.scrollIntoView({ behavior: "smooth", block: "nearest" });
    try {
      const res = await fetch("/api/diagnose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        resultsColumn.innerHTML = `<div class="card"><p style="color:var(--danger);margin:0;">${escapeHtml(data.error || "Something went wrong.")}</p></div>`;
        return;
      }
      renderResults(data);
    } catch (err) {
      resultsColumn.innerHTML = `<div class="card"><p style="color:var(--danger);margin:0;">Request failed: ${escapeHtml(err.message)}</p></div>`;
    }
  }

  // ---- Results rendering ---------------------------------------------------
  function renderResults(data) {
    const ai = data.ai_result;
    const rule = data.rule_checker_result;
    const caseId = data.case_id;

    const isInsufficient = ai.confidence === "Low";
    const evidenceHtml = (ai.evidence || []).length
      ? `<ul class="evidence-list">${(ai.evidence || []).map((e) => `<li>${escapeHtml(e)}</li>`).join("")}</ul>`
      : `<p class="field-hint">No specific evidence was found in the provided text.</p>`;

    const ruleHeading = rule.issues_found
      ? `<p class="rule-summary rule-summary-bad">⚠️ Configuration Problem Found</p>`
      : `<p class="rule-summary rule-summary-good">✅ No obvious configuration error found</p>`;

    const ruleHtml = rule.issues_found
      ? rule.issues.map((iss) => `
          <div class="rule-item">
            <div class="rule-item-head">
              <strong>${escapeHtml(iss.type)}</strong>
              <span class="badge ${severityBadgeClass(iss.severity)}">${escapeHtml(iss.severity)}</span>
            </div>
            <p>${escapeHtml(iss.evidence)}</p>
            <p class="rule-rec">→ ${escapeHtml(iss.recommendation)}</p>
          </div>`).join("")
      : "";

    resultsColumn.innerHTML = `
      <div class="card result-card ai-card">
        <div class="card-title-row">
          <h3 style="margin:0;"><span class="source-tag source-ai">AI Diagnosis</span></h3>
          <span class="badge ${severityBadgeClass(ai.severity)}">${escapeHtml(ai.severity)}</span>
        </div>

        <div class="diag-label">🔴 Problem Found</div>
        <p class="diag-problem ${isInsufficient ? 'diag-problem-warn' : ''}">${escapeHtml(ai.root_cause)}</p>

        <div class="grid grid-2" style="margin:14px 0;">
          <div>
            <div class="diag-label">OSI Layer</div>
            <div class="diag-value">${escapeHtml(ai.osi_layer)}</div>
          </div>
          <div>
            <div class="diag-label">Confidence</div>
            <div class="diag-value">${escapeHtml(ai.confidence)}</div>
          </div>
        </div>

        <div style="margin-bottom:14px;">
          <div class="diag-label">Why?</div>
          ${evidenceHtml}
        </div>

        <div style="margin-bottom:14px;">
          <div class="diag-label">Check This Command</div>
          <div class="terminal">
            <div class="terminal-bar"><span class="terminal-dot"></span><span class="terminal-dot"></span><span class="terminal-dot"></span><span class="terminal-label">Router#</span></div>
            <pre>${escapeHtml(ai.next_command)}</pre>
          </div>
        </div>

        <div style="margin-bottom:14px;">
          <div class="diag-label">How to Fix</div>
          <ol class="fix-steps">${(ai.fix_steps || []).map((s) => `<li>${escapeHtml(s)}</li>`).join("")}</ol>
        </div>

        <div>
          <div class="diag-label">Verify</div>
          <div class="terminal">
            <div class="terminal-bar"><span class="terminal-dot"></span><span class="terminal-dot"></span><span class="terminal-dot"></span><span class="terminal-label">Verify</span></div>
            <pre>${(ai.verification_steps || []).map(escapeHtml).join("\n")}</pre>
          </div>
        </div>

        <p class="field-hint" style="margin-top:12px;">${ai.mode === "demo" ? "AI Mode: DEMO — predefined responses for reliable classroom demonstration." : "AI Mode: Live"}</p>
      </div>

      <div class="card result-card rule-card">
        <div class="card-title-row">
          <h3 style="margin:0;"><span class="source-tag source-rule">Rule Checker</span></h3>
          ${rule.issues_found ? `<span class="tag">${rule.issues.length} issue(s)</span>` : ""}
        </div>
        ${ruleHeading}
        ${ruleHtml}
      </div>

      ${renderReviewCard(data)}
    `;

    attachReviewHandlers(data);
    resultsColumn.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  // ---- Human review -------------------------------------------------------
  function renderReviewCard(data) {
    return `
      <div class="card review-card" data-case="${escapeHtml(data.case_id)}">
        <h3>Human Review</h3>
        <div class="review-title">Question: Do you agree with the AI diagnosis?</div>
        <div class="review-decision-group">
          <button type="button" class="decision-btn" data-decision="Accepted">✅ Accept</button>
          <button type="button" class="decision-btn" data-decision="Edited">✏️ Edit</button>
          <button type="button" class="decision-btn" data-decision="Rejected">❌ Reject</button>
        </div>
        <div class="edit-fields" style="display:none;">
          <div class="field">
            <label>Correct Diagnosis</label>
            <textarea class="corrected-diagnosis" rows="2" placeholder="What is the correct root cause / fix?"></textarea>
          </div>
          <div class="field" style="margin-bottom:10px;">
            <label>Reason</label>
            <textarea class="reviewer-comment" rows="2" placeholder="Why did you make this decision?"></textarea>
          </div>
        </div>
        <button class="btn btn-primary btn-block save-review" disabled>Save Review</button>
        <div class="review-status"></div>
      </div>`;
  }

  function attachReviewHandlers(data) {
    const reviewCard = resultsColumn.querySelector(".review-card");
    const statusEl = reviewCard.querySelector(".review-status");
    const saveBtn = reviewCard.querySelector(".save-review");
    const editFields = reviewCard.querySelector(".edit-fields");
    let decision = null;

    reviewCard.querySelectorAll(".decision-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        reviewCard.querySelectorAll(".decision-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        decision = btn.dataset.decision;
        editFields.style.display = decision === "Edited" ? "block" : "none";
        saveBtn.disabled = false;
        statusEl.innerHTML = "";
      });
    });

    saveBtn.addEventListener("click", async () => {
      if (!decision) return;
      saveBtn.disabled = true;
      saveBtn.textContent = "Saving...";
      const payload = {
        case_id: data.case_id,
        ai_result: data.ai_result,
        human_decision: decision,
        corrected_diagnosis: reviewCard.querySelector(".corrected-diagnosis").value.trim(),
        reviewer_comment: reviewCard.querySelector(".reviewer-comment").value.trim(),
      };
      try {
        const res = await fetch("/api/review", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const result = await res.json();
        if (res.ok) {
          statusEl.innerHTML = `<span class="badge ${decision === "Accepted" ? "badge-low" : decision === "Edited" ? "badge-medium" : "badge-high"} review-status-badge">Review Status: ${escapeHtml(decision.toUpperCase())}</span>`;
          statusEl.innerHTML += `<p class="field-hint" style="margin-top:8px;">Review saved for ${escapeHtml(data.case_id)}.</p>`;
          reviewCard.querySelectorAll(".decision-btn").forEach((b) => (b.disabled = true));
          saveBtn.disabled = true;
        } else {
          statusEl.innerHTML = `<p style="color:var(--danger);font-size:13px;">${escapeHtml(result.error || "Failed to save review.")}</p>`;
          saveBtn.disabled = false;
        }
      } catch (err) {
        statusEl.innerHTML = `<p style="color:var(--danger);font-size:13px;">Error: ${escapeHtml(err.message)}</p>`;
        saveBtn.disabled = false;
      } finally {
        saveBtn.textContent = "Save Review";
      }
    });
  }
});