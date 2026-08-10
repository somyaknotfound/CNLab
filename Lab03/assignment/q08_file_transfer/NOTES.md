# Q8 - File transfer client -> server (TCP)

**Aim:** transfer a text file from the client to the server.

## The real problem: where does the file end?
TCP is a byte stream with no message boundaries. The receiver must be told how much to
read. Two valid strategies:

1. **Length prefix** (used here) — send the size first, then read exactly that many bytes.
   The connection stays usable afterwards, so the server can reply with a status.
2. **Sender closes the socket** — receiver loops `recv()` until it returns `b''`. Simpler,
   but the connection is then dead, so no acknowledgement is possible.

## Protocol on the wire
```
[4 bytes ] filename length   (big-endian unsigned int)
[n bytes ] filename          (UTF-8)
[8 bytes ] content length    (big-endian unsigned int)
[m bytes ] file content      (raw bytes)
        <- status line from the server
```

`int.to_bytes(4, 'big')` / `int.from_bytes(b, 'big')` convert integers to and from a fixed
number of bytes. Big-endian is network byte order.

## Key points
- Files are opened in **binary** mode (`'rb'` / `'wb'`). Text mode would corrupt anything
  non-UTF-8 and would rewrite line endings on Windows.
- `recv_exact()` loops because a single `recv(n)` may legitimately return fewer than `n`
  bytes.
- Content is written in 4096-byte chunks, so a file larger than RAM still works on the
  receiving side.
- `os.path.basename()` on the received filename prevents a malicious client from writing
  to `../../home/user/.bashrc`.

## Directories
- `send/demo.txt` — sample file to transfer
- `received/` — where the server writes incoming files

## Verifying the transfer
```bash
md5sum send/demo.txt received/demo.txt      # the two hashes must match
```

## Test cases
| Case | Expected |
|---|---|
| small text file | byte-identical copy in `received/` |
| empty file | 0-byte file created, `OK: ... (0 bytes)` |
| large file (several MB) | still correct — chunked reads |
| nonexistent path on the client | client reports the error, never connects |
