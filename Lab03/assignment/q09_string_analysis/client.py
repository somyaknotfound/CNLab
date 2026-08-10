"""
Q9 (TCP) - client. Sends a sentence, prints the vowel/consonant/word counts.

Run:  python client.py                       (prompts)
      python client.py "Hello World"
"""
import socket
import sys

HOST = '127.0.0.1'
PORT = 5009


def main():
    if len(sys.argv) > 1:
        sentence = ' '.join(sys.argv[1:])
    else:
        sentence = input("Enter a sentence: ")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        client.sendall(sentence.encode())
        reply = client.recv(4096).decode()

    print("\n--- Analysis ---")
    print(reply)


if __name__ == '__main__':
    main()
