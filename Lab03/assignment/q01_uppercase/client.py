import socket
import sys

HOST = '127.0.0.1'
PORT = 5001

def main():
    text = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else input("Enter a string to convert to uppercase: ")

    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as client:
        client.connect((HOST,PORT))
        print(f"[client] connected to {HOST}:{PORT}")

        client.sendall(text.encode())
        reply = client.recv(1024)
        print(f"[client] received: {reply.decode()}")

if __name__ == "__main__":
    main()
    