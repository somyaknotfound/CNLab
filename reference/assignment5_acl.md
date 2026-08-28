# Assignment 5 — Access Control Lists (ACLs)

**Objective:** Restrict access between networks using ACLs — Students LAN must be
blocked from the Server LAN, while Faculty LAN keeps full access, and all other traffic
is unaffected.

---

## Topology at a glance

```
        Students LAN                                Faculty LAN
       192.168.10.0/24                              192.168.20.0/24
                         G0/0            G0/1
                     192.168.10.1    192.168.20.1
                             \          /
                              \        /
                                  R1
                                  |
                                 G0/2
                             192.168.30.1
                                  |
                              Server LAN
                            192.168.30.0/24
                                  |
                                Server
                             192.168.30.10

   Students side:  SW-S -- PC-S1 (192.168.10.10), PC-S2 (192.168.10.11)
   Faculty side:   SW-F -- PC-F1 (192.168.20.10)
```

### Addressing plan

| Segment | Network | Interface & IP |
|---|---|---|
| Students LAN | 192.168.10.0/24 | R1 G0/0/0 = 192.168.10.1 |
| Faculty LAN | 192.168.20.0/24 | R1 G0/0/1 = 192.168.20.1 |
| Server LAN | 192.168.30.0/24 | R1 **Vlan30** = 192.168.30.1 (see STEP 1b) |

> **Confirmed in lab: this assignment needs THREE LAN interfaces, and an ISR 4321 only
> has TWO** (`GigabitEthernet0/0/0` and `0/0/1`). The Students and Faculty LANs consume
> both, leaving nothing for the Server LAN — you will hit "cannot connect to that port"
> when you try to cable the server. STEP 1b below covers adding the third interface.

| Host | IP | Mask | Gateway |
|---|---|---|---|
| PC-S1 (Students) | 192.168.10.10 | 255.255.255.0 | 192.168.10.1 |
| PC-S2 (Students) | 192.168.10.11 | 255.255.255.0 | 192.168.10.1 |
| PC-F1 (Faculty) | 192.168.20.10 | 255.255.255.0 | 192.168.20.1 |
| Server | 192.168.30.10 | 255.255.255.0 | 192.168.30.1 |

---

## STEP 1 — Place the devices

**Where:** Device palette (bottom-left).

- 1 **Router** — **ISR 4321**, rename **R1**.
- 2 **2960-24TT switches** — **SW-S** (Students), **SW-F** (Faculty).
- 3 **PCs** — PC-S1, PC-S2 (Students), PC-F1 (Faculty).
- 1 **Server-PT** — Server, directly on the Server LAN.

---

## STEP 2 — Cable everything

**Where:** Connections -> **Automatic**.

- PC-S1, PC-S2 -> SW-S -> R1 G0/0/0.
- PC-F1 -> SW-F -> R1 G0/0/1.
- Server -> the new module port from STEP 1b (see below) — you cannot cable it until
  that module is fitted.

---

## STEP 1b — Add a third LAN interface (do this BEFORE cabling the server)

**Where:** R1 -> **Physical** tab.

Power the router **OFF** (click the switch on the chassis), drag **`NIM-ES2-4`** into an
empty slot, then power back **ON**.

> **Which module?** Of the options offered, `NIM-ES2-4` is the 4-port Ethernet switch
> module and the only usable one here. `NIM-2T` is serial. `NIM-Cover` is a blank filler
> panel. `GLC-GE-100FX` and `GLC-LH-SMD` are **fiber** SFP transceivers — they need fiber
> cabling and will not accept a copper connection to a Server-PT.

After powering on, the new ports appear as `GigabitEthernet0/1/0` through `0/1/3`.

> **Confirmed in lab: these are SWITCHPORTS, not routed interfaces.** Trying
> `ip address 192.168.30.1 255.255.255.0` directly on `G0/1/0` is rejected with
> `% Invalid input detected`. You must instead leave the physical port as a Layer 2
> access port and put the IP address on a **VLAN interface** — see STEP 3.

---

## STEP 3 — Configure R1's interfaces

**Where:** R1 -> CLI tab. Confirm real names first with `show ip interface brief`.

```
enable
configure terminal
hostname R1

interface GigabitEthernet0/0/0
 ip address 192.168.10.1 255.255.255.0
 no shutdown
exit

interface GigabitEthernet0/0/1
 ip address 192.168.20.1 255.255.255.0
 no shutdown
exit
```

Now the Server LAN, via the switch module. Note there is **no `vlan 30` command** —
creating `interface Vlan30` directly is what brings the VLAN into existence:

```
interface GigabitEthernet0/1/0
 switchport mode access
 switchport access vlan 30
exit

interface Vlan30
 ip address 192.168.30.1 255.255.255.0
 no shutdown
exit
end
write memory
```

> **Confirmed in lab: `vlan 30` in global config is rejected on a router** with
> `% Invalid input detected`. Routers have no VLAN database — that command only exists on
> switches. This is the same trap as the earlier Packet Tracer lab set. Skip it entirely
> and go straight to `interface Vlan30`.

> **Fallback if `switchport access vlan 30` is also rejected:** use VLAN 1, which always
> exists. Leave `G0/1/0` on its default VLAN 1 membership and put the address on
> `interface Vlan1` instead. Functionally identical for this assignment — all you need is
> a Layer 3 interface owning 192.168.30.1.

Verify:
```
show ip interface brief
```
`Vlan30` must read **up/up** with 192.168.30.1. The physical `G0/1/0` will show
**unassigned** — that is correct, the IP lives on the VLAN interface, not the port.

---

## STEP 4 — Set PC and server IPs

**Where:** Each PC/Server -> Desktop -> IP Configuration -> Static.

Use the addressing table above — every host's gateway is the R1 interface on its own
subnet.

---

## STEP 5 — Verify base connectivity BEFORE applying any ACL

**Golden rule: build → verify → secure.** Confirm the network fully works with no
restrictions first, so any later failure is provably the ACL and not a wiring/IP mistake.

```
! from PC-S1
ping 192.168.10.1     ! own gateway
ping 192.168.30.10    ! server (should succeed — no ACL yet)
ping 192.168.20.10    ! PC-F1 (should succeed — no ACL yet)
```

All three should succeed. If not, fix connectivity before moving on.

---

## STEP 6 — Configure the extended ACL

**Extended ACL anatomy:**
```
access-list <100-199> {permit|deny} <proto> <src> <wildcard> <dst> <wildcard> [eq <port>]
```

Only ONE rule is actually needed: **deny Students -> Server, permit everything else.**
Because Faculty is never mentioned in a deny line, Faculty -> Server keeps working
through the implicit/explicit final permit — you do not need a separate Faculty rule.

```
enable
configure terminal
access-list 110 deny  ip 192.168.10.0 0.0.0.255 192.168.30.0 0.0.0.255
access-list 110 permit ip any any
```

- **Wildcard mask** `0.0.0.255` = match the whole /24 (inverse of 255.255.255.0).
- The `permit ip any any` line is **required** — every ACL ends with an invisible
  `deny any any`; without this line you'd block ALL Students traffic, not just to the
  Server LAN.
- Order matters: the deny must come BEFORE the permit, or the permit would match first
  and the deny would never be reached.

> **Confirmed in lab: `% Incomplete command.` on the deny line.** An extended ACL requires
> **four** values after the protocol — source, source-wildcard, destination,
> destination-wildcard. Stopping after `192.168.10.0 0.0.0.255` gives only the source
> pair, and IOS rejects it as incomplete.
>
> **This is the key difference from the standard ACL used in the NAT assignment.**
> Numbered lists **1–99 are standard** and match on source only:
> `access-list 1 permit 192.168.10.0 0.0.0.255` — two values, complete.
> Numbered lists **100–199 are extended** and require source AND destination — which is
> exactly why this assignment uses 110. If you have just come from the NAT exercise, the
> muscle memory from that shorter syntax is what causes this error.

### Reading the command, piece by piece

`access-list 110 deny ip 192.168.10.0 0.0.0.255 192.168.30.0 0.0.0.255`

| Part | Meaning |
|---|---|
| `access-list 110` | List number 110 — in the 100–199 range, so extended |
| `deny` | Drop packets that match |
| `ip` | Any IP protocol (not just TCP or ICMP) |
| `192.168.10.0 0.0.0.255` | **Source**: the whole Students /24 |
| `192.168.30.0 0.0.0.255` | **Destination**: the whole Server /24 |

---

## STEP 7 — Apply the ACL to the Students-facing interface

Apply it **inbound** on the Students-facing interface so it filters traffic as it arrives
from the Students LAN, before R1 routes it anywhere:

```
interface GigabitEthernet0/0/0
 ip access-group 110 in
exit
end
write memory
```

> **Writing an ACL and applying an ACL are two separate steps.** A list that exists in
> the config but was never attached with `ip access-group` does absolutely nothing, and
> produces no error or warning to tell you so. If your post-ACL pings all still succeed,
> this is the first thing to check.

> **Why inbound, and why on this interface — the design decision worth being able to
> defend in a viva:** extended ACLs go as close to the **source** as possible, so unwanted
> traffic is dropped at the first hop rather than carried across the network and discarded
> at the far end. `in` on the Students interface means R1 checks each packet the moment it
> arrives, before doing any routing work at all. Standard ACLs are the opposite — because
> they match on source only, placing them near the source would block that source from
> reaching *everything*, so they go close to the destination instead.

---

## STEP 8 — Verify (the deliverable)

**Where:** PCs -> Command Prompt.

```
! from PC-S1 or PC-S2 (Students)
ping 192.168.30.10    ! Server -> MUST FAIL
ping 192.168.20.10    ! PC-F1  -> should still SUCCEED (not blocked)

! from PC-F1 (Faculty)
ping 192.168.30.10    ! Server -> MUST SUCCEED
```

On R1:
```
show access-lists      ! match counters increment on the deny line when Students ping the server
show running-config    ! confirm ip access-group 110 in is applied to G0/0
```

- Students PC should **NOT** reach the Server. ✔
- Faculty PC should reach the Server. ✔
- All other communication (Students <-> Faculty, either side <-> gateway) unaffected. ✔

---

## Troubleshooting (ACL-specific)

| Symptom | Cause / fix |
|---|---|
| **`% Incomplete command.` on the deny line** | Extended ACLs need FOUR values after the protocol: source, source-wildcard, destination, destination-wildcard. You stopped after the source pair. Standard ACLs (1–99) take source only — don't carry that syntax over to a 100–199 list. |
| **Cannot cable the server — "cannot connect to that port"** | ISR 4321 has only two Gig ports and this assignment needs three LANs. Fit a `NIM-ES2-4` module (Physical tab, power OFF first). |
| **`ip address` rejected on the new module's port** | `NIM-ES2-4` ports are switchports, not routed interfaces. Put the address on `interface Vlan30` and make the physical port an access port in that VLAN. |
| **`vlan 30` rejected in global config** | Routers have no VLAN database — that command is switch-only. Create `interface Vlan30` directly instead; that brings the VLAN into existence. |
| Vlan30 shows down/down | The physical port isn't in that VLAN, or has no live cable. Check `switchport access vlan 30` was applied and the server is actually connected. |
| Students blocked from EVERYTHING, not just Server | Missing `permit ip any any` line — implicit deny-all at the end of every ACL. |
| ACL has no effect at all | Not applied to an interface (`ip access-group` missing), or applied in the wrong direction. Writing the list and applying it are two separate steps, and skipping the second produces no error. |
| Deny rule never triggers | A broad `permit` was placed above the `deny` — ACLs stop at the first match, so order the specific deny first. |
| Typo'd the ACL number | e.g. `access-list 110 deny ...` then `access-list 100 permit ip any any` by mistake — that permit sits on a different, unused list. List 110 now only has the deny + implicit deny-all, blocking everything. Fix: keep both lines on the SAME number. |
| Faculty also blocked from Server | Wildcard/network typo in the deny line accidentally matches Faculty's subnet too — double check `192.168.10.0 0.0.0.255` is exactly the Students network. |
| `show access-lists` shows 0 matches | ACL applied to the wrong interface, or applied `out` instead of `in`. |

---

## Key concepts to remember

- ACLs are evaluated **top-to-bottom, first match wins** — put specific denies before
  general permits.
- Every ACL has an **invisible final `deny any any`** — always end permissive ACLs with
  an explicit `permit ip any any` unless you intend to block everything else.
- Apply direction (`in`/`out`) and interface matter: `in` on the Students interface
  filters traffic as it enters from Students, which is the earliest and most efficient
  point to stop it.
- A single well-placed deny + a trailing permit-all is usually simpler and less
  error-prone than writing one rule per allowed pair.
- **Always verify the network works before applying ACLs**, and test again immediately
  after — `show access-lists` hit counters prove which line is actually catching traffic.
- **Standard (1–99) vs extended (100–199)** is the distinction most worth knowing cold:
  standard matches on **source only** and takes two values; extended matches on
  **source AND destination** and takes four. That difference dictates both the syntax and
  where you place the ACL — extended near the source, standard near the destination.
- **A blocked ping returns "Destination host unreachable" from the router's own
  interface**, not a timeout. That reply coming from your own gateway is the signature of
  an ACL drop rather than a routing failure — useful for telling the two apart quickly.
- **Writing an ACL and applying it are separate steps.** An unapplied ACL is inert and
  silent; there is no warning that you forgot `ip access-group`.

---

## Design decisions taken in this build (and why)

| Decision | Reasoning |
|---|---|
| Used `NIM-ES2-4` for the third LAN | Only module in the available list that provides usable copper Ethernet. The fiber SFPs can't take a copper cable to a Server-PT, and `NIM-2T` is serial. |
| Put the Server LAN on a VLAN interface | Forced by the hardware — `NIM-ES2-4` gives switchports, which cannot hold an IP directly. `interface Vlan30` is the Layer 3 interface that owns 192.168.30.1. |
| One deny + one permit, rather than a rule per pair | Faculty needs no rule of its own: it's permitted by the trailing `permit ip any any` because the deny above only matches traffic sourced from the Students subnet. Fewer lines, fewer ordering mistakes. |
| Applied inbound on the Students interface | Extended ACLs belong as close to the source as possible — drop unwanted traffic at the first hop instead of routing it across the network to discard it later. |
| Verified full connectivity before adding the ACL | If you filter on top of an already-broken network, a failed ping tells you nothing about which layer caused it. Establishing a known-good baseline first makes the ACL the only variable. |
