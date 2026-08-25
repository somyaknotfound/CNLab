"""
Q6 - Two LANs in DIFFERENT subnets, joined by a router.

  h1 h2 h3 -- s1 --10mbit,10ms-- r1 --10mbit,10ms-- s2 -- h4 h5 h6
  192.168.1.0/24                                          192.168.2.0/24
  host <-> switch links: 100mbit, 1ms

Because the two LANs are separate networks, the hosts now need default
routes pointing at the router interface on their own side.

Run:  sudo python3 q6_two_lans_via_router.py

API used:
    Router.add_route / Node.add_route   nest/topology/node.py  (3rd arg = next hop)
"""

from nest.topology import Node, Switch, Router, connect

h1, h2, h3 = Node("h1"), Node("h2"), Node("h3")
h4, h5, h6 = Node("h4"), Node("h5"), Node("h6")
s1, s2 = Switch("s1"), Switch("s2")
r1 = Router("r1")                                # IPv4 forwarding on by default

# LAN-1 and LAN-2
(eth1, ets1a) = connect(h1, s1, "eth1", "ets1a")
(eth2, ets1b) = connect(h2, s1, "eth2", "ets1b")
(eth3, ets1c) = connect(h3, s1, "eth3", "ets1c")
(eth4, ets2a) = connect(h4, s2, "eth4", "ets2a")
(eth5, ets2b) = connect(h5, s2, "eth5", "ets2b")
(eth6, ets2c) = connect(h6, s2, "eth6", "ets2c")

# Each switch to the router
(ets1d, etr1a) = connect(s1, r1, "ets1d", "etr1a")
(ets2d, etr1b) = connect(s2, r1, "ets2d", "etr1b")

# Network 1
eth1.set_address("192.168.1.1/24")
eth2.set_address("192.168.1.2/24")
eth3.set_address("192.168.1.3/24")
s1.set_address("192.168.1.4/24")                 # optional: a bridge may hold an IP
etr1a.set_address("192.168.1.5/24")              # the gateway for LAN-1

# Network 2
eth4.set_address("192.168.2.1/24")
eth5.set_address("192.168.2.2/24")
eth6.set_address("192.168.2.3/24")
s2.set_address("192.168.2.4/24")
etr1b.set_address("192.168.2.5/24")              # the gateway for LAN-2

# Host <-> switch links
for iface in (eth1, eth2, eth3, eth4, eth5, eth6,
              ets1a, ets1b, ets1c, ets2a, ets2b, ets2c):
    iface.set_attributes("100mbit", "1ms")

# Switch <-> router links
for iface in (ets1d, ets2d, etr1a, etr1b):
    iface.set_attributes("10mbit", "10ms")

# Default routes: "send anything not in my subnet to the router"
h1.add_route("DEFAULT", eth1, etr1a.address)
h2.add_route("DEFAULT", eth2, etr1a.address)
h3.add_route("DEFAULT", eth3, etr1a.address)
h4.add_route("DEFAULT", eth4, etr1b.address)
h5.add_route("DEFAULT", eth5, etr1b.address)
h6.add_route("DEFAULT", eth6, etr1b.address)

h1.ping(eth4.address, packets=5)
h2.ping(eth5.address, packets=5)
h3.ping(eth6.address, packets=5)
