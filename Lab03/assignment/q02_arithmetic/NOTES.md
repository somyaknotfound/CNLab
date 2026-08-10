# Q2 - Arithmetic operations (TCP)

**Aim:** client sends two numbers and an operator, server returns the computed result.

## Wire protocol
| Direction | Payload |
|---|---|
| client -> server | `"<num1> <operator> <num2>"`, e.g. `12 + 5` |
| server -> client | the result as text, or an `Error: ...` message |

Space-separated text is the simplest encoding that carries three values in one message.
`msg.split()` recovers them. Alternatives worth knowing: comma-separated (`12,+,5`) or
JSON (`json.dumps({...})`) — JSON is what you would use in real code.

## Key points
- **Validate on the server.** Never trust the client. This program checks the field count,
  that the operands parse as numbers, that the operator is known, and that the divisor is
  non-zero.
- Do **not** use `eval()` on data received from a socket — a client could send
  `__import__('os').system('rm -rf /')`. Explicit parsing is both safer and the expected
  answer in a viva.
- `float()` is used so `2.5 * 4` works; the result is printed as an integer when it is
  whole.

## Test cases
| Sent | Reply |
|---|---|
| `12 + 5` | `17` |
| `10 - 25` | `-15` |
| `6 * 7` | `42` |
| `7 / 2` | `3.5` |
| `5 / 0` | `Error: division by zero` |
| `5 % 2` | `Error: unsupported operator '%'` |
| `a + 1` | `Error: operands must be numbers` |
