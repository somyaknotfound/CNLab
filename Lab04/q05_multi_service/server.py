"""Q5 - One server, four services chosen from a menu.

Request format:  "<service>|<argument>"
  CALC|12 + 5      STRING|hello      FILE|notes.txt      TIME|
"""
import os, socket
from datetime import datetime

HOST, PORT = '127.0.0.1', 6005
FILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')


def calculator(arg):
    try:
        a, op, b = arg.split()
        a, b = float(a), float(b)
    except ValueError:
        return "Error: use '<num> <op> <num>'"
    if op == '+': r = a + b
    elif op == '-': r = a - b
    elif op == '*': r = a * b
    elif op == '/': r = "undefined" if b == 0 else a / b
    else: return f"Error: unknown operator {op!r}"
    return str(int(r)) if isinstance(r, float) and r == int(r) else str(r)


def string_ops(arg):
    return (f"upper={arg.upper()} | lower={arg.lower()} | reverse={arg[::-1]} | "
            f"length={len(arg)} | words={len(arg.split())}")


def file_service(arg):
    path = os.path.join(FILE_DIR, os.path.basename(arg))
    if not os.path.isfile(path):
        return f"Error: {arg!r} not found on the server"
    with open(path, encoding='utf-8', errors='replace') as f:
        return f.read()


def time_service(_):
    return datetime.now().strftime('Server time: %Y-%m-%d %H:%M:%S')


SERVICES = {'CALC': calculator, 'STRING': string_ops,
            'FILE': file_service, 'TIME': time_service}

os.makedirs(FILE_DIR, exist_ok=True)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
print(f"Multi-service server on {HOST}:{PORT}  services: {', '.join(SERVICES)}")

try:
    while True:
        conn, addr = server.accept()
        f = conn.makefile('r')
        for line in f:
            service, _, arg = line.strip().partition('|')
            handler = SERVICES.get(service.upper())
            result = handler(arg) if handler else f"Error: unknown service {service!r}"
            print(f"{addr[0]} -> {service}: {arg[:40]}")
            conn.sendall((result.replace('\n', ' \\n ') + '\n').encode())
        conn.close()
except KeyboardInterrupt:
    print("\nserver stopped")
finally:
    server.close()
