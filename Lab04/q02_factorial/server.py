"""Q2 - Concurrent TCP server using threads. Computes factorials for many clients at once."""
import math, socket, threading, time

HOST, PORT = '127.0.0.1', 6002


def handle(conn, addr):
    print(f"[+] {addr} handled by {threading.current_thread().name}")
    f = conn.makefile('r')
    for line in f:
        text = line.strip()
        if not text or text.lower() == 'quit':
            break
        try:
            n = int(text)
            if n < 0:
                reply = "Error: factorial is undefined for negative numbers"
            elif n > 5000:
                reply = "Error: n too large (limit 5000)"
            else:
                time.sleep(0.5)            # slow it down so concurrency is visible
                reply = f"{n}! = {math.factorial(n)}"
        except ValueError:
            reply = f"Error: {text!r} is not an integer"
        conn.sendall((reply + '\n').encode())
    conn.close()
    print(f"[-] {addr} done")


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
print(f"Factorial server on {HOST}:{PORT}")

try:
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
except KeyboardInterrupt:
    print("\nserver stopped")
finally:
    server.close()
