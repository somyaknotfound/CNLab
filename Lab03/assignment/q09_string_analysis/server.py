"""
Q9 (TCP) - String analysis
Client sends a sentence; the server returns the number of vowels, consonants
and words.

Run:  python server.py
"""
import socket

HOST = '127.0.0.1'
PORT = 5009
VOWELS = set('aeiou')


def analyse(sentence: str) -> str:
    vowels = consonants = 0

    for ch in sentence.lower():
        if ch.isalpha():                 # ignore digits, spaces, punctuation
            if ch in VOWELS:
                vowels += 1
            else:
                consonants += 1

    words = len(sentence.split())        # split() collapses runs of whitespace

    return (f"Sentence   : {sentence}\n"
            f"Vowels     : {vowels}\n"
            f"Consonants : {consonants}\n"
            f"Words      : {words}")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[Q9 server] Listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            print(f"[Q9 server] Connection from {addr[0]}:{addr[1]}")
            with conn:
                data = conn.recv(8192)
                if not data:
                    continue
                sentence = data.decode().strip()
                report = analyse(sentence)
                print(f"[Q9 server] analysed {sentence!r}")
                conn.sendall(report.encode())
    except KeyboardInterrupt:
        print("\n[Q9 server] Stopped by user")
    finally:
        server.close()


if __name__ == '__main__':
    main()
