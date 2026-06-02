# Build Pipeline Overwrite Conflicts Audit

Date: 2026-06-01

## Pipeline Overview (build_v9.py)

| Step | Script | What it writes to `build/packdata_resources/` |
|------|--------|-----------------------------------------------|
| 1 | `build_full_english_v2.py` | R34-R49, R1053, R1908, R2124, R2654 (any resource with translations in chunk files). Also writes R1272 font atlas (Step 3 inside v2). Also R1188 via Step 3b (patch_r1188_direct.py). Also builds its own PACKDATA.DIG + ISO (wasted work). |
| 1 (cleanup) | build_v9.py lines 20-24 | **Removes** R1053 (type03) and R1908 (type06) from packdata_resources |
| 2 | build_v9.py inline | R35 (type02), R2654 (type44) -- fixed-size flat injection |
| 3 | `build/inject_r39_v2.py` | R39 (type15) -- equipment glyph stream |
| 3.1 | `tools/patch_r39_inline.py` | R39 (type15) -- modifies the file from Step 3 in-place |
| 3.5 | `build/inject_r46_r47.py` | R46, R47 (type03) |
| 3.6 | `tools/patch_r1188_comprehensive.py` | R1188 (type01) |
| 4 | `patch_section1_offsets.py` | Type-02 resources -> `build/patched_type2/` |
| 5 | build_v9.py inline | Copies R1193 from packdata_resources to patched_type2 |
| 6 | build_v9.py inline | Copies ALL of `build/patched_type2/` into `build/packdata_resources/` (merge) |
| 7 | `build/rebuild_packdata.py` | `build/PACKDATA_v3.DIG` |
| 8+ | build_v9.py inline | ISO assembly |

## Files Written by Multiple Steps

### 1. R39 (`0039_type15.raw`) -- CONFLICT (benign, ordering-dependent)

| Order | Step | Script | Reads from | Writes to |
|-------|------|--------|------------|-----------|
| 1st | Step 1 (v2 pipeline) | `build_full_english_v2.py` | `extracted/packdata_raw/0039_type15.raw` | `build/packdata_resources/0039_type15.raw` |
| 2nd | Step 3 | `build/inject_r39_v2.py` | `extracted/packdata_raw/0039_type15.raw` | `build/packdata_resources/0039_type15.raw` |
| 3rd | Step 3.1 | `tools/patch_r39_inline.py` | `build/packdata_resources/0039_type15.raw` | `build/packdata_resources/0039_type15.raw` (in-place) |

**Status: WORKS BY ACCIDENT.** Step 3 overwrites Step 1's output by reading from the *original* extracted file (not from Step 1's output). Step 3.1 correctly reads Step 3's output. The v2 pipeline's R39 processing is wasted work. However, if Step 3's `os.remove()` on line 135 were removed or the ordering changed, Step 1's type-01-style injection (wrong format for type-15) would be used.

**Risk:** Low, but fragile. The v2 pipeline applies type-01 parsing (sub-header + offset table) to a type-15 resource. The result is likely corrupt but gets overwritten.

**Fix:** Add R39 to the skip list in the v2 pipeline, or add it to the unsafe removal list in build_v9.py (lines 20-24).

### 2. R46/R47 (`0046_type03.raw`, `0047_type03.raw`) -- CONFLICT (benign, ordering-dependent)

| Order | Step | Script | Reads from | Writes to |
|-------|------|--------|------------|-----------|
| 1st | Step 1 (v2 pipeline) | `build_full_english_v2.py` | `extracted/packdata_raw/0046_type03.raw` | `build/packdata_resources/0046_type03.raw` |
| 2nd | Step 3.5 | `build/inject_r46_r47.py` | (unknown -- likely extracted) | `build/packdata_resources/0046_type03.raw` |

**Status: WORKS BY ACCIDENT.** Same pattern as R39 -- Step 3.5 overwrites Step 1's output. The v2 pipeline's type-01 parsing on a type-03 resource is wasted work and the result is likely corrupt, but it gets overwritten.

**Fix:** Add R46, R47 to the unsafe removal list in build_v9.py (alongside R1053/R1908), or skip them in the v2 pipeline.

### 3. R35 (`0035_type02.raw`) -- CONFLICT (benign, ordering-dependent)

| Order | Step | Script | Reads from | Writes to |
|-------|------|--------|------------|-----------|
| 1st | Step 1 (v2 pipeline) | `build_full_english_v2.py` | `extracted/packdata_raw/0035_type02.raw` | `build/packdata_resources/0035_type02.raw` |
| 2nd | Step 2 | build_v9.py inline | `extracted/packdata_raw/0035_type02.raw` | `build/packdata_resources/0035_type02.raw` |

**Status: WORKS BY ACCIDENT.** Step 2 overwrites Step 1's output. Both read from the original extracted file. Step 2 uses a simpler flat-format injector that is correct for R35's format.

**CONFIRMED: R35 also has 35 translations in `data/type2_translated/batch_dungeon_a.json`.** This means Step 4 WILL process it (type_code=2, not skipped), writing to `build/patched_type2/0035_type02.raw`. Step 6 then copies that over the Step 2 output. **R35 is written FOUR times:**

1. Step 1 (v2 pipeline) -- type-01 format parsing (likely wrong for type-02)
2. Step 2 (flat inject) -- correct fixed-size replacement
3. Step 4 -> Step 6 (type-2 variable-size) -- OVERWRITES Step 2

**This is a REAL BUG if Step 2's flat-format injection and Step 4's variable-size injection produce different results.** Step 4 uses `inject_and_patch()` which does variable-size injection with offset table rebuilding. Step 2 uses simple fixed-size replacement. If R35's format requires the flat approach, Step 4's version may be corrupt. If R35's format supports variable-size, Step 2's version may truncate long translations.

R35 is NOT in the `binary_resources` removal list (lines 247-256), so Step 6's copy is the final version used by `rebuild_packdata.py`.

**Fix:** Decide which injection method is correct for R35 and remove the other. If flat (Step 2), add R35 to the binary_resources removal list or exclude it from Step 4. If variable-size (Step 4), remove R35 from Step 2.

### 4. R2654 (`2654_type44.raw`) -- CONFLICT (benign, ordering-dependent)

| Order | Step | Script | Reads from | Writes to |
|-------|------|--------|------------|-----------|
| 1st | Step 1 (v2 pipeline) | `build_full_english_v2.py` | `extracted/packdata_raw/2654_type44.raw` | `build/packdata_resources/2654_type44.raw` |
| 2nd | Step 2 | build_v9.py inline | `extracted/packdata_raw/2654_type44.raw` | `build/packdata_resources/2654_type44.raw` |

**Status: Same as R35.** Step 2 overwrites Step 1's output.

**Fix:** Skip R2654 in the v2 pipeline.

### 5. R1188 (`1188_type01.raw`) -- CRITICAL CONFLICT

| Order | Step | Script | Reads from | Writes to |
|-------|------|--------|------------|-----------|
| 1st | Step 1, sub-step 3b | `tools/patch_r1188_direct.py` | `extracted/` (original) | `build/packdata_resources/1188_type01.raw` |
| 2nd | Step 1, sub-step 3b | `tools/patch_r1188_stats.py` | **UNKNOWN** (file not found on disk) | `build/packdata_resources/1188_type01.raw` (likely) |
| 3rd | Step 3.6 | `tools/patch_r1188_comprehensive.py` | `extracted/` (original) | `build/packdata_resources/1188_type01.raw` |

**Status: CONFLICT -- Step 3.6 DESTROYS Step 1's work.**
- `patch_r1188_direct.py` reads from the *original* extracted file and writes tab label patches.
- `patch_r1188_comprehensive.py` ALSO reads from the *original* extracted file, so it does NOT include the changes from `patch_r1188_direct.py`.
- Both write to the same output path.
- Step 3.6 runs AFTER Step 1, so its output wins.

**However**, `patch_r1188_comprehensive.py` is described as replacing `patch_r1188_direct.py` -- it handles all the same labels plus more (stat labels, sidebar labels, banner, etc.). So this is likely **intentional supersession**, not a bug.

**Remaining question:** The v2 pipeline (Step 1) calls BOTH `patch_r1188_direct.py` AND `patch_r1188_stats.py` sequentially. The stats script was supposed to "stack on top" of the direct patch. But `patch_r1188_stats.py` does not exist on disk, which means the v2 pipeline's `os.system()` call silently fails. This is harmless because Step 3.6's comprehensive script handles everything.

**Risk:** The v2 pipeline's Step 3b is dead code. If Step 3.6 were ever removed, the v2 pipeline's R1188 patching would be incomplete (stats script missing).

**Fix:** Remove Step 3b from the v2 pipeline entirely (it's superseded by Step 3.6 in build_v9.py). Or simply note that the v2 pipeline is only called FROM build_v9.py and Step 3.6 always overwrites.

### 6. R1272 (`1272_type01.raw`) -- NO CONFLICT

| Order | Step | Script | Reads from | Writes to |
|-------|------|--------|------------|-----------|
| Pre-build | `tools/generate_font_atlas.py` | `extracted/` | `build/english_font_atlas.bin` (intermediate) |
| 1st | Step 1 (v2 pipeline), Step 3 | `build_full_english_v2.py` | `build/english_font_atlas.bin` + `extracted/packdata_raw/1272_type01.raw` | `build/packdata_resources/1272_type01.raw` |

**Status: NO CONFLICT.** Only one step writes R1272. The font atlas generator creates `build/english_font_atlas.bin`, and the v2 pipeline's Step 3 wraps it with the R1272 sub-header and writes the final resource. No other step touches R1272.

### 7. Type-02 resources from Step 4/6 merge -- POTENTIAL CONFLICT with Step 1

Step 4 writes type-02 resources to `build/patched_type2/`. Step 6 copies them to `build/packdata_resources/`. If any type-02 resource was ALSO processed by the v2 pipeline (Step 1), the Step 6 copy would overwrite it.

**Resources at risk:** R35 (type_code=2) is processed by both Step 1 and Step 2. Step 4 might also process it if R35 has entries in `data/type2_translated/batch_*.json`. R35 would then be written THREE times:
1. Step 1 (v2 pipeline) -- type-01 format (wrong)
2. Step 2 (flat inject) -- correct
3. Step 6 (type-2 variable-size) -- would overwrite Step 2

However, Step 4 explicitly excludes R1193 and only includes resources with translations in `type2_translated/`. R35's translations are in `translate_chunks/`, not `type2_translated/`, so Step 4 likely does NOT process R35.

## rebuild_packdata.py Priority (Question 4)

`rebuild_packdata.py` checks `build/packdata_resources/{fn}` FIRST. If found, it uses the patched version. Otherwise, it falls back to `extracted/packdata_raw/{fn}`. There is no conflict between these two directories -- packdata_resources always wins.

This means **any file in `build/packdata_resources/` will be used, even if stale**. If a build step is removed but its output file remains from a previous run, the stale file persists. Step 6 of build_v9.py has a binary_resources removal list (lines 247-256) that cleans up known-corrupt type-02 files, but this doesn't cover all edge cases.

## Summary of Recommended Fixes

### Priority 1: Prevent wasted/corrupt v2 pipeline processing

Add a skip list to `build_full_english_v2.py`'s `inject_resource()` to skip resources handled by later steps:

```python
# Resources handled by specialized steps in build_v9.py -- skip in v2 pipeline
V9_HANDLED = {35, 39, 46, 47, 2654}
if res_idx in V9_HANDLED:
    return (None, 'handled by build_v9.py specialized step')
```

### Priority 2: Clean up dead R1188 code in v2 pipeline

Remove or comment out Step 3b in `build_full_english_v2.py` (lines 197-205) since:
- `patch_r1188_stats.py` does not exist
- `patch_r1188_direct.py` output is overwritten by Step 3.6's `patch_r1188_comprehensive.py`

### Priority 3: Add R39/R46/R47 to the unsafe removal list

In `build_v9.py` lines 20-24, add R39/R46/R47 to ensure the v2 pipeline's corrupt output is cleaned up even if the skip list fix isn't applied:

```python
for unsafe_r, tc in [(1053, '03'), (1908, '06'), (39, '15'), (46, '03'), (47, '03')]:
```

Note: This alone is insufficient for R39 because Step 3 deletes R39 before writing (line 135), so there's no file to remove. But it provides defense-in-depth.

### Priority 4: Add stale file detection

Before `rebuild_packdata.py` runs, add a check that all files in `build/packdata_resources/` were written during the current build session (e.g., by checking timestamps or maintaining a manifest of expected files).
