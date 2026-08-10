"""
Q10 (TCP) - client. Sends an integer array, prints the sorted result.

Run:  python client.py                  (prompts)
      python client.py 3 1 4 1 5 9 2 6
"""
import json
import socket
import sys

HOST = '127.0.0.1'
PORT = 5010


def main():
    if len(sys.argv) > 1:
        raw = sys.argv[1:]
    else:
        raw = input("Enter integers separated by spaces: ").replace(',', ' ').split()

    try:
        numbers = [int(x) for x in raw]
    except ValueError:
        print("Error: all inputs must be integers")
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        client.sendall(json.dumps(numbers).encode())
        reply = json.loads(client.recv(65536).decode())

    if "error" in reply:
        print("Server error:", reply["error"])
        return

    print("\nOriginal   :", reply["original"])
    print("Sorted     :", reply["sorted"])
    print("Descending :", reply["descending"])
    print(f"Count      : {reply['count']}   Min: {reply['min']}   Max: {reply['max']}")


if __name__ == '__main__':
    main()
