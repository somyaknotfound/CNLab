"""Practice 05 - framing messages with a length prefix.

TCP is a byte stream: send("AB") + send("CD") may arrive as one recv() of "ABCD".
Prefixing each message with its length makes boundaries explicit, which is what
you need for file transfer and for any protocol with more than one message.
"""
import socket

HOST, PORT = '127.0.0.1', 12345
HEADER = 8          # bytes used for the length field


def recv_exact(sock, n):
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def recv_msg(sock):
    header = recv_exact(sock, HEADER)
    if header is None:
        return None
    return recv_exact(sock, int.from_bytes(header, 'big'))


def send_msg(sock, payload: bytes):
    sock.sendall(len(payload).to_bytes(HEADER, 'big') + payload)


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(1)
print(f"[server] listening on {HOST}:{PORT}")

conn, addr = server.accept()
with conn:
    while True:
        msg = recv_msg(conn)
        if msg is None:
            break
        print(f"[server] got a {len(msg)}-byte message: {msg.decode()[:60]}")
        send_msg(conn, f"ok, {len(msg)} bytes".encode())
server.close()
