"""
Q4 (TCP) - Echo server
Receives messages from a client and sends the same message back, until the
client sends "exit".

Run:  python server.py
"""
import socket

HOST = '127.0.0.1'
PORT = 5004


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[Q4 server] Echo server listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            print(f"[Q4 server] Client connected: {addr[0]}:{addr[1]}")
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:                     # client vanished
                        print("[Q4 server] Client disconnected abruptly")
                        break

                    message = data.decode().strip()
                    print(f"[Q4 server] <- {message!r}")

                    if message.lower() == 'exit':
                        conn.sendall(b"Connection closed by server. Bye!")
                        print("[Q4 server] 'exit' received, closing this connection")
                        break

                    conn.sendall(message.encode())   # echo it back unchanged
            print("[Q4 server] Waiting for the next client...")
    except KeyboardInterrupt:
        print("\n[Q4 server] Stopped by user")
    finally:
        server.close()


if __name__ == '__main__':
    main()
