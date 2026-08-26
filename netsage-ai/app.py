import os
import csv
import json
import uuid
from datetime import datetime, timezone

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from ai.diagnosis import diagnose, get_ai_mode
from checker.rule_checker import run_rule_checks

load_dotenv()

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CASES_CSV = os.path.join(DATA_DIR, "cases.csv")
HISTORY_JSON = os.path.join(DATA_DIR, "diagnosis_history.json")
REVIEW_LOG_CSV = os.path.join(DATA_DIR, "review_log.csv")

REVIEW_FIELDNAMES = [
    "case_id", "ai_result", "human_decision",
    "corrected_diagnosis", "reviewer_comment", "timestamp",
    "packet_tracer_case_id", "packet_tracer_device",
    "packet_tracer_command_evidence", "packet_tracer_verification_result",
]


def load_cases():
    """Load the troubleshooting case dataset from CSV."""
    if not os.path.exists(CASES_CSV):
        return []
    with open(CASES_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_case(case_id):
    """Look up a single case from the CSV by its case ID."""
    target = (case_id or "").strip().lower()
    for case in load_cases():
        if (case.get("case_id") or "").strip().lower() == target:
            return case
    return None


def load_history():
    """Load stored AI diagnosis history (JSON list)."""
    if not os.path.exists(HISTORY_JSON):
        return []
    try:
        with open(HISTORY_JSON, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_history(history):
    with open(HISTORY_JSON, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def append_history(entry):
    history = load_history()
    history.append(entry)
    save_history(history)


def load_reviews():
    """Load the human review log from CSV."""
    if not os.path.exists(REVIEW_LOG_CSV):
        return []
    with open(REVIEW_LOG_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def append_review(row: dict):
    file_exists = os.path.exists(REVIEW_LOG_CSV)
    with open(REVIEW_LOG_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        # Ensure all fieldnames are present, use empty string for missing
        writer_row = {fn: row.get(fn, "") for fn in writer.fieldnames}
        writer.writerow(writer_row)


@app.route("/")
def home():
    return render_template("index.html", ai_mode=get_ai_mode())


@app.route("/diagnose")
def diagnose_page():
    return render_template("diagnose.html", ai_mode=get_ai_mode())


@app.route("/cases")
def cases_page():
    return render_template("cases.html")


@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


@app.route("/about")
def about_page():
    return render_template("about.html", ai_mode=get_ai_mode())


@app.route("/api/cases", methods=["GET"])
def api_cases():
    """Return the full case dataset, optionally filtered by query params."""
    cases = load_cases()

    category = request.args.get("category", "").strip()
    severity = request.args.get("severity", "").strip()
    osi_layer = request.args.get("osi_layer", "").strip()

    if category:
        cases = [c for c in cases if c.get("concept", "").lower() == category.lower()]
    if severity:
        cases = [c for c in cases if c.get("severity", "").lower() == severity.lower()]
    if osi_layer:
        cases = [c for c in cases if osi_layer.lower() in c.get("osi_layer", "").lower()]

    return jsonify({"count": len(cases), "cases": cases})


@app.route("/api/check", methods=["POST"])
def api_check():
    """Run the deterministic, AI-independent rule checker."""
    payload = request.get_json(silent=True) or {}
    symptom = payload.get("symptom", "")
    show_output = payload.get("show_output", "")
    topology_note = payload.get("topology_note", "")

    if not symptom and not show_output:
        return jsonify({"error": "Please enter a network symptom or command output."}), 400

    result = run_rule_checks(symptom, show_output, topology_note)
    return jsonify(result)


@app.route("/api/diagnose", methods=["POST"])
def api_diagnose():
    """
    Full diagnosis workflow:
    User Input -> Rule Checker -> AI Diagnosis -> Combine Evidence -> Display
    A human review is still required before this diagnosis is considered final.

    Accepts either:
      - a predefined 'case_id' (the dataset's CASE-001 style id), in which case
        the symptom / topology / show output are taken from the case file, or
      - free-form 'symptom' / 'topology_note' / 'show_output' fields.
    """
    payload = request.get_json(silent=True) or {}
    case = get_case(payload.get("case_id"))

    if case:
        symptom = (case.get("symptom") or "").strip()
        topology_note = (case.get("topology_note") or "").strip()
        show_output = (case.get("show_output") or "").strip()
        case_type = (case.get("concept") or "").strip()
        severity_hint = (case.get("severity") or "").strip()
        final_case_id = case["case_id"]
    else:
        symptom = (payload.get("symptom") or "").strip()
        topology_note = (payload.get("topology_note") or "").strip()
        show_output = (payload.get("show_output") or "").strip()
        case_type = (payload.get("case_type") or "").strip()
        severity_hint = (payload.get("severity") or "").strip()
        final_case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"

    if not symptom:
        return jsonify({"error": "Please enter a network symptom."}), 400

    # Step 1: deterministic rule checker runs first, independent of the AI.
    rule_result = run_rule_checks(symptom, show_output, topology_note)

    # Step 2: AI diagnosis, informed by (but not overridden by) rule findings.
    ai_result = diagnose(
        symptom=symptom,
        topology_note=topology_note,
        show_output=show_output,
        case_type=case_type,
        severity_hint=severity_hint,
        rule_findings=rule_result["issues"],
    )

    record = {
        "case_id": final_case_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": {
            "symptom": symptom,
            "topology_note": topology_note,
            "show_output": show_output,
            "case_type": case_type,
            "severity_hint": severity_hint,
        },
        "rule_checker_result": rule_result,
        "ai_result": ai_result,
        "review_status": "Pending",
        "packet_tracer_case_id": payload.get("packet_tracer_case_id", ""),
        "packet_tracer_device": payload.get("packet_tracer_device", ""),
        "packet_tracer_command_evidence": payload.get("packet_tracer_command_evidence", ""),
        "packet_tracer_verification_result": payload.get("packet_tracer_verification_result", ""),
    }
    append_history(record)

    return jsonify({
        "case_id": final_case_id,
        "case_title": case.get("title", "") if case else "",
        "rule_checker_result": rule_result,
        "ai_result": ai_result,
        "notice": "NetSage AI provides diagnostic suggestions for educational/lab "
                   "environments. Always verify recommendations before applying "
                   "network configuration changes. A human reviewer must approve, "
                   "edit, or reject this diagnosis.",
    })


@app.route("/api/review", methods=["POST"])
def api_review():
    """Store a human reviewer's decision on an AI diagnosis."""
    payload = request.get_json(silent=True) or {}
    case_id = (payload.get("case_id") or "").strip()
    ai_result = payload.get("ai_result", "")
    human_decision = (payload.get("human_decision") or "").strip()
    corrected_diagnosis = payload.get("corrected_diagnosis", "")
    reviewer_comment = payload.get("reviewer_comment", "")

    if not case_id or not human_decision:
        return jsonify({"error": "'case_id' and 'human_decision' are required."}), 400

    if human_decision not in ("Accepted", "Edited", "Rejected"):
        return jsonify({"error": "'human_decision' must be Accepted, Edited, or Rejected."}), 400

    if isinstance(ai_result, (dict, list)):
        ai_result = json.dumps(ai_result)

    row = {
        "case_id": case_id,
        "ai_result": ai_result,
        "human_decision": human_decision,
        "corrected_diagnosis": corrected_diagnosis,
        "reviewer_comment": reviewer_comment,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }
    append_review(row)

    # Update the matching diagnosis_history entry's review_status, if present.
    history = load_history()
    for entry in history:
        if entry.get("case_id") == case_id:
            entry["review_status"] = human_decision
            break
    save_history(history)

    return jsonify({"message": "Review recorded.", "case_id": case_id})


@app.route("/api/reviews", methods=["GET"])
def api_reviews():
    """Return the raw human review log, most recent first."""
    reviews = load_reviews()
    return jsonify({"count": len(reviews), "reviews": list(reversed(reviews))})


@app.route("/api/history", methods=["GET"])
def api_history():
    """Return stored AI diagnosis history, most recent first."""
    history = load_history()
    return jsonify({"count": len(history), "history": list(reversed(history))})


@app.route("/api/statistics", methods=["GET"])
def api_statistics():
    """Compute dashboard statistics from the case dataset and review log."""
    cases = load_cases()
    reviews = load_reviews()

    total_cases = len(cases)

    category_counts = {}
    severity_counts = {}
    osi_counts = {}
    for c in cases:
        cat = c.get("concept", "Other")
        sev = c.get("severity", "Unknown")
        osi = c.get("osi_layer", "Unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        osi_counts[osi] = osi_counts.get(osi, 0) + 1

    decision_counts = {"Accepted": 0, "Edited": 0, "Rejected": 0}
    for r in reviews:
        decision = r.get("human_decision", "")
        if decision in decision_counts:
            decision_counts[decision] += 1

    reviewed_total = sum(decision_counts.values())
    agreement_rate = round((decision_counts["Accepted"] / reviewed_total) * 100, 1) if reviewed_total else 0.0

    mode = get_ai_mode()
    mode_label = "Live AI Mode" if (mode == "live" and os.environ.get("AI_API_KEY")) else "Demo AI Mode"

    return jsonify({
        "total_cases": total_cases,
        "category_counts": category_counts,
        "severity_counts": severity_counts,
        "osi_layer_counts": osi_counts,
        "review_decision_counts": decision_counts,
        "reviewed_total": reviewed_total,
        "ai_agreement_rate": agreement_rate,
        "ai_mode": mode,
        "ai_mode_label": mode_label,
    })


@app.errorhandler(404)
def not_found(_e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(_e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
