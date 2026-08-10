"""Practice 03 - server that keeps running and handles clients one after another,
and stays in a conversation with each client until it says 'bye'.

This is the shape most lab questions want.
"""
import socket

HOST, PORT = '127.0.0.1', 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
print(f"[server] listening on {HOST}:{PORT}  (Ctrl+C to stop)")

try:
    while True:
        conn, addr = server.accept()
        print(f"[server] client connected: {addr}")
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:                       # client closed the socket
                    print("[server] client disconnected")
                    break
                msg = data.decode().strip()
                print(f"[server] <- {msg}")
                if msg.lower() == 'bye':
                    conn.sendall(b"Goodbye")
                    break
                conn.sendall(f"echo: {msg}".encode())
except KeyboardInterrupt:
    print("\n[server] shutting down")
finally:
    server.close()
