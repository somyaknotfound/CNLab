"""Q1 - Multi-client TCP chat server. One thread per client, messages broadcast to all."""
import socket, threading

HOST, PORT = '127.0.0.1', 6001

clients = {}                 # socket -> username
lock = threading.Lock()      # protects the shared dict


def broadcast(message, sender=None):
    with lock:
        for sock in list(clients):
            if sock is not sender:
                try:
                    sock.sendall((message + '\n').encode())
                except OSError:
                    pass


def handle(conn, addr):
    f = conn.makefile('r')                 # lets us read one line at a time
    name = f.readline().strip() or f"user{addr[1]}"

    with lock:
        clients[conn] = name
    print(f"[+] {name} joined ({len(clients)} online)")
    broadcast(f"*** {name} joined the chat ***", conn)
    conn.sendall(f"Welcome {name}! Type 'quit' to leave.\n".encode())

    try:
        for line in f:                     # ends when the client closes
            text = line.strip()
            if not text or text.lower() == 'quit':
                break
            print(f"{name}: {text}")
            broadcast(f"[{name}] {text}", conn)
    except OSError:
        pass                               # client vanished

    with lock:
        clients.pop(conn, None)
    conn.close()
    print(f"[-] {name} left ({len(clients)} online)")
    broadcast(f"*** {name} left the chat ***")


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
print(f"Chat server on {HOST}:{PORT}")

try:
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
except KeyboardInterrupt:
    print("\nserver stopped")
finally:
    server.close()
