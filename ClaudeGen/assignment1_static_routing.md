# Assignment 1 — Static Routing Between Two LANs

**Objective:** Connect two LANs using static routing and verify end-to-end connectivity.

---

## Topology at a glance

```
        S0/0/0                    S0/0/0
   10.0.0.1/30 .------.------. 10.0.0.2/30
              R1        10.0.0.0/30       R2
            G0/0                        G0/0
      192.168.1.1                 192.168.2.1
     LAN-A 192.168.1.0/24    LAN-B 192.168.2.0/24
            |                        |
           SW1                      SW2
          /    \                   /    \
      PC-A1   PC-A2            PC-B1   PC-B2
    .1.10     .1.11            .2.10    .2.11
```

### Addressing plan

| Link / LAN | Network | Interface(s) & IP |
|---|---|---|
| R1 <-> R2 (serial) | 10.0.0.0/30 | R1 S0/0/0 = 10.0.0.1 · R2 S0/0/0 = 10.0.0.2 |
| LAN-A | 192.168.1.0/24 | R1 G0/0 = 192.168.1.1 |
| LAN-B | 192.168.2.0/24 | R2 G0/0 = 192.168.2.1 |

PCs (gateway = their router's G0/0):
| PC | IP | Mask | Gateway |
|---|---|---|---|
| PC-A1 | 192.168.1.10 | 255.255.255.0 | 192.168.1.1 |
| PC-A2 | 192.168.1.11 | 255.255.255.0 | 192.168.1.1 |
| PC-B1 | 192.168.2.10 | 255.255.255.0 | 192.168.2.1 |
| PC-B2 | 192.168.2.11 | 255.255.255.0 | 192.168.2.1 |

---

## STEP 1 — Place the devices

**Where:** Device palette (bottom-left).

- 2 **Routers** — model **ISR 4321** (needs a serial module — confirmed working with **NIM-2T**). Rename **R1, R2**.
- 2 **2960-24TT switches** — **SW1, SW2**.
- 4 **PCs** — PC-A1, PC-A2 on SW1; PC-B1, PC-B2 on SW2.

> **Serial ports need a module.** Double-click each router -> **Physical** tab -> power
> OFF -> drag a **NIM-2T** into an empty slot -> power ON. This creates the serial
> interfaces — but see STEP 3, the actual name is NOT guaranteed to be S0/0/0.

---

## STEP 2 — Cable everything

**Where:** Connections -> **Automatic** for LAN links; **Serial DCE** for the router link.

- R1 G0/0 -> SW1; SW1 -> PC-A1, PC-A2. R2 G0/0 -> SW2; SW2 -> PC-B1, PC-B2.
- R1 S0/0/0 <-> R2 S0/0/0 with the **Serial DCE** cable. Whichever end you plug in
  FIRST becomes the **DCE** end and needs a `clock rate`.

---

## STEP 3 — Discover interface names

**Where:** Each router -> CLI tab.

```
enable
show ip interface brief
```
Confirm the serial name and LAN name. Everything shows
**administratively down** until configured and `no shutdown`.

> **Confirmed in lab: the serial name is NOT always S0/0/0, even with the same
> router model and module.** On a real run, R1's NIM-2T came up as **Serial0/1/0**
> and R2's came up as **Serial0/2/0** — different slot numbers on two identical
> routers, because it depends on which physical bay you dropped the module into.
> Run this command on **every** router individually and use exactly what it prints.
> Do not copy a serial interface name from R1 onto R2 assuming they match.
>
> LAN interfaces on a 4321 are also **GigabitEthernet0/0/0** and **0/0/1**, not
> G0/0 — the examples below use G0/0/0 for this reason.

---

## STEP 4 — Configure R1 interfaces

Substitute the exact interface names STEP 3 printed for R1 — the example below uses
`Serial0/1/0`, which is what one real run produced, but yours may differ.

```
enable
configure terminal
hostname R1

interface GigabitEthernet0/0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown
exit

interface Serial0/1/0
 ip address 10.0.0.1 255.255.255.252
 clock rate 64000        ! ONLY on the DCE end of the cable
 no shutdown
exit
end
write memory
```

> **Do not also touch GigabitEthernet0/0/1.** This assignment only needs one LAN
> interface. Assigning the same subnet's address to the second Gig port by mistake
> triggers `% 192.168.1.0 overlaps with GigabitEthernet0/0/0` — but Packet Tracer
> can still silently apply the address anyway despite the warning, leaving the same
> IP duplicated on two interfaces. Check with `show ip interface brief`; if it shows
> up on both, remove it from the one you don't need: `interface GigabitEthernet0/0/1`
> -> `no ip address`.

---

## STEP 5 — Configure R2 interfaces

Same caveat — use R2's own interface names from STEP 3. A real run gave R2 a
different serial slot entirely (`Serial0/2/0`), even though R1 was `Serial0/1/0`.

```
enable
configure terminal
hostname R2

interface GigabitEthernet0/0/0
 ip address 192.168.2.1 255.255.255.0
 no shutdown
exit

interface Serial0/2/0
 ip address 10.0.0.2 255.255.255.252
 no shutdown             ! DTE end here (R1 side was DCE) - no clock rate
exit
end
write memory
```

Verify both serial ends are **up/up** before adding routes:
```
show ip interface brief
```

---

## STEP 6 — Configure static routes

Static routing means you hand-type the route to every network you're not directly
connected to. Syntax: `ip route <dest-network> <dest-mask> <next-hop>`.

**On R1** (needs a route to reach LAN-B):
```
enable
configure terminal
ip route 192.168.2.0 255.255.255.0 10.0.0.2
end
write memory
```

**On R2** (needs a route to reach LAN-A):
```
enable
configure terminal
ip route 192.168.1.0 255.255.255.0 10.0.0.1
end
write memory
```

Verify:
```
show ip route static      ! routes marked "S"
show ip route             ! C = connected, S = static
```

---

## STEP 7 — Set PC IPs

**Where:** Each PC -> Desktop -> IP Configuration -> Static.

Use the PC table above. PC-A1/PC-A2 gateway = 192.168.1.1, PC-B1/PC-B2 gateway = 192.168.2.1.

> **Confirmed gotcha: clicking Static is not enough by itself.** In a real run, a PC's
> `ipconfig` still showed IPv4 Address 0.0.0.0 / Subnet Mask 0.0.0.0 / Gateway 0.0.0.0
> after the fields looked filled in. Nothing was actually committed. Click directly
> into each field (IP Address, Subnet Mask, Default Gateway) and retype the value,
> then click elsewhere on the panel to commit it. Re-run `ipconfig` on the PC
> afterwards and confirm the real addresses show up before you test connectivity —
> don't assume the static form saved just because you selected the Static radio button.

---

## STEP 8 — Verify end-to-end (the deliverable)

**Where:** PCs -> Command Prompt.

```
! from PC-A1 (192.168.1.10)
ping 192.168.1.1        ! own gateway
ping 192.168.2.1        ! R2's LAN gateway, across the static route
ping 192.168.2.10       ! PC-B1 on the far LAN -> proves full end-to-end connectivity
tracert 192.168.2.10    ! see note below on hop count
```

`ping` succeeding between LAN-A and LAN-B PCs = static routing is working correctly.

> **Confirmed actual tracert output: 3 hops, not 2.** A successful run showed
> `1: 192.168.1.1` (R1's own gateway) `2: 10.0.0.2` (R2's serial interface, the
> next-hop) `3: 192.168.2.10` (PC-B1 itself). The destination PC counts as its own
> hop in Packet Tracer's trace — don't be thrown if you see three lines instead of
> two; that is the correct, working result for this topology.

---

## Troubleshooting (static-routing-specific)

| Symptom | Cause / fix |
|---|---|
| Serial shows `up/down` | Missing/mismatched `clock rate` on the DCE end. |
| `ip route` rejected / no effect | Typo in the destination network, mask, or next-hop IP — must exactly match the far network and a directly reachable next hop. |
| PC-A can ping R2 but not PC-B | Route exists but PC-B's gateway is wrong, or PC-B's subnet mask is wrong. |
| Ping fails both ways | Check the route is configured on BOTH routers — static routes are not automatic; each router only knows what you typed. |
| Route disappears after reload | Never saved. `write memory` on both routers. |
| Next-hop unreachable error | The next-hop IP isn't on a directly connected/up interface — check the serial link is up first. |
| PC ping fails with `Request timed out` and `ipconfig` shows all `0.0.0.0` | The Static IP form was filled in but never actually committed. Re-click into each field, retype, click away to commit, then re-check `ipconfig` before testing again. |
| Router shows the same IP on two interfaces | You addressed the wrong Gig port by mistake and Packet Tracer applied it despite an overlap warning. `interface <wrong-one>` -> `no ip address` to clear it. |
| Assumed serial name from one router doesn't work on the other | Confirmed in lab: R1 and R2 can land their serial module in different slots (e.g. Serial0/1/0 vs Serial0/2/0) even with identical hardware. Always run `show ip interface brief` on each router separately. |

---

## Key concepts to remember

- **Static routing** = you manually tell each router about every remote network; nothing
  is learned automatically (contrast with OSPF in Assignment 2).
- `ip route <dest-net> <dest-mask> <next-hop>` must be configured on **every** router
  that needs to reach a network it isn't directly connected to.
- The next-hop is the neighboring router's interface IP on the shared link, not the
  final destination.
- Always verify the physical/serial link is up before troubleshooting the route itself.
