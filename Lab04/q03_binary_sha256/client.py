"""Q3 - sends a binary file plus its SHA-256 checksum.

    python client.py send/sample.png
"""
import hashlib, os, socket, sys

HOST, PORT = '127.0.0.1', 6003
HERE = os.path.dirname(os.path.abspath(__file__))
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'send', 'sample.bin')

if not os.path.isfile(path):
    sys.exit(f"no such file: {path}")

with open(path, 'rb') as fh:                  # 'rb' - never text mode for binary
    data = fh.read()

digest = hashlib.sha256(data).hexdigest()
name = os.path.basename(path)
print(f"sending {name}, {len(data)} bytes, sha256={digest[:16]}...")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
sock.sendall(f"{name}|{len(data)}|{digest}\n".encode())
sock.sendall(data)
print("server:", sock.makefile('r').readline().strip())
sock.close()
