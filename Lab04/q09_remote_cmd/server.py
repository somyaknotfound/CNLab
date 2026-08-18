"""Q9 - Remote command execution with input validation.

SECURITY: only commands on the allow-list may run, and shell=False is used so
the OS never interprets ;  |  &&  or backticks. Never pass client input to a shell.
"""
import socket, subprocess

HOST, PORT = '127.0.0.1', 6009
ALLOWED = {'ls', 'pwd', 'date', 'whoami', 'uptime', 'df', 'free', 'hostname'}
TIMEOUT = 5


def run(command):
    parts = command.split()
    if not parts:
        return "Error: empty command"

    if parts[0] not in ALLOWED:
        return f"Error: '{parts[0]}' is not allowed. Allowed: {', '.join(sorted(ALLOWED))}"

    for token in parts:                       # reject shell metacharacters outright
        if any(ch in token for ch in ';|&$`><'):
            return f"Error: illegal character in {token!r}"

    try:
        result = subprocess.run(parts, capture_output=True, text=True,
                                timeout=TIMEOUT, shell=False)
        output = result.stdout + result.stderr
        return output.strip() or "(no output)"
    except FileNotFoundError:
        return f"Error: command '{parts[0]}' not found on the server"
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {TIMEOUT}s"


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
print(f"Remote-command server on {HOST}:{PORT}")
print(f"Allowed commands: {', '.join(sorted(ALLOWED))}")

try:
    while True:
        conn, addr = server.accept()
        for line in conn.makefile('r'):
            command = line.strip()
            if not command or command.lower() == 'exit':
                break
            print(f"{addr[0]} ran: {command}")
            output = run(command)
            conn.sendall(f"{len(output.splitlines()) or 1}\n{output}\n".encode())
        conn.close()
except KeyboardInterrupt:
    print("\nserver stopped")
finally:
    server.close()
