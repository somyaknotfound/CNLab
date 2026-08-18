"""Q8 - Concurrent online quiz. Many clients take the quiz at the same time.

Each client gets its own thread; the shared scoreboard is guarded by a lock.
"""
import json, os, socket, threading

HOST, PORT = '127.0.0.1', 6008
HERE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS = json.load(open(os.path.join(HERE, 'questions.json')))

scores = {}                     # name -> score   (shared state)
lock = threading.Lock()


def handle(conn, addr):
    f = conn.makefile('r')
    name = f.readline().strip() or f"player{addr[1]}"
    print(f"[+] {name} started the quiz")

    score = 0
    for i, item in enumerate(QUESTIONS, 1):
        options = "  ".join(f"{n}) {o}" for n, o in enumerate(item['options'], 1))
        conn.sendall(f"Q{i}. {item['q']} | {options}\n".encode())

        answer = f.readline().strip()
        if answer == str(item['answer']):
            score += 1

    with lock:                              # only one thread updates at a time
        scores[name] = score
        board = sorted(scores.items(), key=lambda kv: -kv[1])

    summary = (f"DONE|Your score: {score}/{len(QUESTIONS)}"
               f" || Leaderboard: " + ", ".join(f"{n}={s}" for n, s in board))
    conn.sendall((summary + '\n').encode())
    conn.close()
    print(f"[-] {name} scored {score}/{len(QUESTIONS)}")


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
print(f"Quiz server on {HOST}:{PORT}  ({len(QUESTIONS)} questions)")

try:
    while True:
        c, a = server.accept()
        threading.Thread(target=handle, args=(c, a), daemon=True).start()
except KeyboardInterrupt:
    print("\nserver stopped")
finally:
    server.close()
