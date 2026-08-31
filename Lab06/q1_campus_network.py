"""
Q1 - University campus network with departments and Internet access.

  CSE(192.168.10.0/24) ┐
  ECE(192.168.20.0/24) ┼- R1 -10M,10ms- R2 -5M,20ms- R3 -5M,50ms- R4 (ISP)
  ME (192.168.30.0/24) ┘                             |
                                          Server LAN 192.168.100.0/24

All inter-department traffic goes through the core router R1. Static routing only.

Run:  sudo python3 q1_campus_network.py
      sudo python3 q1_campus_network.py 2mbit      # task 9: shrink R2<->R3
"""

import sys

from nest.topology import Router
from nest.experiment import Experiment, Flow

from nestlab import lan, link, report

# Task 9 asks for the same test with R2<->R3 at 2mbit. Pass it on the command line.
R2R3_BW = sys.argv[1] if len(sys.argv) > 1 else "5mbit"

# The task list says R3<->R4 is 20ms, the topology diagram says 50ms.
# The diagram is per-link and more specific, so we follow it.
R3R4_DELAY = "50ms"

r1, r2, r3, r4 = Router("r1"), Router("r2"), Router("r3"), Router("r4")

# --- department LANs, all hanging off the core router R1 -------------------
_, r1_cse, cse = lan(r1, "cse", ["192.168.10.2/24", "192.168.10.3/24"],
                     "192.168.10.1/24", "100mbit", "1ms")
_, r1_ece, ece = lan(r1, "ece", ["192.168.20.2/24", "192.168.20.3/24"],
                     "192.168.20.1/24", "100mbit", "1ms")
_, r1_me, me = lan(r1, "me", ["192.168.30.2/24", "192.168.30.3/24"],
                   "192.168.30.1/24", "100mbit", "1ms")

# --- server LAN on the Internet-edge router R3 ----------------------------
_, r3_srv, srv = lan(r3, "srv", ["192.168.100.2/24"],
                     "192.168.100.1/24", "100mbit", "1ms")

# --- the router backbone --------------------------------------------------
r1_r2, r2_r1 = link(r1, r2, "10.0.0.1/24", "10.0.0.2/24", "10mbit", "10ms")
r2_r3, r3_r2 = link(r2, r3, "20.0.0.1/24", "20.0.0.2/24", R2R3_BW, "20ms")
r3_r4, r4_r3 = link(r3, r4, "30.0.0.1/24", "30.0.0.2/24", "5mbit", R3R4_DELAY)

# --- static routing -------------------------------------------------------
CAMPUS = ["192.168.10.0/24", "192.168.20.0/24", "192.168.30.0/24"]

r1.add_route("DEFAULT", r1_r2)                       # R1 knows its three LANs

for net in CAMPUS:                                   # R2 reaches the LANs via R1
    r2.add_route(net, r2_r1)
r2.add_route("DEFAULT", r2_r3)

for net in CAMPUS + ["10.0.0.0/24"]:                 # R3 reaches everything via R2
    r3.add_route(net, r3_r2)
r3.add_route("DEFAULT", r3_r4)                       # ...except the Internet

for net in CAMPUS + ["10.0.0.0/24", "20.0.0.0/24", "192.168.100.0/24"]:
    r4.add_route(net, r4_r3)                         # ISP route back into campus

# --- task 7: connectivity tests ------------------------------------------
(cse1, cse1_if), (cse2, _) = cse
(ece1, ece1_if), _ = ece
(me1, me1_if), _ = me
(server, server_if), = srv

report(f"Ping tests (R2<->R3 = {R2R3_BW})", [
    ("CSE-PC1 -> ECE-PC1  (inter-department, via R1)",
     cse1.ping(ece1_if.address, packets=5, verbose=0)),
    ("CSE-PC1 -> ME-PC1   (inter-department, via R1)",
     cse1.ping(me1_if.address, packets=5, verbose=0)),
    ("ECE-PC1 -> Server   (via R1-R2-R3)",
     ece1.ping(server_if.address, packets=5, verbose=0)),
    ("CSE-PC1 -> Internet (R4, via R1-R2-R3-R4)",
     cse1.ping(r4_r3.address, packets=5, verbose=0)),
])

# --- task 8: TCP throughput CSE-PC1 -> Server ----------------------------
# The bottleneck is whichever backbone link is slowest: R2<->R3.
exp = Experiment(f"q1-campus-{R2R3_BW}")
exp.add_tcp_flow(Flow(cse1, server, server_if.get_address(), 0, 30, 1))
exp.require_qdisc_stats(r2_r3)                       # watch the bottleneck queue
exp.run()
