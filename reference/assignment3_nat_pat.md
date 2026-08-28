# Assignment 3 — NAT/PAT (Overload)

**Objective:** Allow a private network to access the Internet using NAT Overload (PAT).

---

## Topology at a glance

```
   Inside Network                                  Internet
   192.168.10.0/24
                     G0/0/0          G0/0/1
        PC1 --.      (Inside)       (Outside)
               \      192.168.10.1  203.0.113.2
        SW1 ----------  R1  ---------------------------- Web Server
               /                                          203.0.113.10
        PC2 --'
```

> **Confirmed in lab: skip the Cloud-PT entirely.** It's optional in theory, but the
> coaxial/cable-mapping headaches from the Cellular Network assignment are not worth
> repeating here for zero benefit — a direct copper cable from R1's outside interface to
> the Web Server satisfies this assignment completely. Both devices are Ethernet, both
> sit on 203.0.113.0/24, and a straight cable is all that's needed.

### Addressing plan

| Segment | Network | Interface & IP |
|---|---|---|
| Inside LAN | 192.168.10.0/24 | R1 G0/0/0 = 192.168.10.1 (**inside**) |
| Outside / ISP link | 203.0.113.0/24 | R1 G0/0/1 = 203.0.113.2 (**outside**) |
| Internet (simulated) | — | Web Server = 203.0.113.10 |

> Interface names shown are for ISR 4321 (`GigabitEthernet0/0/0` / `0/0/1`). Confirm with
> `show ip interface brief` on your actual router before typing anything — this has
> differed from the diagram every single time so far in this lab.

PCs (gateway = R1's inside interface):
| PC | IP | Mask | Gateway |
|---|---|---|---|
| PC1 | 192.168.10.10 | 255.255.255.0 | 192.168.10.1 |
| PC2 | 192.168.10.11 | 255.255.255.0 | 192.168.10.1 |

---

## STEP 1 — Place the devices

**Where:** Device palette (bottom-left).

- 1 **Router** — **ISR 4321**, rename **R1**.
- 1 **2960-24TT switch** — **SW1**.
- 2 **PCs** — PC1, PC2.
- 1 **Server-PT** (HTTP service on) to act as the Internet web server.
- No Cloud-PT needed — see the note above. Cable the server directly to R1's outside
  interface.

---

## STEP 2 — Cable everything

**Where:** Connections -> **Automatic**.

- PC1, PC2 -> SW1 -> R1 inside interface.
- R1 outside interface -> Web Server (direct copper).

---

## STEP 3 — Configure R1's inside interface

**Where:** R1 -> CLI tab. Confirm the real interface name with
`show ip interface brief` first.

```
enable
configure terminal
hostname R1

interface GigabitEthernet0/0/0
 ip address 192.168.10.1 255.255.255.0
 ip nat inside            ! marks this interface as the PRIVATE side
 no shutdown
exit
```

---

## STEP 4 — Configure R1's outside interface

```
interface GigabitEthernet0/0/1
 ip address 203.0.113.2 255.255.255.0
 ip nat outside           ! marks this interface as the PUBLIC side
 no shutdown
exit
```

> Every interface facing the private LAN gets `ip nat inside`; every interface facing
> the ISP/Internet gets `ip nat outside`. NAT will not translate anything until both
> sides are marked.

---

## STEP 5 — Default route towards the ISP

Since R1 doesn't run a routing protocol here, it needs a **default route** so any
unknown destination (i.e., "the whole Internet") goes out G0/1.

```
ip route 0.0.0.0 0.0.0.0 GigabitEthernet0/0/1
```

---

## STEP 6 — Configure PAT (NAT Overload)

Define which inside addresses are allowed to be translated (via a standard ACL), then
overload them all onto the single outside interface IP.

```
access-list 1 permit 192.168.10.0 0.0.0.255   ! "interesting" inside traffic
ip nat inside source list 1 interface GigabitEthernet0/0/1 overload
end
write memory
```

- `overload` is what makes this **PAT**: many inside hosts share ONE public IP,
  distinguished by port number. Without `overload` it would be a strict 1:1 NAT that
  runs out of public addresses immediately.

---

## STEP 7 — Set PC and server IPs

**Where:** Each PC -> Desktop -> IP Configuration -> Static.

- PC1: 192.168.10.10 / 255.255.255.0 / gateway 192.168.10.1
- PC2: 192.168.10.11 / 255.255.255.0 / gateway 192.168.10.1
- Web Server -> **Desktop tab** -> IP Configuration -> Static -> 203.0.113.10 /
  255.255.255.0 / gateway 203.0.113.2
- Server -> **Services tab** -> **HTTP** -> left box, leftmost radio = **On**.

> **Confirmed in lab: this is the step most likely to get skipped, and the failure it
> causes is confusing because everything else tests as working.** It's easy to open the
> server, go straight to the Services tab, switch HTTP on, and never visit the Desktop
> tab at all — leaving the server with no IP address. The symptom is a browser
> "Request Timeout" while `show ip nat translations` on R1 shows real TCP entries on
> port 80 (the request genuinely left the router and went somewhere) — that combination
> means the packets are being sent correctly but nothing is listening at the destination
> to answer them. Always confirm the server's own Desktop -> IP Configuration before
> chasing the HTTP toggle or NAT config further.
>
> On the Services tab: the HTTP page has TWO radio-button groups side by side — HTTP on
> the left, HTTPS on the right — each reading On then Off, left to right. Only the left
> group matters here. As with the PC static-IP fields, click the radio and then click
> elsewhere on the panel before closing the window, to make sure the change actually
> commits rather than silently reverting.

---

## STEP 8 — Access the Web Server from PC1 (the deliverable)

**Where:** PC1 -> Desktop -> Web Browser (or Command Prompt).

```
ping 203.0.113.10
```
Then open the browser and enter `http://203.0.113.10`. The default Cisco Packet Tracer
page loading = the whole NAT chain worked (PC1 -> switch -> R1 inside -> PAT translation
-> R1 outside -> server).

---

## STEP 9 — Verify NAT translations

**Where:** R1 -> CLI tab.

```
show ip nat translations     ! one row per active PC session, all sharing 203.0.113.2 on different ports
show ip nat statistics       ! hit counts, active translations
```

You should see entries like:
```
Pro  Inside global         Inside local          Outside local     Outside global
tcp  203.0.113.2:1025      192.168.10.10:1025    203.0.113.10:80   203.0.113.10:80
```
Same outside IP (203.0.113.2), different port per host — that's PAT/overload in action.

> **This command is your best diagnostic tool when something fails, not just a
> post-success check.** If a ping or the browser test isn't working, run this BEFORE
> troubleshooting anything else. If entries appear here — even ICMP ones from a ping
> that "failed" in the browser, or TCP ones on port 80 from a browser that timed out —
> it proves the entire chain up through NAT is working correctly (routing, ACL,
> inside/outside marking, overload). A confirmed run showed exactly this: real ICMP and
> TCP:80 translation entries existed while the browser still said "Request Timeout" —
> which correctly pointed the problem at the server itself (no IP configured), not at
> anything on R1. Seeing translations here means stop looking at the router.

---

## Troubleshooting (NAT/PAT-specific)

| Symptom | Cause / fix |
|---|---|
| `show ip nat translations` shows nothing | ACL 1 doesn't match the inside subnet, or `ip nat inside`/`ip nat outside` missing on one interface. |
| Ping to server fails, translations exist | Missing default route on R1, or server's gateway/IP wrong. |
| Ping works, translations still show nothing | ICMP alone sometimes doesn't build a full translation depending on PT version — check with `ping` immediately followed by the show command, or test with HTTP instead. |
| Web page won't load but ping works | HTTP service not turned On on the server (check the On/Off radio first). |
| Translations show real TCP:80 entries but browser still times out | Confirmed cause in lab: the server has no IP address configured on its Desktop -> IP Configuration tab. It's easy to only visit the Services tab and skip addressing entirely. The packets are arriving correctly with nothing there to answer. |
| Only ONE PC can reach the Internet | `overload` keyword missing — without it, NAT is 1:1 and only the first host gets translated. |
| NAT works then breaks after reload | Never saved. `write memory` on R1. |
| `show running-config interface <name>` rejected as invalid input | Packet Tracer's IOS doesn't support the interface-scoped form of this command. Use `show running-config \| include ip nat` (or `\| section`) instead — piping does work. |

---

## Key concepts to remember

- **`ip nat inside` / `ip nat outside`** on the respective interfaces is what tells the
  router which direction to translate.
- **PAT (NAT Overload)** lets an entire private subnet share one public IP by
  distinguishing sessions with source ports — this is what your home router does.
- A standard ACL (permit only, matching source network) defines which inside traffic
  is eligible for translation; it is NOT applied to an interface with
  `ip access-group` — it's referenced directly inside the `ip nat inside source` command.
- A **default route** is required so the router knows to send unknown (Internet-bound)
  traffic out the outside interface.
- `show ip nat translations` is the single best command to prove NAT is working.
