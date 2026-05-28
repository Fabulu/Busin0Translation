# Build Pipeline Recon: build_v9.py (Updated)

Generated: 2026-05-28 (refreshed)

## Files Analyzed

| File | Lines | Role |
|------|-------|------|
| `build/build_v9.py` | 241 | Main build orchestrator (v9) |
| `build/build_full_english_v2.py` | 574 | Type-1 sub-pipeline (called by v9 Step 1) |
| `build/rebuild_packdata.py` | 67 | PACKDATA.DIG reassembly |
| `tools/patch_section1_offsets.py` | 746 | Section 1 opcode patcher for variable-size type-2 injection |
| `/tmp/inject_r39.py` | 121 | R39 (type-15) custom injection |

## Build Sequence (8 Steps)

### Step 1: Type-1 Injection (v2 sub-pipeline)
- Calls `build/build_full_english_v2.py` via `os.system()`, stdout suppressed
- v2 pipeline does its own full cycle:
  1. Loads 10 chunk files (`chunk_00..09_translated.json`) + 2 fix files (`chunk_r38_fix.json`, `chunk_r43_fix.json`)
  2. Encodes translations via `encode_english_text.encode_text()`
  3. Injects font atlas into R1272 (type-22 resource)
  4. Injects translations into MSG resources -- handles both Format-A (with offset tables) and simple FFFF-group formats
  5. Rebuilds its own PACKDATA.DIG at `build/PACKDATA.DIG`
  6. Builds its own ISO at `build/BUSIN0_EN.iso`
- **Type codes handled by v2:** type 1, 2, 3, 6, 15, 20, 44 (whatever the translations reference)
- v2 writes patched resources to `build/packdata_resources/`
- **Important:** v2 produces `build/PACKDATA.DIG` (not `_v3`), but v9 Step 7 uses `rebuild_packdata.py` which produces `build/PACKDATA_v3.DIG`, overriding v2's output

### Step 2: Fix Type-1 FFFF Mismatches (R34, R35, R2124, R2654)
- Manually re-patches 4 specific resources that v2 broke (FFFF count mismatches)
- Uses FIXED-SIZE injection (pads/truncates to original group size)
- Type codes: R34=type20, R35=type02, R2654=type44, R2124=type01
- Reads translations from the same chunk files
- Writes directly to `build/packdata_resources/`

### Step 3: R39 Type-15 Injection
- Runs `/tmp/inject_r39.py` -- a standalone script
- R39 is type-15 (special format with "extra data" region beyond payload)
- Translations come from the chunk files (resource==39)
- Uses FIXED-SIZE approach within the extra data's FFFF groups
- Does NOT update the offset table (relies on sequential FFFF-group reading)

### Step 4: Variable-Size Type-2 + Section 1 Patching (MAIN WORK)
- Loads ALL `data/type2_translated/batch_*.json` files (18 files, ~124 unique resources)
- Filters out entries with prefixes: `[DATA]`, `[LAYOUT]`, `[BINARY]`, `[MAP]`, `[SYSTEM]`, `[GLYPH`, `[DEBUG]`
- Filters out entries with non-ASCII characters
- For each type-02 resource with translations:
  - Encodes English text to glyph lists (simple per-char lookup, no word-wrapping)
  - Calls `inject_and_patch()` from `patch_section1_offsets.py`
  - This does VARIABLE-SIZE injection: messages can grow/shrink freely
  - Then patches Section 1 opcodes (DISPLAY_TEXT 0x0004, SET_NAME_REF 0x000C, CLEAR_NAME_REF 0x000D) to match new Section 2 layout
- Outputs to `build/patched_type2/`
- Currently: ~123 resources in patched_type2

### Step 5: R1193 Manual Preserve
- Copies R1193 from `build/packdata_resources/` to `build/patched_type2/` if it exists
- R1193 was manually injected as fixed-size earlier (by v2 pipeline)

### Step 6: Merge and Clean
- Copies all files from `build/patched_type2/` into `build/packdata_resources/` (type-2 results override v2 results)
- **BINARY EXCLUSION LIST:** Removes 94 type-02 resources that are NOT text/dialogue:
  ```
  677,690,712,715,726,741,750,757,769,780,785,787,793,795,797,799,
  801,803,816,837,839,852,860,862,864,866,868,870,871,873,875,877,
  879,881,883,885,889,917,920,1057,1061,1072,1073,1077,1084,1091,
  1093,1099,1105,1109,1110,1112,1123,1133,1141,1145,1146,1147,1174,
  1192,1912,1930,1931,1933,1934,1935,1936,1939,1940,1941,1948,1952,
  1953,1959,1972,2141,2144,2161,2162,2163,2166,2174,2176,2200,2201,
  2204,2206,2207,2208,2588,2589,2651,2652,2653
  ```
- These are type-02 resources that contain binary/non-text data -- injecting text into them would corrupt them

### Step 7: Rebuild PACKDATA.DIG
- Runs `build/rebuild_packdata.py`
- Reads `extracted/packdata_resources/manifest.json` (2883 entries)
- For each entry: prefers `build/packdata_resources/<idx>_type<tc>.raw` over `extracted/packdata_raw/<idx>_type<tc>.raw`
- Writes `build/PACKDATA_v3.DIG` with updated TOC (sector offsets, sector counts, type codes)
- Pads to original size if smaller; warns if larger

### Step 8: Build ISO
- Copies original Japanese ISO to `build/BUSIN0_EN_v9.iso`
- Parses ISO9660 PVD (sector 16) to find root directory
- Finds PACKDATA.DIG entry in root directory
- Updates the file size in the directory entry (both LE and BE copies)
- Overwrites PACKDATA.DIG data at its original LBA position
- **Does NOT update any other ISO files** (no ELF/SLPM patching in v9)

## Resource Type Distribution (2883 total, 2 skipped)

| Type | Count | Translation Coverage |
|------|-------|---------------------|
| 1 | 1642 | Handled by v2 pipeline (type-1 chunks) |
| 2 | 617 | 124 resources translated via type-2 batches; 94 excluded as binary |
| 3 | 226 | Some handled by v2 (chunk_07, chunk_09) |
| 4 | 201 | NOT processed |
| 5 | 33 | NOT processed |
| 6 | 46 | Some handled by v2 (chunk_09) |
| 7-104+ | ~77 | NOT processed (except R39=type15, R1272=type22 font, R2654=type44) |

## Translation Data Files

### Type-1 Chunks (`data/translate_chunks/`)
- 10 main chunks: `chunk_00..09_translated.json`
- 2 fix overrides: `chunk_r38_fix.json`, `chunk_r43_fix.json`
- 1 extra: `chunk_r37_extra.json` (NOT loaded by build)
- Type codes in chunks: 1, 2, 3, 6, 15, 20, 44

### Type-2 Batches (`data/type2_translated/`)
- 16 batch files covering ~124 unique type-02 resources
- Major batches: batch_01..09 (large, 1-4 resources each)
- Gap/extra batches: batch_10, batch_11, batch_gap*, batch_intro, batch_r1198

## Extension Points for New Content

### 1. Add New Type-2 Translation Batches (EASIEST)
- Add new `batch_*.json` to `data/type2_translated/`
- Auto-discovered by `glob.glob('data/type2_translated/batch_*.json')` in Step 4
- No code changes needed -- just add the file
- Must use format: `{"resource": N, "msg_index": M, "english": "text"}`

### 2. Add New Type-1 Translation Chunks
- Add new JSON files to `data/translate_chunks/`
- REQUIRES code changes: `build_v9.py` Step 2 and `build_full_english_v2.py` hardcode `range(10)` + 2 fix files
- To fix: change the loop to use `glob.glob()` instead of hardcoded range

### 3. Add New Resource Type Handlers
- Currently only type-02 gets variable-size injection + Section 1 patching
- Other types (1, 3, 6, 15, 20, 44) use v2's simpler fixed-size injection
- To add a new type handler: insert a new Step between Steps 4 and 6, write patched files to `build/packdata_resources/`

### 4. Add EXE/SLPM Patching
- v9 does NOT patch the game executable (SLPM_653.78)
- There are patched EXE variants in `build/` (SLPM_653.78_patched, _v2, _v3) but NOT integrated into the ISO build
- To add: insert a step after Step 8 that finds SLPM_653.78 in the ISO directory and overwrites it

### 5. Add Non-PACKDATA Resources
- The ISO contains other files besides PACKDATA.DIG
- To patch them: extend Step 8's ISO directory traversal to find and overwrite additional file entries

## Key Design Decisions and Constraints

1. **Two-tier injection:** v2 does type-1 (Format-A with offset tables) at fixed-size; v9 adds variable-size type-2 with Section 1 opcode patching on top
2. **Binary exclusion is hardcoded:** The 94-resource exclusion list is a Python literal in build_v9.py
3. **Translation filtering:** Type-2 entries with `[DATA]`, `[LAYOUT]`, `[BINARY]`, `[MAP]`, `[SYSTEM]`, `[GLYPH`, `[DEBUG]` prefixes are skipped
4. **Non-ASCII filtering:** Any translation containing characters with `ord(c) > 127` is silently skipped
5. **Sector alignment:** All resources are padded to 2048-byte sector boundaries
6. **PACKDATA size constraint:** If rebuilt PACKDATA is larger than original, the build warns but proceeds -- the ISO may be corrupt
7. **v2 pipeline runs fully but its ISO output is discarded** -- only its `build/packdata_resources/` files matter
8. **`chunk_r37_extra.json` exists but is never loaded** by any build step

## How rebuild_packdata.py Works

The rebuilder is straightforward:
1. Reads the manifest (2883 entries) and original TOC (125 sectors = 256,000 bytes of header)
2. Copies the original header (first 125 sectors) verbatim
3. For each non-skipped entry, looks for the resource file in this priority:
   - `build/packdata_resources/<idx>_type<tc>.raw` (patched version)
   - `extracted/packdata_raw/<idx>_type<tc>.raw` (original)
   - Any `extracted/packdata_raw/<idx>_type*.raw` (fallback)
4. Writes each resource at the current sector offset, sector-aligned
5. Rewrites the TOC at offset 0 with new (sector_offset, sector_count, type_code) triples
6. Pads to original file size if smaller

## How ISO Patching Works

1. Parse ISO9660 Primary Volume Descriptor at sector 16
2. Read root directory extent LBA and size from PVD offset 158/166
3. Scan root directory records for "PACKDATA" filename match
4. Extract PACKDATA.DIG's LBA from the directory entry (offset +2 in record)
5. Update the file size field in the directory record (both LE at +10 and BE at +14)
6. Seek to `pack_lba * 2048` and write the new PACKDATA.DIG data

## Critical Gaps / Risks

1. **~399 untranslated type-2 resources:** 617 total - 124 translated - 94 binary = ~399 with no translations
2. **No EXE patching in ISO:** Font table, string tables in the executable are not modified in the final ISO
3. **R39 injection script at `/tmp/`:** Fragile location, lost on reboot
4. **v2 pipeline errors invisible:** stdout/stderr suppressed in Step 1
5. **`chunk_r37_extra.json` orphaned:** Never loaded by any build step
6. **Type-1 chunk loading is hardcoded:** `range(10)` means chunks 10+ would be ignored
7. **No type-4 or type-5 handler:** 234 resources of these types are completely unprocessed
