import socket

HOST,PORT = '127.0.0.1' , 12345
client = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
client.connect((HOST,PORT))

print(f"[client] connected to {HOST}: {PORT}")

client.sendall(b"Hello, Server!")

reply = client.recv(1024)
print(f"[client] received: {reply.decode()}")
client.close()
