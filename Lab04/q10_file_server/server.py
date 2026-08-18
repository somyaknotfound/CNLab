"""Q10 - Distributed file server: login, upload, download, list, per-client activity log.

Commands (one line each, header only; file bytes follow UPLOAD/DOWNLOAD):
  LOGIN|user|password
  UPLOAD|name|size      then <size> raw bytes
  DOWNLOAD|name         server replies OK|size then <size> raw bytes
  LIST|                 ERROR/OK line back
  QUIT|
"""
import os, socket, threading
from datetime import datetime

HOST, PORT = '127.0.0.1', 6010
HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, 'storage')
LOGDIR = os.path.join(HERE, 'logs')

USERS = {'asha': 'pass123', 'ravi': 'pass456'}      # in real life: store hashes
lock = threading.Lock()                             # protects the shared store


def log(user, action):
    os.makedirs(LOGDIR, exist_ok=True)
    stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(os.path.join(LOGDIR, f"{user}.log"), 'a') as f:
        f.write(f"[{stamp}] {action}\n")
    print(f"  {user}: {action}")


def handle(conn, addr):
    f = conn.makefile('rb')
    user = None

    while True:
        line = f.readline()
        if not line:
            break
        cmd, _, rest = line.decode().strip().partition('|')
        cmd = cmd.upper()

        if cmd == 'LOGIN':
            name, _, pw = rest.partition('|')
            if USERS.get(name) == pw:
                user = name
                log(user, f"logged in from {addr[0]}:{addr[1]}")
                conn.sendall(b"OK|login successful\n")
            else:
                conn.sendall(b"ERROR|invalid username or password\n")
            continue

        if user is None:                                  # everything else needs auth
            conn.sendall(b"ERROR|please LOGIN first\n")
            continue

        if cmd == 'UPLOAD':
            name, _, size = rest.partition('|')
            name, size = os.path.basename(name), int(size)
            data = f.read(size)
            with lock:
                os.makedirs(STORE, exist_ok=True)
                open(os.path.join(STORE, name), 'wb').write(data)
            log(user, f"uploaded {name} ({len(data)} bytes)")
            conn.sendall(f"OK|{name} uploaded ({len(data)} bytes)\n".encode())

        elif cmd == 'DOWNLOAD':
            path = os.path.join(STORE, os.path.basename(rest))
            if not os.path.isfile(path):
                conn.sendall(f"ERROR|{rest} not found\n".encode())
                log(user, f"failed download of {rest}")
            else:
                with lock:
                    data = open(path, 'rb').read()
                conn.sendall(f"OK|{len(data)}\n".encode())
                conn.sendall(data)
                log(user, f"downloaded {rest} ({len(data)} bytes)")

        elif cmd == 'LIST':
            files = sorted(os.listdir(STORE)) if os.path.isdir(STORE) else []
            conn.sendall(f"OK|{', '.join(files) or '(empty)'}\n".encode())
            log(user, "listed files")

        elif cmd == 'QUIT':
            log(user, "logged out")
            break
        else:
            conn.sendall(f"ERROR|unknown command {cmd!r}\n".encode())

    conn.close()


os.makedirs(STORE, exist_ok=True)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
print(f"Distributed file server on {HOST}:{PORT}")
print(f"storage: {STORE}\nlogs:    {LOGDIR}\nusers:   {', '.join(USERS)}")

try:
    while True:
        c, a = server.accept()
        threading.Thread(target=handle, args=(c, a), daemon=True).start()
except KeyboardInterrupt:
    print("\nserver stopped")
finally:
    server.close()
