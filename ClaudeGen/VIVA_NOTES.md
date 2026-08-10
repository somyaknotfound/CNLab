# Viva Notes — Week 3 Exercise 2

Condensed from the resource material. Read the "Most likely questions" box at the end of
each section — those are the ones that actually get asked.

---

## Core concepts (asked across all five assignments)

| Term | One-line answer |
|---|---|
| **LAN** | Group of devices in one small area, all in the same network, communicating directly. |
| **Router** | Connects *different* networks and decides where a packet goes. |
| **Switch vs Router** | Switch = within one network (Layer 2, MAC). Router = between networks (Layer 3, IP). |
| **Subnet mask** | Says which part of the IP is the network and which is the host. `192.168.1.10 /255.255.255.0` → network `192.168.1.0`, host `10`. |
| **Default gateway** | The router IP a PC sends to when the destination is *outside* its own network. |
| **Routing** | Finding the path from one network to another. |
| **Routing table** | Each router's list of "where each network is" — like Google Maps. |
| **Next-hop** | IP of the *next router* that should receive the packet — never the final destination. |
| **`no shutdown`** | Router interfaces are administratively down by default. This turns them ON. |
| **`show ip interface brief`** | All interfaces + IPs + status. You want **up/up**. |
| **`show ip route`** | The routing table. `C`=connected, `S`=static, `O`=OSPF. |
| **Ping** | Can device A reach device B? Reply = yes. Timeout = problem. |
| **Traceroute / tracert** | Shows *every router* the packet passes through. |
| **Wildcard mask** | Inverse of subnet mask. `255.255.255.0` → `0.0.0.255`; `255.255.255.252` → `0.0.0.3`. |

**/30 network — always asked.** Mask `255.255.255.252`. Gives exactly **2 usable IPs**
(`.1` and `.2`, with `.3` as broadcast). Perfect for a point-to-point link between two
routers — no addresses wasted.

---

## 1 — Static Routing

**Objective:** connect two LANs across a serial WAN link using manually configured routes.

**What static routing means:** the administrator manually tells the router where each
remote network is. The router learns *nothing* automatically.

**The command:**
```
ip route <destination-network> <mask> <next-hop>
ip route 192.168.2.0 255.255.255.0 10.0.0.2
```

**Why serial and not Ethernet:** a serial link models a WAN/leased line between two
distant sites — only two endpoints, nothing else on the wire.

**Why `clock rate` exists:** a serial link has a **DCE** end (provides timing) and a
**DTE** end. Ethernet is multi-access and self-timing; serial needs one side to be the
master clock. In real life the ISP is DCE — in the lab one of your routers has to pretend.
Missing it → interface reads `up, line protocol down`.

> **Most likely questions**
> - *Why do you need a route on BOTH routers?* A ping needs a path there **and** a path
>   home. R2 without a return route drops the reply — looks identical to a broken link.
> - *What's the next-hop?* The neighbouring router's IP on the shared link, not the far LAN.
> - *Why /30?* Only 2 usable addresses — exactly what a point-to-point link needs.

---

## 2 — OSPF (Dynamic Routing)

**Objective:** routers discover each other and build routing tables automatically.

**How it actually works (say this, it's the real answer):**
1. Routers send **Hello packets** to discover neighbours.
2. Neighbours exchange their full **link-state database** — a map of every network each
   one is connected to, and at what cost.
3. State reaches **FULL** = databases fully synchronised. Every router now holds an
   *identical map* of the whole area.
4. Each router independently runs **SPF (Dijkstra's algorithm)** on that map to compute
   its own best path to every network, and installs the results as `O` routes.

**Link-state vs distance-vector:** OSPF is **link-state** — routers share a *topology
map*, not their routing tables (that's RIP/distance-vector).

**Commands:**
```
router ospf 1
 network 192.168.1.0 0.0.0.255 area 0
```
- `1` = **process ID**, locally significant — does **NOT** need to match other routers.
- `area 0` = **backbone area** — **DOES** need to match across all routers.
- The `network` statement does two jobs: picks which *interfaces* run OSPF, and
  advertises those networks.

**Cost** = OSPF's metric. Lowest total cost wins. Higher bandwidth → lower cost.
**Router ID** = unique 32-bit ID per OSPF router.

**Verify:** `show ip ospf neighbor` (want state **FULL**), `show ip route` (want `O` routes).

> **Most likely questions**
> - *What does FULL mean?* Not just "I see you" — the two routers have finished exchanging
>   their complete link-state databases.
> - *Process ID vs area — which must match?* Area must match. Process ID must not.
> - *Why is your `network` line a wildcard, not a subnet mask?* OSPF requires the inverse
>   mask. Using a subnet mask silently matches nothing and the adjacency never forms.
> - *How is this better than static?* Routes are learned, not typed; adapts automatically
>   if a link fails.

---

## 3 — NAT / PAT (Overload)

**Objective:** let a whole private network reach the internet through one public IP.

**Why NAT exists:** private addresses (`192.168.x.x`, `10.x.x.x`) are reserved and
reusable by anyone, so they **cannot be routed on the internet**. NAT rewrites the private
source address into a globally unique public one on the way out, and reverses it on the
way back.

**NAT vs PAT:**

| NAT | PAT (= NAT Overload) |
|---|---|
| One public IP per private IP | Many private IPs share ONE public IP |
| Burns public addresses | Distinguishes sessions by **port number** |
| Rarely used | What your home router does |

**The four config pieces (and all four are required):**
```
interface <inside>      → ip nat inside          ! mark private side
interface <outside>     → ip nat outside         ! mark public side
access-list 1 permit 192.168.10.0 0.0.0.255      ! WHICH addresses may translate
ip nat inside source list 1 interface <outside> overload
ip route 0.0.0.0 0.0.0.0 <outside>               ! default route to the internet
```

- The ACL here **is not filtering** — it's just a list of translation-eligible addresses.
- **`overload`** is the keyword that makes it PAT rather than 1:1 NAT.
- **Default route** `0.0.0.0 0.0.0.0` = "any destination I have no better route for."

**Verify:** `show ip nat translations` — same Inside Global IP, different ports per host.
That port difference *is* PAT.

```
Pro  Inside global      Inside local        Outside local     Outside global
tcp  203.0.113.2:1025   192.168.10.10:1025  203.0.113.10:80   203.0.113.10:80
tcp  203.0.113.2:1026   192.168.10.11:1026  203.0.113.10:80   203.0.113.10:80
```

> **Most likely questions**
> - *What does `overload` do?* Lets many hosts share one public IP by tracking source ports.
> - *Why is 203.0.113.x used?* Reserved documentation range for examples.
> - *Most forgotten step?* `ip nat inside` / `ip nat outside` on the interfaces — without
>   them nothing translates and no error appears.
> - *Advantages of NAT?* Conserves public IPs, basic security (inside hosts not directly
>   addressable), enables internet access for private networks.

---

## 4 — IPv6 Addressing and Routing

**Why IPv6:** IPv4 is 32-bit ≈ 4.3 billion addresses — exhausted. IPv6 is **128-bit**
≈ 340 undecillion.

| IPv4 | IPv6 |
|---|---|
| 32-bit | 128-bit |
| Decimal, dots | **Hexadecimal, colons** |
| `192.168.1.10` | `2001:DB8:1:1::10` |
| NAT commonly needed | NAT generally not needed |

**Structure:** 8 groups of 4 hex digits. Each group = a **hextet**.
Hex = `0-9` then `A`=10, `B`=11, `C`=12, `D`=13, `E`=14, `F`=15.

**Compression:** `::` replaces consecutive groups of zeros. Usable **only once** per
address (otherwise ambiguous how many zeros go on each side).
`2001:DB8:1:1:0000:0000:0000:0010` → `2001:DB8:1:1::10`

**Prefix length** `/64` = first 64 bits are the network (IPv6's version of a subnet mask).

**Address types:**

| Type | Example | Use |
|---|---|---|
| Global Unicast | `2001:DB8:1:1::10` | Internet-routable — **used in this lab** |
| Link-Local | `FE80::1` | Local segment only; **auto-created on every interface** |
| Loopback | `::1` | The device itself (= `127.0.0.1`) |
| Multicast | `FF02::1` | One-to-many |
| Unspecified | `::` | No address |

**Commands:**
```
ipv6 unicast-routing                              ! ENABLE FORWARDING — see below
ipv6 address 2001:DB8:1:1::1/64                   ! note: prefix attached with /
ipv6 route 2001:DB8:2:1::/64 2001:DB8:0:0::2      ! static route
show ipv6 route / show ipv6 interface brief
```

> **`ipv6 unicast-routing` is the #1 exam answer.** Cisco routers do **not** forward IPv6
> by default. Without it a router accepts IPv6 addresses and answers pings to itself, but
> forwards nothing between networks — everything looks configured and nothing works.

> **Most likely questions**
> - *Why was IPv6 introduced?* IPv4 address exhaustion.
> - *What does `::` mean and how often can you use it?* Compresses consecutive zero
>   groups; once per address.
> - *What's `FE80::`?* Link-local — automatic, local segment only, never configured by hand.
> - *Other IPv6 advantages?* Huge space, built-in IPsec, efficient routing, SLAAC
>   auto-configuration, no NAT needed.

---

## 5 — Access Control Lists

**Objective:** block the Students LAN from the Server while Faculty keeps access.

**What an ACL is:** a top-down list of permit/deny rules — a security guard at the router
deciding which packets pass. This is **packet filtering**.

**Standard vs Extended — know this cold:**

| | Standard | Extended |
|---|---|---|
| Number range | **1–99** | **100–199** |
| Matches on | **Source only** | **Source AND destination** (+ protocol, port) |
| Values after protocol | 2 | **4** |
| Place it | Close to **destination** | Close to **source** |

*Why the placement differs:* a standard ACL only knows the source, so placing it near the
source would block that host from reaching **everything**. An extended ACL knows the
destination too, so it can be placed early and drop unwanted traffic at the first hop.

**The config:**
```
access-list 100 deny ip 192.168.10.0 0.0.0.255 host 192.168.30.10
access-list 100 permit ip any any

interface g0/0
 ip access-group 100 in
```

Reading rule 1: ACL `100` → `deny` → `ip` (all IP traffic) → source `192.168.10.0/24`
(Students) → destination `host 192.168.30.10` (only the Server).

**`host X`** is shorthand for "exactly this one address" (equivalent to `X 0.0.0.0`).

**Three rules that decide whether an ACL works:**
1. **Order matters** — read top-down, stops at first match. A broad permit above your deny
   makes the deny unreachable.
2. **Implicit deny** — every ACL ends with an invisible `deny any`. Without an explicit
   `permit ip any any`, you block *everything*, not just your target.
3. **Direction & placement** — `in` filters traffic entering the interface, `out` filters
   traffic leaving. Wrong direction = silently does nothing.

**Note:** Faculty needs **no rule of its own** — it's allowed by the trailing
`permit ip any any`, because the deny above only matches Students-sourced traffic.

**Verify:** `show access-lists` (match counters prove the deny fired), `show running-config`.

> **Most likely questions**
> - *Standard vs extended?* Source-only vs source+destination; 1–99 vs 100–199.
> - *Why `permit ip any any` at the end?* Implicit deny would otherwise block all traffic.
> - *Where do you apply it and why?* Inbound on the Students interface — extended ACLs go
>   close to the source so unwanted traffic is dropped at the first hop.
> - *How do you know it worked?* Students ping to server FAILS, Students→Faculty still
>   SUCCEEDS (proves it's selective), Faculty→Server SUCCEEDS. Plus match counters.
> - *What does a blocked ping return?* "Destination host unreachable" **from the router's
>   own interface** — that's the ACL refusing to forward, not a routing failure.

---

## Quick command reference

| Purpose | Command |
|---|---|
| Find real interface names | `show ip interface brief` |
| Enable an interface | `no shutdown` |
| Serial DCE timing | `clock rate 64000` |
| Check DCE or DTE end | `show controllers serial 0/1/0` |
| Static route | `ip route <net> <mask> <next-hop>` |
| Default route | `ip route 0.0.0.0 0.0.0.0 <next-hop>` |
| Start OSPF | `router ospf 1` → `network <net> <wildcard> area 0` |
| OSPF adjacencies | `show ip ospf neighbor` |
| Mark NAT interfaces | `ip nat inside` / `ip nat outside` |
| Enable PAT | `ip nat inside source list 1 interface <out> overload` |
| NAT table | `show ip nat translations` |
| Enable IPv6 forwarding | `ipv6 unicast-routing` |
| IPv6 address | `ipv6 address <addr>/<prefix>` |
| IPv6 static route | `ipv6 route <prefix>/<len> <next-hop>` |
| Create ACL | `access-list 100 deny ip <src> <wc> <dst> <wc>` |
| Apply ACL | `ip access-group 100 in` |
| Check ACL + hit counts | `show access-lists` |
| Save | `write memory` (or `copy running-config startup-config`) |

---

## Six things that trip people up in the lab

1. **Interface names differ by router model.** ISR 4321 uses `GigabitEthernet0/0/0`, not
   `G0/0`. Always run `show ip interface brief` first — and separately on *each* router,
   they don't always match.
2. **Serial ports don't exist until you fit a NIM-2T** (Physical tab, router powered OFF).
3. **`administratively down` ≠ `down/down`.** First = missing `no shutdown` (config
   problem). Second = enabled but no partner (cabling problem, or far end not configured).
4. **`vlan 30` is rejected on a router** — routers have no VLAN database, that's a switch
   command.
5. **Extended ACL needs FOUR values** after the protocol. Coming from the NAT assignment's
   standard ACL (two values) causes `% Incomplete command.`
6. **Writing an ACL and applying it are separate steps.** An unapplied ACL is inert and
   gives no warning.

---

## Golden rule for every assignment

**Build → Verify → Secure.** Confirm full connectivity works *before* adding any ACL or
filtering. If you apply security on top of a network that was already broken, a failed
ping tells you nothing about which layer caused it.
