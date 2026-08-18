# Advanced Socket Programming — Lab 04 Revision Notes

Computer Networks Laboratory (CS-302) · Week 5, Exercise 4

Lab 03 covered one client, one request, one reply. This week is about everything that
breaks when you add **many clients, real files, and untrusted input**.

---

## Quick index

| # | Folder | Port | Problem | New idea |
|---|---|---|---|---|
| 1 | `q01_chat/` | 6001 | Multi-client chat, broadcast | threads + shared state + lock |
| 2 | `q02_factorial/` | 6002 | Concurrent factorial server | thread per client |
| 3 | `q03_binary_sha256/` | 6003 | Binary file + SHA-256 check | integrity verification |
| 4 | `q04_reliable_udp/` | 6004 | Reliable transfer over UDP | seq numbers, ACK, timeout, retransmit |
| 5 | `q05_multi_service/` | 6005 | Menu-driven multi-service server | request dispatch table |
| 6 | `q06_student_db/` | 6006 | Student records, CRUD | persistent shared state |
| 7 | `q07_select_server/` | 6007 | `select()` server + benchmark | I/O multiplexing |
| 8 | `q08_quiz/` | 6008 | Concurrent quiz, scoreboard | shared score table |
| 9 | `q09_remote_cmd/` | 6009 | Remote command execution | allow-list, `shell=False` |
| 10 | `q10_file_server/` | 6010 | Distributed file server | auth + logging + concurrency |

Ports differ per question so several servers can run at once.

Run any of them in two terminals, **server first**:

```bash
cd q01_chat
python server.py      # terminal 1
python client.py      # terminal 2
```

Check everything at once:

```bash
python run_all_tests.py          # all 10 -> 21/21 passed
python run_all_tests.py 4 7      # only questions 4 and 7
```

---

## 1. Concurrency: threads

A single-threaded server serves one client and blocks everyone else. Fix:

```python
while True:
    conn, addr = server.accept()
    threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
```

- `target` is the function, `args` its arguments. **Don't call it** — `target=handle`, not
  `target=handle()`.
- `daemon=True` means the thread dies when the main program exits, so `Ctrl+C` works.
- `threading.active_count()` tells you how many are alive.

### The lock

Any data shared between threads needs protection. Two threads doing
`clients[conn] = name` at the same moment can corrupt the dict.

```python
lock = threading.Lock()

with lock:              # only one thread inside this block at a time
    clients[conn] = name
```

Keep the critical section as small as possible — hold the lock while touching shared
data, release it before doing I/O. Used in Q1 (client list), Q6 (records), Q8 (scores),
Q10 (file store).

**Race condition** = the result depends on thread timing. **Deadlock** = two threads each
hold a lock the other wants. Avoid deadlock by always acquiring locks in the same order.

---

## 2. Concurrency: `select()` — I/O multiplexing

`select()` watches many sockets at once in **one thread** and returns those ready to read.

```python
sockets = [server]
while True:
    readable, writable, errored = select.select(sockets, [], [])
    for s in readable:
        if s is server:
            conn, addr = server.accept()
            sockets.append(conn)
        else:
            data = s.recv(1024)
            if not data:
                sockets.remove(s); s.close()
```

The server socket becoming "readable" means *a connection is waiting* — that is your cue
to call `accept()`.

### Threads vs select()

| | Threads | `select()` |
|---|---|---|
| Model | one thread per client | one loop, all clients |
| Blocking call is fine? | yes, it only blocks that thread | no — one slow client stalls everyone |
| Shared state | needs locks | no locks needed, single thread |
| Cost per client | ~8 MB stack + scheduling | one file descriptor |
| Scales to 10k idle connections | badly | well |
| Code readability | better | worse (explicit state machine) |
| CPU-bound work | limited by the GIL anyway | blocks the loop |

`select()` is O(n) per call and capped at 1024 descriptors on Linux. `poll()` removes the
cap; `epoll()` (Linux) and `kqueue()` (BSD) are O(1) and what real servers use. Python's
`selectors` module picks the best one for you.

Run `q07_select_server/benchmark.py` to compare the two side by side.

---

## 3. Line-based protocols with `makefile()`

Most of this week's programs use newline-delimited text. `sock.makefile()` wraps the
socket in a file object so you can use `readline()` and iterate:

```python
f = conn.makefile('r')          # text mode
name = f.readline().strip()     # read exactly one line
for line in f:                  # loop ends when the client closes
    ...
conn.sendall((reply + '\n').encode())    # always terminate what you send
```

This removes all the manual buffering. Use `makefile('rb')` when binary data follows the
text header (Q3, Q10).

**The rule:** if you send a line, end it with `\n`, or the reader blocks forever.

---

## 4. Framing: header line + raw bytes

The standard shape for "metadata then payload":

```
CLIENT: "filename|size|sha256\n"        <- one text line
CLIENT: <size raw bytes>                <- the payload
SERVER: "OK|...\n"
```

The receiver reads the line, parses `size`, then reads exactly that many bytes. Never
guess where a payload ends — TCP has no message boundaries.

```python
name, size, digest = f.readline().decode().strip().split('|')
data = f.read(int(size))        # makefile's read(n) reads exactly n bytes
```

---

## 5. File integrity with SHA-256

```python
import hashlib
digest = hashlib.sha256(data).hexdigest()       # whole file in memory

sha = hashlib.sha256()                          # streaming, for large files
for chunk in chunks:
    sha.update(chunk)
digest = sha.hexdigest()
```

The sender computes the digest, sends it in the header, and the receiver computes its own
over the bytes it actually received. Equal digests ⇒ the file arrived intact.

- Always open binary files with `'rb'` / `'wb'`. Text mode corrupts non-UTF-8 bytes and
  rewrites line endings on Windows.
- SHA-256 produces a 64-character hex string (256 bits).
- Verify from the shell with `sha256sum file` (Linux) or `certutil -hashfile file SHA256`
  (Windows).
- TCP's own checksum is only 16 bits and catches transmission noise, not disk corruption
  or a truncated write — which is why an application-level hash is still worth having.

---

## 6. Reliable data transfer over UDP

UDP gives you speed and nothing else. Reliability is four mechanisms you build yourself:

| Mechanism | Purpose |
|---|---|
| **Sequence number** | identify each packet; detect duplicates and reordering |
| **Acknowledgment (ACK)** | receiver confirms it got packet *n* |
| **Timeout** | sender assumes loss if no ACK arrives in time |
| **Retransmission** | send it again |

### Stop-and-wait ARQ (what Q4 implements)

```
sender                     receiver
  |-- packet 0 ---------->  |
  |<------------- ACK 0 --  |
  |-- packet 1 --X          |     (lost)
  |   ...timeout...         |
  |-- packet 1 ---------->  |     (retransmitted)
  |<------------- ACK 1 --  |
```

```python
sock.settimeout(1.0)
for attempt in range(MAX_TRIES):
    sock.sendto(f"{seq}|".encode() + payload, addr)
    try:
        ack, _ = sock.recvfrom(64)
        if ack.decode() == f"ACK{seq}":
            break
    except socket.timeout:
        continue          # retransmit
```

Two cases the receiver must handle:

- **Packet lost** → no ACK → sender retransmits. Fine.
- **ACK lost** → sender retransmits a packet the receiver already has. The receiver must
  **re-ACK it but not write it twice**. That is why it tracks `expected` sequence number.

Loss is simulated with `if random.random() < LOSS: continue` on the receiver.

Stop-and-wait is correct but slow — one packet in flight at a time. **Sliding window** /
Go-Back-N / Selective Repeat send several before waiting, which is what TCP does.

---

## 7. Dispatch tables

When a server offers several services, a dict beats a chain of `if`s:

```python
SERVICES = {'CALC': calculator, 'STRING': string_ops,
            'FILE': file_service, 'TIME': time_service}

handler = SERVICES.get(name.upper())
result = handler(arg) if handler else "Error: unknown service"
```

Adding a service is one line. Same idea works for the CRUD commands in Q6 and the file
server commands in Q10.

---

## 8. Security: never trust the client

This is the heart of Q9 and Q10, and examiners ask about it.

### Command execution

```python
subprocess.run(parts, shell=False, capture_output=True, text=True, timeout=5)
```

| Do | Don't | Why |
|---|---|---|
| `shell=False` with a list | `shell=True` with a string | with a shell, `ls; rm -rf /` runs both commands |
| allow-list of commands | block-list | you will never think of every bad command |
| reject `; \| & $ \` > <` | assume input is clean | metacharacters are the attack surface |
| `timeout=5` | unbounded | a hung command blocks the server forever |
| never `eval()` socket data | `eval(msg)` | arbitrary code execution |

### File paths

```python
name = os.path.basename(client_supplied_name)
```

Without this, a client requests `../../../../etc/passwd` (**path traversal**) and reads or
overwrites anything the server process can touch.

### Passwords

Q10 keeps a plain dict for clarity. Real systems store a **salted hash**
(`hashlib.pbkdf2_hmac` or `bcrypt`), never the password itself, and send credentials over
TLS — a plain socket transmits them in clear text and anyone running Wireshark on the
path can read them.

### Authentication state

Login sets a per-connection variable; every other command checks it:

```python
if user is None:
    conn.sendall(b"ERROR|please LOGIN first\n")
    continue
```

The state lives in the handler function, so it is naturally per-connection — no leakage
between clients.

---

## 9. Logging

```python
from datetime import datetime
stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
with open(f"logs/{user}.log", 'a') as f:      # 'a' = append, never truncate
    f.write(f"[{stamp}] {action}\n")
```

Log **who did what and when**: connections, authentication successes *and failures*,
uploads, downloads, errors. Q10 keeps one file per user in `logs/`.

Python's `logging` module is the production answer — thread-safe, level filtering,
rotation — but explicit file writes are clearer for a lab demo.

---

## 10. Errors you will actually hit this week

| Symptom | Cause | Fix |
|---|---|---|
| `Address already in use` | port in `TIME_WAIT` | `setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)` before `bind()` |
| Server hangs after one client | no threads / no `select()` | thread per client, or a select loop |
| Output interleaved and garbled | threads sharing state without a lock | wrap shared access in `with lock:` |
| Client waits forever on `readline()` | sender forgot the trailing `\n` | always append `'\n'` |
| Checksum mismatch every time | file opened in text mode | use `'rb'` / `'wb'` |
| UDP client blocks forever | datagram lost, no timeout | `sock.settimeout(1.0)` + retransmit |
| `BrokenPipeError` | wrote to a socket the peer closed | catch `OSError`, drop the client |
| `RuntimeError: dictionary changed size` | iterating a shared dict while another thread edits it | iterate `list(d)` inside the lock |
| Chat message not received | broadcasting only to the sender | loop over all sockets, skip the sender |
| `select()` spins at 100% CPU | closed socket left in the watch list | `sockets.remove(s)` when `recv` returns `b''` |

---

## 11. Viva questions

**Concurrency**

- Why does a single-threaded server block other clients?
- What exactly does a lock protect against? Give a concrete corruption example.
- Thread vs process — which does Python's GIL limit, and does it matter for socket I/O?
  (No: the GIL is released during blocking I/O, so threads are fine for network servers.)
- When would you choose `select()` over threads, and vice versa?
- What is the C10K problem?

**Reliability**

- Name the four mechanisms that make a transfer reliable over UDP.
- What happens if the ACK is lost rather than the data packet?
- Why is stop-and-wait slow? What replaces it?
- Why not just use TCP? (Sometimes you need control over retransmission timing, or
  multicast, or lower latency than TCP's head-of-line blocking allows.)

**Integrity and security**

- Why check SHA-256 when TCP already has a checksum?
- Why is `shell=True` dangerous? Show an input that exploits it.
- What is path traversal and what single function call prevents it?
- Why store password hashes rather than passwords?
- Why is an allow-list safer than a block-list?

**Design**

- How does the server know a client disconnected? (`recv` returns `b''`.)
- Where do you put the authentication check so it cannot be bypassed?
- How would you scale the chat server to 10 000 users?

---

## 12. Tools

```bash
# is the port actually bound?
netstat -tuln | grep 6001            # Linux
netstat -ano | findstr 6001          # Windows

# talk to any of these servers by hand
nc 127.0.0.1 6002                    # netcat
telnet 127.0.0.1 6002

# watch the packets
sudo tcpdump -i lo port 6004 -A
# or Wireshark with filter:  tcp.port == 6004 || udp.port == 6004

# verify a file transfer
sha256sum send/sample.bin received/sample.bin
```

Wireshark on the loopback interface is the fastest way to *see* the three-way handshake,
the retransmissions in Q4, and the fact that Q10 sends passwords in clear text.
