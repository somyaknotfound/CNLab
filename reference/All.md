# Cisco Packet Tracer — Lab Reference & Approach Guide

A personal cheat-sheet built from working through the Assignment 6 Enterprise Campus
Network (and the earlier assignments it builds on). It captures not just the commands,
but *how to think* about each type of problem, the order to do things in, and the
mistakes that cost the most time. Use it as a template for future labs.

---

## 0. The universal workflow (do this every time)

For ANY topology, work in this order. Skipping ahead is what causes the "random
unexplained failure" you can't debug:

1. **Place devices** — pick correct models, rename immediately.
2. **Cable** with the Automatic tool (dashed lightning bolt).
3. **Discover real port names** — `show ip interface brief` + `show cdp neighbors`
   on every switch/router BEFORE configuring anything.
4. **Create VLANs on every switch in the path** (even transit switches with no PCs).
5. **Configure trunks** (switch-to-switch and switch-to-router links).
6. **Configure access ports** (where PCs live) into their VLANs.
7. **Router subinterfaces** (router-on-a-stick) — inter-VLAN routing + DHCP relay.
8. **Central services** — DHCP pools, DNS records, HTTP.
9. **Wireless / cellular** if present.
10. **VERIFY EVERYTHING** — do not touch ACLs until the whole network passes.
11. **ACLs** (security policy), one at a time, testing after each.
12. **Final verification matrix.**

> Golden rule: **build → verify → secure.** Never layer ACLs on an unverified network.

---

## 1. Orientation habits that save time

### Read the prompt before every command
Most `% Invalid input detected` errors are NOT typos — they're the right command on
the wrong device or in the wrong mode. The prompt tells you both.

| Prompt | Where you are | What works |
|---|---|---|
| `Switch>` / `Router>` | User EXEC | show commands only; type `enable` |
| `Switch#` / `Router#` | Privileged EXEC | all show, `write memory`; type `configure terminal` |
| `Switch(config)#` | Global config (SWITCH) | `vlan`, `interface`, `hostname` — VLANs created ONLY here |
| `Router(config)#` | Global config (ROUTER) | `interface`, subinterfaces, `access-list` — **no `vlan` command** |
| `(config-if)#` | One interface | `ip address`, `no shutdown`, `switchport ...` |
| `(config-if-range)#` | Several interfaces | same, applied to all at once |
| `(config-subif)#` | Router subinterface | `encapsulation dot1Q`, then `ip address` |

### Three universal CLI habits
```
enable              -> privileged EXEC (# prompt)
configure terminal  -> global config ((config)# prompt)
end                 -> jump back to privileged EXEC
write memory        -> SAVE (without this, all is lost on reload)
```
Tab autocompletes. `?` lists valid next words. Abbreviations work
(`int g0/0/0`, `sh ip int br`).

### Discover interface names FIRST
Router models name interfaces differently. Using the wrong one gives
`%Invalid interface type and number`.
```
enable
show ip interface brief
```
- ISR 4321/4331 (NIM slots): `GigabitEthernet0/0/0` -> `int g0/0/0` (three segments)
- 1941/2901/2911: `GigabitEthernet0/0` -> `int g0/0` (two segments)
- Older 1841/2811: `FastEthernet0/0` -> `int f0/0`

A three-segment name (0/0/0) and two-segment (0/0) are NOT interchangeable.

### `show cdp neighbors` — the mapping shortcut
Lists every directly-connected **Cisco** device and the local port it's on.
- Routers show capability `R`, switches show `S`.
- Any **up** port NOT listed by CDP is a non-Cisco device (PC, server, AP, hub).
- This is how you figure out which port is a trunk (switch/router neighbor) vs an
  access port (server/PC) without hovering over every cable.

---

## 2. Device model selection

| Role | Model to pick | Why |
|---|---|---|
| Router | **ISR 4321** (or 4331) | Gives `G0/0/0`, `G0/0/1` built in — matches lab command syntax |
| Switch (all tiers) | **2960-24TT** | 24× FastEthernet + 2× Gig uplinks; standard lab switch |
| Server | **Server-PT** | DHCP/DNS/HTTP under Services tab |
| Access Point | **AP-PT** or **AP-PT-N** | Plain AP; central DHCP handles addressing |
| Cellular radio | **Cell Tower** | Under Wireless Devices |
| Cellular bridge | **Central Office Server (CO)** | Bridges cellular <-> wired |
| WAN cloud | **Cloud-PT** | Under Network Devices -> WAN Emulation |
| PCs / laptop / phone | PC-PT / Laptop-PT / Smartphone-PT | End devices |
| Hub (for L1 demo) | **Hub-PT** | Floods everything; no config, no VLANs |

Avoid **WRT300N** and **Home Gateway** as the AP when using a central DHCP server —
they have their own built-in DHCP that fights the central one.

---

## 3. Cabling

- Default: use **Automatic (dashed lightning bolt)** — Packet Tracer picks the right
  cable and avoids the classic "wrong cable, link won't come up" trap.
- Textbook-correct manual choices (auto-MDIX on modern 2960s makes this moot):
  - Switch <-> Switch: **Cross-Over**
  - Switch <-> Router / Switch <-> PC / Server <-> Switch: **Straight-Through**
  - Cell Tower <-> CO Server: **Coaxial**
  - CO Server <-> Cloud: **Straight-Through** (may need to add a Cloud Ethernet
    module first via Cloud -> Physical -> power off -> add module -> power on)
- Auto-cabling fills ports **in order**, so devices often land on ports you didn't
  expect (e.g. router on Fa0/7 after six PCs took Fa0/1-6). Always re-check with
  `show ip interface brief`.

---

## 4. VLANs (create on EVERY switch in the path)

The #1 failure point in multi-switch labs: a VLAN missing on one middle (transit)
switch silently kills traffic passing through it. Create ALL VLANs on Core,
every Distribution, AND every Access switch — even the ones with no PCs.

```
enable
configure terminal
vlan 10
 name Admin
exit
vlan 20
 name Faculty
exit
vlan 30
 name Students
exit
vlan 50
 name Guest
exit
vlan 99
 name Servers
exit
end
write memory
```

---

## 5. Trunk ports (switch-to-switch, switch-to-router)

Every link between switches, and the switch-to-router link, is a **trunk**.
Configure trunks on **both ends** with the same allowed-VLAN list.

```
interface range fa0/1-2          ! or whatever the trunk ports are
 switchport mode trunk
 switchport trunk allowed vlan 10,20,30,50,99
exit
```

Verify:
```
show interfaces trunk
```
Each trunk port should show `trunking`, `802.1q`, and the allowed vlan list.

**SPANTREE warnings while configuring** (`RECV_PVID_ERR`, `BLOCK_PVID_LOCAL`,
"Received 802.1Q BPDU on non trunk...") are normal and self-clear the moment BOTH
ends become trunks. They happen because one end is already trunking (sending tags)
while the other is still an access port. Don't panic — finish the trunk config.

If `show interfaces trunk` returns nothing: the port has no live link. Find a
genuinely up/up port with `show ip interface brief` and trunk that one instead.

---

## 6. Access ports (where PCs connect)

Assign each device-facing port to its VLAN. Two separate commands — don't merge them.

```
interface range fa0/2-3
 switchport mode access
 switchport access vlan 10          ! branch's VLAN
exit
```

- `switchport mode access vlan 10` in one line is REJECTED — that's two commands.
  Type `switchport mode access`, Enter, then `switchport access vlan 10`.
- An **Access Point** port is just a normal access port in the target VLAN; the AP
  bridges Wi-Fi clients into it.
- A **Hub** port is also a normal access port; everything behind the hub rides that
  VLAN (hubs are L1, VLAN-unaware).

Verify:
```
show vlan brief          ! confirms which ports are in each VLAN
```

---

## 7. Router-on-a-stick (inter-VLAN routing + DHCP relay)

The keystone. One physical router interface, one subinterface per VLAN. This is what
routes between VLANs and (with `ip helper-address`) relays DHCP across the routed
boundary.

**ORDER MATTERS:** `encapsulation dot1Q <vlan>` MUST come before `ip address`.
A subinterface has no VLAN identity until encapsulation gives it one; putting the IP
first gives:
`% Configuring IP routing on a LAN subinterface is only allowed if that subinterface
is already configured as part of an IEEE 802.1Q ... VLAN.`

```
enable
configure terminal
interface GigabitEthernet0/0/0        ! parent
 no shutdown                          ! parent gets NO ip address
exit
interface GigabitEthernet0/0/0.10
 encapsulation dot1Q 10               ! FIRST
 ip address 192.168.10.1 255.255.255.0
 ip helper-address 192.168.1.2        ! forwards DHCP broadcasts to the server
exit
interface GigabitEthernet0/0/0.20
 encapsulation dot1Q 20
 ip address 192.168.20.1 255.255.255.0
 ip helper-address 192.168.1.2
exit
interface GigabitEthernet0/0/0.30
 encapsulation dot1Q 30
 ip address 192.168.30.1 255.255.255.0
 ip helper-address 192.168.1.2
exit
interface GigabitEthernet0/0/0.50
 encapsulation dot1Q 50
 ip address 192.168.50.1 255.255.255.0
 ip helper-address 192.168.1.2
exit
interface GigabitEthernet0/0/0.99     ! server VLAN — no helper (server lives here)
 encapsulation dot1Q 99
 ip address 192.168.1.1 255.255.255.0
exit
end
write memory
```

- The **parent interface** must be `no shutdown` but gets NO IP.
- If the router link shows **red/down**: 99% of the time it's a missing `no shutdown`
  on the router interface (ISR interfaces are admin-down by default).
- Each PC's default gateway MUST match its VLAN's subinterface IP (VLAN 20 PC ->
  gateway 192.168.20.1). Mismatched gateway = inter-VLAN routing fails for that PC.

Verify:
```
show ip interface brief    ! all subinterfaces up/up
show ip route              ! one connected (C) route per VLAN subnet
```

**Why `ip helper-address`:** DHCP requests are broadcasts, and routers don't forward
broadcasts. The helper converts the broadcast into a unicast aimed at the DHCP server,
so clients in each VLAN can reach a central server sitting in another VLAN.

---

## 8. Central services (server config)

### The one UI quirk that trips everyone
On a Server -> Services tab, each service (DHCP, DNS, HTTP) has a small **On/Off radio
button** near the top-left. If it's Off, NOTHING on that page works — no pool, no
record, no page — regardless of everything else. Always check this radio FIRST.

### Server static IP
Set in **Config tab -> FastEthernet0** (Port Status = On) AND/OR **Desktop -> IP
Configuration -> Static**. Servers have a single port literally named `FastEthernet0`.
```
IP: 192.168.1.2   Mask: 255.255.255.0   Gateway: 192.168.1.1   DNS: 192.168.1.2
```

### DHCP — one pool per VLAN (Services -> DHCP)
Fill fields, then click **Add** (not Save — Add commits the pool).

| Pool | Default Gateway | DNS | Start IP | Mask |
|---|---|---|---|---|
| Admin | 192.168.10.1 | 192.168.1.2 | 192.168.10.10 | 255.255.255.0 |
| Faculty | 192.168.20.1 | 192.168.1.2 | 192.168.20.10 | 255.255.255.0 |
| Students | 192.168.30.1 | 192.168.1.2 | 192.168.30.10 | 255.255.255.0 |
| Guest | 192.168.50.1 | 192.168.1.2 | 192.168.50.10 | 255.255.255.0 |

- Each pool's gateway must match that VLAN's router subinterface.
- Start at .10 so .1-.9 stays free for gateways/static devices.

### DNS (Services -> DNS)
Service = On, then add an A record:
```
Name: www.company.com   Type: A Record   Address: 192.168.1.3   -> Add
```

### HTTP (Services -> HTTP)
Set On (default index.html is fine).

### Router-based DHCP alternative (if not using a server)
```
configure terminal
ip dhcp excluded-address 192.168.1.1 192.168.1.9
ip dhcp pool WIFI_POOL
 network 192.168.1.0 255.255.255.0
 default-router 192.168.1.1
 dns-server 192.168.1.2
exit
end
```

---

## 9. Testing DHCP (the big proof)
On a PC: **Desktop -> IP Configuration -> DHCP** radio button. Wait a few seconds.
`DHCP request successful.` + a correct address = the ENTIRE chain works
(PC -> access sw -> dist -> core -> router relay -> server -> back). This one test
validates every switch, trunk, subinterface, and the relay at once.

Verify from PC command prompt:
```
ipconfig /all
ping <own gateway>
ping <a host in another VLAN>     ! proves inter-VLAN routing
nslookup www.company.com          ! should return the web server IP
ping www.company.com              ! resolution + reachability
```

---

## 10. Wireless (Assignment 4 pattern)
- AP -> Config tab -> Wireless: set **SSID** and **WPA2** security (SSID is
  case-sensitive; must match on clients exactly).
- Clients: laptops use Desktop -> PC Wireless; phones/tablets use Config -> Wireless0
  (type SSID, auth mode, passphrase directly — they have no "PC Wireless" icon).
- Changing SSID/security invalidates every client's stored profile — reconnect each
  device manually, nothing rejoins by itself.
- Wi-Fi client has IP but gateway ping fails: you're pinging the wrong gateway.
  Read the Default Gateway under the **Wireless0** block (a WRT300N uses 192.168.0.1,
  not .1.1). Ignore the Bluetooth block (shows 0.0.0.0).

---

## 11. Cellular (Assignment 5 pattern)
Chain: **Smartphone -> Cell Tower -> Central Office Server -> Cloud -> wired network.**
- Cell Tower <-> CO Server: **coaxial** cable (not copper).
- CO Server <-> Cloud: straight-through copper; may need to add a Cloud Ethernet
  module (Cloud -> Physical -> power off -> add module -> power on) if no free port.
- Cloud needs **internal Config** to bridge cellular <-> Ethernet — cabling alone
  won't pass traffic. This is the "configure the Cloud to bridge" step.
- Smartphones associate to the tower wirelessly (not cabled to a switch).
- Host-specific ACL example (allow one phone to a server, block others):
```
access-list 101 permit ip host <phone-IP> host 192.168.1.3
access-list 101 deny ip any host 192.168.1.3
access-list 101 permit ip any any
```

---

## 12. Access Control Lists (ACLs)

**Do NOT add any ACL until the whole network passes verification.** Debugging a broken
network and a new ACL at the same time is how you lose a lab session.

### Extended ACL anatomy
```
access-list <100-199> {permit|deny} <proto> <src> <wildcard> <dst> <wildcard> [eq <port>]
```
- **Wildcard mask** is the inverse of the subnet mask: `0.0.0.255` = match a whole /24.
- ACLs have an **invisible `deny any any`** at the end. Without an explicit
  `permit ip any any` as the last line, you block everything from that source.
- ACLs stop at the **first match** — order matters. A broad `permit` above a `deny`
  makes the deny unreachable.
- Apply with direction: `ip access-group <n> in|out`. `in` on a subinterface filters
  traffic arriving FROM that VLAN.

### The four campus rules (Assignment 6)
```
! Rule 1 - Students (30) cannot reach Admin (10)
access-list 110 deny  ip 192.168.30.0 0.0.0.255 192.168.10.0 0.0.0.255
access-list 110 permit ip any any
interface GigabitEthernet0/0/0.30
 ip access-group 110 in
exit

! Rule 2 - Faculty (20) may reach all servers (permissive; only if you add restrictions)
access-list 120 permit ip 192.168.20.0 0.0.0.255 192.168.1.0 0.0.0.255
access-list 120 permit ip any any

! Rule 3 - Guest Wi-Fi (50) gets internet only, no internal
access-list 130 deny  ip 192.168.50.0 0.0.0.255 192.168.0.0 0.0.255.255
access-list 130 permit ip any any
interface GigabitEthernet0/0/0.50
 ip access-group 130 in
exit

! Rule 4 - Cellular/Students may browse web but not reach internal PCs
!          (DNS permit is REQUIRED or name resolution breaks and site "fails")
access-list 140 permit ip  192.168.30.0 0.0.0.255 host 192.168.1.3        ! web OK
access-list 140 permit udp 192.168.30.0 0.0.0.255 host 192.168.1.2 eq 53  ! DNS OK
access-list 140 deny  ip  192.168.30.0 0.0.0.255 192.168.10.0 0.0.0.255
access-list 140 deny  ip  192.168.30.0 0.0.0.255 192.168.20.0 0.0.0.255
access-list 140 permit ip any any
```

### Common ACL mistake (learned the hard way)
Typo'ing the list NUMBER splits your rule across two ACLs:
```
access-list 110 deny ip ...      <- rule on list 110 (applied to interface)
access-list 100 permit ip any any  <- permit on 100 by mistake -> useless
```
Result: list 110 has only the deny + implicit deny-all -> blocks EVERYTHING from the
source, not just the target. Fix: put the permit on the SAME list number (110), and
remove the stray list (`no access-list 100`).

### Proving an ACL works
```
show access-lists     ! match counters increment on the line catching traffic
```
From a source PC: ping the blocked target (must FAIL) and an allowed target
(must SUCCEED).

---

## 13. Verification command quick-reference

| Purpose | Command |
|---|---|
| Discover interfaces | `show ip interface brief` |
| Map neighbors (find trunks) | `show cdp neighbors` |
| Verify VLANs + port membership | `show vlan brief` |
| Verify trunks | `show interfaces trunk` |
| Verify routing | `show ip route` |
| Verify MAC learning (L2) | `show mac address-table` |
| Verify ACLs + hit counts | `show access-lists` |
| Full config | `show running-config` |
| Save | `write memory` |

PC command prompt: `ipconfig`, `ipconfig /all`, `ping <ip|name>`,
`nslookup <name>`, `tracert <ip>`, `arp -a`.

---

## 14. Troubleshooting reference (symptom -> cause)

| Symptom | Most likely cause / fix |
|---|---|
| `%Invalid interface type and number` | Wrong interface name for the model. `show ip int br`, use exact name. |
| `vlan 10` rejected | You're on the router, not the switch. Prompt must read `Switch(config)#`. |
| `switchport mode access vlan 10` rejected | Two merged commands. Split into two lines. |
| `show interfaces trunk` returns nothing | Trunked a port with no live link. Trunk a genuinely up/up port. |
| Router-switch link red/down | Missing `no shutdown` on the router interface. |
| SPANTREE PVID errors on a link | One end trunking, other still access. Clears when both are trunks. |
| Interface "administratively down" | Missing `no shutdown`. |
| DHCP client "DHCP failed" | Pool not Added (clicked Save not Add), or missing `ip helper-address` across a router. |
| Inter-VLAN routing not working | Trunk missing on one end / VLAN missing from allowed list / VLAN not created on a transit switch / parent interface shut. |
| ACL blocks everything | Missing explicit `permit ip any any` (implicit deny-all). |
| ACL does nothing | Line order (broad permit above the deny) or wrong direction/interface. |
| Website unreachable, server pings fine | DNS blocked/misconfigured. Test with raw IP; if that works, it's name resolution. |
| Service (DHCP/DNS/HTTP) not working | The On/Off radio at top-left of the Services page is Off. Check it FIRST. |
| Everything broke after reload | Never saved. Finish with `write memory` on every device. |
| Ping to gateway fails, config looks right | Typo in PC's gateway (192.160 vs 192.168), or router interface not `no shutdown`. |
| Cable refused "cannot be connected" | No free/compatible port. Device -> Physical -> power off -> add module -> power on. Or use Automatic tool. |
| Output stuck at `--More--` | Pagination, not an error. Space = next page, Enter = next line, q = quit. Gig ports appear after all 24 Fa ports. |

---

## 15. Addressing plan used (Assignment 6)

| Segment | VLAN | Subnet | Gateway |
|---|---|---|---|
| Admin | 10 | 192.168.10.0/24 | 192.168.10.1 |
| Faculty (wired + Wi-Fi) | 20 | 192.168.20.0/24 | 192.168.20.1 |
| Students (wired + cellular) | 30 | 192.168.30.0/24 | 192.168.30.1 |
| Guest Wi-Fi | 50 | 192.168.50.0/24 | 192.168.50.1 |
| Server farm | 99 | 192.168.1.0/24 | 192.168.1.1 |
| Servers: DHCP/DNS 192.168.1.2, Web 192.168.1.3 | | | |

---

## 16. What was completed vs. remaining (this session)

**Done and verified:**
- 7 switches placed/renamed (Core, Dist1-3, Access1-3), full hierarchy cabled
- VLANs 10/20/30/50/99 created on all 7 switches
- All trunks up (Core Fa0/1,4,5,6; each Dist Fa0/1-2; each Access Fa0/1)
- Server ports as access VLAN 99 (Core Fa0/2-3)
- Access ports: Access1->VLAN10, Access2->VLAN20, Access3->VLAN30
- Router subinterfaces .10/.20/.30/.50 (+.99), all up/up, helper-address set
- DHCP pools (4) added, service On; DHCP test PASSED (PC0 got 192.168.10.10)

**Remaining:**
- DNS A record + web server HTTP on
- Wireless (AP SSID/WPA2) and cellular (tower->CO->cloud bridge) config
- Full pre-ACL verification pass
- Apply the 4 ACLs (test after each)
- Final verification matrix (the deliverable)

---

## 17. Assignment 2 — Dynamic Routing using OSPF (detailed walkthrough)

**Objective:** Configure OSPF so three routers learn routes from each other automatically,
then verify end-to-end connectivity between all four PCs.

Every step tells you what to place, what to click, what to type, and how to verify it worked.

### Topology at a glance

```
                         R2
              S0/0/0 .------.  S0/0/1
        10.0.12.0/30 |      | 10.0.23.0/30
                   .-'      '-.
                  /            \
                R1 -----------  R3
             S0/0/1  19.0.13.0/30  S0/0/0
             (the R1-R3 link)
             G0/0              G0/0
       192.168.1.0/24    192.168.3.0/24
             |                  |
            SW1                SW3
          /     \            /      \
        PC1     PC2        PC3      PC4
```

R2 also has a LAN (192.168.2.0/24) hanging off its G0/0 with its own switch/PCs.

#### Addressing plan

| Link / LAN | Network | Interface(s) & IP |
|---|---|---|
| R1 <-> R2 (serial) | 10.0.12.0/30 | R1 S0/0/0 = 10.0.12.1 · R2 S0/0/0 = 10.0.12.2 |
| R2 <-> R3 (serial) | 10.0.23.0/30 | R2 S0/0/1 = 10.0.23.2 · R3 S0/0/0 = 10.0.23.3 |
| R1 <-> R3 (serial) | 19.0.13.0/30 | R1 S0/0/1 = 19.0.13.1 · R3 S0/0/1 = 19.0.13.3 |
| R1 LAN | 192.168.1.0/24 | R1 G0/0 = 192.168.1.1 |
| R2 LAN | 192.168.2.0/24 | R2 G0/0 = 192.168.2.1 |
| R3 LAN | 192.168.3.0/24 | R3 G0/0 = 192.168.3.1 |

**/30 refresher:** mask `255.255.255.252`, wildcard `0.0.0.3`, only 2 usable hosts —
perfect for point-to-point router links.

PCs (gateway = their router's G0/0):
| PC | IP | Mask | Gateway |
|---|---|---|---|
| PC1 | 192.168.1.10 | 255.255.255.0 | 192.168.1.1 |
| PC2 | 192.168.1.11 | 255.255.255.0 | 192.168.1.1 |
| PC3 | 192.168.3.10 | 255.255.255.0 | 192.168.3.1 |
| PC4 | 192.168.3.11 | 255.255.255.0 | 192.168.3.1 |

### STEP 1 — Place the devices

**Where:** Device palette (bottom-left).

- 3 **Routers** — model **ISR 4321** (or any router with WIC-2T serial support). Rename
  them **R1, R2, R3** (right-click -> Rename).
- 2–3 **2960-24TT switches** (SW1, SW2, SW3) — one per LAN that has PCs.
- **PCs** — PC1, PC2 on the R1 LAN; PC3, PC4 on the R3 LAN (add R2-LAN PCs if required).

> **Serial ports need a module.** Routers don't ship with serial interfaces by default.
> For each router: double-click -> **Physical** tab -> power OFF (click the switch on the
> chassis) -> drag a **WIC-2T** (or NIM-2T on ISR4321) into an empty slot -> power ON.
> Now you'll have S0/0/0 and S0/0/1. Do this on all three routers before cabling.

### STEP 2 — Cable everything

**Where:** Connections -> **Automatic** for LAN links; **Serial DCE** for router-to-router.

- **LAN links (copper):** R1 G0/0 -> SW1; SW1 -> PC1, PC2. Same for R3/SW3/PC3,PC4
  (and R2/SW2 if used). Automatic tool is fine here.
- **Serial links (router-to-router):** use the **Serial DCE** cable
  (Connections -> the cable icon that looks like a lightning/serial connector).
  - R1 S0/0/0 <-> R2 S0/0/0
  - R2 S0/0/1 <-> R3 S0/0/0
  - R1 S0/0/1 <-> R3 S0/0/1
  - The end you attach FIRST becomes the **DCE** end and needs a **clock rate**
    (Packet Tracer marks the DCE end with a small clock symbol on the cable).

### STEP 3 — Discover interface names

**Where:** Each router -> CLI tab.

```
enable
show ip interface brief
```
Confirm the serial names (S0/0/0, S0/0/1) and the LAN name (G0/0). Substitute whatever
appears in the Interface column into the commands below. All serial/LAN interfaces will
show **administratively down** until you configure and `no shutdown` them.

### STEP 4 — Configure R1 interfaces

**Where:** R1 -> CLI tab.

```
enable
configure terminal
hostname R1

interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown
exit

interface Serial0/0/0
 ip address 10.0.12.1 255.255.255.252
 clock rate 64000            ! ONLY on the DCE end of the cable
 no shutdown
exit

interface Serial0/0/1
 ip address 19.0.13.1 255.255.255.252
 clock rate 64000            ! ONLY if this end is DCE
 no shutdown
exit
end
write memory
```

> **`clock rate`** is required on the DCE end of every serial link (the end where you
> plugged the cable in first). If both ends are missing it, or it's on the DTE end, the
> line protocol stays **down**. If unsure which end is DCE, set `clock rate 64000` on both
> ends — the DTE end simply ignores it. Harmless.

### STEP 5 — Configure R2 interfaces

**Where:** R2 -> CLI tab.

```
enable
configure terminal
hostname R2

interface GigabitEthernet0/0
 ip address 192.168.2.1 255.255.255.0
 no shutdown
exit

interface Serial0/0/0
 ip address 10.0.12.2 255.255.255.252
 no shutdown                ! DTE end here (R1 side was DCE) - no clock rate
exit

interface Serial0/0/1
 ip address 10.0.23.2 255.255.255.252
 clock rate 64000           ! DCE end toward R3
 no shutdown
exit
end
write memory
```

### STEP 6 — Configure R3 interfaces

**Where:** R3 -> CLI tab.

```
enable
configure terminal
hostname R3

interface GigabitEthernet0/0
 ip address 192.168.3.1 255.255.255.0
 no shutdown
exit

interface Serial0/0/0
 ip address 10.0.23.3 255.255.255.252
 no shutdown                ! DTE end (R2 was DCE)
exit

interface Serial0/0/1
 ip address 19.0.13.3 255.255.255.252
 no shutdown                ! DTE end (R1 was DCE)
exit
end
write memory
```

After Steps 4–6, verify each serial link is **up/up** before touching OSPF:
```
show ip interface brief
```
If a serial shows `up / down` (line up, protocol down) -> missing/mismatched
`clock rate` on the DCE end. Fix that first; OSPF can't form a neighbor over a down link.

### STEP 7 — Enable OSPF on R1

**Where:** R1 -> CLI tab.

OSPF advertises networks with `network <address> <wildcard> area <n>`. The wildcard is the
inverse mask. Put everything in **area 0** (the backbone) for a single-area lab.

```
enable
configure terminal
router ospf 1                 ! process ID (locally significant, 1 is fine)
 network 192.168.1.0 0.0.0.255 area 0     ! R1 LAN
 network 10.0.12.0   0.0.0.3   area 0     ! R1-R2 serial
 network 19.0.13.0   0.0.0.3   area 0     ! R1-R3 serial
exit
end
write memory
```

Wildcard cheat sheet: /24 -> `0.0.0.255`, /30 -> `0.0.0.3`.

### STEP 8 — Enable OSPF on R2

```
enable
configure terminal
router ospf 1
 network 192.168.2.0 0.0.0.255 area 0     ! R2 LAN
 network 10.0.12.0   0.0.0.3   area 0     ! R2-R1 serial
 network 10.0.23.0   0.0.0.3   area 0     ! R2-R3 serial
exit
end
write memory
```

As neighbors come up you'll see console messages like:
`%OSPF-5-ADJCHG: Process 1, Nbr 10.0.12.1 on Serial0/0/0 ... LOADING to FULL`
FULL = a working OSPF adjacency. That's what you want.

### STEP 9 — Enable OSPF on R3

```
enable
configure terminal
router ospf 1
 network 192.168.3.0 0.0.0.255 area 0     ! R3 LAN
 network 10.0.23.0   0.0.0.3   area 0     ! R3-R2 serial
 network 19.0.13.0   0.0.0.3   area 0     ! R3-R1 serial
exit
end
write memory
```

### STEP 10 — Set PC IPs

**Where:** Each PC -> Desktop -> IP Configuration -> Static.

Use the PC table above. Gateway = the local router's G0/0 (192.168.1.1 for PC1/PC2,
192.168.3.1 for PC3/PC4).

### STEP 11 — Verify OSPF learned the routes

**Where:** Any router -> CLI tab.

```
show ip ospf neighbor       ! each router should list its directly-connected neighbors, state FULL
show ip route ospf          ! OSPF-learned routes marked with "O"
show ip route               ! full table: C=connected, O=OSPF-learned remote networks
```

On R1 you should see **O** routes for 192.168.2.0, 192.168.3.0, and 10.0.23.0 —
networks R1 is not directly connected to but learned via OSPF. That's the whole point:
you never typed those routes, OSPF discovered them.

### STEP 12 — Verify end-to-end (the deliverable)

**Where:** PCs -> Command Prompt.

```
! from PC1 (192.168.1.10)
ping 192.168.1.1     ! own gateway
ping 192.168.2.1     ! R2 LAN gateway (across OSPF)
ping 192.168.3.10    ! PC3 on the far LAN  -> proves full end-to-end routing
tracert 192.168.3.10 ! shows the hop-by-hop path OSPF chose
```

`ping` between all PCs succeeding = OSPF is fully working. `tracert` reveals which path
was taken (OSPF picks lowest total cost; the direct R1-R3 link usually wins over going
through R2).

### Troubleshooting (OSPF-specific)

| Symptom | Cause / fix |
|---|---|
| Serial shows `up/down` | Missing/mismatched `clock rate` on the DCE end. Set it on the DCE (or both) ends. |
| No OSPF neighbor forms | Link is down, or the interface's network isn't in a `network ... area` statement, or mismatched area numbers, or mismatched subnet mask on the link. |
| Neighbor stuck in INIT/EXSTART | Duplicate router-id, or MTU mismatch (rare in PT). Check both ends' masks match. |
| Some LANs reachable, others not | A `network` statement is missing on one router. Every connected network must be advertised. |
| Wrong wildcard (used mask instead) | `network 192.168.1.0 255.255.255.0` is wrong — OSPF wants the WILDCARD `0.0.0.255`. |
| Ping to far LAN fails, routers ping fine | PC gateway wrong, or the far LAN network not advertised in OSPF. |
| Everything works then breaks on reload | Never saved. `write memory` on all three routers. |

### Key concepts to remember

- **OSPF is dynamic** — you advertise your *connected* networks, and routers exchange
  them automatically. Contrast with static routing where you hand-type every remote route.
- **`network <addr> <wildcard> area <n>`** does two jobs: it tells OSPF which interfaces
  to run on AND which networks to advertise. The wildcard is the inverse of the subnet mask.
- **Area 0** is the backbone; single-area labs put everything in area 0.
- **Process ID** (`router ospf 1`) is local to the router — it does NOT need to match
  between routers (unlike EIGRP's AS number).
- **`clock rate`** on serial DCE is a physical-layer requirement, unrelated to OSPF, but
  it must be right or OSPF has no link to run over.
- Adjacency reaching **FULL** state = success.