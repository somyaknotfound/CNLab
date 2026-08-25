"""
Q2 - Two hosts connected through one router.

    h1 ------- r1 ------- h2
  eth1  etr1a   etr1b  eth2
  .1.1   .1.2    .2.1   .2.2

    left -> right : 5mbit,  5ms
    right -> left : 10mbit, 100ms

Run:  sudo python3 q2_point_to_point_2.py

API used:
    Router      nest/topology/router.py    class Router  (its __init__ calls
                                           Node.enable_ip_forwarding automatically)
    add_route   nest/topology/node.py      Node.add_route
"""

from nest.topology import Node, Router, connect

# 1. Two hosts and one router. Router() turns on IPv4 forwarding for us.
h1 = Node("h1")
h2 = Node("h2")
r1 = Router("r1")                                # router.py -> super().__init__() + enable_ip_forwarding()

# 2. Two veth pairs: h1--r1 and r1--h2
(eth1, etr1a) = connect(h1, r1, "eth1", "etr1a")
(etr1b, eth2) = connect(r1, h2, "etr1b", "eth2")

# 3. Addresses: two separate /24 networks
eth1.set_address("192.168.1.1/24")               # network 1
etr1a.set_address("192.168.1.2/24")
etr1b.set_address("192.168.2.1/24")              # network 2
eth2.set_address("192.168.2.2/24")

# 4. Attributes, per direction
eth1.set_attributes("5mbit", "5ms")              # h1  -> r1
etr1b.set_attributes("5mbit", "5ms")             # r1  -> h2
etr1a.set_attributes("10mbit", "100ms")          # r1  -> h1
eth2.set_attributes("10mbit", "100ms")           # h2  -> r1

# 5. Each host needs a default route pointing at the router
h1.add_route("DEFAULT", eth1)                    # Node.add_route -> node.py
h2.add_route("DEFAULT", eth2)

# 6. Ping across the router
h1.ping(eth2.address, packets=5)
