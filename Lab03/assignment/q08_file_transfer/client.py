"""
Q8 (TCP) - File transfer, sending side.

Run:  python client.py                  (prompts, defaults to send/demo.txt)
      python client.py send/demo.txt
"""
import os
import socket
import sys

HOST = '127.0.0.1'
PORT = 5008
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, 'send', 'demo.txt')


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        entered = input(f"File to send [{DEFAULT}]: ").strip()
        path = entered or DEFAULT

    if not os.path.isfile(path):
        print(f"Error: '{path}' does not exist")
        return

    filename = os.path.basename(path)
    with open(path, 'rb') as f:            # binary mode - works for any file type
        content = f.read()

    print(f"Sending {filename} ({len(content)} bytes) to {HOST}:{PORT}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))

        name_bytes = filename.encode()
        client.sendall(len(name_bytes).to_bytes(4, 'big'))   # filename length
        client.sendall(name_bytes)                           # filename
        client.sendall(len(content).to_bytes(8, 'big'))      # content length
        client.sendall(content)                              # content

        print("Server:", client.recv(1024).decode())


if __name__ == '__main__':
    main()
