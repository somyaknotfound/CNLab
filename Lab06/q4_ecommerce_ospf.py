"""
Q4 - E-commerce network: Mumbai HO + data centre, two branches, OSPF, NAT.

  Bangalore branch --10M,20ms,0.2%--\
                                      R-MUM (HO + DC) --20M,10ms-- ISP/Internet
  Chennai branch   --8M,30ms,0.3%---/

  Mumbai   VLAN10/20/30 = 192.168.10/20/30.0/24, VLAN40 DC = 192.168.40.0/24
  Bangalore VLAN10/20/30 = 192.168.110/120/130.0/24
  Chennai   VLAN10/20/30 = 192.168.210/220/230.0/24

Run:  sudo python3 q4_ecommerce_ospf.py
      sudo python3 q4_ecommerce_ospf.py 16mbit    # improvement: widen MUM-CHE

Needs FRR (or Quagga) installed for OSPF, and iptables for NAT.
VLANs are modelled as one switch + one gateway port each - see README.
"""

import sys

from nest import config
from nest.topology import Router
from nest.experiment import Experiment, Flow
from nest.routing.routing_helper import RoutingHelper

from nestlab import lan, link, report, enable_nat

CHE_BW = sys.argv[1] if len(sys.argv) > 1 else "8mbit"

config.set_value("routing_suite", "frr")      # nest/config.py -> set_value
config.set_value("routing_logs", True)

r_mum, r_blr, r_che, isp = (Router("r-mum"), Router("r-blr"),
                            Router("r-che"), Router("isp"))

# --- Mumbai head office + data centre ------------------------------------
_, mum_sales, _ = lan(r_mum, "m10", ["192.168.10.10/24", "192.168.10.11/24"],
                      "192.168.10.1/24", "100mbit", "1ms", static_default=False)
_, mum_inv, _ = lan(r_mum, "m20", ["192.168.20.10/24", "192.168.20.11/24"],
                    "192.168.20.1/24", "100mbit", "1ms", static_default=False)
_, mum_it, _ = lan(r_mum, "m30", ["192.168.30.10/24", "192.168.30.11/24"],
                   "192.168.30.1/24", "100mbit", "1ms", static_default=False)
# VLAN 40 is the data centre: web .10, app .20, db .30, mail .40
_, mum_dc, dc = lan(r_mum, "m40", ["192.168.40.10/24", "192.168.40.20/24"],
                    "192.168.40.1/24", "100mbit", "1ms", static_default=False)

# --- branches -------------------------------------------------------------
_, blr_sales, blr = lan(r_blr, "b10", ["192.168.110.10/24", "192.168.110.11/24"],
                        "192.168.110.1/24", "100mbit", "1ms", static_default=False)
_, blr_inv, _ = lan(r_blr, "b20", ["192.168.120.10/24", "192.168.120.11/24"],
                    "192.168.120.1/24", "100mbit", "1ms", static_default=False)
_, che_sales, che = lan(r_che, "c10", ["192.168.210.10/24", "192.168.210.11/24"],
                        "192.168.210.1/24", "100mbit", "1ms", static_default=False)
_, che_inv, _ = lan(r_che, "c20", ["192.168.220.10/24", "192.168.220.11/24"],
                    "192.168.220.1/24", "100mbit", "1ms", static_default=False)

# --- WAN links ------------------------------------------------------------
mum_blr, blr_mum = link(r_mum, r_blr, "10.1.1.1/30", "10.1.1.2/30",
                        "10mbit", "20ms", "0.2%")
mum_che, che_mum = link(r_mum, r_che, "10.1.1.5/30", "10.1.1.6/30",
                        CHE_BW, "30ms", "0.3%")
mum_isp, isp_mum = link(r_mum, isp, "203.0.113.1/30", "203.0.113.2/30",
                        "20mbit", "10ms")

# --- OSPF area 0 between the three company routers -----------------------
# The ISP is left out: a real ISP does not run your IGP. R-MUM gets a default
# route towards it, and NAT hides the private addressing behind 203.0.113.1.
RoutingHelper(protocol="ospf", routers=[r_mum, r_blr, r_che]).populate_routing_tables()

r_mum.add_route("DEFAULT", mum_isp)
enable_nat(r_mum, mum_isp)                    # NAT overload towards the ISP

# --- connectivity ---------------------------------------------------------
(web_server, web_if), (app_server, app_if) = dc
(blr_pc, blr_if), _ = blr
(che_pc, che_if), _ = che

report(f"Connectivity  (MUM-CHE = {CHE_BW})", [
    ("Bangalore PC -> Web server (DC)",
     blr_pc.ping(web_if.address, packets=5, verbose=0)),
    ("Chennai PC   -> App server (DC)",
     che_pc.ping(app_if.address, packets=5, verbose=0)),
    ("Bangalore PC -> Chennai PC (branch to branch via OSPF)",
     blr_pc.ping(che_if.address, packets=5, verbose=0)),
    ("Bangalore PC -> Internet   (NAT at R-MUM)",
     blr_pc.ping(isp_mum.address, packets=5, verbose=0)),
])

# --- peak-load traffic, all applications together (task 6) ---------------
exp = Experiment(f"q4-ecommerce-{CHE_BW}")

# Web (HTTP) and application access (TCP 8080) from both branches
exp.add_tcp_flow(Flow(blr_pc, web_server, web_if.get_address(), 0, 200, 2))
exp.add_tcp_flow(Flow(che_pc, web_server, web_if.get_address(), 0, 200, 2))
exp.add_tcp_flow(Flow(blr_pc, app_server, app_if.get_address(), 20, 200, 1))
exp.add_tcp_flow(Flow(che_pc, app_server, app_if.get_address(), 20, 200, 1))

# Bulk file transfer (FTP updates) - this is what saturates the branch links
exp.add_tcp_flow(Flow(che_pc, app_server, app_if.get_address(), 40, 200, 4))

# Video/streaming style UDP, to see loss and jitter under load
exp.add_udp_flow(Flow(blr_pc, web_server, web_if.get_address(), 40, 200, 1),
                 target_bandwidth="2mbit")

exp.require_qdisc_stats(mum_che)              # 8mbit + 30ms: the likely bottleneck
exp.require_qdisc_stats(mum_blr)
exp.run()
