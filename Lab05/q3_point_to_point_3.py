"""
Q3 - Two hosts connected through two routers.

  h1 ---- r1 ---- r2 ---- h2
 eth1 etr1a etr1b etr2a etr2b eth2
 .1.1  .1.2  .2.1  .2.2  .3.1  .3.2

    left -> right : 5mbit,  5ms
    right -> left : 10mbit, 100ms

Run:  sudo python3 q3_point_to_point_3.py

API used: same as Q2. Note each router also needs a default route, because
neither of them knows about the network on the far side.
"""

from nest.topology import Node, Router, connect

h1 = Node("h1")
h2 = Node("h2")
r1 = Router("r1")                                # forwarding enabled by Router.__init__
r2 = Router("r2")

# Three veth pairs -> three /24 networks
(eth1, etr1a) = connect(h1, r1, "eth1", "etr1a")
(etr1b, etr2a) = connect(r1, r2, "etr1b", "etr2a")
(etr2b, eth2) = connect(r2, h2, "etr2b", "eth2")

eth1.set_address("192.168.1.1/24")               # network 1
etr1a.set_address("192.168.1.2/24")
etr1b.set_address("192.168.2.1/24")              # network 2
etr2a.set_address("192.168.2.2/24")
etr2b.set_address("192.168.3.1/24")              # network 3
eth2.set_address("192.168.3.2/24")

# Interfaces whose outgoing direction is left -> right
for iface in (eth1, etr1b, etr2b):
    iface.set_attributes("5mbit", "5ms")

# Interfaces whose outgoing direction is right -> left
for iface in (etr1a, etr2a, eth2):
    iface.set_attributes("10mbit", "100ms")

# Default routes: hosts point at their router, each router points at the other
h1.add_route("DEFAULT", eth1)
h2.add_route("DEFAULT", eth2)
r1.add_route("DEFAULT", etr1b)                   # r1 reaches network 3 through r2
r2.add_route("DEFAULT", etr2a)                   # r2 reaches network 1 through r1

h1.ping(eth2.address, packets=5)
