"""
Q3 (UDP) - Number theory
Client sends an integer; server replies whether it is prime.

Note the absence of listen() and accept() - UDP is connectionless.

Run:  python server.py
"""
import socket

HOST = '127.0.0.1'
PORT = 5003


def is_prime(n: int) -> bool:
    """Trial division up to sqrt(n). O(sqrt(n))."""
    if n < 2:
        return False
    if n < 4:            # 2 and 3
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    print(f"[Q3 server] UDP socket bound to {HOST}:{PORT}")

    try:
        while True:
            data, addr = server.recvfrom(1024)
            text = data.decode().strip()
            try:
                n = int(text)
                reply = f"{n} is {'a PRIME' if is_prime(n) else 'NOT a prime'} number"
            except ValueError:
                reply = f"Error: {text!r} is not a valid integer"

            print(f"[Q3 server] {addr[0]}:{addr[1]} asked about {text!r} -> {reply}")
            server.sendto(reply.encode(), addr)
    except KeyboardInterrupt:
        print("\n[Q3 server] Stopped by user")
    finally:
        server.close()


if __name__ == '__main__':
    main()
