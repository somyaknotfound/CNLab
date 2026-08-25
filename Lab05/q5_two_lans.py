"""
Q5 - Two LANs joined directly by a switch-to-switch link.

  h1 h2 h3 -- s1 ----100mbit,1ms---- s2 -- h4 h5 h6

All six hosts are in ONE subnet 192.168.1.0/24, so the two switches simply
extend the same Layer-2 broadcast domain. No router and no routes required.

Run:  sudo python3 q5_two_lans.py
"""

from nest.topology import Node, Switch, connect

# 1. Six hosts, two switches
h1, h2, h3 = Node("h1"), Node("h2"), Node("h3")
h4, h5, h6 = Node("h4"), Node("h5"), Node("h6")
s1, s2 = Switch("s1"), Switch("s2")

# 2. LAN-1 -> s1, LAN-2 -> s2
(eth1, ets1a) = connect(h1, s1, "eth1", "ets1a")
(eth2, ets1b) = connect(h2, s1, "eth2", "ets1b")
(eth3, ets1c) = connect(h3, s1, "eth3", "ets1c")
(eth4, ets2a) = connect(h4, s2, "eth4", "ets2a")
(eth5, ets2b) = connect(h5, s2, "eth5", "ets2b")
(eth6, ets2c) = connect(h6, s2, "eth6", "ets2c")

# 3. The switch-to-switch trunk link
(ets1d, ets2d) = connect(s1, s2, "ets1d", "ets2d")

# 4. One subnet for everybody
eth1.set_address("192.168.1.1/24")
eth2.set_address("192.168.1.2/24")
eth3.set_address("192.168.1.3/24")
eth4.set_address("192.168.1.4/24")
eth5.set_address("192.168.1.5/24")
eth6.set_address("192.168.1.6/24")

# 5. 100mbit / 1ms everywhere, including the trunk
for iface in (eth1, eth2, eth3, eth4, eth5, eth6,
              ets1a, ets1b, ets1c, ets2a, ets2b, ets2c, ets1d, ets2d):
    iface.set_attributes("100mbit", "1ms")

# 6. Cross-LAN pings still work at Layer 2
h1.ping(eth4.address, packets=5)
h2.ping(eth5.address, packets=5)
h3.ping(eth6.address, packets=5)
