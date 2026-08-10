"""
Q5 (TCP) - client. Sends a filename, prints the line/word/character counts.

Run:  python client.py               (prompts)
      python client.py sample.txt
"""
import socket
import sys

HOST = '127.0.0.1'
PORT = 5005


def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else input("Enter the filename: ").strip()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        client.sendall(filename.encode())
        reply = client.recv(4096).decode()

    print("\n--- Server response ---")
    print(reply)


if __name__ == '__main__':
    main()
