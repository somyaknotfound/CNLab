"""
Q2 - TechNova multi-site network: VLANs at HO, two branches, WAN via an ISP.

  HO Bengaluru                ISP                Branch Pune
   VLAN10 servers  192.168.10.0/24    5M,20ms,0.2%   VLAN20 192.168.120.0/24
   VLAN20 HR       192.168.20.0/24  --------------   VLAN30 192.168.130.0/24
   VLAN30 Engg     192.168.30.0/24        |
   VLAN40 Sales    192.168.40.0/24        |          Branch Hyderabad
                                    3M,30ms,0.5%     VLAN20 192.168.220.0/24
                        Internet 203.0.113.0/30      VLAN30 192.168.230.0/24

Run:  sudo python3 q2_corporate_vlans.py
      sudo python3 q2_corporate_vlans.py 8mbit    # improvement: fatter Hyd link

NOTE on VLANs: NeST has no 802.1Q API (there is no vlan module in nest/topology/).
A VLAN is a broadcast domain with its own subnet and its own gateway, so each
VLAN here is modelled as its own Switch plus its own router port. That is
functionally router-on-a-stick with one physical port per VLAN instead of one
tagged trunk - the IP addressing, the gateways and the routing are unchanged.

NOTE on DHCP: NeST has no DHCP server API either. Addresses are assigned
statically from the pool the question specifies.
"""

import sys

from nest.topology import Router
from nest.experiment import Experiment, Flow

from nestlab import lan, link, report

HYD_BW = sys.argv[1] if len(sys.argv) > 1 else "3mbit"

r_ho, r_pune, r_hyd, isp = (Router("r-ho"), Router("r-pune"),
                            Router("r-hyd"), Router("isp"))

# --- Head Office VLANs ----------------------------------------------------
_, ho_v10, servers = lan(r_ho, "v10", ["192.168.10.10/24", "192.168.10.12/24"],
                         "192.168.10.1/24", "100mbit", "1ms")
_, ho_v20, hr = lan(r_ho, "v20", ["192.168.20.21/24", "192.168.20.22/24"],
                    "192.168.20.1/24", "100mbit", "1ms")
_, ho_v30, engg = lan(r_ho, "v30", ["192.168.30.31/24", "192.168.30.32/24"],
                      "192.168.30.1/24", "100mbit", "1ms")
_, ho_v40, sales = lan(r_ho, "v40", ["192.168.40.41/24", "192.168.40.42/24"],
                       "192.168.40.1/24", "100mbit", "1ms")

# --- Branch VLANs ---------------------------------------------------------
_, pune_v20, pune_hr = lan(r_pune, "p20", ["192.168.120.21/24", "192.168.120.22/24"],
                           "192.168.120.1/24", "100mbit", "1ms")
_, pune_v30, pune_eng = lan(r_pune, "p30", ["192.168.130.31/24", "192.168.130.32/24"],
                            "192.168.130.1/24", "100mbit", "1ms")
_, hyd_v20, hyd_hr = lan(r_hyd, "h20", ["192.168.220.21/24", "192.168.220.22/24"],
                         "192.168.220.1/24", "100mbit", "1ms")
_, hyd_v30, hyd_eng = lan(r_hyd, "h30", ["192.168.230.31/24", "192.168.230.32/24"],
                          "192.168.230.1/24", "100mbit", "1ms")

# --- WAN links (the interesting part: limited bandwidth and real loss) ----
ho_isp, isp_ho = link(r_ho, isp, "10.0.0.1/30", "10.0.0.2/30", "5mbit", "20ms", "0.2%")
pune_isp, isp_pune = link(r_pune, isp, "10.0.0.5/30", "10.0.0.6/30",
                          "5mbit", "20ms", "0.2%")
hyd_isp, isp_hyd = link(r_hyd, isp, "10.0.0.9/30", "10.0.0.10/30",
                        HYD_BW, "30ms", "0.5%")

# The "Internet" is one more node behind the ISP
internet = Router("internet")
isp_net, net_isp = link(isp, internet, "203.0.113.1/30", "203.0.113.2/30",
                        "20mbit", "10ms")

# --- static routing between sites ----------------------------------------
HO_NETS = ["192.168.10.0/24", "192.168.20.0/24",
           "192.168.30.0/24", "192.168.40.0/24"]
PUNE_NETS = ["192.168.120.0/24", "192.168.130.0/24"]
HYD_NETS = ["192.168.220.0/24", "192.168.230.0/24"]

# Every site sends anything it does not own towards the ISP
r_ho.add_route("DEFAULT", ho_isp)
r_pune.add_route("DEFAULT", pune_isp)
r_hyd.add_route("DEFAULT", hyd_isp)

# The ISP is the hub, so it needs a route back into each site
for net in HO_NETS:
    isp.add_route(net, isp_ho)
for net in PUNE_NETS:
    isp.add_route(net, isp_pune)
for net in HYD_NETS:
    isp.add_route(net, isp_hyd)
isp.add_route("DEFAULT", isp_net)

for net in HO_NETS + PUNE_NETS + HYD_NETS:           # return path from Internet
    internet.add_route(net, net_isp)

# --- connectivity ---------------------------------------------------------
(file_server, file_if), (web_server, web_if) = servers
(pune_pc, pune_if), _ = pune_hr
(hyd_pc, hyd_if), _ = hyd_hr
(hr_pc, hr_if), _ = hr

report(f"Connectivity (Hyderabad link = {HYD_BW})", [
    ("HO HR -> HO servers      (inter-VLAN at the HO router)",
     hr_pc.ping(file_if.address, packets=5, verbose=0)),
    ("Pune PC -> File server   (WAN, 5mbit 20ms 0.2% loss)",
     pune_pc.ping(file_if.address, packets=5, verbose=0)),
    ("Hyd PC  -> File server   (WAN, slowest link)",
     hyd_pc.ping(file_if.address, packets=5, verbose=0)),
    ("Pune PC -> Internet",
     pune_pc.ping(net_isp.address, packets=5, verbose=0)),
    ("Pune PC -> Hyd PC        (branch to branch, via ISP)",
     pune_pc.ping(hyd_if.address, packets=5, verbose=0)),
])

# --- the three applications, all running at once (task 7 + 8) ------------
exp = Experiment(f"q2-corporate-{HYD_BW}")

# (a) file transfer: branches -> file server, TCP, the bulk traffic
exp.add_tcp_flow(Flow(pune_pc, file_server, file_if.get_address(), 0, 200, 4))
exp.add_tcp_flow(Flow(hyd_pc, file_server, file_if.get_address(), 0, 200, 4))

# (b) video conference: branches -> HO, UDP, sensitive to jitter and loss
exp.add_udp_flow(Flow(pune_pc, hr_pc, hr_if.get_address(), 20, 200, 1),
                 target_bandwidth="1mbit")
exp.add_udp_flow(Flow(hyd_pc, hr_pc, hr_if.get_address(), 20, 200, 1),
                 target_bandwidth="1mbit")

# (c) web browsing: branches -> web server
exp.add_tcp_flow(Flow(pune_pc, web_server, web_if.get_address(), 40, 200, 1))

exp.require_qdisc_stats(hyd_isp)        # the 3mbit link is the suspected bottleneck
exp.require_qdisc_stats(pune_isp)
exp.run()
