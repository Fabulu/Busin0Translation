# Debug: rebuild_packdata.py Resource Loading Analysis

Date: 2026-05-28

## Script Location
`build/rebuild_packdata.py`

## Q&A

### (a) Where does it read resource files from?

Three locations, checked in priority order:

1. **`build/packdata_resources/{idx:04d}_type{tc:02d}.raw`** -- patched files (PRIORITY)
2. **`extracted/packdata_raw/{idx:04d}_type{tc:02d}.raw`** -- original extracted raws (fallback 1)
3. **`extracted/packdata_raw/{idx:04d}_type*.raw`** via glob -- wildcard fallback (fallback 2)

The manifest is loaded from `extracted/packdata_resources/manifest.json`.

### (b) Could R38 be missed due to naming?

**No.** R38 naming is correct:
- Manifest says: index=38, type_code=1
- Expected filename: `0038_type01.raw`
- Patched file exists: `build/packdata_resources/0038_type01.raw` -- PRESENT
- Original file exists: `extracted/packdata_raw/0038_type01.raw` -- PRESENT

R38 WILL be picked up. The patched version takes priority.

### (c) Does it fall back to original resources if patched ones aren't found?

**Yes.** The logic is:

```python
if os.path.exists(mp):          # build/packdata_resources/...
    d = open(mp, 'rb').read()   # use patched
elif os.path.exists(rp):        # extracted/packdata_raw/...
    d = open(rp, 'rb').read()   # use original raw
else:
    # glob fallback, then empty sector
```

So any resource WITHOUT a patched file in `build/packdata_resources/` will silently use the original Japanese data from `extracted/packdata_raw/`.

### (d) What naming convention does it expect?

`{index:04d}_type{type_code:02d}.raw`

Examples: `0038_type01.raw`, `0034_type20.raw`, `0046_type03.raw`

The `index` and `type_code` come from the manifest entry, NOT from scanning filenames. The script iterates manifest entries and constructs filenames from them.

### (e) Files for resources 34-49

| Index | Type | Patched file exists? | Source used |
|-------|------|---------------------|-------------|
| 34 | 20 | YES `0034_type20.raw` | PATCHED |
| 35 | 02 | YES `0035_type02.raw` | PATCHED |
| 36 | 01 | YES `0036_type01.raw` | PATCHED |
| 37 | 01 | YES `0037_type01.raw` | PATCHED |
| 38 | 01 | YES `0038_type01.raw` | PATCHED |
| 39 | 15 | NO | ORIGINAL (extracted/packdata_raw/0039_type15.raw) |
| 40 | 01 | YES `0040_type01.raw` | PATCHED |
| 41 | 01 | YES `0041_type01.raw` | PATCHED |
| 42 | 01 | YES `0042_type01.raw` | PATCHED |
| 43 | 01 | YES `0043_type01.raw` | PATCHED |
| 44 | 01 | YES `0044_type01.raw` | PATCHED |
| 45 | 01 | YES `0045_type01.raw` | PATCHED |
| 46 | 03 | YES `0046_type03.raw` | PATCHED |
| 47 | 03 | YES `0047_type03.raw` | PATCHED |
| 48 | 01 | YES `0048_type01.raw` | PATCHED |
| 49 | 01 | YES `0049_type01.raw` | PATCHED |

**15 of 16 resources patched.** Only R39 (type 15, non-text) uses original data.

## manifest.json Role

The manifest **drives everything**. The script iterates `manifest` entries, not filesystem files. If a resource is not in the manifest, it is never processed. If a resource has `"skipped": true`, it copies the original TOC entry verbatim (no data written, just preserves original sector pointers).

Currently only 2 entries are skipped: index 1370 and 2100.

The manifest does NOT filter or exclude any resources 34-49 -- all 16 are present and active.

## Key Finding

The rebuild script correctly picks up all patched files from `build/packdata_resources/`. If R38 still shows Japanese text in-game, the problem is NOT the rebuild pipeline -- the patched file itself (`build/packdata_resources/0038_type01.raw`) must contain the untranslated content, or the translation injection step that creates it is at fault.

## Total Patched Resources

The `build/packdata_resources/` directory contains 49 patched `.raw` files total.
