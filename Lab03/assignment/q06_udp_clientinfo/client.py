"""
Q6 (UDP) - client. Sends text messages to the server. Blank line or 'exit' to quit.

Run:  python client.py                 (interactive)
      python client.py hello there     (single message)
"""
import socket
import sys

HOST = '127.0.0.1'
PORT = 5006
TIMEOUT = 5


def send_once(client, message):
    client.sendto(message.encode(), (HOST, PORT))
    try:
        ack, _ = client.recvfrom(1024)
        print("Server ack:", ack.decode())
    except socket.timeout:
        print(f"No acknowledgement within {TIMEOUT}s (UDP is unreliable by design)")


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(TIMEOUT)

    # The client's source port is assigned by the OS on the first sendto().
    try:
        if len(sys.argv) > 1:
            send_once(client, ' '.join(sys.argv[1:]))
        else:
            print(f"Sending to {HOST}:{PORT}. Blank line or 'exit' to quit.\n")
            while True:
                message = input("Message: ").strip()
                if not message or message.lower() == 'exit':
                    break
                send_once(client, message)
                print(f"(my socket was {client.getsockname()[0]}:{client.getsockname()[1]})\n")
    finally:
        client.close()


if __name__ == '__main__':
    main()
