"""Q5 - menu-driven client.

    python client.py                 -> interactive menu
    python client.py CALC "12 + 5"   -> one-shot
"""
import socket, sys

HOST, PORT = '127.0.0.1', 6005
MENU = """
1. Calculator      (e.g. 12 + 5)
2. String ops      (e.g. hello world)
3. File transfer   (e.g. notes.txt)
4. Time service
5. Exit
"""
CHOICES = {'1': ('CALC', 'Expression: '), '2': ('STRING', 'Text: '),
           '3': ('FILE', 'Filename: '), '4': ('TIME', None)}

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
reader = sock.makefile('r')


def ask(service, arg=''):
    sock.sendall(f"{service}|{arg}\n".encode())
    print("Result:", reader.readline().strip(), "\n")


if len(sys.argv) > 1:
    ask(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '')
else:
    while True:
        print(MENU)
        choice = input("Choose a service: ").strip()
        if choice == '5':
            break
        if choice not in CHOICES:
            print("Invalid choice\n")
            continue
        service, prompt = CHOICES[choice]
        ask(service, input(prompt).strip() if prompt else '')

sock.close()
