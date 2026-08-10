import socket
import sys

HOST = '127.0.0.1'
PORT = 5001

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"[server] listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            with conn:
                print(f"[Q1 server] Connection from {addr[0]}:{addr[1]}")
                data = conn.recv(4096)
                if not data:
                    continue
                text = data.decode()
                result = text.upper()
                print(f"[Q1 server] received: {text}, sending back: {result}")
                conn.sendall(result.encode())
    except KeyboardInterrupt:
        print("\n[Q1 server] shutting down...")
    finally:
        server.close()
if __name__ == "__main__":
    main()
