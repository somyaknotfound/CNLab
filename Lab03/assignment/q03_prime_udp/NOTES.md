# Q3 - Prime check (UDP)

**Aim:** client sends an integer over UDP, server replies whether it is prime.

## Why UDP changes the code
| TCP | UDP |
|---|---|
| `listen()`, `accept()` | not used |
| `connect()` on the client | not used |
| `send()` / `recv()` | `sendto(data, addr)` / `recvfrom(n)` |
| server knows the peer from `accept()` | server learns the peer from `recvfrom()`'s second return value |

There is no connection, so the server must reply to the address `recvfrom` gave it.

## Key points
- **The client sets a timeout.** UDP gives no delivery guarantee — without
  `settimeout()`, a lost datagram makes `recvfrom()` block forever.
- `is_prime` uses trial division up to `sqrt(n)`, skipping even divisors: O(sqrt(n)).
- The number is sent as *text* (`"97"`), not as raw bytes, so both sides just
  encode/decode. `int(text)` on the server with a `try/except ValueError` guard.

## Test cases
| Input | Reply |
|---|---|
| `2` | prime (smallest prime) |
| `1` | not prime (by definition) |
| `0`, `-7` | not prime |
| `97` | prime |
| `100` | not prime |
| `7919` | prime |
| `abc` | `Error: 'abc' is not a valid integer` |
