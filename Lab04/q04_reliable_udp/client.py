"""Q4 - Reliable file transfer over UDP (sender side).

Sends one packet, waits for its ACK, retransmits on timeout. That is stop-and-wait
ARQ: sequence numbers + acknowledgments + timeout + retransmission.
"""
import os, socket, sys

HOST, PORT = '127.0.0.1', 6004
CHUNK, TIMEOUT, MAX_TRIES = 1024, 1.0, 8

HERE = os.path.dirname(os.path.abspath(__file__))
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'send.txt')

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(TIMEOUT)
retransmissions = 0


def send_reliably(seq, payload):
    """Keep sending until the matching ACK arrives."""
    global retransmissions
    packet = f"{seq}|".encode() + payload
    for attempt in range(MAX_TRIES):
        sock.sendto(packet, (HOST, PORT))
        try:
            ack, _ = sock.recvfrom(64)
            if ack.decode() == f"ACK{seq}":
                print(f"seq {seq}: ACKed" + (f" after {attempt} retry(s)" if attempt else ""))
                return True
        except socket.timeout:
            retransmissions += 1
            print(f"seq {seq}: timeout, retransmitting ({attempt + 1})")
    return False


with open(path, 'rb') as f:
    data = f.read()

seq = 0
send_reliably(seq, b'START:' + os.path.basename(path).encode())
for i in range(0, len(data), CHUNK):
    seq += 1
    if not send_reliably(seq, data[i:i + CHUNK]):
        sys.exit("gave up: too many retransmissions")
send_reliably(seq + 1, b'END')

print(f"\nsent {len(data)} bytes in {seq} chunk(s), {retransmissions} retransmission(s)")
sock.close()
