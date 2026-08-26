"""
prompts.py

Central place for the prompt(s) sent to the LLM for network diagnosis.
Keeping the prompt text here (mirrored in docs/diagnose_prompt.md) makes
it easy to review, version, and audit what instructions the AI is given.
"""

SYSTEM_PROMPT = """You are a Cisco network troubleshooting assistant embedded in NetSage AI.

Analyze ONLY the provided symptom, topology notes, command output, and rule-checker
findings. Do not invent evidence that is not present in the input. If the provided
evidence is insufficient to reach a confident conclusion, say so explicitly rather
than guessing.

For every request, identify:
1. root_cause - the most likely underlying configuration or network problem
2. confidence - "Low", "Medium", or "High"
3. evidence - a list of short evidence bullet points drawn directly from the
   symptom, topology notes, show output, or rule-checker results
4. osi_layer - the OSI layer(s) most relevant to this fault (e.g. "Layer 2", "Layer 3")
5. next_command - the single most useful next Cisco 'show' command to run to confirm
6. fix_steps - an ordered list of concrete remediation steps
7. severity - "Low", "Medium", "High", or "Critical"
8. verification_steps - commands/tests to confirm the fix worked

If evidence is insufficient, set confidence to "Low" and explicitly state:
"Insufficient evidence - run the recommended command before confirming the diagnosis."

A human reviewer must approve, edit, or reject every diagnosis you produce. You do
not have permission to apply configuration changes; you may only recommend them.

Respond ONLY with a single JSON object matching this exact schema, with no
markdown formatting, code fences, or extra commentary:

{
  "root_cause": "string",
  "confidence": "Low | Medium | High",
  "evidence": ["string", "..."],
  "osi_layer": "string",
  "next_command": "string",
  "fix_steps": ["string", "..."],
  "severity": "Low | Medium | High | Critical",
  "verification_steps": ["string", "..."]
}
"""

# Worked examples included for prompt-engineering documentation purposes
# (see docs/diagnose_prompt.md for the full write-up with commentary).
WORKED_EXAMPLES = [
    {
        "input": {
            "symptom": "PC gets an IP address but cannot reach the server in VLAN 30. "
                       "The PC can ping its default gateway.",
            "topology_note": "PC connected to Switch1. Switch1 connects to Router1. "
                              "Server is located in VLAN 30.",
            "show_output": "show vlan brief\nFa0/5 shows VLAN 1 (expected VLAN 30)\n"
                            "show interfaces trunk\nFa0/1 trunking, native vlan 1",
        },
        "output": {
            "root_cause": "Server-facing switch port is still assigned to the default "
                           "VLAN 1 instead of VLAN 30.",
            "confidence": "High",
            "evidence": [
                "PC successfully obtained an IP and can reach its gateway (Layer 1-2 to the router is fine).",
                "show vlan brief confirms Fa0/5 is in VLAN 1, not VLAN 30 where the server should be.",
            ],
            "osi_layer": "Layer 2",
            "next_command": "show running-config interface fastEthernet0/5",
            "fix_steps": [
                "Enter interface configuration mode for Fa0/5.",
                "Run 'switchport access vlan 30'.",
                "Verify with 'show vlan brief' that Fa0/5 now appears under VLAN 30.",
            ],
            "severity": "High",
            "verification_steps": [
                "ping <server-ip>",
                "show vlan brief",
            ],
        },
    },
    {
        "input": {
            "symptom": "Internal users cannot reach the internet.",
            "topology_note": "Router1 connects internal LAN to ISP via Serial0/1/0.",
            "show_output": "show ip nat translations -> empty\nshow run | include nat inside -> "
                            "only 'ip nat inside source list 1 interface Serial0/1/0 overload' present, "
                            "no 'ip nat inside' on GigabitEthernet0/0",
        },
        "output": {
            "root_cause": "The internal-facing interface (GigabitEthernet0/0) is missing the "
                           "'ip nat inside' command, so NAT overload never triggers for outbound traffic.",
            "confidence": "High",
            "evidence": [
                "NAT translation table is empty despite users reporting internet issues.",
                "Running-config shows the NAT overload statement exists but the inside interface "
                "marker is missing.",
            ],
            "osi_layer": "Layer 3",
            "next_command": "show ip nat statistics",
            "fix_steps": [
                "Enter interface configuration mode for GigabitEthernet0/0.",
                "Run 'ip nat inside'.",
                "Confirm Serial0/1/0 already has 'ip nat outside'.",
                "Re-test outbound connectivity.",
            ],
            "severity": "High",
            "verification_steps": [
                "show ip nat translations",
                "ping 8.8.8.8 from an internal host",
            ],
        },
    },
    {
        "input": {
            "symptom": "One PC on VLAN 10 cannot reach the server in VLAN 30. Ping to gateway works.",
            "topology_note": "PC connected to Switch1. Router1 routes between VLANs.",
            "show_output": "show ip route -> only directly connected routes shown, "
                            "no ACL or trunk output provided",
        },
        "output": {
            "root_cause": "Insufficient evidence - run the recommended command before confirming the diagnosis.",
            "confidence": "Low",
            "evidence": [
                "PC can reach its own gateway, ruling out basic Layer 2 connectivity on its own segment.",
                "No ACL, trunk, or inter-VLAN routing configuration was provided to confirm the exact cause.",
            ],
            "osi_layer": "Layer 3 (tentative)",
            "next_command": "show access-lists",
            "fix_steps": [
                "Gather 'show access-lists' and 'show interfaces trunk' output before proceeding.",
                "Re-run diagnosis once additional evidence is available.",
            ],
            "severity": "Medium",
            "verification_steps": [
                "ping <server-ip>",
                "show ip route",
            ],
        },
    },
]
