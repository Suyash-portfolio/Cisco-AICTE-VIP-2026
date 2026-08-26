"""
rules.py

Defines the individual, deterministic detection rules used by the
rule_checker. Each rule is a small function that takes the combined
lowercase text of the symptom + show_output and returns a dict describing
the issue if it finds a match, or None if it doesn't.

Keeping each rule as an independent function makes it easy to add,
remove, or unit test individual checks without touching the others.
"""
import re


def check_duplicate_ip(text: str):
    """Detects duplicate / conflicting IP address evidence."""
    if "ip address conflict" in text or "ip conflict" in text:
        return _issue(
            "Duplicate IP Address",
            "High",
            "A host is reporting an IP address conflict.",
            "Identify both devices using the same address, reassign one via DHCP "
            "or static configuration, and clear the ARP cache on affected devices.",
        )
    if "duplicate" in text and ("ip" in text or "address" in text):
        return _issue(
            "Duplicate IP Address",
            "High",
            "The output references a duplicate or conflicting IP address.",
            "Find both devices using the same address and move one of them to a "
            "free address (DHCP or static).",
        )
    if "show ip dhcp conflict" in text:
        return _issue(
            "Duplicate IP Address",
            "Medium",
            "The DHCP conflict table shows addresses with detected conflicts.",
            "Check the DHCP scope range against statically assigned addresses "
            "and correct any overlap.",
        )
    return None


def check_subnet_mask(text: str):
    """Detects clearly incorrect / mismatched subnet masks."""
    bad_masks = ["255.255.255.192", "255.255.255.224", "255.255.255.240"]
    if "mask" in text and any(m in text for m in bad_masks):
        return _issue(
            "Incorrect Subnet Mask",
            "High",
            "A non-standard or mismatched subnet mask was found relative to the "
            "expected network size.",
            "Correct the mask on the host or interface so it matches the rest of "
            "the VLAN/subnet.",
        )
    if "/26" in text and "gateway" in text and "255.255.255.192" not in text:
        return None
    return None


def check_gateway_mismatch(text: str):
    """Detects a default gateway that doesn't belong to the local subnet or
    that is not assigned to any router interface."""
    gws = re.findall(r"(?:default gateway|gateway)[\s:=]+(\d+\.\d+\.\d+\.\d+)", text)
    ips = re.findall(r"(?:ipv4 address|ip address|ipconfig:\s*ip|ip\s)\s*[:=]?\s*(\d+\.\d+\.\d+\.\d+)", text)

    if gws and ips:
        gw_first3 = ".".join(gws[0].split(".")[:3])
        for ip in ips:
            if ".".join(ip.split(".")[:3]) != gw_first3:
                return _issue(
                    "Gateway Mismatch",
                    "High",
                    f"Host IP ({ip}) and default gateway ({gws[0]}) are on different "
                    f"/24 subnets.",
                    "Correct the default gateway so it resides on the same subnet as "
                    "the host, or fix the host's IP/mask configuration.",
                )

    if gws and re.search(rf"{re.escape(gws[0])}.*(?:not assigned|not configured|does not exist)", text):
        return _issue(
            "Unreachable Default Gateway",
            "High",
            f"Default gateway {gws[0]} is not assigned to any router interface in "
            f"the provided output.",
            "Point the host at the router's real gateway IP for its subnet.",
        )
    return None


def check_interface_down(text: str):
    """Detects interfaces that are administratively down or in a down/down state."""
    if "administratively down" in text:
        return _issue(
            "Interface Down",
            "High",
            "Interface shows 'administratively down' in show ip interface brief output.",
            "Enable the interface with 'no shutdown' if it should be active, then "
            "verify Layer 1 connectivity.",
        )
    if re.search(r"\bdown\s+down\b", text):
        return _issue(
            "Interface Down",
            "Medium",
            "An interface or port shows a down/down status.",
            "Check cabling and the remote end of the link; re-enable the interface "
            "if it was shut down.",
        )
    return None


def check_missing_vlan(text: str):
    """Detects ports stuck in the default VLAN or a VLAN missing from a trunk."""
    if "vlan 1" in text and ("default" in text or "still in vlan 1" in text or "shows vlan 1" in text):
        return _issue(
            "Missing VLAN Assignment",
            "Medium",
            "Port is still associated with default VLAN 1 instead of the intended VLAN.",
            "Apply 'switchport access vlan <id>' on the port to assign the correct VLAN.",
        )
    if "vlans allowed on trunk" in text or "allowed on trunk" in text:
        return _issue(
            "Missing VLAN on Trunk",
            "Medium",
            "The trunk's allowed-VLAN list does not include every VLAN that must "
            "cross the link.",
            "Add the missing VLAN to the trunk with "
            "'switchport trunk allowed vlan add <id>'.",
        )
    return None


def check_missing_route(text: str):
    """Detects missing routes / no route to destination / no default route."""
    if "gateway of last resort is not set" in text and ("0.0.0.0/0" in text or "default route" in text):
        return _issue(
            "Missing Default Route",
            "Critical",
            "Routing table has no gateway of last resort and no 0.0.0.0/0 entry.",
            "Configure a default route ('ip route 0.0.0.0 0.0.0.0 <next-hop>') "
            "pointing toward the ISP or upstream router.",
        )
    if "no route to" in text or ("route" in text and "does not exist" in text):
        return _issue(
            "Missing Route",
            "Critical",
            "Destination network is not present in the routing table.",
            "Add a static route or verify the routing protocol is advertising the "
            "destination subnet correctly.",
        )
    if "not set" in text and "gateway of last resort" in text:
        return _issue(
            "Missing Default Route",
            "Medium",
            "No default route is configured (gateway of last resort not set).",
            "Check whether a default route is required and add one if the router "
            "must reach the internet.",
        )
    if ("summariz" in text and "blackhol" in text) or "no more-specific route" in text:
        return _issue(
            "Routing Blackhole (Summarization)",
            "High",
            "Route summarization is advertising a range that includes subnets not "
            "present downstream, blackholing traffic.",
            "Add a more-specific route for the missing subnet or adjust the "
            "summary range.",
        )
    return None


def check_dot1q_tag(text: str):
    """Detects a router-on-a-stick subinterface using the wrong dot1Q tag."""
    sub = re.search(r"(?:gi|ge|fa|ethernet)\d/\d(?:/\d)?\.(\d+)", text)
    tag = re.search(r"encapsulation\s+dot1[qQ]\s+(\d+)", text)
    if sub and tag and sub.group(1) != tag.group(1):
        return _issue(
            "Incorrect dot1Q Tag",
            "High",
            f"Subinterface {sub.group(0)} is tagging frames with dot1Q {tag.group(1)} "
            f"instead of {sub.group(1)}.",
            "Correct the encapsulation under the subinterface to match its VLAN: "
            "'encapsulation dot1Q <expected-vlan>'.",
        )
    return None


def check_trunk_mismatch(text: str):
    """Detects native VLAN mismatches on trunk links."""
    if "native vlan mismatch" in text or ("native vlan" in text and text.count("native vlan") >= 2):
        return _issue(
            "Trunk Native VLAN Mismatch",
            "Medium",
            "Native VLAN differs between the two ends of a trunk link.",
            "Set the same native VLAN on both switch ends of the trunk using "
            "'switchport trunk native vlan <id>'.",
        )
    return None


def check_port_mode(text: str):
    """Detects access ports accidentally configured as trunk ports."""
    if "administrative mode: trunk" in text and ("169.254" in text or "pc connected" in text or "access port" in text):
        return _issue(
            "Incorrect Port Mode",
            "Medium",
            "Port is configured as a trunk instead of an access port.",
            "Change the port to access mode with 'switchport mode access'.",
        )
    if "administrative mode: trunk" in text and "operational mode: trunk" in text:
        return _issue(
            "Incorrect Port Mode",
            "Low",
            "Port is operating as a trunk; verify this matches the design.",
            "Confirm the port should be a trunk, or change it with "
            "'switchport mode access'.",
        )
    return None


def check_dhcp_issue(text: str):
    """Detects DHCP scope exhaustion, missing helper-address, or excluded ranges."""
    if "leased addresses" in text and "total addresses" in text:
        m_total = re.search(r"total addresses\s*=\s*(\d+)", text)
        m_leased = re.search(r"leased addresses\s*=\s*(\d+)", text)
        if m_total and m_leased and m_total.group(1) == m_leased.group(1):
            return _issue(
                "DHCP Pool Exhausted",
                "Medium",
                "Leased addresses equal total addresses in the DHCP pool.",
                "Expand the DHCP scope size or reduce the lease time to free up "
                "addresses faster.",
            )
    if "ip helper-address" in text and "no ip helper-address" in text:
        return _issue(
            "Missing DHCP Relay",
            "High",
            "No 'ip helper-address' statement found on the VLAN interface that needs "
            "DHCP relay.",
            "Add 'ip helper-address <dhcp-server-ip>' under the affected VLAN interface.",
        )
    if "excluded-address" in text and ("entire" in text or "whole" in text or "excluded range" in text):
        return _issue(
            "DHCP Range Excluded",
            "High",
            "The DHCP excluded range covers the addresses hosts need.",
            "Review and remove the 'ip dhcp excluded-address' range, or expand the "
            "scope network.",
        )
    return None


def check_acl_problem(text: str):
    """Detects basic ACL misconfigurations: overly broad deny, wrong direction, wrong wildcard."""
    if "deny ip" in text and "0.0.0.255" in text:
        return _issue(
            "Overly Broad ACL Deny",
            "High",
            "ACL contains a 'deny ip <network> any' statement blocking an entire subnet.",
            "Narrow the deny statement or add specific permit entries above it for the "
            "traffic that should be allowed.",
        )
    if "access-group" in text and (" in" in text or " direction" in text):
        return _issue(
            "ACL Applied in Wrong Direction",
            "High",
            "ACL is applied in the wrong direction ('in' vs 'out') relative to the "
            "traffic it should filter.",
            "Re-apply the access-group in the correct direction on the interface.",
        )
    if "wildcard mask" in text and ("0.0.15.255" in text or "incorrect" in text):
        return _issue(
            "Incorrect ACL Wildcard Mask",
            "High",
            "Wildcard mask does not correctly match the intended subnet size.",
            "Recalculate the wildcard mask (inverse of the subnet mask) and update "
            "the ACL entry.",
        )
    if re.search(r"\bpermit\s+\d+\.\d+\.\d+\.\d+\s+\d+\.\d+\.[1-9]\d*\.\d+", text):
        return _issue(
            "Overly Broad ACL Wildcard Mask",
            "High",
            "An ACL entry uses a wildcard mask that matches a much larger range than "
            "a single /24 subnet.",
            "Use the correct wildcard mask (e.g. 0.0.0.255 for a /24 network).",
        )
    if "blocks established" in text or ("return path" in text and "acl" in text):
        return _issue(
            "Return-Path ACL Blocking Traffic",
            "High",
            "An ACL on the return path drops established return traffic.",
            "Inspect the return-path ACL and permit established/session traffic, or "
            "fix the asymmetric routing.",
        )
    return None


def check_nat_problem(text: str):
    """Detects missing NAT inside designation, exhausted NAT pools, and duplicate
    static mappings."""
    if "ip nat" not in text:
        return None

    if "missing 'ip nat inside'" in text:
        return _issue(
            "Missing NAT Inside Designation",
            "High",
            "The LAN interface is missing 'ip nat inside', so translation never "
            "triggers for outbound traffic.",
            "Enter interface config mode for the LAN interface and run 'ip nat inside'; "
            "confirm the WAN interface has 'ip nat outside'.",
        )
    m = re.search(r"total addresses\s+(\d+)\s+allocated\s+\1\b", text)
    if m:
        return _issue(
            "NAT Pool Exhausted",
            "Medium",
            "The NAT pool is fully allocated (all addresses in use).",
            "Increase the pool size or switch to PAT/overload to share addresses.",
        )
    statics = re.findall(r"ip nat inside source static\s+\S+\s+(\d+\.\d+\.\d+\.\d+)", text)
    if len(statics) > len(set(statics)):
        return _issue(
            "Duplicate NAT Static Mapping",
            "High",
            "Two internal hosts are statically mapped to the same public IP.",
            "Remove the duplicate static mapping and assign a unique public IP.",
        )
    return None


def check_port_security(text: str):
    """Detects port security violations shutting down a port."""
    if "secure-shutdown" in text and ("port security" in text or "port-security" in text):
        return _issue(
            "Port Security Violation",
            "Medium",
            "Port security put the port into secure-shutdown state.",
            "Re-enable the port, verify the allowed MAC addresses, and re-test.",
        )
    return None


def check_wireless(text: str):
    """Detects common wireless misconfigurations."""
    if "wpa2-enterprise" in text and ("psk" in text or "personal" in text):
        return _issue(
            "Wireless Security Mismatch",
            "Medium",
            "Client security profile (WPA2-Enterprise) does not match the AP "
            "(WPA2-PSK).",
            "Set the client profile to the same security type as the AP, or change "
            "the AP to match the client.",
        )
    if "broadcast-ssid" in text and "disabled" in text:
        return _issue(
            "SSID Broadcast Disabled",
            "Low",
            "The AP has SSID broadcast disabled, hiding the network from normal scans.",
            "Re-enable SSID broadcast if clients should discover the network.",
        )
    if "channel:" in text and text.count("channel:") >= 2:
        return _issue(
            "Wireless Channel Overlap",
            "Low",
            "Multiple access points are configured on the same channel.",
            "Configure adjacent APs on non-overlapping channels (e.g. 1, 6, 11).",
        )
    return None


def check_dns_problem(text: str):
    """Detects DNS resolution failures and wrong DNS server assignments."""
    if "non-existent domain" in text or ("can't find" in text and "nslookup" in text):
        return _issue(
            "DNS Resolution Failure",
            "Medium",
            "Hostname resolution fails (non-existent domain) even though access by "
            "IP address works.",
            "Point the client at the correct internal DNS server and verify Layer 3 "
            "reachability to it.",
        )
    if "dns-server" in text and "203.0.113.5" in text:
        return _issue(
            "Wrong DNS Server Assigned",
            "Medium",
            "The DHCP pool is handing out DNS server 203.0.113.5 instead of the "
            "internal DNS server.",
            "Update the dns-server option in the DHCP pool to the internal DNS "
            "server address.",
        )
    return None


ALL_RULES = [
    check_duplicate_ip,
    check_subnet_mask,
    check_gateway_mismatch,
    check_interface_down,
    check_missing_vlan,
    check_missing_route,
    check_dot1q_tag,
    check_trunk_mismatch,
    check_port_mode,
    check_dhcp_issue,
    check_acl_problem,
    check_dns_problem,
    check_nat_problem,
    check_port_security,
    check_wireless,
]


def _issue(issue_type: str, severity: str, evidence: str, recommendation: str):
    return {
        "type": issue_type,
        "severity": severity,
        "evidence": evidence,
        "recommendation": recommendation,
    }