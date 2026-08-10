# Q6 - UDP message with client IP and port

**Aim:** transfer a text message from client to server over UDP; the server displays the
message together with the client's IP address and port number.

## Where the client's address comes from
`recvfrom()` returns a tuple:

```python
data, addr = server.recvfrom(4096)
client_ip, client_port = addr
```

This is the central point of the question. In TCP the equivalent information comes from
`accept()`'s second return value, or `conn.getpeername()`.

## Key points
- The server binds to `0.0.0.0`, not `127.0.0.1`, so clients on other machines can reach
  it. `127.0.0.1` restricts it to the same computer.
- The **client never calls `bind()`**. The OS assigns it an ephemeral source port
  (typically 32768–60999 on Linux) on the first `sendto()`. That is the port the server
  prints. It changes every run — expected behaviour, not a bug.
- `client.getsockname()` shows the client its own assigned address.
- The client sets a timeout: UDP has no delivery guarantee, so a lost datagram would
  otherwise block `recvfrom()` forever.

## Test cases
| Input | Server display |
|---|---|
| `Hello Server` | IP `127.0.0.1`, some ephemeral port, 12 bytes |
| run the client twice | same IP, **different** port each time |
| run from another machine | that machine's LAN IP |
| very large message (>65507 bytes) | `OSError: Message too long` — UDP datagram size limit |
