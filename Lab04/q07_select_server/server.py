"""Q7 - Concurrent TCP server using select() instead of threads (I/O multiplexing).

One process, one thread, one loop. select() blocks until any socket is readable,
then tells us which ones. No thread per client, no locks, no context switching.
"""
import select, socket

HOST, PORT = '127.0.0.1', 6007

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
print(f"select() server on {HOST}:{PORT}  (single thread)")

sockets = [server]          # every socket we care about reading from

try:
    while True:
        readable, _, _ = select.select(sockets, [], [])   # blocks here

        for sock in readable:
            if sock is server:                            # a new client is waiting
                conn, addr = server.accept()
                conn.setblocking(False)
                sockets.append(conn)
                print(f"[+] {addr} connected ({len(sockets) - 1} clients)")
                conn.sendall(b"connected to the select() server\n")
            else:                                         # existing client sent data
                peer = sock.getpeername()
                try:
                    data = sock.recv(1024)
                except ConnectionResetError:
                    data = b''

                if not data:                              # client disconnected
                    print(f"[-] {peer} left ({len(sockets) - 2} clients)")
                    sockets.remove(sock)
                    sock.close()
                    continue

                text = data.decode().strip()
                print(f"    <- {text}")
                sock.sendall((text.upper() + '\n').encode())
except KeyboardInterrupt:
    print("\nserver stopped")
finally:
    for s in sockets:
        s.close()
