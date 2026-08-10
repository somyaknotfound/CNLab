"""Practice 03 - interactive client. Type 'bye' to finish."""
import socket

HOST, PORT = '127.0.0.1', 12345

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
print("[client] connected. Type 'bye' to quit.")

while True:
    msg = input("> ")
    if not msg:
        continue
    client.sendall(msg.encode())
    reply = client.recv(1024).decode()
    print("[client]", reply)
    if msg.lower() == 'bye':
        break

client.close()
