"""
Q3 - Hospital network with a remote clinic and service prioritisation.

  Hospital LAN (Bengaluru)                      Remote clinic (Mangalore)
   VLAN10 Patient records 192.168.10.0/24        Staff PC    10.10.20.10
   VLAN20 Doctors         192.168.20.0/24        Patient PC  10.10.20.20
   VLAN30 Administration  192.168.30.0/24        Med device  10.10.30.10
                     R-HOSPITAL ==== WAN ==== R-CLINIC
                        512kbit, 50ms, 1% loss

Run:  sudo python3 q3_hospital_qos.py            # baseline: one FIFO for everything
      sudo python3 q3_hospital_qos.py qos        # fq_codel on the WAN link

The point of the exercise: on a 512kbit link a bulk file transfer fills the
queue, and patient-record traffic then waits behind it. Compare the delay and
throughput of the critical flows between the two runs.

NOTE on addressing: the question sheet gives R-HOSPITAL G0/0 as 192.168.1.2/30
and R-CLINIC G0/1 as 10.10.10.2/30 - two different subnets cannot form one
point-to-point link, so the WAN here is a single 192.168.1.0/30 transit.
Everything else follows the sheet.

NOTE on VLANs: NeST has no 802.1Q API, so each VLAN is its own switch + its own
gateway port on R-HOSPITAL. Same subnets, same gateways, same routing.
"""

import sys

from nest.topology import Router
from nest.experiment import Experiment, Flow

from nestlab import lan, link, report

QOS = len(sys.argv) > 1 and sys.argv[1].lower() == "qos"

r_hosp, r_clinic = Router("r-hosp"), Router("r-clinic")

# --- hospital VLANs -------------------------------------------------------
_, v10, records = lan(r_hosp, "v10", ["192.168.10.10/24", "192.168.10.11/24"],
                      "192.168.10.1/24", "100mbit", "1ms")
_, v20, doctors = lan(r_hosp, "v20", ["192.168.20.10/24", "192.168.20.11/24"],
                      "192.168.20.1/24", "100mbit", "1ms")
_, v30, admin = lan(r_hosp, "v30", ["192.168.30.10/24", "192.168.30.11/24"],
                    "192.168.30.1/24", "100mbit", "1ms")

# --- remote clinic --------------------------------------------------------
_, c_lan, clinic_pcs = lan(r_clinic, "cln", ["10.10.20.10/24", "10.10.20.20/24"],
                           "10.10.20.1/24", "100mbit", "1ms")
_, c_dev, devices = lan(r_clinic, "med", ["10.10.30.10/24"],
                        "10.10.30.1/24", "100mbit", "1ms")

# --- the constrained WAN link --------------------------------------------
h_wan, c_wan = link(r_hosp, r_clinic, "192.168.1.1/30", "192.168.1.2/30",
                    "512kbit", "50ms", "1%")

# Task 6: give the critical traffic a better queue.
# fq_codel isolates thin, latency-sensitive flows from a bulk transfer instead
# of letting one FIFO serve them in arrival order.
if QOS:
    h_wan.set_qdisc("fq_codel")           # base_interface.py -> set_qdisc
    c_wan.set_qdisc("fq_codel")

# --- routing --------------------------------------------------------------
HOSPITAL_NETS = ["192.168.10.0/24", "192.168.20.0/24", "192.168.30.0/24"]
CLINIC_NETS = ["10.10.20.0/24", "10.10.30.0/24"]

for net in CLINIC_NETS:
    r_hosp.add_route(net, h_wan)
for net in HOSPITAL_NETS:
    r_clinic.add_route(net, c_wan)

# --- connectivity ---------------------------------------------------------
(pr_server, pr_if), _ = records
(doc_server, doc_if), _ = doctors
(adm_server, adm_if), _ = admin
(staff_pc, staff_if), (patient_pc, _) = clinic_pcs
(med_device, med_if), = devices

report(f"Connectivity  (QoS = {'fq_codel' if QOS else 'default FIFO'})", [
    ("Clinic staff -> patient-record server  (CRITICAL)",
     staff_pc.ping(pr_if.address, packets=5, verbose=0)),
    ("Med device   -> patient-record server  (CRITICAL)",
     med_device.ping(pr_if.address, packets=5, verbose=0)),
    ("Clinic staff -> doctors server",
     staff_pc.ping(doc_if.address, packets=5, verbose=0)),
    ("Hospital admin -> clinic staff PC",
     adm_server.ping(staff_if.address, packets=5, verbose=0)),
])

# --- task 4/5: run everything at once and compare -------------------------
exp = Experiment("q3-hospital-" + ("qos" if QOS else "baseline"))

# Bulk, non-critical: a big file transfer clinic -> hospital, fills the pipe
exp.add_tcp_flow(Flow(patient_pc, adm_server, adm_if.get_address(), 0, 200, 4))

# Video streaming from the hospital, also non-critical
exp.add_udp_flow(Flow(doc_server, staff_pc, staff_if.get_address(), 0, 200, 1),
                 target_bandwidth="256kbit")

# CRITICAL: patient records and the medical device. Thin flows that must stay
# responsive while the transfer above is saturating the link.
exp.add_tcp_flow(Flow(staff_pc, pr_server, pr_if.get_address(), 20, 200, 1))
exp.add_tcp_flow(Flow(med_device, pr_server, pr_if.get_address(), 20, 200, 1))

exp.require_qdisc_stats(c_wan)            # queue at the clinic end of the WAN
exp.run()
