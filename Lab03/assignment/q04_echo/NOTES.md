# Q4 - Echo server (TCP)

**Aim:** server echoes every message back until the client sends `exit`.

## Wire protocol
| Direction | Payload |
|---|---|
| client -> server | any text line |
| server -> client | the identical text |
| client -> server | `exit` |
| server -> client | `Connection closed by server. Bye!` then closes |

## Structure: two nested loops
```
while True:              # outer - one iteration per client
    accept()
    while True:          # inner - one iteration per message
        recv()
        ...
        break on 'exit'
```
The inner loop keeps the conversation alive; the outer loop makes the server survive a
client disconnect and serve the next one.

## Key points
- **Two exit conditions, both required:**
  - `if not data: break` — the client's socket closed (Ctrl+C, crash). Without this the
    loop spins forever on empty reads and pins the CPU.
  - `if message.lower() == 'exit': break` — the graceful shutdown the question asks for.
- `.strip()` removes stray whitespace/newlines so `"exit\n"` still matches.
- The comparison is case-insensitive, so `EXIT` and `Exit` work too.

## Test sequence
```
You  : hello        Echo : hello
You  : 12345        Echo : 12345
You  : EXIT         Echo : Connection closed by server. Bye!
```
