# Q9 - Vowels, consonants and words (TCP)

**Aim:** client sends a sentence; server returns the count of vowels, consonants and
words.

## The counting logic
```python
for ch in sentence.lower():
    if ch.isalpha():                    # only letters count
        if ch in 'aeiou':
            vowels += 1
        else:
            consonants += 1

words = len(sentence.split())
```

## Decisions worth being able to justify
- **`isalpha()` gate first.** Without it, digits and punctuation get counted as
  consonants — the single most common mistake in this exercise.
- **`.lower()` once**, up front, so `'A'` and `'a'` are treated the same.
- **`split()` with no argument** collapses runs of whitespace and ignores leading/trailing
  spaces, so `"  hello   world  "` is 2 words. `split(' ')` would return empty strings and
  give the wrong count.
- **`y`** is counted as a consonant here. Mention that this is a convention.
- Using a `set` for the vowels gives O(1) membership instead of O(5) — irrelevant at this
  scale, but the right instinct.

## Test cases
| Sentence | Vowels | Consonants | Words |
|---|---|---|---|
| `Hello World` | 3 | 7 | 2 |
| `Computer Networks Lab` | 7 | 12 | 3 |
| `AEIOU` | 5 | 0 | 1 |
| `xyz` | 0 | 3 | 1 |
| `abc 123 !!!` | 1 | 2 | 3 |
| `  spaced   out  ` | 4 | 5 | 2 |
