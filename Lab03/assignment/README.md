# Assignment — Socket Programming (10 Questions)

Each folder contains `server.py`, `client.py` and a `NOTES.md` explaining the approach,
the protocol used on the wire, and the edge cases.

## How to run any of them

Two terminals, **server first**:

```bash
cd q01_uppercase
python server.py        # terminal 1
python client.py        # terminal 2
```

Every client also accepts command-line arguments so you can run it non-interactively:

```bash
python client.py hello world
```

## Index

| # | Folder | Protocol | Port | Problem |
|---|---|---|---|---|
| 1 | `q01_uppercase/` | TCP | 5001 | String → uppercase |
| 2 | `q02_arithmetic/` | TCP | 5002 | Two numbers + operator → result |
| 3 | `q03_prime_udp/` | UDP | 5003 | Integer → prime or not |
| 4 | `q04_echo/` | TCP | 5004 | Echo until the client sends `exit` |
| 5 | `q05_file_stats/` | TCP | 5005 | Filename → line/word/char counts |
| 6 | `q06_udp_clientinfo/` | UDP | 5006 | Message + client IP and port |
| 7 | `q07_palindrome/` | TCP | 5007 | String → palindrome check |
| 8 | `q08_file_transfer/` | TCP | 5008 | Transfer a text file to the server |
| 9 | `q09_string_analysis/` | TCP | 5009 | Sentence → vowels/consonants/words |
| 10 | `q10_sort_array/` | TCP | 5010 | Integer array → sorted |

Each question uses a different port, so you can leave several servers running at once
without collisions.

## Quick examples

```bash
cd q02_arithmetic  && python server.py &  python client.py 12 + 5
cd q03_prime_udp   && python server.py &  python client.py 97
cd q08_file_transfer && python server.py & python client.py send/demo.txt
cd q10_sort_array  && python server.py &  python client.py 3 1 4 1 5 9 2 6
```

## Automated check

`run_all_tests.py` starts each server, runs its client, and verifies the output:

```bash
python run_all_tests.py          # all 10
python run_all_tests.py 3 7      # only questions 3 and 7
```

Expected result: `14/14 passed`.

## Common patterns across all ten

- Every TCP server sets `SO_REUSEADDR` before `bind()` — otherwise restarting it within
  60 seconds fails with `Address already in use`.
- Every server loops on `accept()` (or `recvfrom()`), so one client disconnecting does not
  kill it. `Ctrl+C` stops it cleanly.
- Every server validates its input and returns an `Error: ...` message rather than
  crashing on bad data.
- Anything read from a socket is `bytes`; `.decode()` on the way in, `.encode()` on the
  way out.
- Where a filename comes from the client (Q5, Q8), `os.path.basename()` blocks path
  traversal.

## Where the interesting bits are

| Concept | Question |
|---|---|
| UDP vs TCP call sequence | Q3, Q6 |
| Getting the peer's IP and port | Q6 |
| Nested loops for a multi-message session | Q4 |
| Message framing / length prefix | Q8 |
| Sending structured data (JSON) | Q10 |
| Server-side input validation | Q2, Q10 |
| Reading files in binary mode | Q8 |
