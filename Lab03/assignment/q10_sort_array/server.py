"""
Q10 (TCP) - Array processing
Client sends an array of integers; the server returns it sorted.

The array travels as JSON so the structure survives the trip intact.

Run:  python server.py
"""
import json
import socket

HOST = '127.0.0.1'
PORT = 5010


def handle_request(payload: str) -> str:
    try:
        numbers = json.loads(payload)
    except json.JSONDecodeError:
        return json.dumps({"error": "malformed JSON"})

    if not isinstance(numbers, list):
        return json.dumps({"error": "expected a JSON list of integers"})

    if not all(isinstance(n, int) for n in numbers):
        return json.dumps({"error": "all elements must be integers"})

    return json.dumps({
        "original": numbers,
        "sorted": sorted(numbers),
        "descending": sorted(numbers, reverse=True),
        "count": len(numbers),
        "min": min(numbers) if numbers else None,
        "max": max(numbers) if numbers else None,
    })


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[Q10 server] Listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            print(f"[Q10 server] Connection from {addr[0]}:{addr[1]}")
            with conn:
                data = conn.recv(65536)
                if not data:
                    continue
                payload = data.decode().strip()
                print(f"[Q10 server] received {payload}")
                response = handle_request(payload)
                conn.sendall(response.encode())
    except KeyboardInterrupt:
        print("\n[Q10 server] Stopped by user")
    finally:
        server.close()


if __name__ == '__main__':
    main()
