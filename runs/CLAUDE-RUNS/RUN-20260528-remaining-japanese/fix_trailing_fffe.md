# Fix: Trailing FFFE Overflow in R38 Descriptions

## Problem
57 of 62 R38 class descriptions overflowed the 3-line chargen textbox.
The root cause: all translations ended with ` / ` (e.g. `"Poleaxe weapons. / Dispel vs undead. / Holy Magic Lv5. /"`),
which after `split(' / ')` produced a trailing empty segment, generating a phantom 4th-line FFFE.

## Fix Applied
**File:** `build/build_full_english_v2.py`, function `clean_and_encode()` (line ~125)

Added after `parts = text.split(' / ')`:
```python
# Strip trailing empty segments to avoid phantom blank lines / FFFE overflow
while parts and not parts[-1].strip():
    parts.pop()
```

Updated docstring to reflect the new behavior (no longer preserves trailing empty segments).

## Verification
- Full rebuild completed successfully (build v10+).
- Scanned all 189 FFFF-terminated groups in patched R38 resource.
- **Result: 0 groups with >2 FFFE breaks.** All descriptions fit within the 3-line limit.

## Scope
This fix applies globally to all resources processed by `clean_and_encode()`, not just R38.
Any translation ending with ` / ` will no longer produce a trailing FFFE. This is correct
behavior -- the trailing ` / ` in translation strings is a formatting artifact, not an
intentional blank line.
