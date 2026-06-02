# Build Pipeline Timing/Ordering Guide

This document maps every step of `build/build_v9.py`, what each step reads, what it writes, and where overwrite conflicts can occur.

---

## Pipeline Overview (Execution Order)

```
Step 1    build_full_english_v2.py     Type-01 MSG resources + R1272 font + R1188 (direct)
  |                                    Also builds build/PACKDATA.DIG (UNUSED by v9)
  v
Step 2    (inline in build_v9.py)      R35, R2654 fixed-size injection
  |
  v
Step 3    inject_r39_v2.py             R39 equipment text (glyph stream)
  |
  v
Step 3.1  patch_r39_inline.py          R39 extra data (spell names, NPC names, etc.)
  |
  v
Step 3.5  inject_r46_r47.py            R46/R47 bulletin board + combat text
  |
  v
Step 3.6  patch_r1188_comprehensive.py *** R1188 FULL OVERWRITE (reads ORIGINAL) ***
  |
  v
Step 4    patch_section1_offsets.py     Type-02 variable-size injection + Section 1 patching
  |
  v
Step 5    (inline in build_v9.py)      R1193 copy from packdata_resources -> patched_type2
  |
  v
Step 6    (inline in build_v9.py)      Merge patched_type2 -> packdata_resources + cleanup
  |
  v
Step 7    rebuild_packdata.py          Rebuild PACKDATA_v3.DIG from packdata_resources
  |
  v
Step 8    (inline in build_v9.py)      Build ISO (copy original, overwrite PACKDATA + dir size)
  |
  v
Step 8.4  patch_exe.py                 Patch EXE binary (save names, NPC names, banner, etc.)
  |
  v
Step 8.5  (inline in build_v9.py)      Write patched EXE into ISO
```

---

## Step-by-Step Detail

### Step 1: Type-01 Injection (v2 pipeline)

- **Script**: `build/build_full_english_v2.py`
- **INPUT files**:
  - `data/translate_chunks/chunk_00_translated.json` through `chunk_09_translated.json`
  - `data/translate_chunks/chunk_r38_fix.json`, `chunk_r43_fix.json`, `chunk_r37_extra.json`, `chunk_r36_translated.json`, `chunk_r37_r48_r49_translated.json`, `chunk_r40_r42_translated.json`, `chunk_r43_r45_translated.json`, `chunk_r34_fix.json`
  - `extracted/packdata_raw/{NNNN}_type{NN}.raw` (original resource files)
  - `build/english_font_atlas.bin` (pre-built by `generate_font_atlas.py`)
  - `extracted/packdata_raw/1272_type*.raw` (original R1272)
  - `extracted/packdata_resources/1188_type01.bin` or `extracted/packdata_raw/1188_type01.raw` (original R1188)
  - `extracted/packdata_resources/manifest.json`
  - `extracted/PACKDATA.DIG` (original PACKDATA for its own rebuild)
- **OUTPUT files**:
  - `build/packdata_resources/{NNNN}_type{NN}.raw` for ALL type-01 resources with translations (R34, R35, R36, R37, R38, R39, R40, R42, R43, R45, R48, R49, R2124, R2654, plus R1053, R1908 if present)
  - `build/packdata_resources/1272_type01.raw` (font atlas)
  - `build/packdata_resources/1188_type01.raw` (R1188 via `patch_r1188_direct.py`)
  - `build/pcsx2_texture_replacements/*.png`
  - `build/PACKDATA.DIG` (v2 pipeline's own rebuild -- UNUSED by build_v9.py)
  - `build/BUSIN0_EN.iso` (v2 pipeline's own ISO -- UNUSED by build_v9.py)
- **OVERWRITES**: Creates `build/packdata_resources/` directory and populates it fresh
- **DEPENDENCIES**: `generate_font_atlas.py` must have been run first to produce `build/english_font_atlas.bin`

**Sub-step 1a: R1188 direct patch** (`tools/patch_r1188_direct.py`)
- Called from within Step 1 (build_full_english_v2.py Step 3b)
- INPUT: `extracted/packdata_resources/1188_type01.bin` or `extracted/packdata_raw/1188_type01.raw` (ORIGINAL)
- OUTPUT: `build/packdata_resources/1188_type01.raw`

**Sub-step 1b: R1188 stats patch** (`tools/patch_r1188_stats.py`)
- Called from within Step 1 (build_full_english_v2.py Step 3b)
- NOTE: This script no longer exists on disk. Its functionality was likely folded into `patch_r1188_comprehensive.py`.

**Post-Step 1 cleanup** (in build_v9.py):
- REMOVES `build/packdata_resources/1053_type03.raw` and `build/packdata_resources/1908_type06.raw` if present (unsafe type-03/06 resources that v2 pipeline incorrectly patches)

### Step 2: Fixed-Size Injection (R35, R2654)

- **Script**: Inline in `build/build_v9.py` (lines 26-131)
- **INPUT files**:
  - `data/english_glyph_table.json`
  - `data/translate_chunks/chunk_00_translated.json` through `chunk_09_translated.json`
  - `data/translate_chunks/chunk_r38_fix.json`, `chunk_r43_fix.json`, `chunk_r37_extra.json`, `chunk_r40_r42_translated.json`, `chunk_r36_translated.json`, `chunk_r37_r48_r49_translated.json`, `chunk_r43_r45_translated.json`
  - `extracted/packdata_raw/0035_type02.raw` (ORIGINAL R35)
  - `extracted/packdata_raw/2654_type44.raw` (ORIGINAL R2654)
- **OUTPUT files**:
  - `build/packdata_resources/0035_type02.raw`
  - `build/packdata_resources/2654_type44.raw`
- **OVERWRITES**: Overwrites Step 1's output for R35 and R2654 (these are flat-format resources that Step 1's v2 pipeline also processes, but Step 2's simpler injection is used instead)
- **DEPENDENCIES**: Step 1 must complete first (creates `build/packdata_resources/` directory)

### Step 3: R39 Equipment Injection

- **Script**: `build/inject_r39_v2.py`
- **INPUT files**:
  - `extracted/packdata_raw/0039_type15.raw` (ORIGINAL R39)
  - `data/english_glyph_table.json`
  - `data/translate_chunks/chunk_00_translated.json` through `chunk_09_translated.json`
- **OUTPUT files**:
  - `build/packdata_resources/0039_type15.raw`
- **OVERWRITES**: Overwrites Step 1's output for R39 (Step 1 processes R39 as a type-01 MSG resource, but R39 is actually type-15 with a unique binary layout requiring this specialized injector)
- **DEPENDENCIES**: Step 1 (directory exists). Note: build_v9.py explicitly deletes `build/packdata_resources/0039_type15.raw` before running this step.

### Step 3.1: R39 Inline Japanese Glyph Patching

- **Script**: `tools/patch_r39_inline.py`
- **INPUT files**:
  - `build/packdata_resources/0039_type15.raw` (Step 3's output -- READS THE PATCHED FILE)
  - `data/english_glyph_table.json`
- **OUTPUT files**:
  - `build/packdata_resources/0039_type15.raw` (in-place overwrite)
- **OVERWRITES**: Modifies Step 3's output in-place (patches the extra data section at bytes 2702+ while preserving Step 3's glyph stream patches at bytes 632-2701)
- **DEPENDENCIES**: Step 3 MUST complete first (reads Step 3's output)

### Step 3.5: R46/R47 Bulletin Board Injection

- **Script**: `build/inject_r46_r47.py`
- **INPUT files**:
  - `extracted/packdata_raw/0046_type03.raw` (ORIGINAL R46)
  - `extracted/packdata_raw/0047_type03.raw` (ORIGINAL R47)
  - `data/english_glyph_table.json`
- **OUTPUT files**:
  - `build/packdata_resources/0046_type03.raw`
  - `build/packdata_resources/0047_type03.raw`
- **OVERWRITES**: R46/R47 are type-03 resources. Step 1 post-cleanup removed R1053 (type-03) but R46/R47 were not processed by Step 1, so no conflict.
- **DEPENDENCIES**: Step 1 (directory exists)

### Step 3.6: R1188 Comprehensive Patch

- **Script**: `tools/patch_r1188_comprehensive.py`
- **INPUT files**:
  - `extracted/packdata_resources/1188_type01.bin` or `extracted/packdata_raw/1188_type01.raw` (*** READS FROM ORIGINAL, NOT FROM build/ ***)
  - Uses Pillow + numpy for rendering
- **OUTPUT files**:
  - `build/packdata_resources/1188_type01.raw`
  - `build/pcsx2_texture_replacements/*.png`
  - `build/textures_to_edit/R1188_*.png` (debug images)
- **OVERWRITES**: *** CRITICAL *** Completely overwrites Step 1's R1188 output (`build/packdata_resources/1188_type01.raw`). Because it reads from the ORIGINAL extracted file, all edits made by Step 1's `patch_r1188_direct.py` are LOST.
- **DEPENDENCIES**: Step 1 (directory exists). Does NOT depend on Step 1's R1188 output.

> **KEY CONFLICT**: Step 1 patches R1188 via `patch_r1188_direct.py` (bottom-row labels + PCSX2 PNGs). Step 3.6 then reads from the ORIGINAL R1188 and writes a completely new version, discarding Step 1's work. This is INTENTIONAL -- Step 3.6 is the comprehensive replacement that includes everything Step 1's direct patch did, plus kana cell overwriting, stat label VRAM simulation, and more. The v2 pipeline's R1188 patches (Sub-steps 1a and 1b) are now redundant but harmless since Step 3.6 replaces them entirely.

### Step 4: Type-02 Variable-Size Injection + Section 1 Patching

- **Script**: `tools/patch_section1_offsets.py` (called as library: `inject_and_patch()`)
- **INPUT files**:
  - `data/type2_translated/batch_*.json` (all type-2 translation batches, auto-discovered by glob)
  - `data/english_glyph_table.json` (via glyph encoding in build_v9.py)
  - `extracted/packdata_raw/{NNNN}_type02.raw` (ORIGINAL type-02 resources)
  - `extracted/packdata_resources/manifest.json`
- **OUTPUT files**:
  - `build/patched_type2/{NNNN}_type02.raw` (one per translated type-02 resource)
- **OVERWRITES**: Writes to `build/patched_type2/`, not `build/packdata_resources/`. Does NOT directly conflict with any previous step. R1193 is explicitly excluded (handled in Step 5).
- **DEPENDENCIES**: Steps 1-3.6 (for directory creation), but operates independently on type-02 resources

### Step 5: R1193 Manual Fixed-Size

- **Script**: Inline in `build/build_v9.py` (lines 237-240)
- **INPUT files**:
  - `build/packdata_resources/1193_type02.raw` (from Step 1's v2 pipeline output, if it exists)
- **OUTPUT files**:
  - `build/patched_type2/1193_type02.raw`
- **OVERWRITES**: None (copies from packdata_resources to patched_type2)
- **DEPENDENCIES**: Step 1 (R1193 must have been processed by the v2 pipeline)

### Step 6: Merge and Clean

- **Script**: Inline in `build/build_v9.py` (lines 243-259)
- **INPUT files**:
  - All files in `build/patched_type2/`
- **OUTPUT files**:
  - Copies all `build/patched_type2/*.raw` into `build/packdata_resources/`
  - Then REMOVES a hardcoded list of ~90 binary/non-text type-02 resources from `build/packdata_resources/` (resources 677, 690, 712, etc.)
- **OVERWRITES**: *** CRITICAL *** Any type-02 resource that exists in BOTH `build/packdata_resources/` (from Step 1) AND `build/patched_type2/` (from Step 4) will be overwritten by the Step 4 version. This is INTENTIONAL -- Step 4's variable-size injection with Section 1 patching supersedes Step 1's fixed-size injection for type-02 resources.
- **DEPENDENCIES**: Steps 1-5 must all complete first

### Step 7: Rebuild PACKDATA

- **Script**: `build/rebuild_packdata.py`
- **INPUT files**:
  - `extracted/packdata_resources/manifest.json` (resource index + type codes)
  - `extracted/PACKDATA.DIG` (original TOC for header/skipped entries)
  - `build/packdata_resources/{NNNN}_type{NN}.raw` (*** PATCHED resources take priority ***)
  - `extracted/packdata_raw/{NNNN}_type{NN}.raw` (fallback for unpatched resources)
- **OUTPUT files**:
  - `build/PACKDATA_v3.DIG`
- **PRIORITY RULE**: For each resource index, the script checks:
  1. `build/packdata_resources/{idx}_type{tc}.raw` -- if exists, USE THIS (patched)
  2. `extracted/packdata_raw/{idx}_type{tc}.raw` -- fallback to original
  3. `extracted/packdata_raw/{idx}_type*.raw` -- glob fallback
  4. Zero-filled sector (last resort)
- **OVERWRITES**: None (writes to a new file)
- **DEPENDENCIES**: Steps 1-6 must all complete first. The final state of `build/packdata_resources/` determines what goes into the PACKDATA.

### Step 8: Build ISO

- **Script**: Inline in `build/build_v9.py` (lines 266-290)
- **INPUT files**:
  - `build/PACKDATA_v3.DIG` (from Step 7)
  - `Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso` (original disc image)
- **OUTPUT files**:
  - `build/BUSIN0_EN_v9.iso`
- **OVERWRITES**: Creates a fresh copy of the original ISO, then overwrites the PACKDATA extent and directory size
- **DEPENDENCIES**: Step 7 must complete first

### Step 8.4: Patch EXE

- **Script**: `build/patch_exe.py`
- **INPUT files**:
  - `extracted/SLPM_653.78` (ORIGINAL EXE, 4,185,776 bytes)
- **OUTPUT files**:
  - `build/SLPM_653.78_patched`
- **Patches applied**:
  1. Save slot names (SJIS -> ASCII)
  2. Player-visible SJIS strings (Continue loading, equip message)
  3. NPC names (glyph IDs: Emilia, Lute)
  4. Banner glyph IDs (kanji tiles -> ASCII for "New Reg.")
  5. Banner byte-50 glyph IDs
  6. NOP chargen RenderAllTiles call (disable kanji overlay)
- **OVERWRITES**: None (reads from extracted/, writes to build/)
- **DEPENDENCIES**: None (reads only from extracted originals). Could theoretically run at any time.

### Step 8.5: Write Patched EXE into ISO

- **Script**: Inline in `build/build_v9.py` (lines 299-327)
- **INPUT files**:
  - `build/SLPM_653.78_patched` (from Step 8.4)
  - `build/BUSIN0_EN_v9.iso` (from Step 8)
- **OUTPUT files**:
  - `build/BUSIN0_EN_v9.iso` (modified in-place: EXE extent overwritten + directory size updated)
- **OVERWRITES**: Modifies the ISO created in Step 8
- **DEPENDENCIES**: Steps 8 and 8.4 must complete first

---

## Known Overwrite Conflicts

### 1. R1188: Step 1 vs Step 3.6 (RESOLVED BY DESIGN)

**Step 1** (`patch_r1188_direct.py`): Reads ORIGINAL R1188, writes `build/packdata_resources/1188_type01.raw`
**Step 3.6** (`patch_r1188_comprehensive.py`): Reads ORIGINAL R1188, writes `build/packdata_resources/1188_type01.raw`

Step 3.6 completely replaces Step 1's R1188 output. This is intentional -- the comprehensive patcher is a superset. However, any future R1188 patch MUST be applied:
- AFTER Step 3.6
- BEFORE Step 7 (rebuild PACKDATA)

### 2. R35/R2654: Step 1 vs Step 2 (RESOLVED BY DESIGN)

Step 1's v2 pipeline processes these as type-01 MSG resources. Step 2 re-does them with a simpler flat-format injector that handles their structure correctly. Step 2's output intentionally replaces Step 1's.

### 3. R39: Step 1 vs Step 3 + 3.1 (RESOLVED BY DESIGN)

Step 1 processes R39 as a generic type-01 resource. Step 3 deletes that output and uses a specialized type-15 injector. Step 3.1 then adds inline patches on top.

### 4. Type-02 resources: Step 1 vs Step 6 merge (RESOLVED BY DESIGN)

Step 1 may produce type-02 resources (e.g., R1193). Step 4 produces better versions with variable-size injection and Section 1 offset patching. Step 6's merge copies Step 4's versions over Step 1's. R1193 is special-cased to preserve Step 1's version.

---

## Data Flow Diagram

```
ORIGINAL FILES (extracted/)              INTERMEDIATE              FINAL
================================    ====================    ==================

extracted/packdata_raw/*.raw ----+
                                |
data/translate_chunks/*.json ---+--> Step 1 --> build/packdata_resources/*.raw
                                |              (type-01: R34-R49, R1272, R1188,
build/english_font_atlas.bin ---+               R2124, R2654, etc.)
                                                    |
                                                    | Step 2 overwrites R35, R2654
                                                    |
extracted/packdata_raw/0039 ---------> Step 3 ----> | overwrites R39
                                          |
                                       Step 3.1 --> | modifies R39 in-place
                                                    |
extracted/packdata_raw/0046,0047 ----> Step 3.5 --> | adds R46, R47
                                                    |
extracted/packdata_raw/1188 ---------> Step 3.6 --> | OVERWRITES R1188
                                                    |
extracted/packdata_raw/*_type02 -----> Step 4 ----> build/patched_type2/*.raw
                                                         |
                                                      Step 5: R1193 copy
                                                         |
                                                      Step 6: merge into
                                                         |    packdata_resources
                                                         v
                                              build/packdata_resources/*.raw
                                                    (FINAL state)
                                                         |
                                                      Step 7: rebuild
                                                         |
                                                         v
                                              build/PACKDATA_v3.DIG
                                                         |
original ISO --------------------------------> Step 8 -> build/BUSIN0_EN_v9.iso
                                                              |
extracted/SLPM_653.78 -----> Step 8.4 --> build/SLPM_patched  |
                                                    |         |
                                                 Step 8.5 ----+
                                                              |
                                                              v
                                                   build/BUSIN0_EN_v9.iso
                                                       (COMPLETE)
```

---

## Rules for Adding New Patches

1. **Type-01 MSG resources** (R34-R49, R2124, etc.): Add translations to `data/translate_chunks/` JSON files. Step 1 handles them automatically.

2. **Type-02 dialogue resources**: Add translations to `data/type2_translated/batch_*.json`. Step 4 handles them automatically with variable-size injection and Section 1 offset patching.

3. **R1188 modifications**: MUST be applied AFTER Step 3.6 and BEFORE Step 7. Either modify `patch_r1188_comprehensive.py` directly, or add a new step between 3.6 and 4.

4. **R39 modifications**: If modifying the glyph stream (messages 0-96), edit `inject_r39_v2.py`. If modifying extra data (spells, NPCs, equipment), edit `patch_r39_inline.py`. Step 3.1 MUST run after Step 3.

5. **EXE patches**: Add to `build/patch_exe.py`. This runs independently of resource patching and can be modified without affecting PACKDATA.

6. **New resource types**: Add a new step between 3.6 and 4 (or between 4 and 6). Write output to `build/packdata_resources/`. The resource will be picked up automatically by Step 7's rebuild.

7. **NEVER modify `build/packdata_resources/` after Step 7** -- the PACKDATA has already been built. Any late changes require re-running Steps 7 and 8.
