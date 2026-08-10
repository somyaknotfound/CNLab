# Q5 - Line, word and character count (TCP)

**Aim:** client sends a filename; the server counts lines, words and characters in that
file and returns the counts.

## Important: whose file is it?
The file lives on the **server's** disk. The client sends only a *name* — no file content
crosses the network in this question. (Q8 is the one where the file itself is transferred.)

Test files live in `q05_file_stats/files/`. `sample.txt` is provided.

## Wire protocol
| Direction | Payload |
|---|---|
| client -> server | the filename, e.g. `sample.txt` |
| server -> client | a multi-line report, or `Error: ...` |

## Counting
```python
lines = len(content.splitlines())   # no trailing empty entry, unlike split('\n')
words = len(content.split())        # split() on no argument collapses runs of whitespace
chars = len(content)                # includes newlines and spaces
```
`wc -l` counts newline characters, so it can differ by one on a file with no trailing
newline. Say so if asked — `splitlines()` counts logical lines.

## Security note worth mentioning in the viva
`os.path.basename(filename)` strips any directory component, so a client cannot request
`../../etc/passwd`. Any server that opens a client-supplied path must do this.

## Test cases
| Request | Result |
|---|---|
| `sample.txt` | 4 lines, 18 words, 129 chars |
| `missing.txt` | `Error: file 'missing.txt' not found on the server` |
| an empty file | 0 / 0 / 0 |
