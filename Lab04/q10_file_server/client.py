"""Q10 - file server client.

    python client.py asha pass123                          -> interactive menu
    python client.py asha pass123 upload downloads/a.txt
    python client.py asha pass123 download a.txt
    python client.py asha pass123 list
"""
import os, socket, sys

HOST, PORT = '127.0.0.1', 6010
HERE = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS = os.path.join(HERE, 'downloads')

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
f = sock.makefile('rb')


def reply():
    status, _, message = f.readline().decode().strip().partition('|')
    return status, message


def login(user, password):
    sock.sendall(f"LOGIN|{user}|{password}\n".encode())
    status, message = reply()
    print(f"{status}: {message}")
    return status == 'OK'


def upload(path):
    if not os.path.isfile(path):
        return print(f"no such file: {path}")
    data = open(path, 'rb').read()
    sock.sendall(f"UPLOAD|{os.path.basename(path)}|{len(data)}\n".encode())
    sock.sendall(data)
    print("  ", reply()[1])


def download(name):
    sock.sendall(f"DOWNLOAD|{name}\n".encode())
    status, message = reply()
    if status != 'OK':
        return print("  ", message)
    data = f.read(int(message))
    os.makedirs(DOWNLOADS, exist_ok=True)
    open(os.path.join(DOWNLOADS, name), 'wb').write(data)
    print(f"   saved downloads/{name} ({len(data)} bytes)")


def listing():
    sock.sendall(b"LIST|\n")
    print("  files:", reply()[1])


user = sys.argv[1] if len(sys.argv) > 1 else input("Username: ")
password = sys.argv[2] if len(sys.argv) > 2 else input("Password: ")

if login(user, password):
    args = sys.argv[3:]
    if args:
        action = args[0].lower()
        if action == 'upload':   upload(args[1])
        elif action == 'download': download(args[1])
        elif action == 'list':   listing()
    else:
        while True:
            choice = input("\n1) list  2) upload  3) download  4) quit\nChoice: ").strip()
            if choice == '1':   listing()
            elif choice == '2': upload(input("Local file path: ").strip())
            elif choice == '3': download(input("Filename on server: ").strip())
            elif choice == '4': break
            else: print("invalid choice")

sock.sendall(b"QUIT|\n")
sock.close()
