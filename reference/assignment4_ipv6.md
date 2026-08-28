# Assignment 4 — IPv6 Addressing and Routing

**Objective:** Configure IPv6 on routers and enable end-to-end IPv6 communication.

---

## Topology at a glance

```
                    S0/0/0                    S0/0/0
       2001:DB8:0:0::1/64 .------------. 2001:DB8:0:0::2/64
                        R1                R2
                      G0/0              G0/0
          2001:DB8:1:1::1/64      2001:DB8:2:1::1/64
                        |                  |
                       SW1                SW2
                      /    \              /    \
                   PC1     PC2         PC3     PC4
     2001:DB8:1:1::10/64  ::11/64   2001:DB8:2:1::10/64  ::11/64
```

### Addressing plan

| Link / LAN | Prefix | Interface(s) & Address |
|---|---|---|
| R1 <-> R2 (serial) | 2001:DB8:0:0::/64 | R1 S0/0/0 = 2001:DB8:0:0::1/64 · R2 S0/0/0 = 2001:DB8:0:0::2/64 |
| R1 LAN | 2001:DB8:1:1::/64 | R1 G0/0 = 2001:DB8:1:1::1/64 |
| R2 LAN | 2001:DB8:2:1::/64 | R2 G0/0 = 2001:DB8:2:1::1/64 |

PCs (gateway = their router's G0/0 link-local, or the global address below):
| PC | IPv6 Address | Prefix Length | Gateway |
|---|---|---|---|
| PC1 | 2001:DB8:1:1::10 | /64 | 2001:DB8:1:1::1 |
| PC2 | 2001:DB8:1:1::11 | /64 | 2001:DB8:1:1::1 |
| PC3 | 2001:DB8:2:1::10 | /64 | 2001:DB8:2:1::1 |
| PC4 | 2001:DB8:2:1::11 | /64 | 2001:DB8:2:1::1 |

---

## STEP 1 — Place the devices

**Where:** Device palette (bottom-left).

- 2 **Routers** — **ISR 4321** (needs **NIM-2T** for serial). Rename **R1, R2**.
- 2 **2960-24TT switches** — **SW1, SW2**.
- 4 **PCs** — PC1, PC2 on SW1 (R1's LAN); PC3, PC4 on SW2 (R2's LAN).

> Add the serial module to both routers first: **Physical** tab -> power OFF -> drag
> **NIM-2T** into a slot -> power ON. One card gives two serial ports
> (e.g. Serial0/1/0 and Serial0/1/1), which is more than enough for this assignment.

---

## STEP 2 — Cable everything

**Where:** Connections -> **Automatic** for LAN links; **Serial DCE** for the router link.

- R1 LAN interface -> SW1 -> PC1, PC2. R2 LAN interface -> SW2 -> PC3, PC4.
- R1 serial <-> R2 serial with the **Serial DCE** cable. The end plugged in FIRST is
  the **DCE** end and needs a `clock rate`.

> **Confirmed in lab: the router-to-router link MUST be serial, not Gigabit.** It is easy
> to cable R1 to R2 with a copper cable between their spare Gig ports — it goes green
> immediately and looks correct, which makes it very convincing. But the handout
> specifies a serial WAN link, and using Gig quietly changes the exercise (no DCE/DTE,
> no clock rate, none of the point-to-point WAN concept the assignment is teaching).
> If you did this by mistake: delete the cable, then on BOTH routers
> `interface <the-gig-port>` -> `no ipv6 address` -> `shutdown`, then re-cable with the
> explicit **Serial DCE** cable.

> **Confirmed in lab: a router can have a NIM-2T fitted with no cable attached to it at
> all, and `show ip interface brief` will not tell you that.** A serial port with no
> cable and a serial port whose far end isn't configured yet BOTH read `down/down`. To
> tell them apart, run `show controllers serial 0/1/0` — if it says
> **"No serial cable attached"**, the port is genuinely unconnected and no amount of
> configuration will help. Note the command needs a space: `show controllers serial 0/1/0`,
> not `show controllers Serial0/1/0` (the latter is rejected as invalid input).

---

## STEP 3 — Enable IPv6 routing (both routers)

IPv6 forwarding between interfaces is **off by default** — this single command is easy
to forget and is the #1 reason "everything is configured but nothing pings."

```
enable
configure terminal
ipv6 unicast-routing
```
Run this on **both** R1 and R2.

---

## STEP 4 — Configure R1 interfaces

Confirm real interface names first with `show ip interface brief` — on ISR 4321 the LAN
port is **GigabitEthernet0/0/0** (not G0/0) and the serial is typically **Serial0/1/0**.

```
hostname R1

interface GigabitEthernet0/0/0
 ipv6 address 2001:DB8:1:1::1/64
 no shutdown
exit

interface Serial0/1/0
 ipv6 address 2001:DB8:0:0::1/64
 clock rate 64000        ! ONLY on the DCE end of the cable
 no shutdown
exit
end
write memory
```

> **`show ip interface brief` shows "unassigned" for every interface in this assignment —
> that is normal, not a fault.** That command only reports IPv4 addressing, and this is a
> pure IPv6 build. Use `show ipv6 interface brief` to actually see your addresses. Keep
> using the IPv4 version only to check up/down status and discover interface names.

---

## STEP 5 — Configure R2 interfaces

R2's interface names are NOT guaranteed to match R1's — check with
`show ip interface brief` on R2 specifically before typing.

```
enable
configure terminal
ipv6 unicast-routing
hostname R2

interface GigabitEthernet0/0/0
 ipv6 address 2001:DB8:2:1::1/64
 no shutdown
exit

interface Serial0/1/0
 ipv6 address 2001:DB8:0:0::2/64
 no shutdown             ! DTE end here (R1 side was DCE) - no clock rate
exit
end
write memory
```

Verify the serial link is up before adding routes:
```
show ipv6 interface brief
```

> **`administratively down` vs plain `down/down` tells you which problem you have.**
> `administratively down` = the interface is missing `no shutdown` (a config problem).
> Plain `down/down` = the interface is enabled but sees no partner (a cabling problem —
> either no cable, or the far end isn't configured/up yet). Confirmed in lab: R2's LAN
> interface read `down/down` purely because the cable to SW2 had never been drawn.

---

## STEP 6 — Configure static IPv6 routes

This lab uses static IPv6 routing (same idea as Assignment 1, IPv6 syntax). Each router
needs a route to the LAN it's not directly connected to.

**On R1:**
```
ipv6 route 2001:DB8:2:1::/64 2001:DB8:0:0::2
```

**On R2:**
```
ipv6 route 2001:DB8:1:1::/64 2001:DB8:0:0::1
```

```
end
write memory
```

Verify:
```
show ipv6 route static      ! routes marked "S"
show ipv6 route             ! C = connected, S = static
```

> **Confirmed in lab — check BOTH routers have an `S` entry, not just one.** The exact
> failure seen: R1's table had 6 entries including `S 2001:DB8:2:1::/64`, while R2's had
> only 5 with no `S` line at all. R1 could send traffic to R2's LAN perfectly, but R2 had
> no route home, so every ping timed out. Same lesson as Assignment 1 — a ping needs a
> path there AND a path back. Count the entries: with both static routes in place, each
> router should show **6 entries**.

> **Comparing the two tables side by side is the fastest way to spot this.** If one
> router has more entries than the other, the one with fewer is missing its static route.

---

## STEP 7 — Set PC IPv6 addresses

**Where:** Each PC -> Desktop -> IP Configuration -> select **Static** under IPv6.
The IPv6 fields sit **below** the IPv4 fields on the same panel — scroll down if you
don't see them.

Use the PC table above. PC1/PC2 gateway = 2001:DB8:1:1::1, PC3/PC4 gateway =
2001:DB8:2:1::1. Prefix length = **64** for all.

> **CONFIRMED IN LAB — the single most time-wasting bug in this assignment: `2001:DB8`
> vs `2001:D88`.** These look nearly identical on screen (D-B-eight vs D-eight-eight) but
> are completely different networks. What happened: the routers got configured with
> `2001:D88:...` while the PCs were correctly set to `2001:DB8:...`. Every routing table
> looked perfect, both static routes were present, all interfaces were up — and nothing
> pinged, because the PCs weren't on the same network as their own gateways.
>
> **`2001:DB8::/32` is the correct value** — it's the officially reserved IPv6
> documentation prefix, which is why every textbook and diagram uses it. `2001:D88::` is
> a different, real address block.
>
> After configuring everything, run `show ipv6 route` on both routers and read each
> prefix character by character. If you spot `D88` anywhere, fix it before troubleshooting
> anything else.

> **Fixing a wrong IPv6 address needs an explicit `no ipv6 address` first.** Unlike IPv4
> where retyping `ip address` replaces the old one, an interface can hold MULTIPLE IPv6
> addresses at once — so a second `ipv6 address` command ADDS rather than replaces,
> leaving both the wrong and right prefixes live simultaneously. To correct one:
> ```
> interface GigabitEthernet0/0/0
>  no ipv6 address 2001:D88:1:1::1/64     ! remove the wrong one explicitly
>  ipv6 address 2001:DB8:1:1::1/64
> ```
> Static routes behave the same way — `no ipv6 route <old-prefix> <old-next-hop>` before
> adding the corrected one.

---

## STEP 8 — Test end-to-end IPv6 connectivity (the deliverable)

**Where:** PCs -> Command Prompt.

```
! from PC1 (2001:DB8:1:1::10)
ping 2001:DB8:1:1::1        ! own gateway
ping 2001:DB8:2:1::1        ! R2's LAN gateway, across the static route
ping 2001:DB8:2:1::10       ! PC3 on the far LAN -> proves full end-to-end IPv6 routing
```

All pings succeeding = IPv6 addressing, routing, and forwarding are all correctly
configured.

---

## Troubleshooting (IPv6-specific)

| Symptom | Cause / fix |
|---|---|
| Gateway pings fine, far PC times out, routing tables look perfect | **Check for `DB8` vs `D88` mismatch** between routers and PCs. Confirmed cause in lab. Read every prefix character by character in `show ipv6 route`. |
| Own gateway pings OK, everything beyond fails | Compare `show ipv6 route` entry counts on both routers — one is probably missing its `S` static route. Both need 6 entries. |
| Serial reads `down/down` and config looks right | Run `show controllers serial 0/1/0`. "No serial cable attached" means the port genuinely has no cable — it was never drawn, or landed on a different port. |
| `show controllers Serial0/1/0` rejected as invalid | Needs a space: `show controllers serial 0/1/0`. |
| Interface reads `administratively down` | Missing `no shutdown` (config problem), as opposed to plain `down/down` which is a cabling problem. |
| `show ip interface brief` shows all interfaces "unassigned" | Normal for this assignment — that command only reports IPv4. Use `show ipv6 interface brief`. |
| Corrected an IPv6 address but old behaviour persists | IPv6 interfaces hold multiple addresses; a new `ipv6 address` adds rather than replaces. Use `no ipv6 address <old>` explicitly first. |
| Pings fail everywhere, even to own gateway | `ipv6 unicast-routing` not enabled, or `no shutdown` missing on the interface. |
| Serial shows `up/down` | Missing/mismatched `clock rate` on the DCE end (same as IPv4). |
| Own LAN pings fine, far LAN doesn't | `ipv6 route` missing or has a typo in the prefix/next-hop on one router. |
| Typo'd prefix length (e.g. /48 instead of /64) | Mismatched prefix lengths between router and PC break on-link detection — keep everything /64 in this lab. |
| PC has no IPv6 or only a link-local (fe80::) address | Static IPv6 not actually selected/applied on the PC's IP Configuration page. |
| Route configured but not in table | Next-hop address unreachable — check the serial interface is up first. |

---

## Key concepts to remember

- **`ipv6 unicast-routing`** is required globally on every router that will forward IPv6
  packets between interfaces — there is no IPv4 equivalent step, and it's the most
  commonly forgotten command in this lab.
- IPv6 addresses are configured per interface with `ipv6 address <addr>/<prefix-length>`
  — no separate mask, the prefix length is part of the address line.
- **Static IPv6 routing** mirrors IPv4 static routing:
  `ipv6 route <dest-prefix>/<len> <next-hop-address>`.
- `show ipv6 interface brief` and `show ipv6 route` are the IPv6 equivalents of
  `show ip interface brief` and `show ip route`.
- Every router still needs `no shutdown` and (on the DCE end) `clock rate` — physical/
  data-link requirements don't change just because the layer-3 protocol is IPv6.
- **An IPv6 interface can hold multiple addresses simultaneously**, so `ipv6 address`
  ADDS rather than replaces. This is a real difference from IPv4's `ip address`, and it
  means correcting a mistake requires an explicit `no ipv6 address <old>` first.
- **`2001:DB8::/32` is the reserved documentation prefix** — that's why it appears in
  every textbook example. Worth knowing if asked why the lab uses that specific range.
- The `FF00::/8 via Null0` entry in every routing table is standard IPv6 multicast — it
  appears automatically and is not something you configured or need to worry about.
- Link-local `FE80::` addresses also appear automatically on every IPv6 interface and are
  never configured by hand. A PC showing ONLY a link-local address means its static IPv6
  never actually committed.
