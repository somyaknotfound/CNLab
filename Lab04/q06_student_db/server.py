"""Q6 - TCP server holding a database of student records. Supports full CRUD.

The "database" is a dict kept in memory and saved to students.json after every
change, so records survive a restart. A lock serialises writes because several
client threads share the same dict.

Request format (one line):
  INSERT|roll|name|marks     UPDATE|roll|name|marks
  DELETE|roll                SEARCH|roll                DISPLAY|
"""
import json, os, socket, threading

HOST, PORT = '127.0.0.1', 6006
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'students.json')

lock = threading.Lock()
records = json.load(open(DB)) if os.path.exists(DB) else {}   # roll -> [name, marks]


def save():
    with open(DB, 'w') as f:
        json.dump(records, f, indent=2)


def handle_request(line):
    parts = line.strip().split('|')
    cmd = parts[0].upper()

    with lock:                                     # one writer at a time
        if cmd == 'INSERT' and len(parts) == 4:
            roll, name, marks = parts[1], parts[2], parts[3]
            if roll in records:
                return f"Error: roll {roll} already exists"
            try:
                records[roll] = [name, float(marks)]
            except ValueError:
                return "Error: marks must be a number"
            save()
            return f"Inserted {roll}"

        if cmd == 'UPDATE' and len(parts) == 4:
            roll, name, marks = parts[1], parts[2], parts[3]
            if roll not in records:
                return f"Error: {roll} not found"
            try:
                records[roll] = [name, float(marks)]
            except ValueError:
                return "Error: marks must be a number"
            save()
            return f"Updated {roll}"

        if cmd == 'DELETE' and len(parts) == 2:
            if records.pop(parts[1], None) is None:
                return f"Error: {parts[1]} not found"
            save()
            return f"Deleted {parts[1]}"

        if cmd == 'SEARCH' and len(parts) == 2:
            row = records.get(parts[1])
            return f"{parts[1]} | {row[0]} | {row[1]}" if row else f"Error: {parts[1]} not found"

        if cmd == 'DISPLAY':
            if not records:
                return "(database is empty)"
            return " ;; ".join(f"{r} | {v[0]} | {v[1]}" for r, v in sorted(records.items()))

    return f"Error: bad request {line.strip()!r}"


def handle(conn, addr):
    for line in conn.makefile('r'):
        if not line.strip():
            continue
        reply = handle_request(line)
        print(f"{addr[0]} -> {line.strip()[:40]}  =>  {reply[:50]}")
        conn.sendall((reply + '\n').encode())
    conn.close()


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
print(f"Student DB server on {HOST}:{PORT}  ({len(records)} records loaded)")

try:
    while True:
        c, a = server.accept()
        threading.Thread(target=handle, args=(c, a), daemon=True).start()
except KeyboardInterrupt:
    print("\nserver stopped")
finally:
    server.close()
