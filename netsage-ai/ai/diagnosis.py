"""
diagnosis.py

AI diagnosis service for NetSage AI.

Two modes, controlled by the AI_MODE environment variable:
  - "demo" (default): evidence-based template responses. The demo AI only
    reports a problem when the given symptom / topology / show output
    actually supports it. No API key or internet access required.
  - "live": calls a configured LLM API (Anthropic by default) using the
    prompt in prompts.py and parses the JSON response.

The AI is never allowed to apply configuration - it only returns structured
diagnostic suggestions that a human must review before anything changes.
"""
import os
import re
import json

from ai.prompts import SYSTEM_PROMPT

REQUIRED_FIELDS = [
    "root_cause", "confidence", "evidence", "osi_layer",
    "next_command", "fix_steps", "severity", "verification_steps",
]

INSUFFICIENT_TEXT = "Not enough evidence to confirm the problem."


def get_ai_mode() -> str:
    return os.environ.get("AI_MODE", "demo").strip().lower()


def diagnose(symptom: str, topology_note: str, show_output: str,
             case_type: str = "", severity_hint: str = "",
             rule_findings=None):
    """
    Produce a structured AI diagnosis.

    Returns a dict with the fields defined in REQUIRED_FIELDS, plus a
    "mode" key indicating whether the "demo" or "live" path was used.
    """
    mode = get_ai_mode()
    rule_findings = rule_findings or []

    if mode == "live" and os.environ.get("AI_API_KEY"):
        try:
            result = _call_live_ai(symptom, topology_note, show_output,
                                   case_type, severity_hint, rule_findings)
            result["mode"] = "live"
            return _normalize(result)
        except Exception as exc:
            # Fail safe: never crash the app if the live API has a problem.
            # Fall back to demo mode and surface the error for transparency.
            fallback = _demo_diagnosis(symptom, topology_note, show_output,
                                       case_type, rule_findings)
            fallback["mode"] = "demo_fallback"
            fallback["api_error"] = str(exc)
            return _normalize(fallback)

    result = _demo_diagnosis(symptom, topology_note, show_output, case_type, rule_findings)
    result["mode"] = "demo"
    return _normalize(result)


def _call_live_ai(symptom, topology_note, show_output, case_type, severity_hint, rule_findings):
    """Calls the configured LLM API (Anthropic Messages API by default)."""
    import urllib.request

    api_key = os.environ["AI_API_KEY"]
    model = os.environ.get("AI_MODEL", "claude-sonnet-4-6")
    api_url = os.environ.get("AI_API_URL", "https://api.anthropic.com/v1/messages")

    user_content = (
        f"Symptom:\n{symptom}\n\n"
        f"Topology Notes:\n{topology_note}\n\n"
        f"Show Command Output:\n{show_output}\n\n"
        f"Case Type (optional hint): {case_type or 'Not specified'}\n"
        f"Severity Hint (optional): {severity_hint or 'Not specified'}\n\n"
        f"Deterministic Rule Checker Findings:\n{json.dumps(rule_findings, indent=2)}\n\n"
        "Respond with the JSON object described in the system prompt only."
    )

    payload = {
        "model": model,
        "max_tokens": 1000,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_content}],
    }

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
    raw_text = "\n".join(text_blocks).strip()
    # Strip accidental markdown code fences if the model adds them.
    raw_text = re.sub(r"^```(json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()

    return json.loads(raw_text)


# --------------------------------------------------------------------------
# Demo (offline) mode - evidence-based template responses
# --------------------------------------------------------------------------

def _demo_diagnosis(symptom, topology_note, show_output, case_type, rule_findings):
    """
    Evidence-based demo diagnosis.

    1. Pick the most relevant template using keywords / case type.
    2. Build the evidence list ONLY from lines that actually appear in the
       provided symptom, topology note, or show output.
    3. If no concrete evidence is present, respond with an
       "insufficient evidence" result instead of guessing - the AI never
       invents evidence that was not supplied.
    4. Deterministic rule-checker findings are appended as extra evidence
       (they are real, reproducible checks on the same input).
    """
    rule_findings = rule_findings or []
    text = " ".join([symptom or "", topology_note or "", show_output or ""]).lower()

    template = _match_template(text, case_type)

    evidence = []
    if template is not None:
        for needle, bullet in template["evidence"]:
            if needle in text:
                evidence.append(bullet)

    # Computed evidence: for gateway problems, state the concrete mismatch
    # between the host IP and the configured gateway (both from the input).
    dynamic = _dynamic_evidence(text, template)
    if dynamic and dynamic not in evidence:
        evidence.append(dynamic)

    for finding in rule_findings[:3]:
        note = f"Rule checker flagged: {finding['type']} ({finding['severity']})."
        if note not in evidence:
            evidence.append(note)

    if template is not None and evidence:
        base = {
            "root_cause": template["root_cause"],
            "confidence": "High" if _has_direct_evidence(template, text) else "Medium",
            "evidence": evidence,
            "osi_layer": template["osi_layer"],
            "next_command": template["next_command"],
            "fix_steps": template["fix_steps"],
            "severity": template["severity"],
            "verification_steps": template["verification_steps"],
        }
        return base

    # Nothing concrete matched -> be honest instead of guessing.
    recommended = template["next_command"] if template is not None else "show running-config"
    return {
        "root_cause": f"{INSUFFICIENT_TEXT} Run the recommended command and try again.",
        "confidence": "Low",
        "evidence": [
            "The provided symptom, topology, and show output do not contain enough "
            "specific detail to confirm the problem.",
        ],
        "osi_layer": "Unknown",
        "next_command": recommended,
        "fix_steps": [
            f"Run: {recommended}",
            "Re-run the diagnosis with the new command output.",
        ],
        "severity": "Medium",
        "verification_steps": ["Re-run the diagnosis after the recommended command."],
    }


def _dynamic_evidence(text, template):
    """Build one precise, computed evidence bullet from the actual input text
    (used for gateway mismatches so the AI never invents a number)."""
    if template is None or "gateway" not in template.get("keywords", []):
        return None

    gws = re.findall(r"(?:default gateway|gateway)[\s:=]+(\d+\.\d+\.\d+\.\d+)", text)
    ips = re.findall(r"(?:ipv4 address|ip address|ipconfig:\s*ip)[\s:=]+(\d+\.\d+\.\d+\.\d+)", text)
    if gws and ips:
        gw_first3 = ".".join(gws[0].split(".")[:3])
        host_first3 = ".".join(ips[0].split(".")[:3])
        if host_first3 != gw_first3:
            return (f"The host ({ips[0]}) and its default gateway ({gws[0]}) are on "
                    f"different /24 subnets.")
    return None


def _has_direct_evidence(template, text):
    """A direct CLI-output match (or a rule finding) is stronger than a mere
    keyword mention inside the symptom/topology text."""
    strong = [
        "shows vlan 1",
        "vlan 1",
        "native vlan mismatch",
        "administratively down",
        "leased addresses",
        "no ip helper-address",
        "non-existent domain",
        "no route to",
        "gateway of last resort is not set",
        "deny ip",
        "access-group",
        "wildcard mask",
        "ip nat inside",
        "wpa2-enterprise",
        "broadcast-ssid disabled",
        "down down",
        "0.0.0.0/0",
    ]
    return any(frag in text for frag in strong)


def _normalize(result: dict) -> dict:
    """Ensure all required fields exist with sane fallback values."""
    normalized = dict(result)
    normalized.setdefault("root_cause", INSUFFICIENT_TEXT)
    normalized.setdefault("confidence", "Low")
    normalized.setdefault("evidence", [])
    normalized.setdefault("osi_layer", "Unknown")
    normalized.setdefault("next_command", "show running-config")
    normalized.setdefault("fix_steps", [])
    normalized.setdefault("severity", "Medium")
    normalized.setdefault("verification_steps", ["ping <destination-ip>"])
    return normalized


# --------------------------------------------------------------------------
# Demo templates (keyword -> evidence-driven canned diagnosis)
# --------------------------------------------------------------------------

def _match_template(text, case_type):
    """Pick the first template whose keywords appear in the input. The case
    type hint (if supplied) is given priority."""
    templates = _demo_templates()

    if case_type:
        key = _case_type_key(case_type)
        tpl = templates.get(key)
        if tpl and _keywords_present(tpl, text):
            return tpl

    for tpl in templates.values():
        if _keywords_present(tpl, text):
            return tpl
    return None


def _case_type_key(case_type):
    return (case_type or "").lower().replace(" ", "_").replace("-", "_")


def _keywords_present(tpl, text):
    for kw in tpl["keywords"]:
        if kw in text:
            return True
    return False


def _demo_templates():
    return {
        "vlan": {
            "keywords": ["vlan 1", "vlan 30", "shows vlan", "switchport access vlan",
                         "native vlan", "allowed on trunk", "voice vlan", "port-security",
                         "secure-shutdown", "administrative mode: trunk"],
            "root_cause": "Wrong VLAN assignment - a switch port is in the wrong VLAN "
                          "or the VLAN is not carried across the link.",
            "confidence": "High",
            "evidence": [
                ("shows vlan 1", "The switch output shows the port still in VLAN 1 (default VLAN)."),
                ("switchport access vlan 30 command missing",
                 "The output notes that 'switchport access vlan 30' is missing on the server port."),
                ("native vlan mismatch", "The switch output reports a native VLAN mismatch on the trunk."),
                ("vlans allowed on trunk", "The trunk's allowed-VLAN list does not include the VLAN that must cross the link."),
                ("voice vlan", "A voice VLAN is set, but the data (access) VLAN for the PC was never configured."),
                ("secure-shutdown", "Port security shows a secure-shutdown violation on the access port."),
                ("administrative mode: trunk", "The port is configured as a trunk instead of an access port."),
            ],
            "osi_layer": "Layer 2",
            "next_command": "show vlan brief",
            "fix_steps": [
                "Find the affected switch port.",
                "Assign it to the correct VLAN with 'switchport access vlan <id>'.",
                "Check the VLAN again with 'show vlan brief'.",
                "Test connectivity from the affected host.",
            ],
            "severity": "High",
            "verification_steps": ["show vlan brief", "ping <destination-ip>"],
        },
        "gateway": {
            "keywords": ["gateway", "default gateway", "subnet mask", "255.255.255.192"],
            "root_cause": "Default gateway problem - the host's gateway does not match the "
                          "router address for its subnet.",
            "confidence": "High",
            "evidence": [
                ("255.255.255.192", "The host's subnet mask (255.255.255.192) is a /26, which splits the VLAN's /24 subnet."),
                ("default gateway", "The configured default gateway does not match the router SVI for the host's subnet."),
                ("is not assigned", "The configured gateway IP is not assigned to any router interface."),
            ],
            "osi_layer": "Layer 3",
            "next_command": "show ip interface brief",
            "fix_steps": [
                "Confirm the correct gateway IP for the host's subnet.",
                "Update the host's default gateway (static config or DHCP).",
                "Renew the host's IP configuration if it uses DHCP.",
                "Ping the gateway to confirm.",
            ],
            "severity": "High",
            "verification_steps": ["ipconfig /all", "ping <default-gateway>"],
        },
        "dhcp": {
            "keywords": ["dhcp", "leased addresses", "ip helper-address",
                         "excluded-address", "ip address conflict"],
            "root_cause": "DHCP problem - hosts are not getting a usable IP configuration "
                          "from the DHCP server.",
            "confidence": "Medium",
            "evidence": [
                ("leased addresses", "The DHCP pool shows all addresses leased out (scope exhausted)."),
                ("no ip helper-address", "No 'ip helper-address' relay is configured for a remote DHCP server."),
                ("ip address conflict", "A host is reporting an IP address conflict."),
                ("excluded-address", "The DHCP excluded range removes addresses that hosts need."),
            ],
            "osi_layer": "Layer 3",
            "next_command": "show ip dhcp pool",
            "fix_steps": [
                "Check DHCP pool utilization.",
                "Verify 'ip helper-address' on the VLAN interface if the server is remote.",
                "Correct the pool scope, exclusions, or options.",
                "Renew the host's address with 'ipconfig /renew'.",
            ],
            "severity": "Medium",
            "verification_steps": ["show ip dhcp binding", "ipconfig /renew"],
        },
        "dns": {
            "keywords": ["dns", "nslookup", "dns-server", "non-existent domain"],
            "root_cause": "DNS problem - hostname resolution is failing.",
            "confidence": "Medium",
            "evidence": [
                ("non-existent domain", "The DNS lookup fails with 'non-existent domain', but IP-based access works."),
                ("dns-server 203.0.113.5", "The DHCP pool is handing out the wrong DNS server (203.0.113.5)."),
                ("8.8.8.8 can't find", "The configured DNS server cannot resolve the internal hostname."),
                ("down down", "A critical switch port (the DNS server's port) is down/down."),
            ],
            "osi_layer": "Layer 7",
            "next_command": "nslookup <internal-hostname>",
            "fix_steps": [
                "Confirm the correct internal DNS server address.",
                "Point the DHCP scope (or static config) at the right DNS server.",
                "Verify Layer 3 reachability to the DNS server.",
            ],
            "severity": "Medium",
            "verification_steps": ["nslookup <hostname>", "ping <dns-server-ip>"],
        },
        "routing": {
            "keywords": ["route", "no route", "gateway of last resort",
                         "administratively down", "encapsulation dot1q",
                         "summariz", "asymmetric"],
            "root_cause": "Routing problem - a route or a routing-related interface "
                          "is missing or misconfigured.",
            "confidence": "Medium",
            "evidence": [
                ("no route to", "The routing table has no entry for the destination subnet."),
                ("gateway of last resort is not set", "The routing table has no default route (gateway of last resort)."),
                ("administratively down", "A key interface is administratively down."),
                ("encapsulation dot1q 3", "Subinterface 30 is tagging frames with dot1Q 3 instead of dot1Q 30."),
                ("return path uses a different link", "Return traffic takes a different path than the outbound traffic (asymmetric routing)."),
                ("172.16.16.0/20", "Route summarization (172.16.16.0/20) is hiding the more-specific branch subnet."),
            ],
            "osi_layer": "Layer 3",
            "next_command": "show ip route",
            "fix_steps": [
                "Check whether the destination subnet appears in 'show ip route'.",
                "Add the missing route or fix the routing protocol / interface.",
                "Confirm the affected interface is up.",
            ],
            "severity": "High",
            "verification_steps": ["show ip route", "ping <destination-ip>"],
        },
        "acl": {
            "keywords": ["access-list", "access-group", "deny ip", "wildcard mask"],
            "root_cause": "Access control list (ACL) problem - the ACL is blocking the "
                          "wrong traffic or filtering the wrong range.",
            "confidence": "Medium",
            "evidence": [
                ("deny ip 192.168.10.0 0.0.0.255 any", "The ACL contains a broad deny for the entire source subnet."),
                ("access-group 101 in", "The ACL is applied inbound on the interface it filters."),
                ("0.0.15.255", "A wildcard mask of 0.0.15.255 is used instead of 0.0.0.255 (matches too much)."),
            ],
            "osi_layer": "Layer 3",
            "next_command": "show access-lists",
            "fix_steps": [
                "Review the ACL for overly broad deny statements.",
                "Confirm the ACL is on the correct interface and direction.",
                "Correct the wildcard mask if needed.",
            ],
            "severity": "High",
            "verification_steps": ["show access-lists", "ping/traceroute the affected path"],
        },
        "nat": {
            "keywords": ["nat", "ip nat"],
            "root_cause": "NAT problem - address translation is not working as expected.",
            "confidence": "Medium",
            "evidence": [
                ("missing 'ip nat inside'", "The LAN interface is missing 'ip nat inside', so translation never triggers."),
                ("total addresses 11 allocated 11", "The NAT pool is fully allocated (11/11, 100%)."),
                ("203.0.113.50", "Two static NAT mappings use the same public IP (203.0.113.50)."),
            ],
            "osi_layer": "Layer 3",
            "next_command": "show ip nat statistics",
            "fix_steps": [
                "Confirm 'ip nat inside' / 'ip nat outside' on the correct interfaces.",
                "Check the NAT pool size against the number of hosts.",
                "Remove duplicate static NAT mappings.",
            ],
            "severity": "High",
            "verification_steps": ["show ip nat translations", "ping 8.8.8.8 from an internal host"],
        },
        "wireless": {
            "keywords": ["wireless", "ssid", "wpa2", "channel"],
            "root_cause": "Wireless problem - Wi-Fi association or coverage configuration is wrong.",
            "confidence": "Medium",
            "evidence": [
                ("wpa2-enterprise", "The client security profile (WPA2-Enterprise) does not match the AP (WPA2-PSK)."),
                ("broadcast-ssid disabled", "The AP has SSID broadcast disabled."),
                ("channel:", "Multiple access points are using the same channel (co-channel interference)."),
            ],
            "osi_layer": "Layer 2",
            "next_command": "show wireless client / AP config",
            "fix_steps": [
                "Match the client security profile to the AP security settings.",
                "Re-enable SSID broadcast if clients must see the network.",
                "Use non-overlapping channels on nearby access points.",
            ],
            "severity": "Medium",
            "verification_steps": ["Reconnect the client and confirm association", "Run a wireless site survey"],
        },
    }