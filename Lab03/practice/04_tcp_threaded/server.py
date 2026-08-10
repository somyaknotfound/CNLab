"""Practice 04 - concurrent TCP server using one thread per client.

Open three terminals and run the client in two of them at the same time to see
that both are served simultaneously.
"""
import socket
import threading

HOST, PORT = '127.0.0.1', 12345


def handle_client(conn, addr):
    print(f"[server] + {addr} (active threads: {threading.active_count() - 1})")
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data.decode().upper().encode())
    print(f"[server] - {addr}")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[server] listening on {HOST}:{PORT}")
    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client,
                             args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[server] shutting down")
    finally:
        server.close()


if __name__ == '__main__':
    main()
