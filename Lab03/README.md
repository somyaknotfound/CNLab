# Socket Programming in Python — Lab 03 Notes

Computer Networks Laboratory (CS-302) · Week 4, Exercise 3

---

## 1. What is a socket?

A **socket** is one endpoint of a two-way communication link between two programs on a
network. It is identified by a pair: `(IP address, port number)`.

A connection is identified by a **4-tuple**:

```
(source IP, source port, destination IP, destination port)
```

Python exposes sockets through the built-in `socket` module — no installation needed.

```python
import socket
```

---

## 2. TCP vs UDP

| | TCP | UDP |
|---|---|---|
| Type | Connection-oriented | Connectionless |
| Reliability | Guaranteed delivery, ordered | Best-effort, may drop/reorder |
| Handshake | 3-way handshake | None |
| Speed | Slower (ACKs, retransmit) | Faster |
| Socket type | `SOCK_STREAM` | `SOCK_DGRAM` |
| Used in Qs | 1, 2, 4, 5, 7, 8, 9, 10 | 3, 6 |
| Real use | HTTP, SSH, FTP, email | DNS, video streaming, games |

**Rule of thumb:** if the exercise says "reliable" or "file transfer", use TCP. If it says
"fast", "datagram", or asks for the client's address, UDP is usually intended.

---

## 3. The two call sequences

### TCP

```
SERVER                            CLIENT
socket()                          socket()
bind((host, port))
listen(backlog)
accept()          <───────────    connect((host, port))
recv() / send()   <──────────>    send() / recv()
close()                           close()
```

### UDP

```
SERVER                            CLIENT
socket(SOCK_DGRAM)                socket(SOCK_DGRAM)
bind((host, port))
recvfrom()        <───────────    sendto(data, (host, port))
sendto()          ──────────>     recvfrom()
close()                           close()
```

Key difference: UDP has **no** `listen()`, `accept()`, or `connect()`. Every datagram
carries its own destination address.

---

## 4. Function reference

| Function | Purpose |
|---|---|
| `socket.socket(family, type)` | Create a socket. `AF_INET` = IPv4. `SOCK_STREAM` = TCP, `SOCK_DGRAM` = UDP |
| `s.bind((host, port))` | Attach the socket to a local address. Server-side |
| `s.listen(n)` | Mark as passive; `n` = pending-connection queue size (TCP only) |
| `s.accept()` | Block until a client connects. Returns `(conn, addr)` (TCP only) |
| `s.connect((host, port))` | Initiate a connection to a server (TCP only) |
| `conn.send(b)` / `sendall(b)` | Send bytes. `sendall` loops until everything is sent — prefer it |
| `conn.recv(n)` | Receive up to `n` bytes. Returns `b''` when peer closes |
| `s.sendto(b, addr)` | Send a datagram (UDP) |
| `s.recvfrom(n)` | Receive a datagram; returns `(data, addr)` (UDP) |
| `s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)` | Reuse a port immediately after restart |
| `s.close()` | Release the socket |
| `socket.gethostname()` | Local machine's hostname |

### Addresses

| Value | Meaning |
|---|---|
| `'127.0.0.1'` / `'localhost'` | Loopback — same machine only |
| `'0.0.0.0'` | Listen on **all** interfaces (use to accept from other machines) |
| `''` (empty string) | Same as `0.0.0.0` when passed to `bind` |

Ports below 1024 are privileged. Use something in `1024–65535`, e.g. `12345`.

---

## 5. Bytes, not strings

Sockets carry **bytes**. Convert at every boundary:

```python
sock.send("hello".encode())          # str -> bytes
sock.send(b"hello")                  # bytes literal
msg = sock.recv(1024).decode()       # bytes -> str
```

Forgetting this gives `TypeError: a bytes-like object is required, not 'str'`.

---

## 6. TCP is a byte stream — there are no "messages"

`recv(1024)` may return fewer bytes than were sent, or bytes from two `send()` calls
glued together. TCP has no message boundaries. Three ways to cope:

1. **Fixed protocol per exchange** — one request, one response, then close. Sufficient for
   most lab questions.
2. **Delimiter** — terminate each message with `\n` and read until you see it.
3. **Length prefix** — send an 8-byte length header, then read exactly that many bytes.
   This is the correct approach for file transfer (Q8).

```python
def recv_exact(sock, n):
    """Read exactly n bytes or return None if the peer closes early."""
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf
```

For "read until the peer closes" (also valid for file transfer):

```python
while True:
    chunk = sock.recv(4096)
    if not chunk:
        break
    f.write(chunk)
```

---

## 7. Boilerplate to memorise

### TCP server

```python
import socket

HOST, PORT = '127.0.0.1', 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
print(f"Server listening on {HOST}:{PORT}")

while True:
    conn, addr = server.accept()
    print("Connected by", addr)
    data = conn.recv(1024).decode()
    conn.sendall(data.upper().encode())
    conn.close()
```

### TCP client

```python
import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 12345))
client.sendall(input("Enter: ").encode())
print("Reply:", client.recv(1024).decode())
client.close()
```

### UDP server

```python
import socket

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(('127.0.0.1', 12345))

while True:
    data, addr = server.recvfrom(1024)
    print(f"From {addr[0]}:{addr[1]} -> {data.decode()}")
    server.sendto(data.decode().upper().encode(), addr)
```

### UDP client

```python
import socket

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.sendto(input("Enter: ").encode(), ('127.0.0.1', 12345))
print("Reply:", client.recvfrom(1024)[0].decode())
client.close()
```

Use `with socket.socket(...) as s:` where you can — it closes automatically.

---

## 8. Using `SO_REUSEADDR`

After a TCP server closes, the port sits in `TIME_WAIT` for ~60s and rebinding fails with
`OSError: [Errno 98] Address already in use`. Fix:

```python
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # BEFORE bind()
```

Put this line in every TCP server you write.

---

## 9. Handling multiple clients

The single-threaded loop above serves one client at a time. To serve concurrently:

```python
import threading

def handle(conn, addr):
    ...
    conn.close()

while True:
    conn, addr = server.accept()
    threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
```

---

## 10. Common errors

| Error | Cause | Fix |
|---|---|---|
| `ConnectionRefusedError` | Server not running, or wrong port | Start the server **first**; check port matches |
| `OSError: Address already in use` | Port in `TIME_WAIT` or another process holds it | Add `SO_REUSEADDR`, or change port, or `lsof -i :12345` and kill |
| `TypeError: a bytes-like object is required` | Sent a `str` | `.encode()` before sending |
| `UnicodeDecodeError` | Decoded binary data as text | Keep binary data as bytes |
| Program hangs on `recv()` | Both sides waiting to receive | One side must send first; check the protocol order |
| `ConnectionResetError` | Peer closed abruptly | Wrap in `try/except`, close cleanly |
| Empty `recv()` result | Peer closed the connection | `if not data: break` |
| Only part of a message arrives | TCP stream, no boundaries | Use a delimiter or length prefix |
| `socket.timeout` | `settimeout()` expired | Increase timeout or check the peer is alive |

Debugging: run `netstat -tuln | grep 12345` (Linux) or `netstat -ano | findstr 12345`
(Windows) to see whether the port is actually bound.

---

## 11. How to run

Open **two terminals**. Server first, always.

```bash
# Terminal 1
python server.py

# Terminal 2
python client.py
```

Stop a server with `Ctrl+C`.

---

## 12. Folder layout

```
Lab03/
├── README.md              ← this file
├── practice/              ← warm-up drills, build these before the assignment
│   ├── 01_tcp_hello/
│   ├── 02_udp_hello/
│   ├── 03_tcp_loop/
│   ├── 04_tcp_threaded/
│   ├── 05_length_prefix/
│   ├── netutils.py        ← reusable helpers
│   └── DRILLS.md          ← exercises with hints, no solutions
└── assignment/            ← the 10 lab questions, solved
    ├── q01_uppercase/
    ├── q02_arithmetic/
    ├── ...
    └── run_all_tests.py   ← automated check of all 10
```

---

## 13. The 10 lab questions

| # | Problem | Protocol | Topic |
|---|---|---|---|
| 1 | Client sends a string, server returns it uppercased | TCP | String processing |
| 2 | Client sends two numbers + an operator, server computes | TCP | Arithmetic |
| 3 | Client sends an integer, server says prime or not | UDP | Number theory |
| 4 | Echo server, loops until the client sends `exit` | TCP | Echo / loop |
| 5 | Client sends a filename, server returns line/word/char counts | TCP | File processing |
| 6 | Client sends text, server prints it with the client IP and port | UDP | Client info |
| 7 | Client sends a string, server checks palindrome | TCP | String processing |
| 8 | Client transfers a text file to the server | TCP | File transfer |
| 9 | Client sends a sentence, server counts vowels/consonants/words | TCP | String analysis |
| 10 | Client sends an integer array, server returns it sorted | TCP | Array processing |

Each lives in its own folder inside `assignment/` with `server.py`, `client.py`, and a
`NOTES.md` explaining the approach, the protocol used on the wire, and edge cases.

---

## 14. Viva questions worth preparing

- Why does the server call `bind()` but the client usually does not?
- What does the backlog argument to `listen()` actually control?
- Why does `accept()` return a *new* socket?
- What happens if two servers bind to the same port?
- Why is `sendall()` safer than `send()`?
- How does the server know a client has disconnected?
- Why does UDP not need `accept()`?
- What is the maximum safe UDP datagram payload? (~508 bytes to be safe on the internet;
  65507 bytes is the theoretical IPv4 maximum)
- What is the difference between `AF_INET` and `AF_INET6`?
- Explain the TCP three-way handshake and four-way termination.

---

## 15. Further reading

- Python docs — `socket` module: https://docs.python.org/3/library/socket.html
- Python Socket Programming HOWTO: https://docs.python.org/3/howto/sockets.html
- Beej's Guide to Network Programming: https://beej.us/guide/bgnet/
