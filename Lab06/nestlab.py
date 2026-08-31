"""
Small helpers shared by the Week-7 scripts.

Nothing clever here - each function is a few lines of plain NeST calls, pulled
out only because the six topologies repeat the same three shapes over and over.

NeST API used (paths inside the installed `nest` package):
    Node, Router, Switch, connect   nest/topology/{node,router,switch,connect}.py
    set_address, set_attributes     nest/topology/interface/base_interface.py
    add_route                       nest/topology/node.py
"""

from nest.topology import Node, Switch, connect

# The question papers show 20-100 PCs per department. Every host is a real Linux
# namespace, so the scripts create two per LAN (plus every named server) and keep
# the addressing exactly as the papers specify. Raise this only if your machine
# has the RAM: `ips()` uses it, and `lan()` creates one host per address given.
HOSTS_PER_LAN = 2


def lan(router, name, host_ips, gateway_ip, bw, delay, static_default=True):
    """
    One access LAN / VLAN: a Layer-2 switch, some PCs, and a router port that
    acts as the gateway (the SVI in the question papers).

    Returns (switch, router_interface, [(host, host_interface), ...]).
    """
    sw = Switch(f"sw-{name}")

    # Router port -> this is the default gateway for the LAN
    r_if, _ = connect(router, sw, f"e-{name}", f"{name}-r")
    r_if.set_address(gateway_ip)
    r_if.set_attributes(bw, delay)

    hosts = []
    for i, ip in enumerate(host_ips, 1):
        h = Node(f"{name}-pc{i}")
        h_if, _ = connect(h, sw, f"e-{name}{i}", f"{name}-s{i}")
        h_if.set_address(ip)
        h_if.set_attributes(bw, delay)
        if static_default:
            h.add_route("DEFAULT", h_if, r_if.address)
        hosts.append((h, h_if))

    return sw, r_if, hosts


def link(a, b, a_ip, b_ip, bw, delay, loss=None):
    """
    A point-to-point link between two routers (or a router and a switch).

    Returns (a_interface, b_interface).
    """
    a_if, b_if = connect(a, b)
    a_if.set_address(a_ip)
    b_if.set_address(b_ip)
    for iface in (a_if, b_if):
        iface.set_attributes(bw, delay)
        if loss:
            iface.set_packet_loss(loss)     # base_interface.py -> set_packet_loss
    return a_if, b_if


def ips(subnet_prefix, start=10, count=HOSTS_PER_LAN):
    """['192.168.10.10/24', '192.168.10.11/24', ...] for a /24 prefix."""
    return [f"{subnet_prefix}.{start + i}/24" for i in range(count)]


def enable_nat(router, wan_interface):
    """
    NAT overload (PAT) on `router`, translating everything that leaves
    `wan_interface` to that interface's address.

    NeST has no NAT API, so this shells out to iptables inside the router's
    namespace. `Node.id` is the namespace name and `BaseInterface.id` is the
    device name inside it - the same two values NeST's own engine passes to
    `ip` and `tc`.

    Requires iptables on the host.
    """
    from nest.engine.exec import exec_subprocess      # nest/engine/exec.py

    # exec_subprocess splits the string itself when shell=False, so a plain
    # string is what it wants here.
    rc = exec_subprocess(
        f"ip netns exec {router.id} iptables -t nat -A POSTROUTING "
        f"-o {wan_interface.id} -j MASQUERADE"
    )
    if rc != 0:
        print(f"WARNING: NAT setup on {router.name} failed (is iptables installed?)")
    return rc


def report(title, results):
    """Print a small PASS/FAIL table of ping results."""
    print(f"\n===== {title} =====")
    for label, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    print()
