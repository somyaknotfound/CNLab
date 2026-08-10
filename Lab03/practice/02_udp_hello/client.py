"""Practice 02 - minimal UDP client. No connect() needed."""
import socket

HOST, PORT = '127.0.0.1', 12345

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.sendto(b"Hello from the UDP client", (HOST, PORT))

data, addr = client.recvfrom(1024)
print(f"[client] reply from {addr}: {data.decode()}")

client.close()
