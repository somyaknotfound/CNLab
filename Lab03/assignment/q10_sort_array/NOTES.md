# Q10 - Sort an integer array (TCP)

**Aim:** client sends an array of integers; server returns the sorted array.

## How do you put a list on a socket?
A socket carries bytes, not Python objects. Three options:

| Method | Send | Receive | Comment |
|---|---|---|---|
| **JSON** (used here) | `json.dumps([3,1,2])` | `json.loads(s)` | Human-readable, language-neutral, safe |
| Space-separated text | `' '.join(map(str, a))` | `[int(x) for x in s.split()]` | Fine for flat integer lists |
| `pickle` | `pickle.dumps(a)` | `pickle.loads(b)` | **Never** on untrusted data — unpickling executes arbitrary code |

JSON is the right answer in a viva: it is safe, it survives nesting, and a client written
in another language can talk to the same server.

## Key points
- Server validates: valid JSON, is a list, all elements are integers. It replies with a
  JSON `{"error": ...}` object rather than crashing.
- `sorted()` returns a new list; `list.sort()` sorts in place. `sorted()` is used so the
  original can also be returned.
- Python's `sorted()` is Timsort — O(n log n) worst case, stable.
- The response includes min/max/count as a bonus; the required field is `sorted`.
- `recv(65536)` covers a fairly large array. For arbitrarily large arrays you would need
  the length-prefix framing from Q8 / `practice/05_length_prefix/`.

## Test cases
| Input | Sorted |
|---|---|
| `3 1 4 1 5 9 2 6` | `[1, 1, 2, 3, 4, 5, 6, 9]` |
| `5 4 3 2 1` | `[1, 2, 3, 4, 5]` |
| `1 2 3` (already sorted) | `[1, 2, 3]` |
| `-5 3 -1 0` | `[-5, -1, 0, 3]` |
| `7` (single element) | `[7]` |
| `[]` (empty) | `[]`, min/max `null` |
