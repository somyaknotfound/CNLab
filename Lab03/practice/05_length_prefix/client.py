"""Practice 05 - sends three messages back to back, including a large one.
Without framing these would blur together on the server side.
"""
import socket

HOST, PORT = '127.0.0.1', 12345
HEADER = 8


def recv_exact(sock, n):
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def send_msg(sock, payload: bytes):
    sock.sendall(len(payload).to_bytes(HEADER, 'big') + payload)


def recv_msg(sock):
    header = recv_exact(sock, HEADER)
    if header is None:
        return None
    return recv_exact(sock, int.from_bytes(header, 'big'))


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((HOST, PORT))
    for payload in [b"first", b"second", b"X" * 50000]:
        send_msg(client, payload)
        print("[client]", recv_msg(client).decode())
