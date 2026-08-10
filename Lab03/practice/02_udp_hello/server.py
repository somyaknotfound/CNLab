"""Practice 02 - minimal UDP server.

Note what is missing compared to TCP: no listen(), no accept(), no connection.
recvfrom() hands you the sender's address so you know where to reply.
"""
import socket

HOST, PORT = '127.0.0.1', 12345

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
print(f"[server] UDP socket bound to {HOST}:{PORT}")

data, addr = server.recvfrom(1024)
print(f"[server] datagram from {addr[0]}:{addr[1]} -> {data.decode()}")

server.sendto(b"Hello from the UDP server", addr)
server.close()
