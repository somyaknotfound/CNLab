"""
Q4 (TCP) - echo client. Type messages; type 'exit' to end the session.

Run:  python client.py
"""
import socket

HOST = '127.0.0.1'
PORT = 5004


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        print(f"Connected to echo server at {HOST}:{PORT}. Type 'exit' to quit.\n")

        while True:
            message = input("You  : ").strip()
            if not message:
                continue

            client.sendall(message.encode())
            reply = client.recv(1024).decode()
            print(f"Echo : {reply}")

            if message.lower() == 'exit':
                break

    print("Disconnected.")


if __name__ == '__main__':
    main()
