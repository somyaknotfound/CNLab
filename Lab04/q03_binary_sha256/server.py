"""Q3 - Receives a binary file and verifies integrity with a SHA-256 checksum.

Protocol:  "<filename>|<size>|<sha256>\n"  then <size> raw bytes.
"""
import hashlib, os, socket

HOST, PORT = '127.0.0.1', 6003
SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'received')

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
os.makedirs(SAVE_DIR, exist_ok=True)
print(f"File server on {HOST}:{PORT}, saving to {SAVE_DIR}")

try:
    while True:
        conn, addr = server.accept()
        f = conn.makefile('rb')
        name, size, expected = f.readline().decode().strip().split('|')
        size = int(size)
        name = os.path.basename(name)                  # block path traversal
        print(f"receiving {name} ({size} bytes) from {addr[0]}")

        sha = hashlib.sha256()
        got = 0
        with open(os.path.join(SAVE_DIR, name), 'wb') as out:
            while got < size:
                chunk = f.read(min(4096, size - got))  # binary mode, chunked
                if not chunk:
                    break
                out.write(chunk)
                sha.update(chunk)
                got += len(chunk)

        actual = sha.hexdigest()
        if got != size:
            reply = f"FAIL: incomplete ({got}/{size} bytes)"
        elif actual == expected:
            reply = f"OK: {name} verified, sha256={actual[:16]}..."
        else:
            reply = f"FAIL: checksum mismatch\n  expected {expected}\n  actual   {actual}"

        print(reply)
        conn.sendall((reply + '\n').encode())
        conn.close()
except KeyboardInterrupt:
    print("\nserver stopped")
finally:
    server.close()
