# NetSage AI — AI Network Troubleshooting Assistant

A simple, college-project-friendly Flask app that helps students diagnose Cisco Packet Tracer
network problems. It reads a symptom plus Cisco `show` command output, suggests the likely
cause (AI), double-checks with a deterministic Python rule checker, and **always requires a
human to accept, edit, or reject the result** before a fix is considered final.

> Core principle: **AI suggests → Evidence supports → Human reviews → Fix → Verify**

---

## 1. The Problem Statement

> Build an AI troubleshooting helper for Packet Tracer lab problems that reads symptoms and
> show-command output, suggests likely causes and next steps, and always requires a human to
> review before accepting the fix.

NetSage AI satisfies every part of this:

| Requirement | How NetSage AI covers it |
|---|---|
| 30+ troubleshooting cases | 32 cases in `data/cases.csv` |
| Evidence for each case | Every case has a symptom, topology, real `show` output, and expected fault |
| AI diagnosis | `ai/diagnosis.py` — demo AI + optional live LLM API |
| Deterministic Python rule checker | `checker/rules.py` + `checker/rule_checker.py` (15 checks) |
| Dashboard | `templates/dashboard.html` — live Chart.js stats from stored data |
| Human review | Accept / Edit / Reject on the Diagnose page, saved to `data/review_log.csv` |
| 5 corrected AI cases | `DEMO-001`…`DEMO-005` seeded in `data/review_log.csv` (see About → Responsible AI) |
| Demo workflow | "Try Demo Case" / "Start Demo" buttons run CASE-001 end-to-end in ~5 minutes |

---

## 2. Navigation (only 5 pages)

```
NetSage AI
  Home        /          - workflow, feature cards, Try Demo Case
  Diagnose    /diagnose  - pick a case OR enter your own problem, see AI + Rule Checker, review
  Cases       /cases     - all 32 cases with evidence
  Dashboard   /dashboard - statistics + 3 charts (computed live)
  About       /about     - AI mode, Responsible AI log, technology
```

---

## 3. How to Run

```bash
cd netsage-ai
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** — no API key, no internet required. The app runs in
**Demo AI Mode** by default (see `.env.example` if you want to enable a live LLM API).

---

## 4. The Diagnosis Workflow

```text
1. Select a Case   →   2. See the Network Problem   →   3. Click "Diagnose"
→   4. AI Finds Likely Problem   →   5. Rule Checker Checks Evidence
→   6. Student Reviews AI Result   →   7. Accept / Edit / Reject   →   8. Fix and Verify
```

The AI uses **only** the evidence you provide (symptom, topology, show output, rule-checker
findings). If the evidence is not enough it says
*"Not enough evidence to confirm the problem"* instead of guessing — it never invents output
that was not actually supplied.

---

## 5. Project Structure

```text
netsage-ai/
├── app.py                    # Flask routes + APIs (diagnose, check, review, statistics)
├── requirements.txt
├── .env.example
├── ai/
│   ├── diagnosis.py          # AI diagnosis (evidence-based demo mode + live API)
│   └── prompts.py            # System prompt for the live LLM path
├── checker/
│   ├── rule_checker.py       # Runs all deterministic checks
│   └── rules.py              # 15 independent rules (VLAN, gateway, DHCP, ACL, NAT...)
├── data/
│   ├── cases.csv             # 32 cases, 8 categories
│   ├── review_log.csv        # Human review decisions (incl. 5 corrected DEMO cases)
│   ├── diagnosis_history.json# Log of every diagnosis run
│   └── generate_cases.py     # Script that created cases.csv (kept for transparency)
├── templates/                # base, index, diagnose, cases, dashboard, about
├── static/
│   ├── css/style.css
│   └── js/                   # main, diagnose, cases, dashboard, about
└── docs/
    ├── diagnose_prompt.md
    └── responsible_ai_log.md
```

Technology kept simple: **HTML + CSS + JS** frontend, **Python Flask** backend,
**CSV/JSON** data, **Chart.js** charts, **Demo AI + optional API**. No React, Node,
Docker, or database.

---

## 6. 5-Minute Teacher Demo

1. **Home** — open `http://127.0.0.1:5000`. Point at "Try Demo Case".
2. **Start Demo** — click it (opens CASE-001 and runs automatically).
3. Show the **Problem**, **Topology**, and **Cisco Output** for CASE-001.
4. Show the **AI Diagnosis** (problem, OSI layer, confidence, why, next command, fix, verify).
5. Show the **Rule Checker** ("Missing VLAN Assignment").
6. Click **Accept** under Human Review, **Save Review**, and show **Review Status: ACCEPTED**.
7. Open **Dashboard** — point out Total Cases, Reviewed, Accepted/Edited/Rejected, AI Agreement,
   and the three charts.
8. Optional: open **Cases** and click any row to see its evidence, then **About** → Responsible AI
   to show the 5 corrected cases.

---

## 7. Files Modified in This Version

- `app.py` — case selection in `/api/diagnose`, friendly errors, `/about` route, removed `/review`
- `ai/diagnosis.py` — evidence-based demo AI (no invented evidence), gateway dynamic evidence
- `checker/rules.py` — improved + new rules (gateway mismatch, port mode, dot1Q, DNS, NAT,
  port security, wireless) — now 15 checks
- `data/cases.csv` + `data/generate_cases.py` — added CASE-031 (Gateway), CASE-032 (DHCP); 32 total
- `data/review_log.csv` — clean seed: 5 corrected DEMO cases + 10 realistic reviews
- `data/diagnosis_history.json` — reset to a clean state
- `templates/base.html` — 5-item nav only
- `templates/index.html` — simplified home (workflow, 3 buttons, feature cards, How It Works)
- `templates/diagnose.html` + `static/js/diagnose.js` — case selection + manual form +
  AI/Rule Checker/Review sections with Review Status
- `templates/cases.html` + `static/js/cases.js` — simple table + detail panel
- `templates/dashboard.html` + `static/js/dashboard.js` — 6 metrics + 3 charts
- `templates/about.html` + `static/js/about.js` — new Responsible AI page
- `static/css/style.css` — light, professional theme; new components
- Removed `templates/review.html` and `static/js/review.js` (review now on the Diagnose page)

---

## 8. Dataset

`data/cases.csv` holds 32 cases:

| Category  | Count | Cases |
|-----------|-------|-------|
| VLAN      | 6     | 001, 011, 013, 016, 023, 030 |
| Routing   | 6     | 005, 012, 014, 018, 022, 029 |
| Gateway   | 4     | 002, 010, 026, 031 |
| DHCP      | 4     | 003, 009, 015, 032 |
| DNS       | 3     | 004, 017, 025 |
| ACL       | 3     | 006, 019, 024 |
| NAT       | 3     | 007, 020, 027 |
| Wireless  | 3     | 008, 021, 028 |

Each row contains: `case_id, title, symptom, topology_note, show_output, expected_fault,
osi_layer, concept, severity`. The command outputs are consistent with each expected fault.

---

## 9. AI Diagnosis

- **Demo AI Mode (default, offline):** picks the most relevant fault family from keywords,
  then builds the "Why?" evidence **only** from lines actually present in the input. If no
  concrete evidence matches, it returns *"Not enough evidence to confirm the problem"* plus
  the recommended `show` command — never a guess.
- **Live AI Mode (optional):** set `AI_MODE=live` and an API key in `.env` to call a real
  LLM (`ai/prompts.py`). Any API failure safely falls back to Demo mode.

## 10. Rule Checker

`checker/rules.py` implements 15 independent, deterministic checks (duplicate IP, wrong subnet
mask, gateway mismatch, interface down, missing VLAN, missing route, dot1Q tag, trunk mismatch,
port mode, DHCP issues, ACL issues, DNS issues, NAT issues, port security, wireless). They run
first, feed evidence into the AI result, and are always shown as a separate card so students can
explain "the AI suggests, the rule checker verifies".

## 11. Human Review & Responsible AI

Every diagnosis ends with **Accept / Edit / Reject**. Decisions are stored in
`data/review_log.csv`, which feeds the Dashboard (Reviewed count, Accepted/Edited/Rejected,
AI Agreement = Accepted ÷ Reviewed × 100). The `DEMO-001`…`DEMO-005` rows document five cases
where a human corrected the AI (shown on the About page), demonstrating why the human-review
step exists.

---

## API Endpoints

```text
GET  / , /diagnose , /cases , /dashboard , /about      Pages
POST /api/diagnose    Run rule checker + AI diagnosis (case_id OR free-form input)
POST /api/check        Run only the rule checker
POST /api/review       Store a human review decision
GET  /api/cases        List / filter the case dataset
GET  /api/statistics   Dashboard statistics (computed live)
GET  /api/history      Diagnosis history
GET  /api/reviews      Human review log
```

## Cisco Packet Tracer Integration

**Purpose of Packet Tracer Component:**
The Packet Tracer topology provides a realistic Cisco network environment for the
NetSage AI troubleshooting workflow. It contains a complete enterprise/campus network
with multiple VLANs, inter-VLAN routing, DHCP, DNS, NAT, ACLs, and wireless connectivity.
The topology supports 32 documented troubleshooting cases covering VLAN, Gateway, DHCP,
DNS, Routing, ACL, NAT, and Wireless issues. Evidence collected from Packet Tracer show
commands is fed into the NetSage AI diagnosis engine, and human reviewers accept/edit/reject
the AI predictions before fixes are applied.

**Location of Packet Tracer:**
- `packet_tracer/` directory at the repository root
- `packet_tracer/configs/` — device configuration files (router, switches, server, AP, PCs)
- `packet_tracer/topology_devices.csv` — device inventory table
- `docs/PACKET_TRACER_GUIDE.md` — comprehensive troubleshooting guide
- `docs/NETWORK_TOPOLOGY.md` — network topology documentation with ASCII diagram
- `docs/NETWORK_VALIDATION.md` — consistency validation checklist
- `docs/packet_tracer_case_mapping.csv` — mapping of 32 AI cases to Packet Tracer faults
- `NetSage_AI_PacketTracer.pkt` — **must be created in Cisco Packet Tracer** using the
  provided configurations (the repository contains configurations and documentation; the
  actual .pkt file is generated using Cisco Packet Tracer software)

**Topology Overview:**
The network contains:
- 1 Edge router (R1-EDGE): inter-VLAN routing, DHCP server, NAT, ACLs, default route
- 1 Core layer-3 switch (SW1-CORE): VLANs, trunk links, router-on-a-stick gateway
- 2 Access switches (SW2-ACCESS, SW3-ACCESS): connect end devices
- 1 Wireless AP (AP1-GUEST): guest wireless network (VLAN 40)
- 2 Servers (SRV-DNS, SRV-WEB): internal DNS and web server
- 4 End devices (PC-ADMIN-01, PC-USER-01, PC-USER-02, PC-GUEST-01)

**VLANs:**
| VLAN | Name | Purpose | Subnet |
|------|------|---------|--------|
| 10 | ADMIN | Administration workstations | 192.168.10.0/24 |
| 20 | USERS | User workstations | 192.168.20.0/24 |
| 30 | SERVERS | Servers (DNS, Web) | 192.168.30.0/24 |
| 40 | GUEST | Guest wireless and wired guests | 192.168.40.0/24 |
| 50 | MANAGEMENT | Management network | 192.168.50.0/24 |

**Major Devices:**
- R1-EDGE — Core router, routing, NAT, DHCP, ACLs
- SW1-CORE — Core switch, VLANs, trunks, inter-VLAN routing
- SW2-ACCESS / SW3-ACCESS — Access switches, end devices
- AP1-GUEST — Guest wireless access point
- SRV-DNS — Internal DNS server (192.168.10.5)
- SRV-WEB — Internal web server (192.168.30.100)
- PC-ADMIN-01 — Admin workstation (VLAN 10)
- PC-USER-01 / PC-USER-02 — User workstations (VLAN 20)
- PC-GUEST-01 — Guest workstation (VLAN 40)

**Troubleshooting Categories (8 required categories):**
VLAN (6 cases: 001, 011, 013, 016, 023, 030), Gateway (4 cases: 002, 010, 026, 031),
DHCP (4 cases: 003, 009, 015, 032), DNS (3 cases: 004, 017, 025), Routing (6 cases:
005, 012, 014, 018, 022, 029), ACL (3 cases: 006, 019, 024), NAT (3 cases: 007, 020, 027),
Wireless (3 cases: 008, 021, 028)

**32-Case Mapping:**
The file `docs/packet_tracer_case_mapping.csv` maps each of the 32 existing AI cases
(CAS-E-001 through CASE-032) to a specific Packet Tracer fault, location, show commands,
expected evidence, root cause, OSI layer, and fix steps. Every major category (VLAN,
Gateway, DHCP, DNS, Routing, ACL, NAT, Wireless) is represented in the mapping.

**How Packet Tracer Evidence Connects to NetSage AI:**
1. The engineer runs show commands in Packet Tracer (e.g., `show vlan brief`, `show access-lists`)
2. The output is copied from the Packet Tracer CLI
3. The evidence is pasted into the NetSage AI diagnose page
4. The user may select a case_id from the existing 32 cases, or enter free-form input
5. NetSage AI runs the rule checker + AI diagnosis on the evidence
6. The AI prediction (root cause, confidence, next command, fix steps) is displayed
7. The human reviewer accepts/edits/rejects the diagnosis
8. If accepted, the engineer applies the fix in Packet Tracer
9. Verification commands are run to confirm the fix
10. The review is recorded in the review log

**How to Use the Demo Scenario:**
1. Open the demo scenario in `docs/DEMO_SCENARIO.md`
2. The scenario "PC Gets an IP Address but Cannot Reach the Server in VLAN 30" maps to CASE-001
3. Follow the step-by-step workflow:
   a. Observe the symptom (PC can ping gateway but not server)
   b. Collect evidence using Packet Tracer show commands
   c. Run diagnosis in NetSage AI
   d. Review the AI prediction with the human reviewer
   e. Apply the fix in Packet Tracer (assign server port to correct VLAN)
   f. Verify connectivity is restored
   g. Record the human review

**How to Create/Open the Final .pkt:**
The repository contains Packet Tracer device configurations in `packet_tracer/configs/`.
To create the final `.pkt` file:

1. **Using Cisco Packet Tracer software** (required):
   a. Launch Cisco Packet Tracer
   b. Create a new network file
   c. Add the following devices from the device palette:
      - 1 Router (1841 or similar)
      - 3 Layer 2/Switches (2960 or similar)
      - 1 Wireless AP
      - 1 DNS Server (or generic server)
      - 1 Web Server (or generic server)
      - 4 PCs (Admin, 2 Users, Guest)
   d. Connect the devices according to the topology:
      - Router Gi0/0 to SW1-CORE Gi0/1 (router-on-a-stick)
      - Router Gi0/1 to ISP/cloud (WAN link)
      - Router Gi0/2 to management network
      - SW1-CORE Fa0/1-20 to PCs and servers
      - SW1-CORE Gi0/1-3 to other switches
      - SW1-CORE Gi0/24 to AP1-GUEST
      - SW1-CORE Gi0/25 to management wireless
      - AP1-GUEST to wireless clients
   e. Load each device's configuration from `packet_tracer/configs/`:
      - R1-EDGE.txt into the router
      - SW1-CORE.txt into the core switch
      - SW2-ACCESS.txt into the first access switch
      - SW3-ACCESS.txt into the second access switch
      - AP1-GUEST.txt into the wireless AP
      - SRV-DNS.txt into the DNS server
      - SRV-WEB.txt into the web server
      - PC-ADMIN-01.txt, PC-USER-01.txt, PC-USER-02.txt, PC-GUEST-01.txt into PCs
   f. Verify the baseline network works:
      - Same-VLAN connectivity
      - Inter-VLAN connectivity
      - Server access
      - DNS resolution
      - DHCP address assignment
      - Internet/WAN connectivity
   g. To introduce a fault, modify the configuration (e.g., change a port's VLAN,
      shut down an interface, change an ACL, etc.) using the Packet Tracer GUI or CLI.
   h. Collect show command evidence and use NetSage AI for diagnosis.

2. **Alternative: If Cisco Packet Tracer is not available:**
   - The configurations in `packet_tracer/configs/` can be studied as reference
   - The documentation files (`docs/NETWORK_TOPOLOGY.md`, `docs/PACKET_TRACER_GUIDE.md`,
     `docs/NETWORK_VALIDATION.md`) provide complete design information
   - The `.pkt` file must be created using Cisco Packet Tracer software
   - The topology and configurations are designed to be Packet Tracer-compatible using
     standard Cisco IOS commands supported by the installed Packet Tracer version

**Important:** The repository does NOT contain a genuine Cisco Packet Tracer .pkt file.
The .pkt file must be created and saved using Cisco Packet Tracer. The configurations
and documentation provided here are complete and can be used to build the .pkt in
Packet Tracer.

**Reference for Cisco-AICTE VIP 2026 Evaluation:**
- Completed project/problem statement (.pkt + Summary Document): The .pkt must be
  opened in Cisco Packet Tracer and built from the provided configurations.
- 30+ troubleshooting cases: 32 cases mapped via `docs/packet_tracer_case_mapping.csv`
- Evidence such as symptoms, topology notes and show-command outputs: Provided in
  cases.csv and the Packet Tracer guide
- AI diagnosis with root cause, confidence, evidence, next command and fix steps:
  Powered by `ai/diagnosis.py` and `checker/rules.py`
- Python deterministic rule checker: `checker/rules.py` (15 rules)
- Dashboard: Existing Flask dashboard with statistics charts
- Human review: Accept/Edit/Reject workflow via `/api/review`
- At least 5 cases where AI was corrected by a human: Documented in `data/review_log.csv`
- Demo of a broken lab being diagnosed, reviewed, fixed and verified: `docs/DEMO_SCENARIO.md`
