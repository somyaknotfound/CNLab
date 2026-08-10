import socket

HOST, PORT = '127.0.0.1', 5002


def compute(expression: str) -> str:
    parts = expression.split()

    if len(parts) != 3:
        return "Error: Invalid expression format. Use: a op b"

    a_str, op, b_str = parts

    try:
        a, b = float(a_str), float(b_str)
    except ValueError:
        return "Error: Invalid numbers."

    if op == '+':
        result = a + b

    elif op == '-':
        result = a - b

    elif op == '*':
        result = a * b

    elif op == '/':
        if b == 0:
            return "Error: Division by zero."
        result = a / b

    else:
        return "Error: Unsupported operator. Use +, -, *, or /."

    # Format result nicely
    if result == int(result):
        return str(int(result))

    return f"{result:.6g}"


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST, PORT))
    server.listen(1)

    print(f"[server] listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()

            with conn:
                print(f"[server] connected by {addr}")

                data = conn.recv(1024).decode().strip()

                if not data:
                    continue

                print(f"[server] received: {data}")

                expression = data
                result = compute(expression)

                print(f"[server] {expression} = {result}")

                conn.sendall(result.encode())

    except KeyboardInterrupt:
        print("\n[server] shutting down.")

    finally:
        server.close()


if __name__ == "__main__":
    main()