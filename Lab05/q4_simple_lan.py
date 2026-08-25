"""
Q4 - Simple LAN: four hosts on one switch.

    h1   h2      h3   h4      all links 100mbit, 1ms
     \    \      /    /       all hosts in 192.168.1.0/24
      ------ s1 ------

Run:  sudo python3 q4_simple_lan.py

API used:
    Switch   nest/topology/switch.py   class Switch(Node, BaseInterface)
             -> creates a namespace AND a Linux bridge inside it

Note: a switch works at Layer 2, so its ports get no IP addresses.
"""

from nest.topology import Node, Switch, connect

# 1. Four hosts and one switch
h1, h2, h3, h4 = Node("h1"), Node("h2"), Node("h3"), Node("h4")
s1 = Switch("s1")                                # switch.py -> Node.__init__ + Bridge

# 2. Each host gets a veth pair to the switch.
#    connect() returns (host_side, switch_side); the switch side needs no address.
(eth1, ets1a) = connect(h1, s1, "eth1", "ets1a")
(eth2, ets1b) = connect(h2, s1, "eth2", "ets1b")
(eth3, ets1c) = connect(h3, s1, "eth3", "ets1c")
(eth4, ets1d) = connect(h4, s1, "eth4", "ets1d")

# 3. All four hosts share one subnet
eth1.set_address("192.168.1.1/24")
eth2.set_address("192.168.1.2/24")
eth3.set_address("192.168.1.3/24")
eth4.set_address("192.168.1.4/24")

# 4. Same attributes on both ends of every link
for iface in (eth1, eth2, eth3, eth4, ets1a, ets1b, ets1c, ets1d):
    iface.set_attributes("100mbit", "1ms")

# 5. Pings stay inside the LAN - no routes needed, the switch floods/learns
h1.ping(eth2.address, packets=5)
h3.ping(eth4.address, packets=5)
