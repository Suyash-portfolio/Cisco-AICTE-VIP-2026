# Responsible AI Log

NetSage AI is built around one non-negotiable principle:

> **AI suggests → Evidence supports → Human reviews → Fix → Verify**

The AI never applies configuration changes automatically, and every diagnosis is
recorded with its review outcome in `data/review_log.csv`. This log documents five
sample cases — seeded into `data/review_log.csv` with the `DEMO-` prefix — where a
human reviewer corrected an intentionally flawed AI answer. **These five are labeled
demo/sample cases for demonstration purposes**; they show how the review workflow
catches AI mistakes rather than reflecting real production incidents.

## Demo Case 1 — Routing vs. ACL

- **AI said:** Missing route to branch subnet 172.16.20.0/24 (Routing / Layer 3).
- **Human found:** The route already existed; an ACL on the return path was
  silently dropping the traffic instead.
- **Decision:** Rejected.
- **Lesson:** The AI weighted the routing-table symptom pattern too heavily and
  did not fully account for the ACL evidence present in the show output.

## Demo Case 2 — DHCP vs. VLAN

- **AI said:** DHCP scope exhausted on VLAN 20 (DHCP / Layer 3).
- **Human found:** The switch port had never been assigned to VLAN 20 at all — it
  was still sitting in default VLAN 1.
- **Decision:** Edited.
- **Lesson:** A misread of `show vlan brief` output led the AI to a plausible but
  incorrect DHCP-focused conclusion.

## Demo Case 3 — DNS vs. Gateway

- **AI said:** DNS server misconfigured with wrong forwarder (DNS / Layer 7).
- **Human found:** The PC's default gateway was wrong, so it couldn't reach the
  DNS server's subnet at all — a Layer 3 problem, not Layer 7.
- **Decision:** Rejected.
- **Lesson:** The AI diagnosed a higher-layer symptom without first confirming
  basic Layer 3 reachability, which is why NetSage AI presents rule-checker
  findings (which include Layer 3 checks) alongside every AI answer.

## Demo Case 4 — Missed Interface-Down Evidence

- **AI said:** Routing issue between VLANs (Routing / Layer 3).
- **Human found:** The real cause was an interface administratively down, visible
  directly in the `show ip interface brief` output.
- **Decision:** Edited.
- **Lesson:** Directly-stated evidence ("administratively down") should always
  outweigh an inferred routing explanation. This case motivated the
  `check_interface_down` rule in the deterministic checker, which now flags this
  pattern independently of the AI.

## Demo Case 5 — Unnecessary Change Recommendation

- **AI said:** Recommended adding a static route for 172.16.20.0/24 via Serial0/0/0.
- **Human found:** The route already existed in the routing table.
- **Decision:** Rejected.
- **Lesson:** Reviewers must reject redundant or unnecessary configuration change
  recommendations, since applying them adds risk with no benefit — reinforcing why
  NetSage AI never applies AI-suggested changes automatically.

## How these feed the Dashboard

All five demo cases are counted in the dashboard's **Human Review Decisions** chart
and **AI Agreement Rate** calculation, alongside real reviewed cases, so the
dashboard always reflects genuine stored review data rather than hardcoded numbers.
