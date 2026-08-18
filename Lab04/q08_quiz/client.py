"""Q8 - quiz client.

    python client.py Asha            -> interactive
    python client.py Asha 2 3 2 3 2  -> auto-answers (handy for testing)
"""
import socket, sys

HOST, PORT = '127.0.0.1', 6008

name = sys.argv[1] if len(sys.argv) > 1 else input("Your name: ").strip()
auto = list(sys.argv[2:])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
sock.sendall((name + '\n').encode())
reader = sock.makefile('r')

for line in reader:
    line = line.strip()
    if line.startswith('DONE|'):
        print("\n" + line[5:].replace(' || ', '\n'))
        break
    question, _, options = line.partition(' | ')
    print("\n" + question)
    print("  " + options)
    answer = auto.pop(0) if auto else input("Your answer (1-4): ").strip()
    sock.sendall((answer + '\n').encode())

sock.close()
