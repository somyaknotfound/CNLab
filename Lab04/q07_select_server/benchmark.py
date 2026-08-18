"""Q7 - crude comparison: threaded server vs select() server.

Starts each server, fires N concurrent clients at it, reports wall-clock time.
Run:  python benchmark.py [N]      (default 30 clients)
"""
import os, socket, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
MSGS = 20


def hammer(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', port))
    r = s.makefile('r')
    r.readline()                       # greeting (select server only sends one)
    for i in range(MSGS):
        s.sendall(f"msg{i}\n".encode())
        r.readline()
    s.close()


def run(script, port, label):
    proc = subprocess.Popen([sys.executable, script], cwd=HERE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    start = time.time()
    threads = [threading.Thread(target=hammer, args=(port,)) for _ in range(N)]
    for t in threads: t.start()
    for t in threads: t.join()
    elapsed = time.time() - start
    proc.terminate(); proc.wait()
    print(f"{label:<22} {N} clients x {MSGS} messages : {elapsed:.2f}s")


print(f"Benchmarking with {N} concurrent clients\n" + "-" * 55)
run('server.py', 6007, 'select() server')
run('threaded_server.py', 6017, 'threaded server')
print("-" * 55)
print("select(): one thread, no locks, scales to many idle connections.")
print("threads : simpler code, but ~8 MB stack each and OS scheduling overhead.")
