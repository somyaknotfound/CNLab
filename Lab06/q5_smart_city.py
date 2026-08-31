"""
Q5 - Smart city network: City Hall, public services, surveillance, public Wi-Fi.

                          City Hall (R-CH)  --50M,10ms-- ISP / Internet
   VLAN10 Admin      192.168.10.0/24   |
   VLAN20 Employees  192.168.20.0/24   +--20M,20ms,0.1%-- R-PSD  (public services)
   VLAN30 Servers    192.168.30.0/24   +--15M,25ms,0.1%-- R-SCC  (surveillance)
   VLAN40 CCTV mgmt  192.168.40.0/24   +--10M,30ms,0.2%-- R-WIFI (public Wi-Fi)
   VLAN50 WiFi mgmt  192.168.50.0/24

Run:  sudo python3 q5_smart_city.py
      sudo python3 q5_smart_city.py 20mbit    # improvement: widen the Wi-Fi link

Needs FRR (or Quagga) for OSPF and iptables for NAT.
"""

import sys

from nest import config
from nest.topology import Router
from nest.experiment import Experiment, Flow
from nest.routing.routing_helper import RoutingHelper

from nestlab import lan, link, report, enable_nat

WIFI_BW = sys.argv[1] if len(sys.argv) > 1 else "10mbit"

config.set_value("routing_suite", "frr")
config.set_value("routing_logs", True)

r_ch, r_psd, r_scc, r_wifi, isp = (Router("r-ch"), Router("r-psd"), Router("r-scc"),
                                   Router("r-wifi"), Router("isp"))

# --- City Hall VLANs ------------------------------------------------------
_, v10, admin = lan(r_ch, "v10", ["192.168.10.10/24", "192.168.10.11/24"],
                    "192.168.10.1/24", "100mbit", "1ms", static_default=False)
_, v20, employees = lan(r_ch, "v20", ["192.168.20.10/24", "192.168.20.11/24"],
                        "192.168.20.1/24", "100mbit", "1ms", static_default=False)
# VLAN 30 is the city data centre: app .10, database .20, CCTV storage .30
_, v30, datacentre = lan(r_ch, "v30", ["192.168.30.10/24", "192.168.30.20/24",
                                       "192.168.30.30/24"],
                         "192.168.30.1/24", "100mbit", "1ms", static_default=False)

# --- the three remote sites, each with its own access LAN ----------------
_, psd_lan, psd = lan(r_psd, "psd", ["192.168.20.101/24", "192.168.20.102/24"],
                      "192.168.20.100/24", "100mbit", "1ms", static_default=False)
_, scc_lan, scc = lan(r_scc, "scc", ["192.168.40.101/24", "192.168.40.102/24"],
                      "192.168.40.1/24", "100mbit", "1ms", static_default=False)
_, wifi_lan, wifi = lan(r_wifi, "wifi", ["192.168.50.2/24", "192.168.50.21/24"],
                        "192.168.50.1/24", "100mbit", "1ms", static_default=False)

# --- WAN links ------------------------------------------------------------
ch_psd, psd_ch = link(r_ch, r_psd, "10.0.0.1/30", "10.0.0.2/30",
                      "20mbit", "20ms", "0.1%")
ch_scc, scc_ch = link(r_ch, r_scc, "10.0.0.5/30", "10.0.0.6/30",
                      "15mbit", "25ms", "0.1%")
ch_wifi, wifi_ch = link(r_ch, r_wifi, "10.0.0.9/30", "10.0.0.10/30",
                        WIFI_BW, "30ms", "0.2%")
ch_isp, isp_ch = link(r_ch, isp, "203.0.113.1/30", "203.0.113.2/30",
                      "50mbit", "10ms")

# --- OSPF area 0 across the city routers ---------------------------------
RoutingHelper(protocol="ospf",
              routers=[r_ch, r_psd, r_scc, r_wifi]).populate_routing_tables()

r_ch.add_route("DEFAULT", ch_isp)
enable_nat(r_ch, ch_isp)                      # NAT overload at the City Hall router

# --- connectivity ---------------------------------------------------------
(app_server, app_if), (db_server, db_if), (cctv_store, cctv_if) = datacentre
(service_pc, service_if), _ = psd
(cctv_op, cctv_op_if), (analytics, _) = scc
(ap1, ap1_if), _ = wifi
(admin_pc, _), _ = admin

report(f"Connectivity  (Wi-Fi link = {WIFI_BW})", [
    ("Public services -> Application server",
     service_pc.ping(app_if.address, packets=5, verbose=0)),
    ("Surveillance    -> CCTV storage server",
     cctv_op.ping(cctv_if.address, packets=5, verbose=0)),
    ("Wi-Fi AP        -> Internet (NAT at R-CH)",
     ap1.ping(isp_ch.address, packets=5, verbose=0)),
    ("Admin PC        -> Database server",
     admin_pc.ping(db_if.address, packets=5, verbose=0)),
    ("Public services -> Surveillance (site to site via OSPF)",
     service_pc.ping(cctv_op_if.address, packets=5, verbose=0)),
])

# --- peak-hour traffic, everything at once (task 6) ----------------------
exp = Experiment(f"q5-smart-city-{WIFI_BW}")

# City data access (TCP 8080) and database queries (TCP 3306)
exp.add_tcp_flow(Flow(service_pc, app_server, app_if.get_address(), 0, 200, 2))
exp.add_tcp_flow(Flow(admin_pc, db_server, db_if.get_address(), 0, 200, 1))

# CCTV stream: constant-rate UDP, surveillance -> storage. Loss here is visible
# as dropped video, so this is the flow to watch.
exp.add_udp_flow(Flow(cctv_op, cctv_store, cctv_if.get_address(), 0, 200, 2),
                 target_bandwidth="6mbit")

# Public Wi-Fi users browsing the Internet over the narrowest link
exp.add_tcp_flow(Flow(ap1, app_server, app_if.get_address(), 20, 200, 4))

exp.require_qdisc_stats(ch_wifi)              # 10mbit / 30ms / 0.2%: the bottleneck
exp.require_qdisc_stats(ch_scc)
exp.run()
