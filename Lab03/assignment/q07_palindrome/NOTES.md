# Q7 - Palindrome check (TCP)

**Aim:** server receives a string and checks whether it reads the same forwards and
backwards.

## The check
```python
cleaned = ''.join(ch.lower() for ch in text if ch.isalnum())
is_palindrome = cleaned == cleaned[::-1]
```

`s[::-1]` is slice notation with a step of -1 — the idiomatic Python reversal.

## Normalisation: a design decision to defend
`"A man, a plan, a canal: Panama"` is a palindrome in the usual sense but not a strict
character-by-character one. This solution **normalises** first: lowercase, drop
punctuation and spaces. Mention the choice in the viva — the strict version is simply
`text == text[::-1]`.

## Key points
- `str.isalnum()` filters out spaces and punctuation.
- Single characters and the empty string are trivially palindromes; the empty case is
  handled with an explicit message rather than a misleading "yes".
- The reply includes the normalised and reversed forms so the result is verifiable.

## Test cases
| Input | Verdict |
|---|---|
| `racecar` | palindrome |
| `Madam` | palindrome (case-insensitive) |
| `A man, a plan, a canal: Panama` | palindrome (punctuation ignored) |
| `hello` | not a palindrome |
| `12321` | palindrome |
| `a` | palindrome |
| `!!!` | no alphanumeric characters |
