# Assignment 2 — Dynamic Routing using OSPF

**Objective:** Configure OSPF so three routers learn routes from each other automatically,
then verify end-to-end connectivity between all four PCs.

Every step tells you what to place, what to click, what to type, and how to verify it worked.

---

## Topology at a glance

```
                         R2
              serial  .------.  serial
        10.0.12.0/30 |      | 10.0.23.0/30
                   .-'      '-.
                  /            \
                R1 -----------  R3
                serial  10.0.13.0/30  serial
             (the R1-R3 link)
             G0/0/0            G0/0/0
       192.168.1.0/24    192.168.3.0/24
             |                  |
            SW1                SW3
          /     \            /      \
        PC1     PC2        PC3      PC4
```

R2 also has a LAN (192.168.2.0/24) hanging off its G0/0/0. The original handout doesn't
draw PCs under R2 — configuring the interface with `no shutdown` is enough to satisfy the
diagram; you don't need to attach a switch/PCs there unless you want extra test hosts.

> **Confirmed in lab: this is a full triangle (R1-R2, R2-R3, R1-R3 all directly cabled),
> matching the handout exactly.** Build it this way, not as a hub-and-spoke through R2
> only — the direct R1-R3 link is what produces the nice OSPF equal-cost-path result
> mentioned near the bottom of this doc.

> **Network used in practice was 10.0.13.0/30, not 19.0.13.0/30.** The original handout
> image is ambiguous/possibly a typo here. 10.0.13.0/30 is consistent with the other two
> links (10.0.12.0/30, 10.0.23.0/30) and is what was actually configured and verified
> working. Use 10.0.13.0/30 unless your instructor explicitly says otherwise.

### Addressing plan

| Link / LAN | Network | Interface(s) & IP |
|---|---|---|
| R1 <-> R2 (serial) | 10.0.12.0/30 | R1 = 10.0.12.1 · R2 = 10.0.12.2 |
| R2 <-> R3 (serial) | 10.0.23.0/30 | R2 = 10.0.23.1 · R3 = 10.0.23.2 |
| R1 <-> R3 (serial) | 10.0.13.0/30 | R1 = 10.0.13.1 · R3 = 10.0.13.2 |
| R1 LAN | 192.168.1.0/24 | R1 G0/0/0 = 192.168.1.1 |
| R2 LAN | 192.168.2.0/24 | R2 G0/0/0 = 192.168.2.1 |
| R3 LAN | 192.168.3.0/24 | R3 G0/0/0 = 192.168.3.1 |

**/30 refresher:** mask `255.255.255.252`, wildcard `0.0.0.3`, only 2 usable hosts —
perfect for point-to-point router links.

PCs (gateway = their router's G0/0):
| PC | IP | Mask | Gateway |
|---|---|---|---|
| PC1 | 192.168.1.10 | 255.255.255.0 | 192.168.1.1 |
| PC2 | 192.168.1.11 | 255.255.255.0 | 192.168.1.1 |
| PC3 | 192.168.3.10 | 255.255.255.0 | 192.168.3.1 |
| PC4 | 192.168.3.11 | 255.255.255.0 | 192.168.3.1 |

---

## STEP 1 — Place the devices

**Where:** Device palette (bottom-left).

- 3 **Routers** — model **ISR 4321** (or any router with WIC-2T serial support). Rename
  them **R1, R2, R3** (right-click -> Rename).
- 2–3 **2960-24TT switches** (SW1, SW2, SW3) — one per LAN that has PCs.
- **PCs** — PC1, PC2 on the R1 LAN; PC3, PC4 on the R3 LAN (add R2-LAN PCs if required).

> **Serial ports need a module.** Routers don't ship with serial interfaces by default.
> For each router: double-click -> **Physical** tab -> power OFF (click the switch on the
> chassis) -> drag a **NIM-2T** into an empty slot -> power ON. Each router in this
> assignment needs TWO serial links (the triangle), and a single NIM-2T provides two
> ports, so one card per router is enough.
>
> **Confirmed in lab: fitting two NIM-2T cards on one router gives FOUR serial
> interfaces (e.g. Serial0/1/0, 0/1/1, 0/2/0, 0/2/1), not two.** If you only need two
> links, one NIM-2T card is sufficient — don't add a second one, it just creates
> ambiguity about which of the four ports is actually cabled to which neighbor.

---

## STEP 2 — Cable everything

**Where:** Connections -> **Automatic** for LAN links; **Serial DCE** for router-to-router.

- **LAN links (copper):** R1 G0/0 -> SW1; SW1 -> PC1, PC2. Same for R3/SW3/PC3,PC4
  (and R2/SW2 if used). Automatic tool is fine here.
- **Serial links (router-to-router):** use the **Serial DCE** cable
  (Connections -> the cable icon that looks like a lightning/serial connector).
  - R1 <-> R2, R2 <-> R3, R1 <-> R3 — three serial cables total for the full triangle.
  - The end you attach FIRST becomes the **DCE** end and needs a **clock rate**
    (Packet Tracer marks the DCE end with a small clock symbol on the cable).

> **After cabling, confirm exactly which port goes to which neighbor before typing any
> config.** With a NIM-2T you'll have two (or four, with two cards) serial interfaces per
> router, and it is not safe to assume `Serial0/1/0` is "the first link you made" — hover
> the mouse directly over each serial cable on the canvas; a tooltip names both ends, e.g.
> `R1: Serial0/1/0 <--> R2: Serial0/1/0`. Do this for every serial cable on every router.

---

## STEP 3 — Discover interface names

**Where:** Each router -> CLI tab.

```
enable
show ip interface brief
```
Confirm the serial names and the LAN name. Substitute whatever appears in the Interface
column into the commands below. All serial/LAN interfaces will show
**administratively down** until you configure and `no shutdown` them.

> **Confirmed in lab: LAN interfaces on ISR 4321 are GigabitEthernet0/0/0 and
> GigabitEthernet0/0/1, not G0/0.** The commands below use `GigabitEthernet0/0/0` for
> this reason. Serial names vary by which NIM slot the card landed in and are NOT
> guaranteed to be the same across two identical routers — verify each router
> individually, exactly as you did in Assignment 1.
>
> **How to find the DCE end for real, rather than guessing:** after cabling and before
> configuring `clock rate`, run `show controllers <interface>` on the interface. The very
> first line reports either `DCE V.35, clock rate 64000` or `DTE V.35, no clock rate`.
> Whichever router reports DCE for that link is the one that needs `clock rate` typed on
> it. If you'd rather not check and just want it to work, setting `clock rate 64000` on
> both ends is harmless — the DTE side ignores it — but checking is more thorough and is
> good practice to be able to explain in a viva.

---

## STEP 4 — Configure R1 interfaces

**Where:** R1 -> CLI tab. Substitute your own confirmed interface names.

```
enable
configure terminal
hostname R1

interface GigabitEthernet0/0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown
exit

interface <R1-serial-to-R2>
 ip address 10.0.12.1 255.255.255.252
 clock rate 64000            ! ONLY on the DCE end of the cable — check with show controllers
 no shutdown
exit

interface <R1-serial-to-R3>
 ip address 10.0.13.1 255.255.255.252
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

---

## STEP 5 — Configure R2 interfaces

**Where:** R2 -> CLI tab. Hover its cables first — R2's serial ports are not guaranteed
to match R1's naming even on identical hardware.

```
enable
configure terminal
hostname R2

interface GigabitEthernet0/0/0
 ip address 192.168.2.1 255.255.255.0
 no shutdown
exit

interface <R2-serial-to-R1>
 ip address 10.0.12.2 255.255.255.252
 no shutdown                ! only add clock rate if show controllers reports DCE here
exit

interface <R2-serial-to-R3>
 ip address 10.0.23.1 255.255.255.252
 clock rate 64000           ! only if this end is DCE
 no shutdown
exit
end
write memory
```

---

## STEP 6 — Configure R3 interfaces

**Where:** R3 -> CLI tab. Hover its cables first, same as R2.

```
enable
configure terminal
hostname R3

interface GigabitEthernet0/0/0
 ip address 192.168.3.1 255.255.255.0
 no shutdown
exit

interface <R3-serial-to-R2>
 ip address 10.0.23.2 255.255.255.252
 no shutdown                ! only add clock rate if this end is DCE
exit

interface <R3-serial-to-R1>
 ip address 10.0.13.2 255.255.255.252
 no shutdown                ! only add clock rate if this end is DCE
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

> **Confirmed in lab: it's completely normal for a serial link to show `down` on BOTH
> routers even when correctly addressed and `no shutdown`, if the far-end router hasn't
> been configured yet.** A serial line protocol only comes up once both ends agree —
> don't treat a down link as broken while you're still mid-way through Steps 4-6. Re-check
> `show ip interface brief` after every router is done, not after just one.

---

## STEP 7 — Enable OSPF on R1

**Where:** R1 -> CLI tab.

OSPF advertises networks with `network <address> <wildcard> area <n>`. The wildcard is the
inverse mask. Put everything in **area 0** (the backbone) for a single-area lab.

```
enable
configure terminal
router ospf 1                 ! process ID (locally significant, 1 is fine)
 network 192.168.1.0 0.0.0.255 area 0     ! R1 LAN
 network 10.0.12.0   0.0.0.3   area 0     ! R1-R2 serial
 network 10.0.13.0   0.0.0.3   area 0     ! R1-R3 serial
exit
end
write memory
```

Wildcard cheat sheet: /24 -> `0.0.0.255`, /30 -> `0.0.0.3`.

---

## STEP 8 — Enable OSPF on R2

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

---

## STEP 9 — Enable OSPF on R3

```
enable
configure terminal
router ospf 1
 network 192.168.3.0 0.0.0.255 area 0     ! R3 LAN
 network 10.0.23.0   0.0.0.3   area 0     ! R3-R2 serial
 network 10.0.13.0   0.0.0.3   area 0     ! R3-R1 serial
exit
end
write memory
```

---

## STEP 10 — Set PC IPs

**Where:** Each PC -> Desktop -> IP Configuration -> Static.

Use the PC table above. Gateway = the local router's G0/0 (192.168.1.1 for PC1/PC2,
192.168.3.1 for PC3/PC4).

---

## STEP 11 — Verify OSPF learned the routes

**Where:** Any router -> CLI tab.

```
show ip ospf neighbor       ! each router should list its directly-connected neighbors, state FULL
show ip route ospf          ! OSPF-learned routes marked with "O"
show ip route               ! full table: C=connected, O=OSPF-learned remote networks
```

On R1 you should see **O** routes for 192.168.2.0, 192.168.3.0, and 10.0.23.0 —
networks R1 is not directly connected to but learned via OSPF. That's the whole point:
you never typed those routes, OSPF discovered them.

> **Confirmed working output, for reference — this is what success looks like:**
> ```
> R1#show ip ospf neighbor
> Neighbor ID     Pri   State           Dead Time   Address         Interface
> 192.168.2.1     0     FULL/  -        00:00:38    10.0.12.2       Serial0/1/0
> 192.168.3.1     0     FULL/  -        00:00:38    10.0.13.2       Serial0/1/1
> ```
> Both neighbors FULL confirms R1's adjacencies with R2 and R3 are both up and the
> link-state databases have fully synchronized — FULL means more than "I see you",
> it means the two routers have finished exchanging their complete topology info.
>
> Also worth noticing in `show ip route`: `10.0.23.0/30` (the R2-R3 link itself) can
> appear reachable via TWO equal-cost paths at once — through R2 *and* through R3,
> both cost 128. That only happens because R1 is directly connected to both of them
> in the full triangle; OSPF installs and load-balances across both. It's a nice piece
> of evidence that the triangle topology (not hub-and-spoke) is actually working as
> intended.

---

## STEP 12 — Verify end-to-end (the deliverable)

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

---

## Troubleshooting (OSPF-specific)

| Symptom | Cause / fix |
|---|---|
| Serial shows `up/down` | Missing/mismatched `clock rate` on the DCE end. Set it on the DCE (or both) ends. |
| No OSPF neighbor forms | Link is down, or the interface's network isn't in a `network ... area` statement, or mismatched area numbers, or mismatched subnet mask on the link. |
| Neighbor stuck in INIT/EXSTART | Duplicate router-id, or MTU mismatch (rare in PT). Check both ends' masks match. |
| Some LANs reachable, others not | A `network` statement is missing on one router. Every connected network must be advertised. |
| Wrong wildcard (used mask instead) | `network 192.168.1.0 255.255.255.0` is wrong — OSPF wants the WILDCARD `0.0.0.255`. |
| Ping to far LAN fails, routers ping fine | PC gateway wrong, or the far LAN network not advertised in OSPF. |
| Everything works then breaks on reload | Never saved. `write memory` on all three routers. |

---

## Key concepts to remember

**What OSPF actually is, mechanically:** routers first say hello to every directly
connected neighbor over each OSPF-enabled interface. If they agree to become neighbors,
they don't gossip routing tables at each other the way older protocols like RIP do —
instead they exchange their **complete link-state database**: a map of "here is every
network I'm connected to, and at what cost." Once that exchange finishes, the adjacency
reaches **FULL**, and every router in the area is holding an identical copy of the whole
topology map. From that shared map, each router independently runs a shortest-path
calculation (Dijkstra's algorithm) to work out its own best route to every network, and
installs the results into its routing table marked `O`. That's why an `O` route appearing
for a network you never configured is real proof OSPF worked — the router computed that
path itself from the flooded topology data, nobody told it directly.

- **OSPF is dynamic** — you advertise your *connected* networks, and routers exchange
  them automatically. Contrast with static routing where you hand-type every remote route.
- **`network <addr> <wildcard> area <n>`** does two jobs: it tells OSPF which interfaces
  to run on AND which networks to advertise. The wildcard is the inverse of the subnet mask.
- **Area 0** is the backbone; single-area labs put everything in area 0.
- **Process ID** (`router ospf 1`) is local to the router — it does NOT need to match
  between routers (unlike EIGRP's AS number). The **area number** DOES need to match.
- **`clock rate`** on serial DCE is a physical-layer requirement, unrelated to OSPF, but
  it must be right or OSPF has no link to run over.
- Adjacency reaching **FULL** state = success. `LOADING` means the database exchange is
  still in progress; wait a few seconds.
- A full-mesh triangle (vs. hub-and-spoke) lets OSPF discover equal-cost alternate paths
  between routers, which is worth pointing out if asked to explain your topology choice.
