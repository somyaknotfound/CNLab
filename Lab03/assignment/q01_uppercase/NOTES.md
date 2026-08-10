# Q1 - Uppercase conversion (TCP)

**Aim:** client sends a string, server returns it in uppercase.

## Wire protocol
| Direction | Payload |
|---|---|
| client -> server | the raw string, UTF-8 encoded |
| server -> client | the uppercased string, UTF-8 encoded |

One request, one response, then the connection closes. No framing needed because the
whole exchange is a single message in each direction.

## Key points
- `str.upper()` does the work; everything else is socket plumbing.
- `.encode()` before `sendall`, `.decode()` after `recv` — sockets carry bytes only.
- `SO_REUSEADDR` avoids `Address already in use` when you restart the server.
- The server loops on `accept()` so it survives after a client disconnects.

## Edge cases
| Input | Output |
|---|---|
| `hello world` | `HELLO WORLD` |
| `Already UPPER` | `ALREADY UPPER` |
| `abc123!@#` | `ABC123!@#` (digits and symbols unchanged) |
| empty string | server's `recv` returns `b''`; the `if not data: continue` guard skips it |
