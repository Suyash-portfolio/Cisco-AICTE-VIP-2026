# Network Topology Documentation

## ASCII Topology Diagram
```text
R2-ISP Gi0/0 (203.0.113.2/30)
          |
R1-EDGE Gi0/1 (203.0.113.1/30)
R1-EDGE Gi0/0 trunk
          |
SW1-CORE Gi0/1 trunk
  |       |       |       |       |       |       |       |
 Fa0/1  Fa0/2  Fa0/3  Fa0/4  Fa0/5  Fa0/6  Gi0/2  Gi0/3  Gi0/24
  |       |       |       |       |       |       |       |
 ADMIN  USER1  USER2  DNS    WEB    GUEST  SW2    SW3    AP1-GUEST
 VLAN10 VLAN20 VLAN20 VLAN10 VLAN30 VLAN40 trunk  trunk  VLAN40
```
```

## Device Names and Roles

| Device | Type | Role |
|--------|------|------|
| R1-EDGE | Router | Core router, inter-VLAN routing, DHCP server, NAT, ACL, default route |
| SW1-CORE | Layer 2 switch | Core switch, VLANs, trunk links to R1 and access switches |
| SW2-ACCESS | Switch | Access switch, connects user PCs and servers |
| SW3-ACCESS | Switch | Access switch, connects user PCs and guest devices |
| AP1-GUEST | Wireless AP | Guest wireless network (VLAN 40) |
| SRV-DNS | Server | Internal DNS server (192.168.10.5) |
| SRV-WEB | Server | Internal web server (192.168.30.100) |
| PC-ADMIN-01 | PC | Admin workstation (VLAN 10) |
| PC-USER-01 | PC | User workstation (VLAN 20) |
| PC-USER-02 | PC | User workstation (VLAN 20) |
| PC-GUEST-01 | PC | Guest workstation (VLAN 40) |

## VLAN Table

| VLAN | Name | Purpose | Subnet | Gateway |
|------|------|---------|--------|---------|
| 10 | ADMIN | Administration workstations | 192.168.10.0/24 | 192.168.10.1 |
| 20 | USERS | User workstations | 192.168.20.0/24 | 192.168.20.1 |
| 30 | SERVERS | Servers (DNS, Web) | 192.168.30.0/24 | 192.168.30.1 |
| 40 | GUEST | Guest wireless and wired guests | 192.168.40.0/24 | 192.168.40.1 |
| 50 | MANAGEMENT | Management network | 192.168.50.0/24 | 192.168.50.1 |

## IP Addressing Summary

### Router (R1-EDGE) Interfaces

| Interface | IP Address | Subnet | Description |
|-----------|-----------|--------|-------------|
| GigabitEthernet0/0.10 | 192.168.10.1/24 | VLAN 10 | Admin gateway |
| GigabitEthernet0/0.20 | 192.168.20.1/24 | VLAN 20 | Users gateway |
| GigabitEthernet0/0.30 | 192.168.30.1/24 | VLAN 30 | Servers gateway |
| GigabitEthernet0/0.40 | 192.168.40.1/24 | VLAN 40 | Guest gateway |
| GigabitEthernet0/0.50 | 192.168.50.1/24 | VLAN 50 | Management gateway |
| GigabitEthernet0/1 | 203.0.113.1/30 | Point-to-point | WAN/ISP link |

### DHCP Pools

| Pool | Network | Subnet Mask | Gateway | DNS Server |
|------|---------|-------------|---------|------------|
| VLAN10 | 192.168.10.0 | /24 | 192.168.10.1 | 192.168.10.5 |
| VLAN20 | 192.168.20.0 | /24 | 192.168.20.1 | 192.168.10.5 |
| VLAN30 | 192.168.30.0 | /24 | 192.168.30.1 | 192.168.10.5 |
| VLAN40 | 192.168.40.0 | /24 | 192.168.40.1 | 192.168.10.5 |

### Server Static IPs

| Device | IP Address | VLAN | Purpose |
|--------|-----------|------|---------|
| SRV-DNS | 192.168.10.5 | 10 | Internal DNS server |
| SRV-WEB | 192.168.30.100 | 30 | Internal web server |

### End Device Addressing

| Device | IP Address | Mask | Gateway | DNS | VLAN |
|--------|------------|------|---------|-----|------|
| PC-ADMIN-01 | 192.168.10.50 | 255.255.255.0 | 192.168.10.1 | 192.168.10.5 | 10 |
| PC-USER-01 | 192.168.20.10 | 255.255.255.0 | 192.168.20.1 | 192.168.10.5 | 20 |
| PC-USER-02 | 192.168.20.20 | 255.255.255.0 | 192.168.20.1 | 192.168.10.5 | 20 |
| PC-GUEST-01 | 192.168.40.10 | 255.255.255.0 | 192.168.40.1 | 192.168.10.5 | 40 |

SRV-DNS is a Server-PT at 192.168.10.5/24 with gateway 192.168.10.1 and DNS 192.168.10.5.
Its DNS service is ON with `web.netsage.local` mapped to 192.168.30.100.
SRV-WEB is a Server-PT at 192.168.30.100/24 with gateway 192.168.30.1 and DNS 192.168.10.5; HTTP is ON.

## Routing Design

### Router-on-a-Stick (Inter-VLAN Routing)

The router uses subinterfaces on Gi0/0 to route between VLANs:

- Gi0/0.10 - VLAN 10, IP 192.168.10.1
- Gi0/0.20 - VLAN 20, IP 192.168.20.1
- Gi0/0.30 - VLAN 30, IP 192.168.30.1
- Gi0/0.40 - VLAN 40, IP 192.168.40.1
- Gi0/0.50 - VLAN 50, IP 192.168.50.1

Each subinterface has `encapsulation dot1Q <vlan-id>` and the appropriate IP address.

### Default Route (Internet/WAN)

The router has a default route pointing to the ISP:

```
ip route 0.0.0.0 0.0.0.0 203.0.113.2
```

or via the directly connected WAN interface.

## DHCP Configuration

Router (R1-EDGE) acts as DHCP server for VLANs 10, 20, 30, and 40:

- DHCP pool VLAN10: 192.168.10.0/24, gateway 192.168.10.1, DNS 192.168.10.5
- DHCP pool VLAN20: 192.168.20.0/24, gateway 192.168.20.1, DNS 192.168.10.5
- DHCP pool VLAN30: 192.168.30.0/24, gateway 192.168.30.1, DNS 192.168.10.5
- DHCP pool VLAN40: 192.168.40.0/24, gateway 192.168.40.1, DNS 192.168.10.5

Excluded addresses are 192.168.10.1-20, 192.168.20.1-20, and 192.168.30.1-20.

The DHCP relay (ip helper-address) is configured on VLAN interfaces to forward
requests to the central DHCP server if the server is on a different subnet.

## ACL Design

ACL 100 is used only for NAT. ACL 110 isolates guest traffic inbound on Gi0/0.40:

| ACL | Rule | Purpose |
|-----|------|---------|
| 100 | permit VLANs 10, 20, 30, 40, 50 | NAT source networks |
| 110 | deny guest to VLANs 10, 20, 30; permit guest to any | Guest isolation |

## NAT Design

NAT overloaded (PAT) for internet access from all internal VLANs:

```
ip nat inside source list 100 interface GigabitEthernet0/1 overload
```

Inside interfaces: Gi0/0.10, Gi0/0.20, Gi0/0.30, Gi0/0.40, Gi0/0.50
Outside interface: GigabitEthernet0/1 (WAN/ISP link)

## Wireless Design

- AP1-GUEST Gi0/0 connects to SW1-CORE Gi0/24 (access port, VLAN 40)
- SSID: CorpGuest
- Security: WPA2-PSK, password: GuestPass123
- VLAN mapping: 40 (Guest isolation)
- The guest network is isolated from Admin and Users VLANs via ACLs and VLAN separation

There is no separate management AP or Gi0/25 connection in the baseline topology.

## Baseline Verification Checklist

### Working Network Verification

- [x] Same-VLAN connectivity: PC can ping another PC in same VLAN
- [x] Inter-VLAN connectivity: PC can ping gateway and servers in other VLANs
- [x] Server access: SRV-WEB (192.168.30.100) accessible from VLAN 20 PCs
- [x] DNS resolution: PCs can resolve internal hostnames via 192.168.10.5
- [x] DHCP address assignment: PCs obtain IPs from DHCP pools
- [x] Internet/WAN connectivity: Internal hosts can reach 8.8.8.8
- [x] Guest isolation: Guest VLAN 40 devices cannot reach VLAN 10/20/30 resources
- [x] Administrative access: VLAN 10 management reachable

### Commands to Verify Baseline

```
show ip interface brief
show vlan brief
show interfaces trunk
show ip route
show ip dhcp pool
show ip nat translations
show access-lists
ping 192.168.10.1  (from VLAN 10 PC)
ping 192.168.20.1  (from VLAN 20 PC)
ping 192.168.30.1  (from VLAN 20 PC)
ping 192.168.30.100 (from any PC - server)
ping 8.8.8.8       (from any PC - internet)
nslookup intranet.local (from any PC - DNS)
```

## Troubleshooting Scenarios

The following fault scenarios are documented and can be introduced in Packet Tracer:

1. **Wrong VLAN assignment** - Access port in wrong VLAN (CASE-001, CASE-011, CASE-016, CASE-023)
2. **Access port as trunk** - Port configured as trunk instead of access (CASE-016)
3. **Trunk native VLAN mismatch** - Native VLAN differs between trunk ends (CASE-011)
4. **Missing VLAN on trunk** - VLAN not in trunk allowed list (CASE-013)
5. **Wrong default gateway** - Gateway on different subnet (CASE-002, CASE-010, CASE-026, CASE-031)
6. **DHCP pool exhaustion** - All addresses leased (CASE-003)
7. **DHCP excluded range covers all** - No usable addresses (CASE-032)
8. **DNS misconfiguration** - Wrong DNS server in DHCP scope (CASE-004, CASE-017)
9. **Missing DNS configuration** - DNS server unreachable (CASE-025)
10. **Missing static route** - No route to remote subnet (CASE-005, CASE-022, CASE-029)
11. **Incorrect routing** - Wrong encapsulation or tag (CASE-014)
12. **Interface shutdown** - Administrative shutdown (CASE-012)
13. **Incorrect subnet mask** - /26 instead of /24 (CASE-010)
14. **Duplicate IP address** - Static IP overlaps DHCP scope (CASE-009)
15. **ACL blocking legitimate traffic** - Overly broad deny (CASE-006, CASE-024)
16. **ACL wrong direction** - Applied in vs out (CASE-019)
17. **Incorrect ACL wildcard mask** - 0.0.15.255 instead of 0.0.0.255 (CASE-024)
18. **NAT missing inside designation** - No 'ip nat inside' (CASE-007)
19. **NAT pool exhausted** - All pool addresses allocated (CASE-020)
20. **Duplicate static NAT mapping** - Two hosts mapped to same public IP (CASE-027)
21. **Guest network isolation failure** - Guest VLAN can reach internal resources
22. **Wireless security mismatch** - WPA2-Enterprise vs WPA2-Personal (CASE-008)
23. **Wireless channel overlap** - Same channel on multiple APs (CASE-021)
24. **SSID broadcast disabled** - SSID not visible (CASE-028)
25. **Voice VLAN without data VLAN** - Data port defaults to VLAN 1 (CASE-030)
26. **Port security shutdown** - Port goes into err-disable (CASE-023)
27. **Route summarization blackhole** - Supernet hides specific subnet (CASE-029)
28. **Gateway on wrong subnet** - Default gateway mismatched (CASE-031)
29. **Entire DHCP scope excluded** - Excluded range covers whole pool (CASE-032)
30. **Multi-factor combined fault** - Multiple issues simultaneously
31. **Missing VLAN on trunk allowed list** - VLAN not carried across trunk
32. **Default route problem** - No 0.0.0.0/0 entry for internet access