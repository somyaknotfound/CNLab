"""
Q6 (UDP) - Client info
Server receives a text message and displays it along with the client's IP
address and port number, then acknowledges.

Run:  python server.py
"""
import socket
from datetime import datetime

HOST = '0.0.0.0'      # listen on every interface so other machines can reach us
PORT = 5006


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    print(f"[Q6 server] UDP server listening on {HOST}:{PORT}")
    print("[Q6 server] Waiting for messages... (Ctrl+C to stop)\n")

    try:
        while True:
            data, addr = server.recvfrom(4096)
            client_ip, client_port = addr
            timestamp = datetime.now().strftime('%H:%M:%S')

            print("-" * 46)
            print(f"Time         : {timestamp}")
            print(f"Client IP    : {client_ip}")
            print(f"Client Port  : {client_port}")
            print(f"Bytes        : {len(data)}")
            print(f"Message      : {data.decode(errors='replace')}")
            print("-" * 46)

            ack = f"Received {len(data)} bytes from {client_ip}:{client_port}"
            server.sendto(ack.encode(), addr)
    except KeyboardInterrupt:
        print("\n[Q6 server] Stopped by user")
    finally:
        server.close()


if __name__ == '__main__':
    main()
