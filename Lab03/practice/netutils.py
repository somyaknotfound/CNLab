"""
netutils.py - small helpers reused across the practice programs.

Import from a sibling folder with:

    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from netutils import make_tcp_server, recv_exact
"""
import socket

HOST = '127.0.0.1'
PORT = 12345


def make_tcp_server(host=HOST, port=PORT, backlog=5):
    """Create a bound, listening TCP server socket with SO_REUSEADDR set."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(backlog)
    return s


def make_tcp_client(host=HOST, port=PORT, timeout=None):
    """Create a TCP socket already connected to the server."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if timeout:
        s.settimeout(timeout)
    s.connect((host, port))
    return s


def make_udp_server(host=HOST, port=PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    return s


def make_udp_client():
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def recv_exact(sock, n):
    """Read exactly n bytes. Returns None if the peer closes early."""
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def send_msg(sock, data: bytes):
    """Send a length-prefixed message (8-byte big-endian header)."""
    sock.sendall(len(data).to_bytes(8, 'big') + data)


def recv_msg(sock):
    """Receive a length-prefixed message. Returns None on clean close."""
    header = recv_exact(sock, 8)
    if header is None:
        return None
    return recv_exact(sock, int.from_bytes(header, 'big'))


def recv_line(sock, buffer=b''):
    r"""Read until b'\n'. Returns (line_without_newline, leftover_buffer)."""
    while b'\n' not in buffer:
        chunk = sock.recv(1024)
        if not chunk:
            return (buffer or None), b''
        buffer += chunk
    line, _, rest = buffer.partition(b'\n')
    return line, rest
