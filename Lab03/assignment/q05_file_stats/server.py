"""
Q5 (TCP) - File processing
Client sends a filename; the server opens that file on ITS OWN disk and returns
the number of lines, words and characters.

Files are read from the 'files' directory next to this script.

Run:  python server.py
"""
import os
import socket

HOST = '127.0.0.1'
PORT = 5005
FILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')


def file_stats(filename: str) -> str:
    # Reject path traversal: the client must not be able to ask for ../../etc/passwd
    safe_name = os.path.basename(filename)
    path = os.path.join(FILE_DIR, safe_name)

    if not os.path.isfile(path):
        return f"Error: file {safe_name!r} not found on the server"

    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except OSError as e:
        return f"Error: could not read the file ({e})"

    lines = len(content.splitlines())
    words = len(content.split())
    chars = len(content)

    return (f"File   : {safe_name}\n"
            f"Lines  : {lines}\n"
            f"Words  : {words}\n"
            f"Chars  : {chars}")


def main():
    os.makedirs(FILE_DIR, exist_ok=True)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[Q5 server] Listening on {HOST}:{PORT}")
    print(f"[Q5 server] Serving files from {FILE_DIR}")

    try:
        while True:
            conn, addr = server.accept()
            print(f"[Q5 server] Connection from {addr[0]}:{addr[1]}")
            with conn:
                data = conn.recv(1024)
                if not data:
                    continue
                filename = data.decode().strip()
                print(f"[Q5 server] Request for {filename!r}")
                conn.sendall(file_stats(filename).encode())
    except KeyboardInterrupt:
        print("\n[Q5 server] Stopped by user")
    finally:
        server.close()


if __name__ == '__main__':
    main()
