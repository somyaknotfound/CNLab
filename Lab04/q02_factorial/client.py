"""Q2 - client. Run several copies at the same time to see the server serve them in parallel.

    python client.py 5 10 20      -> sends three numbers
    python client.py              -> interactive
"""
import socket, sys, time

HOST, PORT = '127.0.0.1', 6002

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
f = sock.makefile('r')

numbers = sys.argv[1:]
start = time.time()

if numbers:
    for n in numbers:
        sock.sendall((n + '\n').encode())
        print(f.readline().strip())
else:
    while True:
        n = input("n (or 'quit'): ").strip()
        if not n or n.lower() == 'quit':
            break
        sock.sendall((n + '\n').encode())
        print(f.readline().strip())

print(f"elapsed: {time.time() - start:.2f}s")
sock.close()
