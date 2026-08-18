"""Q7 - client for the select() server. Run several at once.

    python client.py hello world     -> sends two messages then exits
    python client.py                 -> interactive
"""
import socket, sys

HOST, PORT = '127.0.0.1', 6007

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
reader = sock.makefile('r')
print(reader.readline().strip())

messages = sys.argv[1:]
if messages:
    for m in messages:
        sock.sendall((m + '\n').encode())
        print(f"{m} -> {reader.readline().strip()}")
else:
    while True:
        m = input("> ").strip()
        if not m or m.lower() == 'quit':
            break
        sock.sendall((m + '\n').encode())
        print(reader.readline().strip())

sock.close()
