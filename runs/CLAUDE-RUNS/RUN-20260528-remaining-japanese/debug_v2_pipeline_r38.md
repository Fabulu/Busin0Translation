# Debug: Does build_full_english_v2.py overwrite R38?

## Answer: NO -- Step 2 overwrites Step 1's R38. The pipeline is SAFE.

---

## Question-by-question

### a. Does v2 pipeline process R38?
**YES.** `build_full_english_v2.py` loads chunk_00 through chunk_09 (Step 1 of v2),
plus `chunk_r38_fix.json` (line 63). R38 translations exist in:
- `chunk_01_translated.json`: 11 R38 entries
- `chunk_02_translated.json`: 113 R38 entries
- `chunk_03_translated.json`: 52 R38 entries
- `chunk_r38_fix.json`: 188 entries (OVERRIDE)

The fix chunk overrides via de-duplication (later entries win, line 74).
v2 pipeline encodes these and writes `build/packdata_resources/0038_type01.raw`.

### b. Does it write to build/packdata_resources/0038_type01.raw?
**YES.** The `inject_resource()` function (line 296) reads from
`extracted/packdata_raw/0038_type01.raw`, injects translations, and writes to
`build/packdata_resources/0038_type01.raw` (line 413).

### c. What translations does it use?
It uses **both** chunk_00-09 AND chunk_r38_fix.json. The fix chunk entries
override chunk entries for the same (resource, message) pair via the
`trans_map` de-duplication on line 73-81.

However, v2 pipeline does NOT load:
- `chunk_r37_extra.json`
- `chunk_r40_r42_translated.json`
- `chunk_r36_translated.json`
- `chunk_r37_r48_r49_translated.json`
- `chunk_r43_r45_translated.json`

Those are only loaded by build_v9.py Step 2.

### d. Does Step 1 run BEFORE or AFTER Step 2?
**Step 1 runs BEFORE Step 2.** In `build_v9.py`:
- Line 16: `os.system('python build/build_full_english_v2.py ...')` -- runs v2 pipeline FIRST
- Line 79: Loop over R38 (among others) -- runs SECOND, overwrites the file

### e. Could Step 1's R38 output be OVERWRITING Step 2's R38 output?
**NO.** The order is:

```
Step 1 (v2 pipeline) -> writes build/packdata_resources/0038_type01.raw  [FORMAT-A, variable-size]
Step 2 (build_v9.py) -> writes build/packdata_resources/0038_type01.raw  [FIXED-SIZE, pad/truncate]
```

Step 2 OVERWRITES Step 1. Step 2 is the final writer for R38.

---

## Critical difference: Step 1 vs Step 2 injection methods

### Step 1 (v2 pipeline) -- FORMAT-A variable-size
- Parses offset table, rebuilds it after injection
- Allows glyph stream to grow/shrink
- Uses `encode_text()` from `encode_english_text.py` (with word-wrapping, page breaks)
- Loads chunk_r38_fix.json overrides

### Step 2 (build_v9.py) -- FIXED-SIZE pad/truncate
- Finds FFFF groups by brute scan (line 84)
- Pads short translations with 0x0000 (line 119)
- **TRUNCATES** translations that exceed the original group size (line 121: `nc = nc[:ocs]`)
- Uses its own simpler `enc()` + `word_wrap()` functions
- Loads chunk_r38_fix.json AND additional fix files

### The real risk: TRUNCATION in Step 2
Step 2 uses fixed-size injection: if the English text is longer than the
original Japanese, it gets silently truncated (line 121). This is the likely
cause of any remaining Japanese or cut-off text in R38.

Step 1's variable-size injection would actually be BETTER for R38, but Step 2
overwrites it with the inferior fixed-size version.

---

## Recommendations

1. **R38 should NOT be in Step 2's fixed-size list.** Step 1 already handles it
   correctly with variable-size injection + offset table rebuild.

2. **To fix:** Remove `38` from the list on line 79 of `build_v9.py`:
   ```python
   for r_id in [34, 35, 36, 37, 40, 41, 42, 43, 44, 45, 48, 49, 2124, 2654]:
   ```
   This lets Step 1's variable-size R38 survive to the final ISO.

3. **Or:** Convert R38 in Step 2 to use variable-size injection (like the
   type-2 resources in Step 4), but that's more work for no benefit since
   Step 1 already does it correctly.

---

## Order of operations (full pipeline)

```
build_v9.py
  Step 1: build_full_english_v2.py    -> writes ALL type-1 resources (including R38)
  Step 2: Fixed-size re-inject        -> OVERWRITES R34,35,36,37,38,40-45,48,49,2124,2654
  Step 3: R39 type-15 injection
  Step 3.5: R46/R47 type-03
  Step 3.6: R1188 tab labels
  Step 4: Type-2 variable-size        -> writes to build/patched_type2/
  Step 5: R1193 manual
  Step 6: Merge patched_type2 -> packdata_resources
  Step 7: Rebuild PACKDATA.DIG
  Step 8: Build ISO + patch EXE
```
