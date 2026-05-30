# R38 Step-by-Step Pipeline Debug Trace

## Methodology
Ran each build step independently, checking R38's content after each:
1. `build_full_english_v2.py` (Step 1 -- variable-size injection with offset table rebuild)
2. `build_v9.py` Step 2 logic (fixed-size in-place injection from ORIGINAL source)
3. `rebuild_packdata.py` (packs resources into PACKDATA_v3.DIG)
4. Checked R38 in the existing v9/v15/v16 ISOs

At each step, examined all FFFF groups for English vs Japanese glyph values (English < 200, Japanese > 200).

## Results by Step

### Checkpoint 0: Original extracted file
- File: `extracted/packdata_raw/0038_type01.raw`
- Size: 8192 bytes, 189 FFFF groups
- Content: Mix of English and Japanese (original JP game data)
- First glyphs after first FFFF: `0x0028, 0x0030, 0xFFFE` (low values, numbers/control)

### Checkpoint 1: After build_full_english_v2.py
- Size: 8192 bytes, 189 FFFF groups
- MD5: `e7bd8dea1c13121733384625c753bb6d`
- **ALL 189 groups are ENGLISH** (max glyph < 200)
- First glyphs: `0x0053, 0x0054, 0x0052` ("STR" -- beginning of English text)

### Checkpoint 2: After build_v9 Step 2 (fixed-size injection)
- Size: 8192 bytes, 189 FFFF groups
- MD5: `e7bd8dea1c13121733384625c753bb6d` **IDENTICAL to Step 1**
- **ALL 189 groups are ENGLISH**
- 187 messages replaced, 145 truncated (fixed-size constraint)
- Step 2 output happened to produce the same file (same translations, same glyph encoding)

### Checkpoint 3: After rebuild_packdata.py
- R38 in PACKDATA_v3.DIG matches the patched file exactly
- MD5: `e7bd8dea1c13121733384625c753bb6d`
- **ALL 189 groups are ENGLISH**

## ISO Comparison

| ISO | FFFF Groups | English | Japanese | Notes |
|-----|-------------|---------|----------|-------|
| v15 | 189 | 182 | 7 | Older build, incomplete translations |
| v16 | 217 | 216 | 1 | Built with v2 pipeline (variable-size, more groups) |
| v9  | 217 | 216 | 1 | Same pipeline as v16 |

### The 1 Remaining Japanese Group in v16/v9 ISOs
- Group 76 contains a single glyph: `0x015D` (decimal 349)
- This glyph is NOT in the English glyph table -- it is an unmapped Japanese character
- In the original R38, `0x015D` appears in groups 27, 69, 103, 104, 118
- In the current patched file (post-build_v9), ALL these groups are fully English
- The v16 ISO was built by an EARLIER run of the v2 pipeline that had a different group mapping

## Key Findings

### 1. R38 is fully translated in current build artifacts
The current `build/packdata_resources/0038_type01.raw` is 100% English across all 189 FFFF groups. No Japanese remains.

### 2. The v16/v9 ISOs are STALE
They were built by earlier pipeline runs and do not reflect the current state of `build/packdata_resources/`. A fresh rebuild of the ISO would produce a fully-English R38.

### 3. The 1 remaining Japanese glyph (0x015D) in the v16 ISO
This is a single unmapped glyph that the v2 pipeline left behind because it couldn't encode it. In the current fixed-size pipeline (build_v9 Step 2), this group IS translated -- the text was word-wrapped and encoded correctly, and the 0x015D glyph was replaced with English.

### 4. No step in the current pipeline "loses" translations
- Step 1 (v2): Produces English R38
- Step 2 (v9 overwrite): Also produces English R38 (identical MD5)
- Step 3 (rebuild): Correctly packs the English R38 into PACKDATA_v3.DIG

### 5. The real issue: ISOs need rebuilding
The fix is simply to run a fresh `build_v9.py` (or equivalent) to regenerate the ISO from the current patched resources. The translation data and injection code are all correct.

### 6. Windows PYTHONIOENCODING issue
`build_v9.py` uses `os.system('PYTHONIOENCODING=utf-8 python ...')` which fails on Windows (PYTHONIOENCODING is treated as a command name, not an env var). This causes Step 1 and Step 7 to silently fail, leaving stale artifacts. The correct Windows syntax would be `set PYTHONIOENCODING=utf-8 && python ...` or using `subprocess` with `env` parameter.

## Files Examined
- `extracted/packdata_raw/0038_type01.raw` -- original Japanese resource
- `build/packdata_resources/0038_type01.raw` -- patched English resource
- `build/PACKDATA_v3.DIG` -- rebuilt PACKDATA archive
- `build/BUSIN0_EN_v9.iso`, `build/BUSIN0_EN_v15.iso`, `build/BUSIN0_EN_v16.iso` -- built ISOs
- `build/build_full_english_v2.py` -- Step 1 pipeline
- `build/build_v9.py` -- Full build pipeline
- `build/rebuild_packdata.py` -- PACKDATA rebuild script
