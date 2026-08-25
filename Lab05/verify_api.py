#!/usr/bin/env python3
"""
Checks that every NeST API used in this folder actually exists in the installed
`nest` package, and prints the file and line number where each one is defined.

Runs WITHOUT sudo: it parses the package source instead of importing it
(importing `nest` calls sys.exit() when you are not root).

    python3 verify_api.py
"""
import ast
import importlib.util
import os
import sys

# what we use  ->  (module file inside the nest package, class or None)
USED = [
    ("Node",                 "topology/node.py",                      None),
    ("Router",               "topology/router.py",                    None),
    ("Switch",               "topology/switch.py",                    None),
    ("connect",              "topology/connect.py",                   None),
    ("Address",              "topology/address.py",                   None),
    ("ping",                 "topology/node.py",                      "Node"),
    ("add_route",            "topology/node.py",                      "Node"),
    ("enable_ip_forwarding", "topology/node.py",                      "Node"),
    ("disable_ip_dad",       "topology/node.py",                      "Node"),
    ("capture_packets",      "topology/node.py",                      "Node"),
    ("set_address",          "topology/interface/base_interface.py",  "BaseInterface"),
    ("get_address",          "topology/interface/base_interface.py",  "BaseInterface"),
    ("address",              "topology/interface/base_interface.py",  "BaseInterface"),
    ("set_attributes",       "topology/interface/base_interface.py",  "BaseInterface"),
    ("set_bandwidth",        "topology/interface/base_interface.py",  "BaseInterface"),
    ("set_delay",            "topology/interface/base_interface.py",  "BaseInterface"),
    ("set_qdisc",            "topology/interface/base_interface.py",  "BaseInterface"),
    ("set_packet_loss",      "topology/interface/base_interface.py",  "BaseInterface"),
    ("set_value",            "config.py",                             None),
    ("delete_namespaces",    "clean_up.py",                           None),
]


def find_nest():
    spec = importlib.util.find_spec("nest")      # does not execute the package
    if spec is None or not spec.submodule_search_locations:
        sys.exit("nest is not installed.  pip3 install nest")
    return spec.submodule_search_locations[0]


def locate(root, rel_path, name, cls):
    path = os.path.join(root, rel_path)
    if not os.path.exists(path):
        return None
    tree = ast.parse(open(path, encoding='utf-8').read())

    scope = tree.body
    if cls:
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == cls:
                scope = node.body
                break
        else:
            return None

    for node in scope:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name:
            return node.lineno
    return None


def main():
    root = find_nest()
    print(f"nest package: {root}\n")
    print(f"{'API':<22} {'defined in':<40} {'line':>5}")
    print("-" * 70)

    missing = 0
    for name, rel_path, cls in USED:
        line = locate(root, rel_path, name, cls)
        label = f"{cls}.{name}" if cls else name
        if line is None:
            print(f"{label:<22} {'NOT FOUND — API may have changed':<40}")
            missing += 1
        else:
            print(f"{label:<22} nest/{rel_path:<35} {line:>5}")

    print("-" * 70)
    print("all APIs present" if not missing else f"{missing} API(s) not found")
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
