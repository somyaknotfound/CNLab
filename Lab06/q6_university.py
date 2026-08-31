"""
Q6 - University network: blocks, hostel, library, data centre, Internet.

   Admin    VLAN10 192.168.10.0/24  --100M, 10ms
   Academic VLAN20 192.168.20.0/24  --100M, 10ms
   Library  VLAN30 192.168.30.0/24  --100M, 10ms -- R-CORE --100M,10ms-- R-BORDER
   Hostel   VLAN40 192.168.40.0/24  -- 50M, 20ms, 0.1%                     |
   DataCtr  VLAN50 192.168.50.0/24  --100M,  5ms                50M,30ms,0.2%
                                                                           |
                                                                        Internet

Run:  sudo python3 q6_university.py
      sudo python3 q6_university.py 100mbit    # improvement: widen the ISP link

Needs FRR (or Quagga) for OSPF and iptables for NAT.

NOTE: the question sheet gives the VLAN gateways as SVIs on R-CORE but also
lists /30 point-to-point links from R-CORE to each block. Those two models are
mutually exclusive; this program uses the SVI model (gateways on R-CORE, which
is what the addressing table specifies) and applies the L1-L5 bandwidth and
delay values to the R-CORE-to-block links. L6 and L7 stay as real /30s.
"""

import sys

from nest import config
from nest.topology import Router
from nest.experiment import Experiment, Flow
from nest.routing.routing_helper import RoutingHelper

from nestlab import lan, link, report, enable_nat

ISP_BW = sys.argv[1] if len(sys.argv) > 1 else "50mbit"

config.set_value("routing_suite", "frr")
config.set_value("routing_logs", True)

r_core, r_border, isp = Router("r-core"), Router("r-border"), Router("isp")

# --- the five campus segments, gateways on R-CORE ------------------------
_, admin_gw, admin = lan(r_core, "adm", ["192.168.10.10/24", "192.168.10.11/24"],
                         "192.168.10.1/24", "100mbit", "10ms", static_default=False)
_, acad_gw, acad = lan(r_core, "acd", ["192.168.20.10/24", "192.168.20.11/24"],
                       "192.168.20.1/24", "100mbit", "10ms", static_default=False)
_, lib_gw, lib = lan(r_core, "lib", ["192.168.30.10/24", "192.168.30.11/24"],
                     "192.168.30.1/24", "100mbit", "10ms", static_default=False)
_, hostel_gw, hostel = lan(r_core, "hos", ["192.168.40.10/24", "192.168.40.11/24"],
                           "192.168.40.1/24", "50mbit", "20ms", static_default=False)
# VLAN 50 data centre: LMS .10, database .20, file .30, DNS/web .40
_, dc_gw, dc = lan(r_core, "dc", ["192.168.50.10/24", "192.168.50.20/24",
                                  "192.168.50.30/24"],
                   "192.168.50.1/24", "100mbit", "5ms", static_default=False)

hostel_gw.set_packet_loss("0.1%")             # L4 is the lossy one

# --- core -> border -> ISP ------------------------------------------------
core_bdr, bdr_core = link(r_core, r_border, "10.0.0.21/30", "10.0.0.22/30",
                          "100mbit", "10ms")
bdr_isp, isp_bdr = link(r_border, isp, "203.0.113.1/30", "203.0.113.2/30",
                        ISP_BW, "30ms", "0.2%")

# --- OSPF area 0 between the two university routers ----------------------
RoutingHelper(protocol="ospf", routers=[r_core, r_border]).populate_routing_tables()

r_border.add_route("DEFAULT", bdr_isp)
enable_nat(r_border, bdr_isp)                 # NAT overload at the border router

# --- connectivity ---------------------------------------------------------
(lms_server, lms_if), (db_server, db_if), (file_server, file_if) = dc
(student_pc, student_if), _ = hostel
(faculty_pc, faculty_if), _ = acad
(admin_pc, _), _ = admin
(library_pc, _), _ = lib

report(f"Connectivity  (Border-ISP = {ISP_BW})", [
    ("Hostel student -> LMS server",
     student_pc.ping(lms_if.address, packets=5, verbose=0)),
    ("Faculty        -> Database server",
     faculty_pc.ping(db_if.address, packets=5, verbose=0)),
    ("Library PC     -> File server",
     library_pc.ping(file_if.address, packets=5, verbose=0)),
    ("Hostel student -> Internet (NAT at R-BORDER)",
     student_pc.ping(isp_bdr.address, packets=5, verbose=0)),
    ("Admin PC       -> Faculty PC (inter-VLAN at R-CORE)",
     admin_pc.ping(faculty_if.address, packets=5, verbose=0)),
])

# --- peak-load traffic (task 5) ------------------------------------------
exp = Experiment(f"q6-university-{ISP_BW}")

# Students browsing the Internet - this is what fills the 50mbit border link
exp.add_tcp_flow(Flow(student_pc, isp, isp_bdr.get_address(), 0, 200, 4))

# LMS access from students and faculty
exp.add_tcp_flow(Flow(student_pc, lms_server, lms_if.get_address(), 0, 200, 2))
exp.add_tcp_flow(Flow(faculty_pc, lms_server, lms_if.get_address(), 0, 200, 1))

# Database queries from the academic block
exp.add_tcp_flow(Flow(faculty_pc, db_server, db_if.get_address(), 20, 200, 1))

# Bulk file transfer from all departments
exp.add_tcp_flow(Flow(library_pc, file_server, file_if.get_address(), 40, 200, 4))

exp.require_qdisc_stats(bdr_isp)              # 50mbit / 30ms / 0.2%: the bottleneck
exp.require_qdisc_stats(hostel_gw)
exp.run()
