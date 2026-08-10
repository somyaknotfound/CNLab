"""
Q8 (TCP) - File transfer, receiving side
Receives a text file from the client and saves it in 'received/'.

Protocol (length-prefixed, so it works for files of any size):
    [4 bytes ] length of the filename
    [n bytes ] the filename (UTF-8)
    [8 bytes ] length of the file content
    [m bytes ] the file content
    <- server replies with a status line

Run:  python server.py
"""
import os
import socket

HOST = '127.0.0.1'
PORT = 5008
SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'received')


def recv_exact(sock, n):
    """Read exactly n bytes. Returns None if the peer closes early.
    Necessary because TCP is a stream: one recv() may return fewer bytes."""
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(min(4096, n - len(buf)))
        if not chunk:
            return None
        buf += chunk
    return buf


def handle(conn, addr):
    header = recv_exact(conn, 4)
    if header is None:
        print("[Q8 server] Client closed before sending anything")
        return
    name_len = int.from_bytes(header, 'big')

    filename = recv_exact(conn, name_len).decode()
    filename = os.path.basename(filename)            # block path traversal

    size = int.from_bytes(recv_exact(conn, 8), 'big')
    print(f"[Q8 server] Incoming: {filename} ({size} bytes) from {addr[0]}:{addr[1]}")

    os.makedirs(SAVE_DIR, exist_ok=True)
    path = os.path.join(SAVE_DIR, filename)

    received = 0
    with open(path, 'wb') as f:
        while received < size:
            chunk = conn.recv(min(4096, size - received))
            if not chunk:
                break
            f.write(chunk)
            received += len(chunk)

    if received == size:
        status = f"OK: '{filename}' received ({received} bytes), saved to received/"
    else:
        status = f"INCOMPLETE: expected {size} bytes, got {received}"

    print(f"[Q8 server] {status}")
    conn.sendall(status.encode())


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[Q8 server] Listening on {HOST}:{PORT}")
    print(f"[Q8 server] Files will be saved to {SAVE_DIR}")

    try:
        while True:
            conn, addr = server.accept()
            with conn:
                handle(conn, addr)
    except KeyboardInterrupt:
        print("\n[Q8 server] Stopped by user")
    finally:
        server.close()


if __name__ == '__main__':
    main()
