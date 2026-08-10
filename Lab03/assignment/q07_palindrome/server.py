"""
Q7 (TCP) - Palindrome check
Server accepts a string from the client and reports whether it is a palindrome.

Run:  python server.py
"""
import socket

HOST = '127.0.0.1'
PORT = 5007


def normalise(text: str) -> str:
    """Keep letters and digits only, lowercased.
    So 'A man, a plan, a canal: Panama' counts as a palindrome."""
    return ''.join(ch.lower() for ch in text if ch.isalnum())


def check_palindrome(text: str) -> str:
    cleaned = normalise(text)
    if not cleaned:
        return f"{text!r} contains no alphanumeric characters to check"

    is_pal = cleaned == cleaned[::-1]
    verdict = "IS a palindrome" if is_pal else "is NOT a palindrome"
    return f"{text!r} {verdict}  (normalised: {cleaned!r}, reversed: {cleaned[::-1]!r})"


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[Q7 server] Listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            print(f"[Q7 server] Connection from {addr[0]}:{addr[1]}")
            with conn:
                data = conn.recv(4096)
                if not data:
                    continue
                text = data.decode().strip()
                result = check_palindrome(text)
                print(f"[Q7 server] {result}")
                conn.sendall(result.encode())
    except KeyboardInterrupt:
        print("\n[Q7 server] Stopped by user")
    finally:
        server.close()


if __name__ == '__main__':
    main()
