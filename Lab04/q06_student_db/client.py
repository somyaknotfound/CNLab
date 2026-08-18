"""Q6 - menu-driven student record client.

    python client.py                              -> menu
    python client.py "INSERT|101|Asha|88"         -> one-shot raw command
"""
import socket, sys

HOST, PORT = '127.0.0.1', 6006
MENU = """
1. Insert a record
2. Delete a record
3. Search a record
4. Update a record
5. Display all records
6. Exit
"""

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
reader = sock.makefile('r')


def send(command):
    sock.sendall((command + '\n').encode())
    reply = reader.readline().strip()
    for record in reply.split(' ;; '):
        print("  ", record)
    print()


if len(sys.argv) > 1:
    send(sys.argv[1])
else:
    while True:
        print(MENU)
        choice = input("Choice: ").strip()
        if choice == '6':
            break
        elif choice in ('1', '4'):
            roll = input("Roll  : ").strip()
            name = input("Name  : ").strip()
            marks = input("Marks : ").strip()
            send(f"{'INSERT' if choice == '1' else 'UPDATE'}|{roll}|{name}|{marks}")
        elif choice in ('2', '3'):
            roll = input("Roll: ").strip()
            send(f"{'DELETE' if choice == '2' else 'SEARCH'}|{roll}")
        elif choice == '5':
            send("DISPLAY|")
        else:
            print("Invalid choice\n")

sock.close()
