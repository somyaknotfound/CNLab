# NeST Real-World Scenarios — Lab 06 Notes

Computer Networks Laboratory (CS-302) · Week 7, Exercise 6

Week 6 was "build a topology". This week is "build an enterprise, load it, find the
bottleneck, fix it". Six scenarios, each with VLANs, routing, traffic generation and a
before/after comparison.

---

## Files

| Q | File | Scenario | Routing | Extras |
|---|---|---|---|---|
| 1 | `q1_campus_network.py` | University campus, 3 departments + ISP | static | iperf, bandwidth change |
| 2 | `q2_corporate_vlans.py` | TechNova HO + Pune + Hyderabad | static | 3 app types, WAN loss |
| 3 | `q3_hospital_qos.py` | Hospital + remote clinic | static | QoS prioritisation |
| 4 | `q4_ecommerce_ospf.py` | Mumbai HO/DC + 2 branches | OSPF | NAT |
| 5 | `q5_smart_city.py` | City Hall + 3 remote sites | OSPF | NAT, CCTV UDP |
| 6 | `q6_university.py` | Blocks, hostel, library, DC | OSPF | NAT |
| — | `nestlab.py` | shared helpers (`lan`, `link`, `enable_nat`, `report`) | | |

Every script takes one optional argument — the "improvement" value for the bottleneck
link — so you can produce the before/after results the papers ask for:

```bash
sudo python3 q1_campus_network.py              # before
sudo python3 q1_campus_network.py 2mbit        # after (task 9)

sudo python3 q3_hospital_qos.py                # before: one FIFO
sudo python3 q3_hospital_qos.py qos            # after: fq_codel

sudo python3 q4_ecommerce_ospf.py 16mbit       # after: widen MUM-CHE
```

---

## Setup

```bash
sudo apt install iproute2 ethtool iperf3 netperf iptables
sudo apt install frr                    # for OSPF (Q4, Q5, Q6)
pip3 install nest
```

For FRR, enable the OSPF daemon once:

```bash
sudo sed -i 's/^ospfd=no/ospfd=yes/' /etc/frr/daemons
sudo systemctl restart frr
```

Each run creates `<experiment-name>(timestamp)_dump/` with a `README`, plus `iperf3`,
`netperf`, `ping` and `qdisc` subdirectories containing the JSON results and the
throughput / delay / loss plots. Those plots are the graphs the submission asks for.

If a script crashes, clear the leftover namespaces:

```bash
sudo ip -all netns delete
```

---

## Three things NeST does not have, and what these scripts do instead

This matters — say it in the viva rather than pretending the emulation is something it
isn't.

### 1. VLANs / 802.1Q

There is no VLAN module in `nest/topology/` and no VLAN example in the upstream
repository. NeST models Layer 2 with `Switch`, which is a Linux bridge — untagged.

A VLAN is a broadcast domain with its own subnet and its own gateway. So each VLAN here
is **one `Switch` plus one router port carrying that VLAN's gateway address**:

```python
sw = Switch("sw-v10")
r_if, _ = connect(router, sw)
r_if.set_address("192.168.10.1/24")     # this is the SVI / gateway
```

That is router-on-a-stick with one physical port per VLAN instead of one tagged trunk.
The subnets, the gateways, the inter-VLAN routing and every measurement are identical;
only the frame tagging is absent. Real 802.1Q would need `ip link add link eth0 name
eth0.10 type vlan id 10` inside the namespace, which NeST does not wrap.

### 2. DHCP

No DHCP API either. Q2 asks for DHCP pools at the head office; addresses are assigned
statically from exactly the pools the paper specifies.

### 3. NAT

No NAT API. `nestlab.enable_nat()` shells out to iptables inside the router's namespace:

```python
from nest.engine.exec import exec_subprocess          # nest/engine/exec.py

exec_subprocess(
    f"ip netns exec {router.id} iptables -t nat -A POSTROUTING "
    f"-o {wan_interface.id} -j MASQUERADE"
)
```

`Node.id` is the namespace name and `BaseInterface.id` is the device name inside it —
the same two values NeST's own engine passes to `ip` and `tc`.

---

## New API this week

Everything from Lab 05 still applies. What is new:

### Dynamic routing — `nest/routing/routing_helper.py`

```python
from nest.routing.routing_helper import RoutingHelper

RoutingHelper(protocol="ospf", routers=[r1, r2]).populate_routing_tables()
```

| Thing | Where |
|---|---|
| `RoutingHelper(protocol, ipv6_routing=False, hosts=None, routers=None)` | `nest/routing/routing_helper.py` → `class RoutingHelper` |
| `populate_routing_tables()` | same file |
| supported protocols | `"ospf"`, `"rip"`, `"isis"`, `"static"` (the `_module_map` dict) |
| `Ospf` implementation | `nest/routing/ospf.py` |
| `StaticRouting` | `nest/routing/static_routing.py` |
| suite selection | `config.set_value("routing_suite", "frr")` — also `"quagga"`, `"bird"` |
| daemon logs | `config.set_value("routing_logs", True)` |

If you leave `routers=` out, NeST calls every node with more than one interface a router
and runs a daemon on it. These scripts pass the list explicitly so the ISP node stays out
of the university's IGP — which is also how it works in reality.

### Traffic generation — `nest/experiment/experiment.py`

```python
from nest.experiment import Experiment, Flow

exp = Experiment("name")
flow = Flow(src_node, dst_node, dst_address, start_time, stop_time, n_streams)
exp.add_tcp_flow(flow, congestion_algorithm="cubic", tool="netperf")
exp.add_udp_flow(flow, target_bandwidth="12mbit")
exp.require_qdisc_stats(interface)
exp.run()
```

| Thing | Line in `experiment.py` |
|---|---|
| `class Flow` | 35 |
| `Flow.__init__(source_node, destination_node, destination_address, start_time, stop_time, number_of_streams, source_address=None)` | 40 |
| `class Experiment` | 627 |
| `add_flow` | 658 |
| `add_tcp_flow` | 672 |
| `add_udp_flow` | 802 |
| `add_http_application` | 893 |
| `require_qdisc_stats` | 914 |
| `configure_tcp_module_params` | 944 |
| `run` | 959 |

**`destination_address` must be an address that lives on `destination_node`** — the iperf
or netperf server is started on that node and the client dials that address. Pointing a
flow at a gateway address while naming a PC as the destination silently produces no
traffic.

### Address helpers — used indirectly

```python
from nest.topology.network import Network                    # nest/topology/network.py:17
from nest.topology.address_helper import AddressHelper       # address_helper.py:17

n1 = Network("192.168.1.0/24")
eth1, eth2 = connect(h1, h2, network=n1)
AddressHelper.assign_addresses()
```

These scripts set addresses explicitly instead, because the question papers pin every
host to a specific address.

### QoS — `nest/topology/interface/base_interface.py`

```python
iface.set_qdisc("fq_codel")                 # line 568
iface.set_packet_loss("0.2%")               # line 373
iface.set_attributes("10mbit", "20ms")      # line 597
```

`set_qdisc` takes any qdisc `tc` knows: `pfifo`, `pfifo_fast`, `fq_codel`, `codel`,
`pie`, `red`, `htb`, `prio`. For **true** class-based priority (a strict-priority class
for patient records, a lower one for bulk transfer) you need classes and filters, which
are in the engine but not surfaced on the interface object:

```python
from nest.engine.tc import add_qdisc, add_class, add_filter   # nest/engine/tc.py
add_qdisc(node.id, iface.id, "htb", parent="root", handle="1:")
add_class(node.id, iface.id, "1:", "htb", classid="1:10", rate="400kbit", prio="0")
add_class(node.id, iface.id, "1:", "htb", classid="1:20", rate="112kbit", prio="1")
```

Q3 uses the one-line `fq_codel` version because it is honest, reproducible, and
demonstrates the same point: with a single FIFO the bulk transfer's packets sit in front
of the critical ones; with flow queueing they do not.

---

## Question notes

### Q1 — campus, static routing

Four routers in a line. R1 owns the three department LANs, R3 owns the server LAN, R4 is
the ISP. Static routes only, as the paper requires: each router points inward at the
specific campus prefixes and outward with a default route.

The bottleneck is whichever backbone link is slowest. At the given values that is
R2↔R3 (5 Mbps, 20 ms) — and task 9's drop to 2 Mbps makes it dramatically worse. Run both
and compare the iperf throughput.

*Discrepancy:* the task list says R3↔R4 is 20 ms, the topology diagram says 50 ms. The
diagram is per-link and more specific, so the script uses 50 ms (`R3R4_DELAY` at the
top — change it if your evaluator wants the other reading).

### Q2 — corporate, three sites

The ISP is the hub; each site has a default route towards it and the ISP has a route back
into each site. Branch-to-branch traffic therefore crosses two WAN links.

Hyderabad is the weak link: 3 Mbps, 30 ms, 0.5 % loss. Under the file transfer + video +
web load, that is where the video conference loses packets. Widening it to 8 Mbps is the
improvement.

### Q3 — hospital, QoS

512 kbit is tiny. A single bulk file transfer fills the queue, and the patient-record
flows queue behind it — that is the congestion the scenario describes. Run without
arguments for the baseline, then with `qos` for `fq_codel`, and compare the per-flow
throughput and delay plots.

*Discrepancy:* the sheet gives R-HOSPITAL G0/0 as `192.168.1.2/30` and R-CLINIC G0/1 as
`10.10.10.2/30`. Two different subnets cannot form one point-to-point link, so the WAN is
a single `192.168.1.0/30` transit. Everything else follows the sheet.

### Q4 — e-commerce, OSPF + NAT

OSPF area 0 across R-MUM, R-BLR, R-CHE — no static routes between sites at all, which is
the point of the exercise. The ISP stays outside the IGP; R-MUM has a default route
towards it and NAT hides the private addressing.

Chennai's 8 Mbps / 30 ms / 0.3 % link is the bottleneck under peak load.

### Q5 — smart city

Same shape as Q4 with four routers. The CCTV stream is UDP at a constant 6 Mbps — watch
what happens to its loss rate when the public Wi-Fi TCP traffic ramps up on the 10 Mbps
link at 20 s.

### Q6 — university

*Discrepancy:* the sheet gives the VLAN gateways as SVIs on R-CORE **and** lists /30
point-to-point links from R-CORE to each block. Those are mutually exclusive. The script
uses the SVI model (which the addressing table specifies) and applies the L1–L5 bandwidth
and delay values to the R-CORE-to-block links. L6 and L7 remain real /30s.

The border link (50 Mbps, 30 ms, 0.2 %) saturates first because every student's Internet
traffic crosses it.

---

## How to find the bottleneck

1. Run the script and open the `iperf3`/`netperf` plots in the dump directory. The flow
   whose throughput collapses is crossing the bottleneck.
2. Look at `require_qdisc_stats` output for the suspect interface — a queue that stays
   full is a queue that is the constraint.
3. Compare end-to-end ping RTT before and during the load. A large increase is
   bufferbloat at that queue.
4. The arithmetic check: the bottleneck is the link with the lowest
   `bandwidth ÷ number of flows crossing it`. Delay alone does not cause loss; it caps
   throughput per TCP flow at roughly `window ÷ RTT`.
5. Fix it and re-run with the command-line argument, then put the two graphs side by side.

---

## Viva questions

- Why is a VLAN "the same as" a separate switch plus a separate subnet here? What is
  actually missing? (802.1Q tags, and therefore trunking on one physical port)
- What does inter-VLAN routing mean, and where does it happen in these scripts?
- Why does OSPF need a daemon (FRR) while static routes do not?
- What is OSPF area 0, and why is the ISP left out of it?
- What does NAT overload / PAT translate, and why is a return route still needed?
- On a congested link, why does a UDP video flow lose packets while a TCP flow just slows
  down?
- What is bufferbloat, and how does `fq_codel` help?
- Why does raising bandwidth sometimes not improve a flow's throughput? (RTT-limited
  window)
- Which of these six networks would break first if a link went down, and why?
