import socket
import sys

HOST,PORT = '127.0.0.1' , 5002

def main():
    if (len(sys.argv) == 4):
        expression = ' '.join(sys.argv[1:])
    else:
        a = input("Enter first number: ").strip()
        op = input("Enter operator (+, -, *, /): ").strip()
        b = input("Enter second number: ").strip()
        expression = f"{a} {op} {b}"
    with socket.socket(socket.AF_INET , socket.SOCK_STREAM) as client:
        client.connect((HOST,PORT))
        client.sendall(expression.encode())
        reply = client.recv(1024).decode()

    print(f"{expression} = {reply}")


if __name__ == "__main__": 
    main()

