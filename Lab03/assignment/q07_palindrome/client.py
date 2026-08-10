"""
Q7 (TCP) - client. Sends a string, prints the palindrome verdict.

Run:  python client.py            (prompts)
      python client.py racecar
"""
import socket
import sys

HOST = '127.0.0.1'
PORT = 5007


def main():
    text = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else input("Enter a string: ")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        client.sendall(text.encode())
        reply = client.recv(4096).decode()

    print("Server:", reply)


if __name__ == '__main__':
    main()
