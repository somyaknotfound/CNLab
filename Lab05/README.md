# NeST (NITK) Network Emulation — Lab 05 Notes

Computer Networks Laboratory (CS-302) · Week 6, Exercise 5

NeST = **Ne**twork **S**tack **T**ester, a Python 3 package from NITK Surathkal that builds
emulated topologies out of **Linux network namespaces**, veth pairs, bridges and `tc`.

- Source: <https://gitlab.com/nitk-nest/nest>
- Examples: <https://gitlab.com/nitk-nest/nest/-/tree/master/examples/basic-examples>
- Docs: <https://nest.nitk.ac.in/>

---

## Files here

| Q | File | Topology |
|---|---|---|
| 1 | `q1_point_to_point_1.py` | `h1 — h2` |
| 2 | `q2_point_to_point_2.py` | `h1 — r1 — h2` |
| 3 | `q3_point_to_point_3.py` | `h1 — r1 — r2 — h2` |
| 4 | `q4_simple_lan.py` | 4 hosts on switch `s1` |
| 5 | `q5_two_lans.py` | `h1–h3 — s1 — s2 — h4–h6`, one subnet |
| 6 | `q6_two_lans_via_router.py` | `s1 — r1 — s2`, two subnets |
| — | `verify_api.py` | prints where every API used here is defined |

---

## Setup and running

```bash
sudo apt install iproute2 net-tools ethtool iperf3 netperf
pip3 install nest

sudo python3 q1_point_to_point_1.py       # root is mandatory
```

`nest/__init__.py` calls `sys.exit(1)` if `os.geteuid() != 0`, so a non-root run fails
immediately with `nest: python package requires root access`.

Each run leaves a timestamped results directory in the current folder. If a script
crashes, namespaces can be left behind — clear them with:

```bash
sudo ip netns list
sudo ip -all netns delete
```

Verify the API surface (works without sudo, it parses the source):

```bash
python3 verify_api.py
```

---

## Where every method is defined

Paths are relative to the installed `nest` package (`python3 -c "import nest, os;
print(os.path.dirname(nest.__file__))"`). Line numbers are from **nest 0.4.4** — run
`verify_api.py` to get them for your installed version.

### Things you import

| Name | Defined in | Line | Note |
|---|---|---|---|
| `Node` | `nest/topology/node.py` | 25 | one Linux network namespace |
| `Router` | `nest/topology/router.py` | 9 | `class Router(Node)` |
| `Switch` | `nest/topology/switch.py` | 16 | `class Switch(Node, BaseInterface)` |
| `connect` | `nest/topology/connect.py` | 22 | creates a veth pair |
| `Address` | `nest/topology/address.py` | 12 | IPv4/IPv6 address + prefix |
| `Subnet` | `nest/topology/address.py` | 247 | hands out sequential addresses |
| `Network` | `nest/topology/network.py` | 17 | context manager for auto-addressing |
| `AddressHelper` | `nest/topology/address_helper.py` | 17 | `assign_addresses()` |
| `Interface` | `nest/topology/interface/interface.py` | 16 | one end of a veth pair |
| `BaseInterface` | `nest/topology/interface/base_interface.py` | 22 | parent of everything addressable |

All of these are re-exported by `nest/topology/__init__.py`, which is why
`from nest.topology import Node, Router, Switch, connect` works.

### Methods on `Node` — `nest/topology/node.py`

| Method | Line | What it does |
|---|---|---|
| `Node.__init__(name)` | 36 | creates the namespace |
| `Node.ping(dest, preload=1, packets=5, verbose=2)` | 548 | returns `True`/`False` |
| `Node.add_route(dest_addr, via_interface, next_hop_addr=None)` | 147 | `dest_addr` may be `"DEFAULT"` |
| `Node.enable_ip_forwarding(ipv4=True, ipv6=True)` | 617 | sysctl inside the namespace |
| `Node.disable_ip_dad()` | 631 | needed before IPv6 addresses |
| `Node.get_interface(node, connection_number=1)` | 205 | look up an interface by peer |
| `Node.configure_tcp_param(param, value)` | 365 | e.g. congestion control |
| `Node.read_tcp_param(param)` | 403 | |
| `Node.capture_packets(...)` | 641 | tcpdump/tshark inside the namespace |
| `Node.get_arp_table()` | 443 | also `set_/get_/delete_/flush_arp_entry` |
| `Node.print_routes_to_file(*args)` | 194 | dump the routing table |
| `Node.name` / `Node.id` / `Node.interfaces` | 707 / 695 / 702 | properties |

`Router.__init__` (router.py:19) is just `super().__init__(name)` followed by
`self.enable_ip_forwarding()` — that is exactly what the lab sheet means by
"handled by Router API".

`Switch.__init__` (switch.py:26) calls `Node.__init__`, creates a `Bridge`
(`nest/topology/device/bridge.py`), then `BaseInterface.__init__`. Because `Switch`
inherits `BaseInterface`, a switch can hold an IP address — but a Layer-2 switch does not
need one.

### Methods on interfaces — `nest/topology/interface/base_interface.py`

| Method | Line | What it does |
|---|---|---|
| `set_address(address)` | 123 | replaces any existing address |
| `add_address(address)` | 134 | adds a second address |
| `del_address(address)` | 145 | |
| `get_address(ipv4=True, ipv6=True, as_list=False)` | 206 | |
| `address` (property + setter) | 98 / 109 | what you pass to `ping()` |
| `set_attributes(bandwidth, delay, qdisc=None, **kwargs)` | 597 | calls the three below |
| `set_bandwidth(bandwidth)` | 275 | `tc` rate limit |
| `set_delay(delay)` | 294 | `netem` delay |
| `set_qdisc(qdisc, **kwargs)` | 568 | `codel`, `fq_codel`, `pie`, `red`, … |
| `set_packet_loss(loss_rate)` | 373 | `netem loss` |
| `set_packet_corruption(...)` | 344 | |
| `set_packet_duplication(rate)` | 517 | |
| `set_packet_reordering(...)` | 536 | |
| `set_delay_distribution(...)` | 314 | normal / pareto jitter |
| `set_mode(mode, delay=0.0)` | 231 | bring the link `UP` / `DOWN` |
| `disable(...)` / `enable(...)` | 647 / 691 | timed link failure |
| `mtu` (property + setter) | 191 / 198 | |
| `enable_offload` / `disable_offload` | 620 / 631 | GSO, TSO, GRO |

`Interface.pair` (`interface/interface.py`:51) gives the interface at the **other** end of
the veth pair — `add_route` uses it to work out the next hop when you omit it.

### Module-level helpers

| Name | Defined in | Line |
|---|---|---|
| `nest.config.set_value(param, value)` | `nest/config.py` | 45 |
| `nest.config.get_value(param)` | `nest/config.py` | 88 |
| `nest.config.import_custom_config(path)` | `nest/config.py` | 109 |
| `nest.clean_up.delete_namespaces()` | `nest/clean_up.py` | 55 |
| `nest.topology_map.TopologyMap` | `nest/topology_map.py` | 21 |
| `TopologyMap.dump()` | `nest/topology_map.py` | 346 |
| `Experiment`, `Flow` | `nest/experiment/experiment.py` | — |

### Under the hood — `nest/engine/`

Everything above eventually shells out to `ip`, `tc` and friends. Useful when a viva asks
"what Linux command does this run?":

| Python call | Engine module | Linux command |
|---|---|---|
| `Node("h1")` | `engine/ip_netns.py` | `ip netns add h1-<id>` |
| `connect(a, b)` | `engine/ip_link.py` | `ip link add … type veth peer …` |
| `set_address()` | `engine/ip_address.py` | `ip netns exec … ip address add` |
| `add_route()` | `engine/ip_route.py` | `ip route add default via …` |
| `set_attributes()` | `engine/tc.py` | `tc qdisc add … htb / netem` |
| `ping()` | `engine/ping.py` | `ping -c <packets> …` |
| `enable_ip_forwarding()` | `engine/sysctl.py` | `sysctl -w net.ipv4.ip_forward=1` |
| `Switch("s1")` | `engine/ip_link.py` | `ip link add … type bridge` |
| `capture_packets()` | `engine/t_shark.py` | `tshark` / `tcpdump` |

---

## The five-step pattern

Every script in this folder is the same five steps:

```python
from nest.topology import Node, Router, Switch, connect

h1 = Node("h1")                             # 1. create nodes
(eth1, eth2) = connect(h1, h2)              # 2. connect them  -> (near_end, far_end)
eth1.set_address("192.168.1.1/24")          # 3. address the interfaces
eth1.set_attributes("5mbit", "5ms")         # 4. bandwidth + delay
h1.ping(eth2.address, packets=5)            # 5. test
```

Routers add step 4.5: `h1.add_route("DEFAULT", eth1)`.

---

## Six things that are easy to get wrong

**1. `set_attributes` shapes the OUTGOING direction only.**
For "h1 → h2 at 5mbit" you set it on `eth1` (h1's interface). For the reverse direction
you set it on `eth2`. That is why Q1 has two different values, and why Q2/Q3 set
`5mbit/5ms` on every left-to-right interface and `10mbit/100ms` on every right-to-left
one.

**2. `connect()` returns the ends in argument order.**

```python
(eth1, etr1a) = connect(h1, r1)     # eth1 is on h1, etr1a is on r1
(etr1b, eth2) = connect(r1, h2)     # etr1b is on r1, eth2 is on h2
```

Swapping these silently addresses the wrong namespace and the ping fails.

**3. Switch ports get no IP address.**
A switch is Layer 2 — it forwards frames by MAC address. Hosts attached to it must be in
the **same subnet** for pings to work without a router (Q4, Q5). In Q6 the two LANs are in
different subnets, so a Layer-3 device (the router) is required.

**4. Routers need forwarding; hosts need routes.**
`Router("r1")` enables forwarding for you. But each host still needs
`add_route("DEFAULT", its_interface)` or it has no idea where to send packets for another
subnet. In Q3 the **routers** need default routes too — r1 does not know about network 3.

**5. `ping()` takes an address object, not a node.**
`h1.ping(eth2.address)` or `h1.ping("192.168.1.2")`. `h1.ping(h2)` is wrong.

**6. Everything needs `sudo`.**
Namespaces, veth pairs and `tc` are all privileged operations.

---

## Question-by-question

### Q1 — point-to-point

One veth pair, two addresses in `192.168.1.0/24`, asymmetric attributes. Directly
connected hosts in the same subnet need no routes at all.

### Q2 — one router

Two networks (`192.168.1.0/24`, `192.168.2.0/24`). `Router` turns on IPv4 forwarding;
each host gets a default route via its own interface. NeST infers the next hop from
`Interface.pair` when you leave the third argument out.

### Q3 — two routers

Three networks. Both hosts **and** both routers need default routes — r1's default points
at r2 (`etr1b`), r2's points back at r1 (`etr2a`). Without those, the ping reaches r1 and
stops.

### Q4 — LAN with a switch

Four hosts, one `Switch`, one subnet, no routes. `connect(h1, s1)` returns the host side
first; only the host side is addressed. This demonstrates Layer-2 flooding and MAC
learning.

### Q5 — two LANs, switch to switch

Six hosts, two switches, a trunk link between them. All still `192.168.1.0/24`, so the
two switches form **one** broadcast domain and cross-LAN pings work with no router.

### Q6 — two LANs via a router

Now the LANs are `192.168.1.0/24` and `192.168.2.0/24`. Each switch connects to the
router, each host's default route points at the router interface on its own side, and the
router forwards between subnets. Host↔switch links are 100mbit/1ms, switch↔router links
are 10mbit/10ms — the router link is the bottleneck, which is realistic.

The switch addresses (`s1.set_address(...)`) are optional. They are included to match the
topology diagram; a switch works fine without one.

---

## Viva questions

- What Linux feature does a NeST `Node` map to? (a network namespace)
- What is a veth pair, and why do they always come in twos?
- Why does NeST need root?
- Which direction does `set_attributes()` affect?
- Difference between a `Node` and a `Router` in NeST? (`Router.__init__` calls
  `enable_ip_forwarding`)
- Why do Q4 and Q5 need no routes but Q6 does?
- What is a broadcast domain, and how many are there in Q5? (one) In Q6? (two)
- Which Linux commands does `set_attributes("5mbit", "5ms")` produce? (`tc qdisc`, htb +
  netem)
- How would you emulate 2% packet loss? (`iface.set_packet_loss("2%")`)
- How would you bring a link down mid-experiment? (`iface.set_mode("DOWN")` or
  `iface.disable(start_time, end_time)`)
- What does `ping()` return, and how would you assert on it in a test?

---

## Useful extras

```python
# congestion-control experiments
h1.configure_tcp_param("congestion_control", "cubic")   # node.py:365

# impairments
eth1.set_packet_loss("2%")                              # base_interface.py:373
eth1.set_qdisc("codel", limit="100")                    # base_interface.py:568

# capture traffic
h1.capture_packets(interface=eth1, packet_count=20)     # node.py:641

# see what NeST built
from nest.topology_map import TopologyMap
TopologyMap.dump()                                      # topology_map.py:346

# more logging
from nest import config
config.set_value("log_level", "INFO")                   # config.py:45
```
