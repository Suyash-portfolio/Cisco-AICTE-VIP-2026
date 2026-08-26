# Packet Tracer Guide for NetSage AI

## 1. Topology Overview

The NetSage AI Packet Tracer topology represents a small enterprise/campus network
with multiple VLANs, inter-VLAN routing, DHCP, DNS, NAT, ACLs, and wireless connectivity.
The network is designed to support 32 documented troubleshooting cases covering VLAN,
Gateway, DHCP, DNS, Routing, ACL, NAT, and Wireless issues.

The baseline network is fully functional. faults can be introduced to simulate real-world
network problems. The topology uses router-on-a-stick for inter-VLAN routing and
a Layer 2 core switch with router-on-a-stick inter-VLAN routing.

### Exact Physical Mapping

SW1-CORE Fa0/1 -> PC-ADMIN-01 (VLAN 10); Fa0/2 -> PC-USER-01 (VLAN 20);
Fa0/3 -> PC-USER-02 (VLAN 20); Fa0/4 -> SRV-DNS (VLAN 10);
Fa0/5 -> SRV-WEB (VLAN 30); Fa0/6 -> PC-GUEST-01 (VLAN 40).
SW1 Gi0/1 -> R1 Gi0/0, Gi0/2 -> SW2 Gi0/1, Gi0/3 -> SW3 Gi0/1 are trunks.
SW1 Gi0/24 -> AP1-GUEST Gi0/0 is an access port in VLAN 40. Gi0/25 is unused.

## 2. Device Inventory

| Device Name | Type | Role |
|-------------|------|------|
| R1-EDGE | Router | Main edge router, inter-VLAN routing, DHCP server, NAT, ACL, default route |
| SW1-CORE | Layer 2 Switch | Core switching, VLANs, and trunk links; R1 provides gateways |
| SW2-ACCESS | Switch | Access switch, connects user PCs |
| SW3-ACCESS | Switch | Access switch, connects guest devices and APs |
| AP1-GUEST | Wireless AP | Guest wireless network (SSID: CorpGuest, VLAN 40) |
| SRV-DNS | Server | Internal DNS server (192.168.10.5) |
| SRV-WEB | Server | Internal web server (192.168.30.100) |
| PC-ADMIN-01 | PC | Admin workstation (VLAN 10) |
| PC-USER-01 | PC | User workstation (VLAN 20) |
| PC-USER-02 | PC | User workstation (VLAN 20) |
| PC-GUEST-01 | PC | Guest workstation (VLAN 40) |

## 3. VLAN Table

| VLAN | Name | Purpose | Subnet | Gateway |
|------|------|---------|--------|---------|
| 10 | ADMIN | Administration workstations | 192.168.10.0/24 | 192.168.10.1 |
| 20 | USERS | User workstations | 192.168.20.0/24 | 192.168.20.1 |
| 30 | SERVERS | Servers (DNS, Web) | 192.168.30.0/24 | 192.168.30.1 |
| 40 | GUEST | Guest wireless and wired guests | 192.168.40.0/24 | 192.168.40.1 |
| 50 | MANAGEMENT | Management network | 192.168.50.0/24 | 192.168.50.1 |

## 4. IP Addressing Table

### R1 Router-on-a-Stick Subinterfaces

| VLAN | Interface | IP Address | Subnet Mask |
|------|-----------|------------|-------------|
| 10 | Gi0/0.10 | 192.168.10.1 | 255.255.255.0 |
| 20 | Gi0/0.20 | 192.168.20.1 | 255.255.255.0 |
| 30 | Gi0/0.30 | 192.168.30.1 | 255.255.255.0 |
| 40 | Gi0/0.40 | 192.168.40.1 | 255.255.255.0 |
| 50 | Gi0/0.50 | 192.168.50.1 | 255.255.255.0 |

### DHCP Pools

| Pool | Network | Gateway | DNS Server | Usable Range |
|------|---------|---------|------------|--------------|
| VLAN10 | 192.168.10.0/24 | 192.168.10.1 | 192.168.10.5 | 192.168.10.2 - 192.168.10.254 |
| VLAN20 | 192.168.20.0/24 | 192.168.20.1 | 192.168.10.5 | 192.168.20.2 - 192.168.20.254 |
| VLAN30 | 192.168.30.0/24 | 192.168.30.1 | 192.168.10.5 | 192.168.30.21 - 192.168.30.254 |
| VLAN40 | 192.168.40.0/24 | 192.168.40.1 | 192.168.10.5 | 192.168.40.2 - 192.168.40.254 |

Excluded addresses: 192.168.10.1-20, 192.168.20.1-20, and 192.168.30.1-20.

### Server Static IPs

| Device | IP Address | VLAN | Purpose |
|--------|-----------|------|---------|
| SRV-DNS | 192.168.10.5 | 10 | Internal DNS server |
| SRV-WEB | 192.168.30.100 | 30 | Internal web server |

### WAN/ISP Link

| Interface | IP Address | Subnet | Description |
|-----------|-----------|--------|-------------|
| Gi0/1 (R1-EDGE) | 203.0.113.1/30 | /30 | WAN/ISP link |
| Gi0/1 (ISP side) | 203.0.113.2/30 | /30 | ISP side |

## 5. Routing Design

### Router-on-a-Stick (Inter-VLAN Routing)

The router uses subinterfaces on GigabitEthernet0/0 to route between VLANs:

```
! Subinterface for VLAN 10
interface GigabitEthernet0/0.10
 encapsulation dot1Q 10
 ip address 192.168.10.1 255.255.255.0

! Subinterface for VLAN 20
interface GigabitEthernet0/0.20
 encapsulation dot1Q 20
 ip address 192.168.20.1 255.255.255.0

! Subinterface for VLAN 30
interface GigabitEthernet0/0.30
 encapsulation dot1Q 30
 ip address 192.168.30.1 255.255.255.0

! Subinterface for VLAN 40
interface GigabitEthernet0/0.40
 encapsulation dot1Q 40
 ip address 192.168.40.1 255.255.255.0

! Subinterface for VLAN 50
interface GigabitEthernet0/0.50
 encapsulation dot1Q 50
 ip address 192.168.50.1 255.255.255.0
```

### Default Route (Internet Access)

```
ip route 0.0.0.0 0.0.0.0 203.0.113.2
```

or via the directly connected WAN interface.

### WAN Link

The GigabitEthernet0/1 interface connects to the ISP/cloud with:
- IP 203.0.113.1/30
- Directly connected, no static route needed (already has default route via connected interface)

## 6. DHCP Configuration

The router (R1-EDGE) acts as a DHCP server for VLANs 10, 20, 30, and 40.

```
! DHCP pool for VLAN 10 (Admin)
ip dhcp pool VLAN10
 network 192.168.10.0 255.255.255.0
 default-router 192.168.10.1
 dns-server 192.168.10.5

! DHCP pool for VLAN 20 (Users)
ip dhcp pool VLAN20
 network 192.168.20.0 255.255.255.0
 default-router 192.168.20.1
 dns-server 192.168.10.5

! DHCP pool for VLAN 30 (Servers)
ip dhcp pool VLAN30
 network 192.168.30.0 255.255.255.0
 default-router 192.168.30.1
 dns-server 192.168.10.5

ip dhcp pool VLAN40
 network 192.168.40.0 255.255.255.0
 default-router 192.168.40.1
 dns-server 192.168.10.5
```

### DHCP Relay (ip helper-address)

DHCP relay is not used in this baseline because R1 is the DHCP server. Do not add
`ip helper-address` to the R1 subinterfaces.

```
interface GigabitEthernet0/0.20
 ip address 192.168.20.1 255.255.255.0
```

## 7. DNS Configuration

### Internal DNS Server (SRV-DNS)

- IP: 192.168.10.5
- VLAN: 10 (Admin)
- Provides resolution for internal hostnames (e.g., intranet.local, srv-web)
- DNS record: `web.netsage.local` -> `192.168.30.100`
- Configured as the DNS server in DHCP scopes for VLANs 10, 20, 30, and 40

### DNS in Packet Tracer

Packet Tracer's internal DNS server can resolve:
- Hostnames to IP addresses for configured servers
- The server responds to pings and nslookup queries

### Verifying DNS

```
nslookup intranet.local
ping 192.168.10.5
```

## 8. ACL Design

### ACLs on R1-EDGE

| ACL Number | Rule | Direction | Purpose |
|------------|------|-----------|---------|
| 100 | VLAN 10, 20, 30, 40, 50 permit entries | NAT source ACL | PAT source networks |
| 110 | Guest denies to VLANs 10, 20, 30, then permit any | In on Gi0/0.40 | Guest isolation |

### ACL Configuration

```
! NAT source ACL
access-list 100 permit 192.168.10.0 0.0.0.255
access-list 100 permit 192.168.20.0 0.0.0.255
access-list 100 permit 192.168.30.0 0.0.0.255
access-list 100 permit 192.168.40.0 0.0.0.255
access-list 100 permit 192.168.50.0 0.0.0.255
! Guest isolation, applied inbound on Gi0/0.40
access-list 110 deny ip 192.168.40.0 0.0.0.255 192.168.10.0 0.0.0.255
access-list 110 deny ip 192.168.40.0 0.0.0.255 192.168.20.0 0.0.0.255
access-list 110 deny ip 192.168.40.0 0.0.0.255 192.168.30.0 0.0.0.255
access-list 110 permit ip 192.168.40.0 0.0.0.255 any
```

### Common ACL Problems

- **Overly broad deny**: `deny ip 192.168.10.0 0.0.0.255 any` blocks more than intended
- **Wrong direction**: ACL applied with `in` instead of `out` blocks return traffic
- **Incorrect wildcard mask**: `0.0.15.255` instead of `0.0.0.255` matches too large a range

## 9. NAT Design

### NAT Configuration (PAT/Overload)

```
! One PAT rule for all internal VLANs
ip nat inside source list 100 interface GigabitEthernet0/1 overload
```

### NAT Inside/Outside

- **Inside**: R1 Gi0/0.10, .20, .30, .40, and .50 (`ip nat inside`)
- **Outside**: GigabitEthernet0/1 - WAN/ISP link

### Verifying NAT

```
show ip nat translations
show ip nat statistics
```

### Common NAT Problems

- **Missing 'ip nat inside'**: The LAN interface is not marked as inside, NAT never triggers
- **NAT pool exhausted**: All addresses in the pool are allocated
- **Duplicate static mappings**: Two internal hosts mapped to the same public IP

## 10. Wireless Design

### AP1-GUEST Configuration

- **SSID**: CorpGuest
- **Security**: WPA2-PSK
- **Password**: GuestPass123
- **VLAN**: 40 (Guest isolation)
- **Interface**: Connected to SW1-CORE Gi0/24 (access port, VLAN 40)

### Wireless Setup in Packet Tracer

1. Click the AP (AP1-GUEST)
2. Go to the Configuration tab
3. Set SSID to "CorpGuest"
4. Set Security to "WPA2-Personal"
5. Set Password to "GuestPass123"
6. Set VLAN to 40 (if applicable)
7. Apply configuration

### Guest Network Isolation

The guest network is isolated from internal VLANs (10, 20, 30) via:
- VLAN separation (Guest is VLAN 40, separate from Admin/Users/Servers)
- ACLs on the router blocking guest-to-internal traffic
- No routing between VLAN 40 and VLANs 10/20/30 except through the gateway

### Common Wireless Issues

- **Security mismatch**: Client configured for WPA2-Enterprise, AP is WPA2-Personal
- **SSID broadcast disabled**: AP has `broadcast-ssid disabled`, clients cannot discover the network
- **Channel overlap**: Multiple APs on the same 2.4GHz channel (1, 6, 11 are non-overlapping)
- **Client profile wrong**: Client has saved profile from different network

### Verifying Wireless

```
show interfaces status  (on the switch, to verify AP link)
ping 192.168.40.1   (from wireless client - gateway)
show run | section dot11  (on the AP)
```

## 11. Baseline Verification

### Verifying the Working Network

#### Same-VLAN Connectivity

```
! From a VLAN 10 PC:
ping 192.168.10.50  (another VLAN 10 PC)

! From a VLAN 20 PC:
ping 192.168.20.10  (another VLAN 20 PC)
```

#### Inter-VLAN Connectivity

```
! From a VLAN 20 PC:
ping 192.168.10.1  (VLAN 10 gateway)
ping 192.168.30.1  (VLAN 30 gateway)

! From a VLAN 20 PC:
ping 192.168.30.100  (web server)
```

#### Server Access

```
! From any PC:
ping 192.168.30.100  (web server)

! From any PC:
nslookup srv-web  (DNS resolution)
```

#### DHCP Address Assignment

```
! From a new PC (or release/renew):
ipconfig /renew  (Windows) or dhclient -r && dhclient (Linux)

! Verify:
ipconfig /all  (check IP, subnet, gateway, DNS)
show ip dhcp binding  (on the router)
```

#### Internet/WAN Connectivity

```
! From any PC:
ping 8.8.8.8  (Google DNS)

! From any PC:
ping www.google.com  (name resolution)

! From the router:
show ip nat translations  (verify translations exist)
```

#### DNS Resolution

```
! From any PC:
nslookup intranet.local  (should resolve to internal IP)

! From any PC:
ping srv-web  (should work if DNS is correct)

! If IP ping works but nslookup fails:
  - Check DHCP DNS server address
  - Verify DNS server reachability (ping 192.168.10.5)
  - Check nslookup from the DNS server itself
```

#### Guest Isolation

```
! From a Guest PC (VLAN 40):
! Should NOT be able to ping:
  - 192.168.10.1 (VLAN 10 gateway)
  - 192.168.20.1 (VLAN 20 gateway)
  - 192.168.30.100 (web server)

! Should be able to ping:
  - 192.168.40.1 (own gateway)
  - 8.8.8.8 (internet, if NAT works)
```

#### Administrative Access

```
! From a VLAN 10 PC:
ping 192.168.10.1  (own gateway)

! SSH or HTTP to 192.168.50.1  (management VLAN)
```

### Baseline Verification Commands Summary

```
show ip interface brief
show vlan brief
show interfaces trunk
show ip route
show ip dhcp pool
show ip dhcp binding
show ip nat translations
show ip nat statistics
show access-lists
show cdp neighbors
arp -a
ping <destination>
traceroute <destination>
nslookup <hostname>
ipconfig /all  (Windows) or ifconfig (Linux/macOS)
```

## 12. Troubleshooting Scenarios

### Scenario Format

Each scenario follows this pattern:

1. **SYMPTOM** - What the user observes
2. **EXPECTED RESULT** - What should happen in a working network
3. **FAULT** - The intentional misconfiguration introduced
4. **COMMAND TO RUN** - The show command to diagnose
5. **EXPECTED COMMAND EVIDENCE** - What the correct output looks like
6. **ROOT CAUSE** - The actual problem
7. **OSI LAYER** - The layer most relevant to the fault
8. **FIX** - The configuration command to fix
9. **VERIFICATION COMMAND** - The command to confirm the fix

### Documented Scenarios

| # | Title | Issue Type | OSI Layer |
|---|-------|-----------|-----------|
| 1 | VLAN Connectivity Issue | VLAN | Layer 2 |
| 2 | Default Gateway Misconfiguration | Gateway | Layer 3 |
| 3 | DHCP Pool Exhaustion | DHCP | Layer 3 |
| 4 | DNS Resolution Failure | DNS | Layer 7 |
| 5 | Missing Static Route | Routing | Layer 3 |
| 6 | ACL Blocking Legitimate Traffic | ACL | Layer 3/4 |
| 7 | NAT Overload Not Translating | NAT | Layer 3 |
| 8 | Wireless Client Cannot Associate | Wireless | Layer 2 |
| 9 | Duplicate IP Address Conflict | DHCP | Layer 3 |
| 10 | Incorrect Subnet Mask | Gateway | Layer 3 |
| 11 | Trunk Native VLAN Mismatch | VLAN | Layer 2 |
| 12 | Interface Administratively Down | Routing | Layer 1/2 |
| 13 | Missing VLAN on Trunk Allowed List | VLAN | Layer 2 |
| 14 | Router-on-a-Stick Subinterface Misconfigured | Routing | Layer 3 |
| 15 | DHCP Relay Missing | DHCP | Layer 3 |
| 16 | Access Port Configured as Trunk | VLAN | Layer 2 |
| 17 | Wrong DNS Server Pushed by DHCP | DNS | Layer 7 |
| 18 | Asymmetric Routing | Routing | Layer 3/4 |
| 19 | ACL Applied to Wrong Interface Direction | ACL | Layer 3 |
| 20 | NAT Pool Exhausted | NAT | Layer 3 |
| 21 | Wireless Channel Overlap | Wireless | Layer 1/2 |
| 22 | Missing Default Route | Routing | Layer 3 |
| 23 | Port Security Shutting Down Access Port | VLAN | Layer 2 |
| 24 | Incorrect ACL Wildcard Mask | ACL | Layer 3 |
| 25 | DNS Server Interface Reachability | DNS | Layer 1/7 |
| 26 | Overlapping Static and DHCP Gateway | Gateway | Layer 3 |
| 27 | NAT Static Mapping Conflict | NAT | Layer 3 |
| 28 | Wireless AP Not Broadcasting SSID | Wireless | Layer 2 |
| 29 | Route Summarization Blackhole | Routing | Layer 3 |
| 30 | Incorrect VLAN Assignment on Voice Port | VLAN | Layer 2 |
| 31 | Default Gateway on Wrong Subnet | Gateway | Layer 3 |
| 32 | Entire DHCP Scope Excluded | DHCP | Layer 3 |

### Detailed Scenario: "PC gets an IP address but cannot reach the server in VLAN 30" (End-to-End Demo)

#### 1. SYMPTOM

PC (VLAN 20) has obtained an IP address via DHCP and can ping the default gateway (192.168.20.1),
but cannot reach the web server in VLAN 30 (192.168.30.100).

#### 2. EXPECTED RESULT (in working network)

The PC should be able to:
- Ping the gateway (192.168.20.1) - WORKS
- Ping the web server (192.168.30.100) - FAILS
- Browse the web server by IP - FAILS
- Resolve the web server hostname via DNS - FAILS

#### 3. FAULT

The server port (Fa0/9 on SW1-CORE) is configured in VLAN 20 instead of VLAN 30,
so the server is in the wrong VLAN and inter-VLAN routing sends traffic to the wrong destination.

#### 4. COMMAND TO RUN (on the switch)

```
show vlan brief
show interfaces trunk
show ip interface brief
```

#### 5. EXPECTED COMMAND EVIDENCE (with fault)

```
show vlan brief
VLAN Name Status Ports
10 Data active Fa0/2
20 Data active Fa0/5 - Fa0/8
30 Servers active Fa0/9  <-- FAULT: Fa0/9 should be in VLAN 30 but is in VLAN 20

show interfaces trunk
Port Mode Encapsulation Status Native vlan
Gi0/1 on 802.1q trunking 1

! Note: Fa0/9 is in VLAN 20 instead of VLAN 30
```

#### 6. ROOT CAUSE

Switch access port Fa0/9 (connected to SRV-WEB) is misconfigured and belongs to VLAN 20
instead of VLAN 30. The server is in the wrong VLAN, so even though routing is
correctly configured, traffic sent to VLAN 30 is sent to the wrong switch port.

#### 7. OSI LAYER

Layer 2 (Data Link) - VLAN misassignment on a switch port

#### 8. FIX

```
! On SW1-CORE, assign Fa0/9 to VLAN 30
interface Fa0/9
 switchport mode access
 switchport access vlan 30

! Verify:
show vlan brief
```

#### 9. VERIFICATION COMMAND

```
! From the PC:
ping 192.168.30.100  (should now work)

! From the PC:
show vlan brief  (confirm Fa0/9 is now in VLAN 30)
```

### Mapping of All 32 Cases to Fault Scenarios

Each of the 32 existing AI cases maps to a specific Packet Tracer fault:

| Case ID | Case Title | PT Fault | PT Location | Key Command |
|---------|-----------|----------|-------------|-------------|
| CASE-001 | VLAN Connectivity Issue | Wrong VLAN assignment | Server port Fa0/9 in VLAN 1 instead of 30 | show vlan brief |
| CASE-002 | Default Gateway Misconfiguration | Wrong default gateway configured on PC | PC has gateway 192.168.20.1 instead of 192.168.10.1 (or vice versa) | show ip interface brief |
| CASE-003 | DHCP Pool Exhaustion | DHCP pool fully allocated | VLAN 20 pool has 30 addresses all leased | show ip dhcp pool |
| CASE-004 | DNS Resolution Failure | Wrong DNS server in DHCP scope | DHCP offers 8.8.8.8 instead of 192.168.10.5 | ipconfig /all, nslookup |
| CASE-005 | Missing Static Route | No route to branch subnet | No ip route 0.0.0.0 or specific route on router | show ip route |
| CASE-006 | ACL Blocking Legitimate Traffic | Overly broad ACL deny | ACL 101 denies VLAN 10 traffic to VLAN 30 | show access-lists |
| CASE-007 | NAT Overload Not Translating | Missing 'ip nat inside' | Gi0/0 missing ip nat inside, so PAT never triggers | show ip nat translations |
| CASE-008 | Wireless Client Cannot Associate | Security mismatch | Client WPA2-Enterprise, AP WPA2-Personal | AP config, show interfaces |
| CASE-009 | Duplicate IP Address Conflict | Static IP overlaps DHCP | Static IP 192.168.10.20 in DHCP scope VLAN 10 | show ip dhcp conflict |
| CASE-010 | Incorrect Subnet Mask | /26 instead of /24 | PC has subnet mask 255.255.255.192 instead of 255.255.255.0 | ipconfig /all |
| CASE-011 | Trunk Native VLAN Mismatch | Native VLAN 1 vs 99 | SW1 Gi0/1 native 1, SW2 Gi0/1 native 99 | show interfaces trunk |
| CASE-012 | Interface Administratively Down | Interface shut | Serial0/0/0 or Fa0/shut on router/switch | show ip interface brief |
| CASE-013 | Missing VLAN on Trunk | VLAN 40 not in trunk allowed list | VLAN 40 not in switch trunk Gi0/2 allowed list | show interfaces trunk |
| CASE-014 | Router-on-a-Stick Misconfigured | Wrong dot1Q tag | Subinterface Gi0/0.30 has encapsulation dot1Q 3 instead of 30 | show run interface Gi0/0.30 |
| CASE-015 | DHCP Relay Missing | No ip helper-address | VLAN 20 SVI missing ip helper-address | show run interface vlan20 |
| CASE-016 | Access Port as Trunk | Port mode trunk | Fa0/8 configured as trunk instead of access | show interfaces switchport |
| CASE-017 | Wrong DNS Server by DHCP | Incorrect dns-server | DHCP pool has 203.0.113.5 instead of 192.168.10.5 | show run | section ip dhcp pool |
| CASE-018 | Asymmetric Routing | Different routes out/back | Dual WAN links with different static routes + ACL blocking return | show ip route |
| CASE-019 | ACL Wrong Interface Direction | ACL in vs out | ACL 101 applied 'in' on Gi0/1 instead of 'out' | show run interface Gi0/1 |
| CASE-020 | NAT Pool Exhausted | Pool too small | NAT pool has 11 addresses, 11 allocated | show ip nat statistics |
| CASE-021 | Wireless Channel Overlap | Same channel on APs | AP1, AP2, AP3 all on channel 6 | AP configs |
| CASE-022 | Missing Default Route | No 0.0.0.0/0 route | No default route configured on edge router | show ip route |
| CASE-023 | Port Security Shutdown | Port security violation | Fa0/12 has port-security with violation shutdown | show port-security interface |
| CASE-024 | Incorrect ACL Wildcard Mask | 0.0.15.255 instead of 0.0.0.255 | ACL 10 permits 192.168.10.0 0.0.15.255 instead of /24 | show access-lists 10 |
| CASE-025 | DNS Server Reachability | DNS server port down | Fa0/5 on Switch1 connected to DNS server is down/down | show ip interface brief |
| CASE-026 | Overlapping Gateway Values | Static gateway wrong | Static PCs have gateway 192.168.10.254 (non-existent) instead of 192.168.10.1 | ipconfig, show ip interface brief |
| CASE-027 | NAT Static Mapping Conflict | Duplicate static NAT | Two static mappings both use 203.0.113.50 | show run | include nat |
| CASE-028 | Wireless SSID Disabled | broadcast-ssid disabled | AP2 has SSID broadcast disabled | AP config, show wireless |
| CASE-029 | Route Summarization Blackhole | Summary hides subnet | Router summarizes 172.16.16.0/20 but 172.16.25.0/24 not present | show ip route |
| CASE-030 | Voice VLAN without Data VLAN | Data port in VLAN 1 | Fa0/15 has voice vlan 50 but no switchport access vlan (defaults to 1) | show run interface Fa0/15 |
| CASE-031 | Gateway on Wrong Subnet | Gateway different subnet | PC gateway 192.168.30.1 but PC IP 192.168.20.10 (VLAN 20) | ipconfig, show ip interface brief |
| CASE-032 | Entire DHCP Scope Excluded | Excluded covers whole pool | DHCP excluded 192.168.30.1 192.168.30.254 covers entire VLAN 30 scope | show run | section ip dhcp pool |

## 13. Commands to Collect Evidence

### Core Show Commands

| Command | Purpose | Typical Use |
|---------|---------|-------------|
| `show ip interface brief` | Interface status and IP addresses | Check up/down status, IPs |
| `show interfaces` | Detailed interface information | Check interface statistics |
| `show interfaces trunk` | Trunk link VLAN information | Verify VLANs carried on trunks |
| `show vlan brief` | VLAN membership | Check which VLAN ports belong to |
| `show running-config` | Current running configuration | Verify full config |
| `show startup-config` | Startup configuration | Compare with running config |
| `show ip route` | Routing table | Check routes, default route |
| `show access-lists` | ACL configuration | Verify ACL rules and direction |
| `show ip dhcp pool` | DHCP pool parameters | Check pool size, utilization, exclusions |
| `show ip dhcp binding` | Active DHCP leases | See assigned IP addresses |
| `show ip nat translations` | NAT translation table | See active NAT mappings |
| `show ip nat statistics` | NAT statistics | Pool utilization, misses, etc. |
| `show cdp neighbors` | CDP neighbors | Discover topology, connected devices |
| `show interfaces status` | Port status | Quick port up/down status |
| `show mac address-table` | MAC address table | Learn MACs, port mapping |
| `show arp` | ARP table | IP-to-MAC mapping |
| `show ip protocols` | Routing protocol status | OSPF, RIP, etc. |

### Wireless-Specific Commands

| Command | Purpose |
|---------|---------|
| `show wireless client` | Connected wireless clients |
| `show ap config general` | Access point general configuration |
| `show ap summary` | AP summary information |

### Diagnosis Workflow

1. **Identify the symptom** from the user or AI input
2. **Determine the likely layer** (L2, L3, L4, etc.)
3. **Run the appropriate show command** based on the layer
4. **Compare output** with expected/baseline values
5. **Identify the fault** from the command output
6. **Apply the fix** (configuration change)
7. **Verify with the same command** (confirm connectivity restored)
8. **Document the fix** in the diagnosis history

## 14. How to Introduce Each Fault

### Fault Introduction Methods

Each fault can be introduced by modifying the device configuration in Packet Tracer:

#### Wrong VLAN Assignment
1. Select the switch port
2. Go to the "Port" tab
3. Change "Switchport Mode" to "Access"
4. Change "Access VLAN" to the wrong VLAN number
5. Apply

#### Access Port as Trunk
1. Select the switch port
2. Go to the "Port" tab
3. Change "Switchport Mode" from "Access" to "Trunk"
4. Apply

#### Trunk Native VLAN Mismatch
1. Select the first switch
2. Go to the trunk port, change "Native VLAN" to 1
3. Select the second switch
4. Go to the trunk port, change "Native VLAN" to 99
5. Apply

#### Missing VLAN on Trunk
1. Select the switch
2. Go to the trunk port
3. Remove the VLAN from "Allowed VLANs" list
4. Apply

#### Wrong Default Gateway
1. Select the PC
2. Go to the "Config" tab
3. IP Configuration - change the Gateway field to a wrong IP
4. Apply

#### DHCP Pool Exhaustion
1. Select the router
2. Go to the "Services" tab
3. DHCP Server - reduce the pool size or increase lease time
4. Or: configure many static IPs to exhaust the pool

#### Missing DNS Configuration
1. Select the router
2. Go to the "Configuration" tab
3. Remove the dns-server line from the DHCP pool
4. Apply

#### Interface Shutdown
1. Select the interface
2. Click the "Shutdown" button or uncheck the "Enabled" box
3. Apply

#### Incorrect Subnet Mask
1. Select the PC
2. Go to the "Config" tab
3. IP Configuration - change the Subnet Mask to 255.255.255.192
4. Apply

#### Duplicate IP
1. Assign static IP on one PC that falls within the DHCP scope
2. Ensure the DHCP scope includes that address range

#### ACL Blocking Traffic
1. Add or modify an ACL with overly broad deny statements
2. Apply the ACL to the wrong interface direction

#### Missing 'ip nat inside'
1. Select the router
2. Go to the interface configuration
3. Remove or ensure 'ip nat inside' is not configured on the LAN interface
4. Apply

#### NAT Pool Exhausted
1. Select the router
2. Configure NAT pool with too few addresses
3. Ensure many internal hosts need translation

#### Port Security Violation
1. Select the switch port
2. Go to the "Port Security" tab
3. Enable port security with "Maximum" addresses = 1
4. Connect a new device (different MAC)
5. The port will go into secure-shutdown

#### SSID Broadcast Disabled
1. Select the AP
2. Go to the "Configuration" tab
3. Uncheck "Broadcast SSID"
4. Apply

#### Route Summarization Blackhole
1. Configure a summary route that supernets a specific subnet
2. Ensure the specific subnet is not present downstream

#### Voice VLAN without Data VLAN
1. Select the switch port
2. Go to the "Port" tab
3. Set "Voice VLAN" to 50
4. Do NOT set "Switchport Access VLAN" - it defaults to 1
5. Apply

#### Default Gateway on Wrong Subnet
1. Select the PC
2. Go to the "Config" tab
3. Set IP to 192.168.20.10 with gateway 192.168.30.1 (different subnet)
4. Apply

#### Entire DHCP Scope Excluded
1. Select the router
2. Go to the DHCP pool configuration
3. Set "Excluded Addresses" to cover the entire pool range
   (e.g., 192.168.30.1 192.168.30.254 for a /24 pool)
4. Apply

## 15. How to Fix Each Fault

### General Fix Pattern

Each fault has a specific fix, but the general pattern is:

1. **Identify the faulty component** from the show command output
2. **Determine the correct configuration** based on the network design
3. **Apply the configuration change** using the Packet Tracer GUI or CLI
4. **Verify the fix** with the same or appropriate show command
5. **Test connectivity** from the affected client

### Example Fixes

#### Wrong VLAN Assignment
```
! On the switch, assign the port to the correct VLAN
interface Fa0/9
 switchport mode access
 switchport access vlan 30
!
Verification: show vlan brief
```

#### Wrong Default Gateway
```
! On the PC, set the correct gateway
! IP Config -> Gateway: 192.168.20.1 (for VLAN 20)
! Or: 192.168.10.1 (for VLAN 10)
```

#### DHCP Pool Exhaustion
```
! On the router, expand the DHCP pool
! ip dhcp pool VLAN20
! network 192.168.20.0 255.255.255.0  (larger pool)
! default-router 192.168.20.1
! dns-server 192.168.10.5
! Or: reduce lease time to free addresses faster
! ip dhcp lease 0 10  (10 minute lease)
```

#### DNS Resolution Failure
```
! On the router, fix the DHCP DNS server
! ip dhcp pool VLAN10
! network 192.168.10.0 255.255.255.0
! default-router 192.168.10.1
! dns-server 192.168.10.5  (correct internal DNS)
! Or: set the PC's DNS manually to 192.168.10.5
```

#### Missing Static Route
```
! On the router, add the static route
! ip route 172.16.20.0 255.255.255.0 10.0.0.2
! Or: configure a dynamic routing protocol
```

#### ACL Blocking Traffic
```
! On the router, correct the ACL
! access-list 101 permit ip 192.168.10.0 0.0.0.255 any
! Or: remove the overly broad deny, add specific permits
! access-list 101 permit ip 192.168.10.50 0.0.0.0 any  (specific host)
! Then: apply in the correct direction
! interface Gi0/1
! ip access-group 101 out  (out instead of in)
```

#### Missing 'ip nat inside'
```
! On the router, mark the interface as inside
! interface Gi0/0
! ip nat inside
! Or: verify the WAN interface has 'ip nat outside'
! interface Gi0/1
! ip nat outside
```

#### NAT Pool Exhaustion
```
! On the router, expand the NAT pool
! ip nat inside source list 1 interface Gi0/1 overload
! Or: increase the pool size
! ip nat pool NAT-POOL 203.0.113.10 203.0.113.20 netmask 255.255.255.240
! ip nat inside source list 1 pool NAT-POOL
```

#### Port Security Violation
```
! On the switch, re-enable the port
! interface Fa0/12
! no shutdown
! Or: reset the port security
! interface Fa0/12
! switchport port-security maximum 2  (allow 2 MACs)
! switchport port-security violation shutdown  -> use 'errdisable reset'
! switchport port-security
```

#### SSID Broadcast Disabled
```
! On the AP, re-enable SSID broadcast
! AP Configuration -> Broadcast SSID -> Check/Enable
! Or via CLI: no dot11 ssid CorpGuest broadcast-ssid disabled
```

#### Route Summarization Blackhole
```
! On the router, add a more-specific route
! ip route 172.16.25.0 255.255.255.0 10.0.0.2
! Or: adjust the summary to not include missing subnets
! Instead of: ip route 172.16.16.0 255.255.240.0 10.0.0.2
! Use: specific routes for each actual subnet
```

#### Voice VLAN without Data VLAN
```
! On the switch, add the access VLAN
! interface Fa0/15
! switchport mode access
! switchport access vlan 20  (or whatever the data VLAN is)
! switchport voice vlan 50
! Verification: show vlan brief (should show Fa0/15 in VLAN 20, not VLAN 1)
```

#### Default Gateway on Wrong Subnet
```
! On the PC, set the correct gateway
! For VLAN 20: Gateway 192.168.20.1
! For VLAN 10: Gateway 192.168.10.1
! Or: fix the PC's IP address to match the gateway subnet
```

#### Entire DHCP Scope Excluded
```
! On the router, fix the DHCP excluded addresses
! ip dhcp pool VLAN30
! network 192.168.30.0 255.255.255.0
! ip dhcp excluded-address 192.168.30.1 192.168.30.2  (only gateway excluded, not the whole pool)
! Or: remove the excluded-address command entirely
! no ip dhcp excluded-address
```

## 16. How to Verify the Fix

### Verification Commands per Fault

| Fault | Verification Command |
|-------|---------------------|
| Wrong VLAN | `show vlan brief`, then `ping <server-IP>` |
| Wrong Gateway | `ipconfig /all`, then `ping <gateway>` |
| DHCP Exhaustion | `show ip dhcp pool`, then `ipconfig /renew` |
| DNS Failure | `nslookup <hostname>`, then `ping <DNS-IP>` |
| Missing Route | `show ip route`, then `ping <destination>` |
| ACL Blocking | `show access-lists`, then `ping/traceroute` |
| NAT Not Translating | `show ip nat translations`, then `ping 8.8.8.8` |
| Wireless Issue | `show interfaces`, `show ap config`, then `reconnect` |
| Duplicate IP | `show ip dhcp conflict`, then reassign IP |
| Wrong Subnet Mask | `ipconfig /all`, correct the mask |
| Trunk Mismatch | `show interfaces trunk`, fix native VLAN |
| Interface Down | `show ip interface brief`, `no shutdown` |
| ACL Wrong Mask | `show access-lists`, recalculate wildcard |
| DNS Server Down | `ping <DNS-IP>`, check cabling/port |
| Overlapping Gateway | `ipconfig /all`, fix the gateway IP |
| NAT Conflict | `show run | include nat`, remove duplicate |
| SSID Not Visible | `show ap config`, re-enable broadcast |
| Route Blackhole | `show ip route`, add specific route |
| Voice Port VLAN | `show vlan brief`, add access vlan |
| Gateway Wrong Subnet | `ipconfig /all`, fix gateway IP |
| DHCP Scope Excluded | `show run | section ip dhcp pool`, fix exclusions |

### Post-Fix Verification Checklist

After applying any fix, verify:

- [ ] The show command output is now correct/expected
- [ ] The affected host can ping the gateway
- [ ] The affected host can reach the intended destination
- [ ] Inter-VLAN routing is working (if applicable)
- [ ] DNS resolution is working (if applicable)
- [ ] Internet connectivity is working (if applicable)
- [ ] No new faults have been introduced
- [ ] The configuration is consistent across all devices
- [ ] Run the full baseline verification checklist (Section 11)

## 17. How Packet Tracer Connects Conceptually to NetSage AI

### Evidence Flow

1. **User/Engineer introduces a fault** in Packet Tracer or encounters it in a real network
2. **Engineer collects evidence** using Cisco show commands in Packet Tracer
3. **Evidence is sent to NetSage AI** via the API (`/api/diagnose`)
4. **NetSage AI analyzes the evidence** using:
   - Template-based demo mode (evidence from show output)
   - Deterministic rule checker results
   - AI pattern matching (live mode with API key)
5. **AI predicts root cause, confidence, next command, and fix steps**
6. **Human reviewer accepts/edits/rejects** the AI prediction
7. **Engineer applies the fix** in Packet Tracer
8. **Verification commands** are run to confirm the fix
9. **New evidence is collected** and the cycle repeats

### Integration Points

The NetSage AI dashboard can use Packet Tracer evidence in these ways:

1. **Case selection**: User selects a case, the show output is fetched from Packet Tracer
2. **Evidence collection**: User runs show commands in Packet Tracer and copies the output
3. **Diagnosis input**: The show output is pasted into the NetSage AI diagnose page
4. **AI analysis**: NetSage AI processes the evidence and returns a diagnosis
5. **Human review**: Reviewer accepts/edits/rejects the AI diagnosis
6. **Fix verification**: Engineer applies the fix in Packet Tracer, verifies, and updates the review log

### API Integration

The existing NetSage AI API endpoints accept:
- `case_id`: Reference to the dataset case
- `symptom`: User-observed problem description
- `topology_note`: Network topology context
- `show_output`: Cisco `show` command output

The Packet Tracer configurations and show command outputs provide the `show_output` field
for the API. The `topology_note` can reference the device names and VLAN structure.

### How to Send Evidence from Packet Tracer to NetSage AI

1. **Run the diagnostic command** in Packet Tracer (e.g., `show vlan brief`)
2. **Copy the output** from the CLI window
3. **Go to the NetSage AI web interface**
4. **Paste the output** into the diagnose page's "Show Output" field
5. **Optionally select a case_id** from the existing 32 cases
6. **Click "Diagnose"** to run the AI + rule checker workflow
7. **Review the AI prediction** and human review options
8. **Apply the fix** in Packet Tracer if approved
9. **Verify connectivity** and collect new evidence
10. **Record the review** in the review log

## 18. Device Configuration Reload

If you modify configurations in Packet Tracer and want to verify:

1. Click the router/switch
2. Go to the "CLI" tab
3. Type `reload` and press Enter (confirm when prompted)
4. Or: right-click the device -> "Reload"
5. The configuration changes should persist (saved in NVRAM)

### Saving Configuration

1. Click the device
2. Go to the "CLI" tab
3. Type `copy running-config startup-config` or `write memory`
4. Confirm the save

## Appendix A: Quick Reference Commands

### Router (R1-EDGE) Key Commands

```
enable
show ip interface brief
show vlan brief
show interfaces trunk
show ip route
show ip dhcp pool
show ip dhcp binding
show ip nat translations
show ip nat statistics
show access-lists
copy running-config startup-config
configure terminal
```

### Switch (SW1-CORE) Key Commands

```
enable
show ip interface brief
show vlan brief
show interfaces trunk
show interfaces switchport
show mac address-table
show cdp neighbors
configure terminal
interface range Fa0/1 - Fa0/20
 switchport mode access
 switchport access vlan <10-50>
end
copy running-config startup-config
```

### PC Key Commands

```
ipconfig /all    (Windows)
dhclient -r && dhclient  (Linux)
ping <IP-address>
nslookup <hostname>
ipconfig /release
ipconfig /renew
```