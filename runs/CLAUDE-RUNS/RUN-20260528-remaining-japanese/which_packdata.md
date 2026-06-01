# Which PACKDATA ends up in the ISO?

## Answer: PACKDATA_v3.DIG (from rebuild_packdata.py) goes into the v9/v29 ISO

The v2 pipeline's PACKDATA.DIG is built first but then OVERWRITTEN in the ISO by
the v9 pipeline's Step 8, which uses PACKDATA_v3.DIG.

---

## Full trace for the v29 ISO

### Execution order of build_v9.py

1. **Step 1** - Calls `build_full_english_v2.py` (the entire v2 pipeline)
   - v2 Step 5 builds `build/PACKDATA.DIG` (from `build/packdata_resources/`)
   - v2 Step 6 copies original ISO to `build/BUSIN0_EN.iso`, writes `build/PACKDATA.DIG` into it
   - v2 Step 6b patches EXE into `build/BUSIN0_EN.iso`

2. **Steps 2-6** - build_v9.py modifies files in `build/packdata_resources/`
   (type-2 variable-size injection, section-1 opcode patching, etc.)

3. **Step 7** - Calls `rebuild_packdata.py`
   - Reads from `build/packdata_resources/` (now modified by steps 2-6)
   - Writes `build/PACKDATA_v3.DIG`

4. **Step 8** - Builds the ISO
   - Reads `build/PACKDATA_v3.DIG` into memory (line 262)
   - Copies ORIGINAL ISO (not v2's BUSIN0_EN.iso!) to `build/BUSIN0_EN_v9.iso` (line 263)
   - Writes PACKDATA_v3.DIG data into the new ISO at the PACKDATA extent

5. **Step 8.4/8.5** - Patches EXE into `build/BUSIN0_EN_v9.iso`

### Key finding: v9 does NOT build on v2's ISO

build_v9.py line 263:
```python
shutil.copy2('Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso', 'build/BUSIN0_EN_v9.iso')
```

It copies the ORIGINAL Japanese ISO, not `build/BUSIN0_EN.iso`. So v2's ISO output
is effectively wasted -- it is overwritten each run but never used by the v9 pipeline.

### v29 = v9 (confirmed)

```
md5: af4a534af33ef000a8d045af38db40ab  BUSIN0_EN_v9.iso
md5: af4a534af33ef000a8d045af38db40ab  BUSIN0_EN_v29.iso
```

v29 is a byte-identical copy of v9, renamed post-build (2.8 seconds later).
The "v29" version number is a manual rename, not a separate build script.

---

## Two PACKDATA files in build/

| File | Size | Modified | MD5 | Source |
|------|------|----------|-----|--------|
| PACKDATA.DIG | 839,837,696 | May 31 22:47 | 840895832f... | v2 pipeline Step 5 |
| PACKDATA_v3.DIG | 839,829,504 | May 31 22:48 | 7d83ad8849... | rebuild_packdata.py (Step 7) |

PACKDATA.DIG is 8,192 bytes (4 sectors) LARGER than PACKDATA_v3.DIG.
They have different MD5 hashes -- they contain different data.

### Why the size difference?

Both scripts read resources from `build/packdata_resources/`, but:
- v2's Step 5 runs FIRST (before steps 2-6 modify resources)
- rebuild_packdata.py runs AFTER steps 2-6 (variable-size type-2 injection)

The type-2 variable-size resources may pack differently, and the v2 pipeline may
include resources that build_v9.py explicitly removes (R1053 type-03, R1908 type-06
are deleted between Step 1 and Step 2).

### What goes in the v29 ISO: PACKDATA_v3.DIG

The v29 ISO contains the PACKDATA_v3.DIG data -- the one built by rebuild_packdata.py
after all v9-pipeline modifications. This is correct behavior.

---

## Potential concern: BUSIN0_EN.iso is a red herring

`build/BUSIN0_EN.iso` (md5: 6752ce44...) is built by v2's Step 6 but never consumed
by any subsequent step. It sits there as a stale artifact. It contains PACKDATA.DIG
(the v2-only version without type-2 variable-size injection).
