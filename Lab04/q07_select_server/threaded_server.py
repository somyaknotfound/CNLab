"""Q7 - the threaded equivalent, for comparison with server.py (select-based)."""
import socket, threading

HOST, PORT = '127.0.0.1', 6017


def handle(conn, addr):
    conn.sendall(b"connected to the threaded server\n")
    for line in conn.makefile('r'):
        text = line.strip()
        if not text or text.lower() == 'quit':
            break
        conn.sendall((text.upper() + '\n').encode())
    conn.close()


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(50)
print(f"threaded server on {HOST}:{PORT}")

try:
    while True:
        c, a = server.accept()
        threading.Thread(target=handle, args=(c, a), daemon=True).start()
except KeyboardInterrupt:
    pass
finally:
    server.close()
