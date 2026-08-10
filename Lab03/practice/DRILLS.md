# Practice Drills

Work through these **before** looking at `assignment/`. Each drill is small enough to
write from a blank file in a few minutes. That is the point — the exam tests whether you
can produce the boilerplate from memory.

Run every program in two terminals, server first:

```bash
python server.py      # terminal 1
python client.py      # terminal 2
```

---

## Warm-ups (read the provided code first)

| Folder | What it shows |
|---|---|
| `01_tcp_hello/` | Bare minimum TCP: `socket → bind → listen → accept → recv → send → close` |
| `02_udp_hello/` | Bare minimum UDP: no listen/accept, `recvfrom` gives you the sender's address |
| `03_tcp_loop/` | Server that stays alive, conversation loop, clean disconnect detection |
| `04_tcp_threaded/` | One thread per client so multiple clients are served at once |
| `05_length_prefix/` | Message framing — why `recv()` boundaries cannot be trusted |

`netutils.py` has reusable helpers (`make_tcp_server`, `recv_exact`, `send_msg`,
`recv_msg`) if you want to skip the boilerplate while practising the logic.

---

## Drill 1 — Blank-file boilerplate

Close every file. Open an empty one. Write a TCP echo server and client from memory. No
copy-paste, no reference. Repeat until you can do it without a syntax error.

*Checklist:* did you set `SO_REUSEADDR`? did you `.encode()` / `.decode()`? did you start
the server before the client?

---

## Drill 2 — Reverse the string

Client sends a string, server sends back the reverse.

*Hint:* `s[::-1]`. This is Q1 and Q7 with a different transform — get comfortable with the
shape.

---

## Drill 3 — Same thing over UDP

Take Drill 2 and convert it to UDP. Delete `listen()` and `accept()`, swap `send`/`recv`
for `sendto`/`recvfrom`.

*Question to answer:* why does the UDP client not need `bind()`?

---

## Drill 4 — Send structured data

Client sends two numbers and an operator. You need more than one value in a single
message. Try all three encodings and note the trade-offs:

1. Space-separated text: `"12 + 5"` → `msg.split()`
2. Comma-separated: `"12,+,5"` → `msg.split(',')`
3. JSON: `json.dumps({"a": 12, "op": "+", "b": 5})`

*Question:* what breaks in approach 1 if a value can contain a space?

---

## Drill 5 — Loop until a sentinel

Client keeps sending lines; server echoes each back; the loop ends when the client sends
`exit`. Make sure the server ALSO exits its inner loop cleanly and goes back to
`accept()`, ready for the next client.

*Trap:* if you only check `if msg == 'exit'` and the client is killed with `Ctrl+C`
instead, `recv()` returns `b''` forever and you spin at 100% CPU. Always check
`if not data: break` too.

---

## Drill 6 — Deliberately break things

Reproduce each of these, read the traceback, then fix it. Recognising the error message
instantly is worth more than avoiding it.

1. Start the client with no server running → `ConnectionRefusedError`
2. Start two servers on the same port → `OSError: Address already in use`
3. `sock.send("hi")` without `.encode()` → `TypeError`
4. Make both sides call `recv()` first → deadlock, program hangs
5. Kill the server mid-conversation → `ConnectionResetError` on the client

---

## Drill 7 — Big payload

Send a 1 MB string over TCP with a single `sendall()`. On the server, count how many times
`recv(4096)` fires before you have it all. This is the concrete demonstration of why
`recv()` is not "receive one message".

Then repeat over UDP with a 70 000-byte datagram and observe the failure — UDP datagrams
have a hard size ceiling (65507 bytes payload on IPv4).

---

## Drill 8 — Read a file over the wire

Server reads a local file and streams it to the client in 4096-byte chunks. Client writes
it to disk. Compare checksums:

```bash
md5sum original.txt received.txt
```

*Question:* how does the client know the file has ended? (Two valid answers — sender
closes the socket, or a length prefix. Implement both.)

---

## Drill 9 — Timeout

Add `sock.settimeout(5)` to a client, point it at a server that never replies, and catch
`socket.timeout`. Useful for UDP where a lost datagram means you wait forever.

---

## Drill 10 — Two clients at once

Run `04_tcp_threaded/server.py` and open two clients. Then run `03_tcp_loop/server.py`
and open two clients. Explain the difference in behaviour in one sentence.

---

## Self-check before the lab

You should be able to answer these without looking anything up:

- [ ] Order of calls on a TCP server, and on a TCP client
- [ ] Which of those calls UDP does not use, and why
- [ ] What `accept()` returns and why there are two sockets
- [ ] What `recv()` returning `b''` means
- [ ] Difference between `send()` and `sendall()`
- [ ] What `SO_REUSEADDR` fixes
- [ ] Why `127.0.0.1` only works on one machine and what to use instead
- [ ] How to send an integer, a list, and a file over a socket
