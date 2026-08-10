"""
Q3 (UDP) - client. Sends an integer, prints the verdict.

Run:  python client.py         (prompts)
      python client.py 97      (from the command line)
"""
import socket
import sys

HOST = '127.0.0.1'
PORT = 5003
TIMEOUT = 5


def main():
    number = sys.argv[1] if len(sys.argv) > 1 else input("Enter an integer: ").strip()

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(TIMEOUT)          # UDP can silently lose a datagram
    try:
        client.sendto(number.encode(), (HOST, PORT))
        reply, _ = client.recvfrom(1024)
        print("Server says:", reply.decode())
    except socket.timeout:
        print(f"No reply within {TIMEOUT}s - is the server running?")
    finally:
        client.close()


if __name__ == '__main__':
    main()
