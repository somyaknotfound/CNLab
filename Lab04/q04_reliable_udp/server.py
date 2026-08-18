"""Q4 - Reliable file transfer over UDP (receiver side).

Stop-and-wait: for every packet received, send back an ACK carrying its sequence
number. Duplicate packets (caused by a lost ACK) are ACKed again but not written.

Packet format:  b"<seq>|<data>"      ACK format: b"ACK<seq>"
"""
import os, random, socket

HOST, PORT = '127.0.0.1', 6004
LOSS = 0.2          # probability of pretending an incoming packet was lost

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((HOST, PORT))
print(f"Reliable-UDP receiver on {HOST}:{PORT} (simulated loss {LOSS:.0%})")

out = None
expected = 0
try:
    while True:
        packet, addr = sock.recvfrom(2048)

        if random.random() < LOSS:                 # simulate the network dropping it
            print("  ...packet dropped (simulated)")
            continue

        seq_bytes, _, payload = packet.partition(b'|')
        seq = int(seq_bytes)

        if payload.startswith(b'START:'):
            name = os.path.basename(payload[6:].decode())
            out = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), name), 'wb')
            expected = 0
            print(f"start receiving {name}")
        elif payload == b'END':
            if out:
                out.close()
                out = None
            print("transfer complete\n")

        if seq == expected:                        # new, in-order data
            if out and not payload.startswith(b'START:') and payload != b'END':
                out.write(payload)
                print(f"  seq {seq}: {len(payload)} bytes written")
            expected += 1
        else:
            print(f"  seq {seq}: duplicate, re-ACKing")

        sock.sendto(f"ACK{seq}".encode(), addr)    # ACK every packet we accept
except KeyboardInterrupt:
    print("\nreceiver stopped")
finally:
    sock.close()
