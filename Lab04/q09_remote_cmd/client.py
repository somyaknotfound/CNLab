"""Q9 - remote shell client.

    python client.py date        -> one command
    python client.py             -> interactive, 'exit' to quit
"""
import socket, sys

HOST, PORT = '127.0.0.1', 6009

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
reader = sock.makefile('r')


def run(command):
    sock.sendall((command + '\n').encode())
    n = int(reader.readline())                # first line = how many lines follow
    for _ in range(n):
        print("  " + reader.readline().rstrip())


if len(sys.argv) > 1:
    run(' '.join(sys.argv[1:]))
else:
    print("Connected. Type a command ('exit' to quit).")
    while True:
        command = input("remote$ ").strip()
        if not command:
            continue
        if command.lower() == 'exit':
            sock.sendall(b"exit\n")
            break
        run(command)

sock.close()
