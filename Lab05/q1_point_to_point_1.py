"""
Q1 - Point-to-point network between two hosts.

    h1 ---------------- h2
     eth1            eth2
   192.168.1.1/24   192.168.1.2/24

    h1 -> h2 : 5mbit,  5ms
    h2 -> h1 : 10mbit, 100ms

Run:  sudo python3 q1_point_to_point_1.py

API used (file inside the installed `nest` package):
    Node            nest/topology/node.py            class Node
    connect         nest/topology/connect.py         def connect
    set_address     nest/topology/interface/base_interface.py   BaseInterface.set_address
    set_attributes  nest/topology/interface/base_interface.py   BaseInterface.set_attributes
    ping            nest/topology/node.py            Node.ping
"""

from nest.topology import Node, connect          # nest/topology/__init__.py re-exports both

# 1. Create the two hosts (each becomes a Linux network namespace)
h1 = Node("h1")                                  # Node.__init__  -> node.py
h2 = Node("h2")

# 2. Connect them with a veth pair; returns the interface at each end
(eth1, eth2) = connect(h1, h2, "eth1", "eth2")   # connect() -> connect.py

# 3. Assign IP addresses
eth1.set_address("192.168.1.1/24")               # BaseInterface.set_address
eth2.set_address("192.168.1.2/24")

# 4. Link attributes shape the traffic LEAVING that interface
eth1.set_attributes("5mbit", "5ms")              # h1 -> h2 direction
eth2.set_attributes("10mbit", "100ms")           # h2 -> h1 direction

# 5. Ping h2 from h1
h1.ping(eth2.address, packets=5)                 # Node.ping ; .address -> BaseInterface.address
