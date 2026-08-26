# Demo End-to-End Scenario

## Scenario Title
"PC Gets IP but Cannot Reach Server in VLAN 30"

## Scenario ID
CASE-001 (mapped to Packet Tracer fault: Wrong VLAN assignment on server port)

## Initial Topology
The network is in its baseline working state. Devices and connections:

- **PC-USER-01** connected to SW1-CORE Fa0/5, assigned to VLAN 20 (192.168.20.0/24)
  - IP: 192.168.20.10 (obtained via DHCP)
  - Gateway: 192.168.20.1
  - DNS: 192.168.10.5

- **SRV-WEB** (web server) connected to SW1-CORE Fa0/9, but the fault makes it appear in VLAN 20
  - Actual IP: 192.168.30.100 (in VLAN 30)
  - The server port Fa0/9 is misconfigured and belongs to VLAN 1 (default) instead of VLAN 30

- **Router (R1-EDGE)** provides inter-VLAN routing via router-on-a-stick
  - Subinterfaces Gi0/0.20 (VLAN 20) and Gi0/0.30 (VLAN 30)
  - DHCP server for VLANs 10, 20, 30
  - NAT for internet access

- **Switch trunks** carry VLANs 10, 20, 30, 40, 50 between all switches and the router

## Initial Symptom
PC-USER-01 (VLAN 20) has obtained a valid IP address via DHCP and can ping its default
gateway (192.168.20.1), but cannot reach the web server at 192.168.30.100.

**Ping test results from PC-USER-01:**
- `ping 192.168.20.1` (gateway): **SUCCESS**
- `ping 192.168.30.100` (web server): **FAILURE**
- `ping 8.8.8.8` (internet): **SUCCESS** (NAT is working)

**nslookup test:** Fails for internal hostnames (DNS resolution issue since inter-VLAN routing
is broken).

## Evidence Collection
The engineer collects the following show-command outputs from the Packet Tracer network:

### Command 1: `show vlan brief` (on SW1-CORE)
```
VLAN Name Status Ports
10 Data active Fa0/2
20 Data active Fa0/5 - Fa0/8
30 Servers active Fa0/5  <-- FAULT: Fa0/9 should be in VLAN 30 but is in VLAN 20 area shown
```
**Evidence:** Port Fa0/9 (connected to server) shows as VLAN 1 (default) or in the wrong VLAN.

### Command 2: `show interfaces trunk` (on SW1-CORE)
```
Port Mode Encapsulation Status Native vlan
Gi0/1 on 802.1q trunking 1
Gi0/2 on 802.1q trunking 1
Gi0/3 on 802.1q trunking 1
```
**Evidence:** Trunks are up and carrying VLANs, but this doesn't reveal the access port VLAN assignment.

### Command 3: `show interfaces switchport Fa0/9` (on SW1-CORE)
```
Administrative Mode: trunk
Operational Mode: trunk
```
**Evidence:** If the port is supposed to be access mode but shows trunk, or if it's access but in wrong VLAN.

### Command 4: `show ip interface brief` (on R1-EDGE)
```
Vlan10 192.168.10.1 up up
Vlan20 192.168.20.1 up up
Vlan30 192.168.30.1 up up
Gi0/0 not set
Gi0/1 203.0.113.1 point-to-point
```
**Evidence:** All VLAN interfaces are up and have correct IPs.

### Command 5: `show ip route` (on R1-EDGE)
```
Gateway of last resort is not set
C 192.168.10.0/24 is directly connected, GigabitEthernet0/0
C 192.168.20.0/24 is directly connected, Vlan20
C 192.168.30.0/24 is directly connected, Vlan30
C 192.168.40.0/24 is directly connected, Vlan40
C 192.168.50.0/24 is directly connected, Vlan50
```
**Evidence:** Routing table is correct, all VLAN subnets are directly connected.

## Expected AI Diagnosis
When the evidence is sent to NetSage AI via `/api/diagnose`:

**AI Root Cause:** "Wrong VLAN assignment - a switch port is in the wrong VLAN or the VLAN is not carried across the link."

**AI Confidence:** "High" (because `shows vlan 1` or "port shows VLAN 1" evidence is directly present in the show output)

**AI Evidence:** 
- "The switch output shows the port still in VLAN 1 (default VLAN)."
- "The output notes that 'switchport access vlan 30' is missing on the server port."
- Deterministic rule checker finding: "Missing VLAN Assignment"

**AI OSI Layer:** "Layer 2"

**AI Next Command:** "show vlan brief"

**AI Fix Steps:**
1. Find the affected switch port.
2. Assign it to the correct VLAN with 'switchport access vlan <id>'.
3. Check the VLAN again with 'show vlan brief'.
4. Test connectivity from the affected host.

**AI Severity:** "High"

**AI Verification Steps:** ["show vlan brief", "ping <destination-ip>"]

## Human Review
The human reviewer examines the AI diagnosis and:

1. **Confirms** the root cause is indeed a VLAN misassignment on the switch port.
2. **Verifies** the evidence from `show vlan brief` confirms Fa0/9 is in the wrong VLAN.
3. **May edit** the severity if needed (remains High).
4. **Accepts** the diagnosis.

**Human decision:** ACCEPT

**Reviewer comment:** "The `show vlan brief` output clearly shows the server port Fa0/9 is not in VLAN 30 as designed. The fix is correct."

## Fix Application
The engineer applies the fix in Packet Tracer:

### Configuration change on SW1-CORE
```
! Enter interface Fa0/9 configuration
interface Fa0/9
 switchport mode access
 switchport access vlan 30

! Verify the fix
show vlan brief  -> Now shows Fa0/9 in VLAN 30 (Servers)
```

### Alternative CLI approach
1. Select SW1-CORE in Packet Tracer
2. Go to the CLI tab
3. Type: `configure terminal`
4. Type: `interface Fa0/9`
5. Type: `switchport mode access`
6. Type: `switchport access vlan 30`
7. Type: `end`
8. Type: `copy running-config startup-config`

## Verification
After applying the fix, the engineer verifies:

### Ping test results from PC-USER-01:
- `ping 192.168.20.1` (gateway): **SUCCESS** (was already working)
- `ping 192.168.30.100` (web server): **SUCCESS** (was failing, now working)
- `ping 8.8.8.8` (internet): **SUCCESS** (still working)

### Additional verification commands:
- `show vlan brief` on SW1-CORE: Fa0/9 now shows "30 Servers active"
- `show interfaces switchport Fa0/9`: Administrative Mode: access, Operational Mode: access, Access VLAN: 30
- `nslookup intranet.local`: Now works (inter-VLAN routing is functional, DNS can resolve)

### Dashboard update
The human review is recorded via `/api/review`:
- case_id: CASE-001
- human_decision: Accepted
- reviewer_comment: "Server port VLAN misassignment fixed - Fa0/9 now in VLAN 30"
- The diagnosis_history.json entry is updated with review_status: "Accepted"

## Final Expected Result
All connectivity is restored:
- PC-USER-01 can ping the web server at 192.168.30.100
- PC-USER-01 can browse the web server by hostname
- Inter-VLAN routing works for all VLANs
- Internet connectivity via NAT is preserved
- The scenario demonstrates the complete NetSage AI workflow:
  1. Symptom observation → 2. Evidence collection → 3. AI diagnosis → 
  4. Human review → 5. Fix application → 6. Verification

**Scenario complete.** The network is restored to baseline, and all 32 troubleshooting cases
can now be demonstrated using the Packet Tracer topology.