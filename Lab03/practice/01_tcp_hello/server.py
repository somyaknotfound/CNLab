import socket

HOST,PORT = '127.0.0.1' ,12345
server = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST,PORT))
server.listen(1)
print(f"[server] listening on {HOST}:{PORT}")

conn, addr = server.accept()
print(f"[server] connected by {addr}")

data = conn.recv(1024)
print(f"[server] received: {data.decode()}")
conn.sendall(b"Hello, Client!")
conn.close()
server.close()
print(f"[server] connection closed")
