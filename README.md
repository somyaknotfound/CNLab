# Computer Networks Lab — Network Application Engineering

Hands-on implementations of network application tooling: **TCP/UDP servers and clients,
concurrency models, application-layer protocol design, reliable transport over an
unreliable channel, and emulated + simulated topologies.**

Everything here is written from scratch against the raw `socket` API — no web framework,
no RPC library, no ORM. The point is what happens on the wire.

`Computer Networks Laboratory (CS-302) · NITK Surathkal`

---

## Stack

`Python 3` · `socket` · `threading` · `select` · `hashlib` · `subprocess` · `sqlite3` ·
`NeST` (Linux network namespaces, veth, bridges, `tc`/`netem`) · `Cisco Packet Tracer` ·
`Wireshark` / `tcpdump` · `iperf3` / `netperf`

**62 Python programs · ~2,900 LOC · 35 automated assertions · 8 simulated topologies · 6 emulated topologies**

---

## What's inside

| Lab | Focus | Deliverables |
|---|---|---|
| [`Lab01/`](Lab01) | LAN fundamentals | Router/switch/hub LAN, VLANs + inter-VLAN routing (router-on-a-stick) |
| [`Lab02/`](Lab02) | Routing, translation, security | Static routing over a serial WAN, OSPF, NAT/PAT overload, IPv6 routing, ACLs — [notes](Lab02/material.md) |
| [`Lab03/`](Lab03) | Socket programming | 10 TCP/UDP client-server programs + 5 warm-up drills + a shared helper module — [notes](Lab03/README.md) |
| [`Lab04/`](Lab04) | Concurrent & secure servers | 10 multi-client servers: chat, reliable UDP, `select()` vs threads, auth'd file server — [notes](Lab04/README.md) |
| [`Lab05/`](Lab05) | Network emulation | 6 NeST topologies with traffic shaping, routing and link impairments — [notes](Lab05/README.md) |
| [`reference/`](reference) | Reference | Per-assignment Packet Tracer walkthroughs + an enterprise-campus build guide |

---

## Skills demonstrated

**Socket programming**
Both transports end to end — `SOCK_STREAM` and `SOCK_DGRAM`, the full `bind → listen →
accept` and `sendto → recvfrom` sequences, `SO_REUSEADDR`, timeouts, clean shutdown, and
the byte/string boundary handled explicitly at every hop.

**Concurrency models — and a benchmark between them**
Thread-per-client with `threading.Lock` around shared state, and a single-threaded
`select()` I/O-multiplexing loop. [`benchmark.py`](Lab04/q07_select_server/benchmark.py)
runs 30 concurrent clients × 20 messages against both servers and reports wall-clock time,
so the trade-off (stack cost and scheduling overhead vs. an explicit state machine) is
measured rather than asserted.

**Application-layer protocol design**
TCP is a byte stream with no message boundaries, so framing is designed per program:
newline-delimited text via `makefile()`, a `header|line` + raw payload shape for
metadata-then-bytes transfers, and exact-length reads. Multi-service servers dispatch
through a command table rather than an `if` chain.

**Reliable data transfer over UDP**
[`q04_reliable_udp`](Lab04/q04_reliable_udp) implements stop-and-wait ARQ from the four
primitives — sequence numbers, ACKs, timeouts, retransmission — against a receiver that
drops datagrams at a configurable rate. Handles the hard case correctly: a *lost ACK*
causes a retransmit of data the receiver already has, so it re-ACKs without writing twice.

**Data integrity**
Binary transfers carry a SHA-256 digest in the header; the receiver hashes what actually
arrived and compares. Files are opened `'rb'`/`'wb'` throughout — text mode silently
corrupts non-UTF-8 bytes and rewrites line endings.

**Security engineering on untrusted input**
- Remote command execution restricted to an **allow-list** with `shell=False` and a
  timeout — shell metacharacters rejected outright.
- **Path traversal** blocked with `os.path.basename()` on every client-supplied filename.
- Per-connection **authentication state** checked before any privileged command, so it
  cannot be bypassed by reordering requests.
- Per-user **audit logging** of connections, auth successes *and failures*, and transfers.

**Network emulation (Linux internals)**
[`Lab05/`](Lab05) builds topologies out of network namespaces and veth pairs via NeST:
point-to-point links, a 4-host switched LAN, two LANs bridged into one broadcast domain,
and two subnets routed through a Layer-3 device. Links are shaped with `tc` (HTB rate
limits, `netem` delay/loss) in the correct — *outbound* — direction, which is the detail
most people get wrong.

**Device configuration**
Cisco IOS across static routing (`/30` point-to-point links, `clock rate` on the DCE end),
OSPF adjacency and SPF, NAT/PAT overload, dual-stack IPv6, standard/extended ACLs, and
802.1Q trunking with subinterfaces.

**Testing**
Each of Lab03 and Lab04 ships a harness that starts every server as a subprocess, drives
its client, asserts on the output, and tears the server down — **14 and 21 assertions**
respectively, runnable whole or per-question.

---

## Worth a look

| | |
|---|---|
| [`Lab04/q07_select_server/`](Lab04/q07_select_server) | Same workload, two concurrency models, one benchmark script |
| [`Lab04/q04_reliable_udp/`](Lab04/q04_reliable_udp) | ARQ built by hand over a lossy channel |
| [`Lab04/q10_file_server/`](Lab04/q10_file_server) | Auth + upload/download + per-user audit log, concurrent |
| [`Lab04/q09_remote_cmd/`](Lab04/q09_remote_cmd) | Command execution written defensively |
| [`Lab05/q6_two_lans_via_router.py`](Lab05/q6_two_lans_via_router.py) | Two subnets, a router, and a deliberately bottlenecked link |
| [`Lab03/practice/netutils.py`](Lab03/practice/netutils.py) | The framing helpers everything else reuses |

---

## Running it

**Socket programs** (Lab03, Lab04) — no dependencies, standard library only. Two
terminals, server first:

```bash
cd Lab04/q01_chat
python server.py        # terminal 1
python client.py        # terminal 2
```

Every client also takes command-line arguments for non-interactive use:

```bash
cd Lab03/assignment/q10_sort_array && python client.py 3 1 4 1 5 9 2 6
```

Run the full check for a lab:

```bash
python Lab04/run_all_tests.py          # all 10 programs
python Lab04/run_all_tests.py 4 7      # only questions 4 and 7
```

**Emulation** (Lab05) — Linux + root, since namespaces, veth and `tc` are privileged:

```bash
sudo apt install iproute2 net-tools ethtool iperf3 netperf
pip3 install nest
sudo python3 Lab05/q1_point_to_point_1.py
```

**Simulation** (Lab01, Lab02) — open the `.pkt` files in Cisco Packet Tracer 8.x.

---

## Repository layout

```
CNLab/
├── Lab01/                     Packet Tracer — LAN, VLAN, inter-VLAN routing
├── Lab02/                     Packet Tracer — static routing, OSPF, NAT/PAT, IPv6, ACL
│   └── material.md            concept notes
├── Lab03/                     Socket programming
│   ├── practice/              warm-up drills + netutils.py
│   ├── assignment/            10 programs, each with server.py, client.py, NOTES.md
│   └── run_all_tests.py
├── Lab04/                     Concurrent, reliable and secure servers
│   ├── q01_chat … q10_file_server/
│   └── run_all_tests.py
├── Lab05/                     NeST emulation — 6 topologies + verify_api.py
└── reference/                 Packet Tracer build guides + viva notes
```

Each program folder carries its own `NOTES.md` covering the approach, the exact protocol
put on the wire, and the edge cases handled. Each lab's `README.md` is a full write-up of
the concepts, the failure modes, and the diagnostic commands used.

---

## Debugging toolkit used throughout

```bash
netstat -tuln | grep 6001            # is the port actually bound?  (Linux)
netstat -ano | findstr 6001          #                              (Windows)
nc 127.0.0.1 6002                    # drive any server by hand
sudo tcpdump -i lo port 6004 -A      # watch the retransmissions
sha256sum send/sample.bin received/sample.bin
sudo ip netns list                   # what did NeST leave behind?
```

Wireshark on loopback (`tcp.port == 6004 || udp.port == 6004`) is the fastest way to see
the three-way handshake, the ARQ retransmissions, and the fact that a plain socket sends
credentials in clear text.
