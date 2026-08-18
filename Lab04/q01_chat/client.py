"""Q1 - chat client. One thread receives, the main thread sends."""
import socket, sys, threading, time

HOST, PORT = '127.0.0.1', 6001

name = sys.argv[1] if len(sys.argv) > 1 else input("Username: ").strip()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
sock.sendall((name + '\n').encode())


def receive():
    for line in sock.makefile('r'):
        print('\r' + line.strip() + '\n> ', end='')
    print("\nDisconnected from server.")


threading.Thread(target=receive, daemon=True).start()

try:
    while True:
        msg = input('> ').strip()
        if not msg:
            continue
        sock.sendall((msg + '\n').encode())
        if msg.lower() == 'quit':
            time.sleep(0.3)          # let the receiver thread print what is pending
            break
except (KeyboardInterrupt, EOFError):
    pass
finally:
    sock.close()
