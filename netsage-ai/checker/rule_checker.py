"""
rule_checker.py

Deterministic, non-AI rule checker. Given a symptom description and Cisco
show-command output, this module runs a fixed set of pattern/heuristic
checks (see rules.py) and returns any configuration issues it finds.

This checker is intentionally independent of the AI diagnosis service so
that its output can be used as objective, reproducible evidence alongside
(or in contrast to) the AI's suggestions.
"""
from checker.rules import ALL_RULES


def run_rule_checks(symptom: str, show_output: str, topology_note: str = ""):
    """
    Run every deterministic rule against the combined input text.

    Args:
        symptom: user-provided description of the problem.
        show_output: pasted Cisco 'show' command output.
        topology_note: optional topology description text.

    Returns:
        dict with 'issues_found' (bool) and 'issues' (list of dicts).
    """
    combined_text = " ".join([
        symptom or "",
        show_output or "",
        topology_note or "",
    ]).lower()

    issues = []
    for rule_fn in ALL_RULES:
        try:
            result = rule_fn(combined_text)
        except Exception:
            # A single faulty rule should never crash the whole checker.
            result = None
        if result:
            issues.append(result)

    return {
        "issues_found": len(issues) > 0,
        "issues": issues,
    }
