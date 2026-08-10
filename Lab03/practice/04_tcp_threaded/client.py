"""Practice 04 - client for the threaded server. Blank line to quit."""
import socket

HOST, PORT = '127.0.0.1', 12345

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((HOST, PORT))
    print("[client] connected. Empty line to quit.")
    while True:
        msg = input("> ")
        if not msg:
            break
        client.sendall(msg.encode())
        print("[client]", client.recv(1024).decode())
