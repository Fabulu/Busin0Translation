# Implementation Plan: Busin 0 Remaining Japanese Text
**Generated**: 2026-05-28
**Baseline**: Build v11 (commit a62c7bb), build_v9.py pipeline
**Source**: 10 recon agent reports consolidated

---

## 1. Quick Wins (Do NOW -- High Impact, Low Risk)

### QW-1. Fix Consolidation Bug (BUG-C1): 368 Lost Translations
**Impact**: HIGH -- 368 translations already exist but render as Japanese in current ISO
**Risk**: LOW
**Complexity**: ~30 lines of investigation + fix

**Problem**: `build/v3_type2_translations.json` drops 368 entries during consolidation. R1354 lost 300, R1353 lost 34, R1212 lost 33, R1213 lost 1. The empty indices follow a systematic pattern (67, 78, 88, 92, 96, 97...).

**Action**:
1. Find the consolidation script that produces `build/v3_type2_translations.json` (likely in `tools/` or `build/`)
2. The bug is probably an off-by-one or key collision during merge -- the pattern of dropped indices suggests a modular skip
3. Fix the script so all 13,112 batch entries survive consolidation
4. Verify: count entries in output must equal sum of entries across all `data/type2_translated/batch_*.json` files (excluding [DATA]/[LAYOUT]/etc. prefixed entries)

**Note**: build_v9.py Step 4 reads batch files directly via glob, NOT via v3_type2_translations.json. So this bug only affects the v2 sub-pipeline (Step 1) and any tools that read the consolidated file. Verify which pipeline step actually uses v3_type2_translations.json.

---

### QW-2. Wire Up chunk_r37_extra.json (BUG-B1): 111 Lost Translations
**Impact**: HIGH -- 111 translations including chargen confirm dialog sitting unused
**Risk**: LOW
**Complexity**: 1 line of code

**Problem**: `data/translate_chunks/chunk_r37_extra.json` (111 entries for R37) is never loaded by any build step.

**Action**: In `build/build_v9.py`, Step 2 (lines 24-43), add `chunk_r37_extra.json` to the fix file list:
```python
for fix in ['chunk_r38_fix.json', 'chunk_r43_fix.json', 'chunk_r37_extra.json']:
```
Also add it to `build/build_full_english_v2.py` in its chunk loading loop (search for `chunk_r38_fix`).

**Files to modify**:
- `build/build_v9.py` line 34
- `build/build_full_english_v2.py` (find the corresponding fix file loading section)

---

### QW-3. Stop Patching Unsafe Resources (BUG-B2)
**Impact**: MEDIUM -- prevents potential corruption
**Risk**: LOW
**Complexity**: ~5 lines

**Problem**: R1053 (type-03) and R1908 (type-06) are still being patched by the v2 sub-pipeline despite being documented as unsafe in KNOWN_ISSUES.md (M2). Type-03 = 3D scene data, type-06 = mixed data. Injecting MSG text into these corrupts their binary structure.

**Action**: In `build/build_full_english_v2.py`, add R1053 and R1908 to whatever exclusion list or type-code filter prevents injection. Alternatively, after Step 1 in build_v9.py, delete the patched files:
```python
for unsafe_r in [1053, 1908]:
    for tc in ['03', '06']:
        f = f'build/packdata_resources/{unsafe_r:04d}_type{tc}.raw'
        if os.path.exists(f): os.remove(f)
```

**Files to modify**: `build/build_v9.py` (after line 16) or `build/build_full_english_v2.py`

---

### QW-4. Move R39 Inject Script Into Repo (BUG-B3)
**Impact**: LOW (prevents data loss)
**Risk**: NONE
**Complexity**: 1 file copy + 1 line path update

**Problem**: `/tmp/inject_r39.py` lives outside the repo and will be lost on cleanup/reboot.

**Action**:
1. Copy `/tmp/inject_r39.py` to `build/inject_r39.py`
2. Update `build/build_v9.py` line 107: change `/tmp/inject_r39.py` to `build/inject_r39.py`

---

### QW-5. Add R1350 Translation (1 Trivial Message)
**Impact**: LOW (completes R1347-R1355 gap coverage)
**Risk**: NONE
**Complexity**: Add 1 JSON entry

**Problem**: R1350 has one 12-glyph sound effect message ("ibakaaaa--- go") not in any batch file.

**Action**: Add to `data/type2_translated/batch_gap1347.json`:
```json
{"resource": 1350, "msg_index": 0, "english": "Ibakaaaa--- go!"}
```

---

### QW-6. Save Slot Display Names (EXE Table 2G)
**Impact**: MEDIUM -- visible on PS2 memory card browser
**Risk**: LOW (simple SJIS byte replacement within fixed buffer)
**Complexity**: ~20 lines of binary patching

**Problem**: Save slot names show Japanese on the PS2 memory card screen.

**Action**: Patch `extracted/SLPM_653.78` at these offsets with ASCII equivalents:

| Offset | Current (SJIS) | Replace With |
|--------|---------------|-------------|
| 0x3FC720 | BUSIN0 | BUSIN 0 (already ASCII -- verify) |
| 0x3FC750 | BUSIN0 Data 1 | BUSIN 0 Data 1 (verify) |
| 0x3FC770 | BUSIN0 Data 2 | BUSIN 0 Data 2 (verify) |
| 0x3FC790 | BUSIN0 Data 3 | BUSIN 0 Data 3 (verify) |
| 0x3F9370 | BUSIN0 Suspend Data | BUSIN 0 Suspend (verify) |

**Blocker**: EXE patching is not yet wired into the ISO build (see MT-7). These patches can be prepared now but won't take effect until GAP-B1 is addressed.

**Files**: `extracted/SLPM_653.78`, write patched copy to `build/SLPM_653.78_patched`

---

### QW-7. Two Player-Visible SJIS Strings (EXE Table 2L)
**Impact**: LOW (2 strings visible during gameplay)
**Risk**: LOW
**Complexity**: ~10 lines

**Problem**: Two SJIS strings visible to players:

| Offset | Japanese | English |
|--------|----------|---------|
| 0x3F8240 | koNtinyuurooddo! | Continue Load! |
| 0x3F8260 | toritsukeru hito ga inai yo. | No one to equip. |

**Action**: Replace SJIS bytes at these offsets with ASCII. Pad shorter English with nulls. Must stay within original byte length.

**Blocker**: Same as QW-6 -- needs EXE wired into ISO build.

---

### QW-8. NPC Names in EXE (Table 2F)
**Impact**: LOW (2 names, may be redundant with MSG system)
**Risk**: LOW
**Complexity**: ~10 lines

**Action**: At offset 0x3C93B0, replace katakana glyph IDs with ASCII glyph IDs:
- emiiria -> E,m,i,l,i,a (glyph IDs: 25,53,49,52,49,41 using ASCII-0x20 formula)
- ryuuto -> L,u,t,e (glyph IDs: 32,65,64,45)
Preserve null terminators. Each glyph stored as LE u16.

**Blocker**: Same EXE patching gap.

---

## 2. Medium Tasks (Path Is Clear, Needs Some Work)

### MT-1. Translate R1193/R1194 Intro Narration
**Impact**: VERY HIGH -- first thing players see; currently all Japanese
**Risk**: MEDIUM (need ~50 glyph mappings first)
**Complexity**: ~50 glyph mappings + 2 resources of translation text
**Dependencies**: None for glyph mapping; existing pipeline handles injection

**Background**: R1193 and R1194 are standard type-2 MSG resources (NOT textures as previously believed). R1193 has 351 glyph indices (Battle of Banquo backstory). R1194 has 482 glyph indices (Queen Oriana's speech). Together they have ~50 unique unmapped glyph IDs.

**Action**:
1. Map the ~50 unmapped glyph indices using font bitmap analysis:
   - R1193 unmapped: 384, 447, 448, 488, 654, 813, 907, 1027, 1034, 1060, 1089, 1178, 1186, 1187, 1200, 1320, 1342, 1398, 1409, 1483, 65505
   - R1194 unmapped: 323, 357, 424, 437, 447, 448, 474, 485, 631, 654, 907, 1021, 1022, 1034, 1035, 1051, 1072, 1083, 1106, 1116, 1149, 1152, 1198, 1200, 1277, 1370, 1385, 1419, 1463, 1497, 1525, 1577, 1580, 1684, 1697, 1710, 1720, 1721, 1722, 1723
   - Add mappings to `data/msg_glyph_map.json`
   - Use `tools/analyze_font_entry.py` or render from R1272 font atlas at each glyph position
2. Translate using `data/guide_full_text.txt` lines 164-178 as reference (Battle of Banquo / Ortrud backstory)
3. Use canonical terminology from Busin 1 US release (Kingdom of Duhan, Battle of Banquo, Holy King Ortrud)
4. Create `data/type2_translated/batch_intro_narration.json` with entries for R1193 and R1194
   - Note: `batch_intro.json` already exists with 3 entries for R1193/R1194 -- extend or replace it
5. Pipeline: These are standard type-2 MSG resources; the existing build_v9.py Step 4 will auto-discover them via glob

**Reference files**:
- `extracted/packdata_raw/1193_type02.raw` (source)
- `extracted/packdata_raw/1194_type02.raw` (source)
- `data/guide_full_text.txt` (English reference)
- `data/msg_glyph_map.json` (glyph mappings to update)

---

### MT-2. Fix R39 Equipment Text (4 Bugs)
**Impact**: HIGH -- fixes tavern softlock (M8), enables equipment menu translation
**Risk**: MEDIUM (complex binary format but root cause fully documented)
**Complexity**: ~100-150 lines to rewrite R39 injector
**Dependencies**: None

**Root cause** (4 interrelated bugs in `build/build_full_english_v2.py`):

1. **BUG-R39a**: `stream_end` clips at `payload_end=2478`, but messages 91-96 extend to byte 2701. Fix: parse glyph stream to byte 2701 (scan for 97 FFFF terminators, not stopping at payload_end).

2. **BUG-R39b**: Group 90 straddles payload boundary (starts 2454, FFFE at 2478, FFFF at 2480). Pipeline truncates and appends spurious FFFF, adding 2 extra bytes. Fix: don't truncate at payload_end; read the full group.

3. **BUG-R39c**: Rebuilt offset table uses found count (91) instead of original (97). Fix: preserve original count of 97 in rebuilt OT header.

4. **BUG-R39d**: Wrong offset base. Pipeline produces offsets relative to byte 16 (payload start), but game reads them relative to byte 240 (OT start). Every offset is off by 224 bytes. Fix: compute offsets relative to byte 240.

**Recommended approach** -- write `build/inject_r39_v2.py`:
```
File layout:
  bytes 0-15:    sub-header (preserve verbatim)
  bytes 16-239:  sequential ID table (preserve verbatim)
  bytes 240-631: offset table (97 entries, offsets relative to byte 240)
  bytes 632-2701: glyph stream (97 FFFF-delimited groups)
  bytes 2702+:   sequential data sections (preserve verbatim)
```

**Safest strategy**: Fixed-length in-place replacement with padding (zero OT changes needed):
- For each of the 97 OT-indexed messages with a translation, replace glyph content within the original group's byte range
- Pad shorter English with 0x0000 glyphs
- Truncate if English is longer (with warning)
- Leave offset table and all surrounding data untouched
- This avoids all 4 bugs by not rebuilding the OT at all

**Current translation status**: 84 of 97 OT-indexed messages have translations in chunk files. 558 messages in sequential sections (equipment names/descriptions) are untranslated.

**Files**:
- `extracted/packdata_raw/0039_type15.raw` (source, 26,624 bytes)
- `/tmp/inject_r39.py` -> move to `build/inject_r39.py` (current broken version)
- `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/analyze_r39.py` (analysis script)
- Update `build/build_v9.py` Step 3 to call new injector

---

### MT-3. Translate R1163-R1173 Narration Text (54 Messages)
**Impact**: MEDIUM (narration/description/lore text)
**Risk**: MEDIUM (FE:xx glyph mapping needed)
**Complexity**: ~50 FE:xx glyph mappings + 54 message translations
**Dependencies**: FE:xx glyph range mapping

**Action**:
1. Map FE:xx range glyphs (FFE0-FFFC) -- these appear extensively in R1163-R1173 but are absent from the current 810-entry glyph map
2. Use R1174 (already translated, same format) as a mapping reference
3. Translate 54 messages across 9 resources
4. Create `data/type2_translated/batch_r1163.json`
5. Auto-discovered by build pipeline

**Source files**: `extracted/packdata_raw/1163_type02.raw` through `1173_type02.raw`

---

### MT-4. Translate High-Value Dungeon Event Resources (~3,950 Lines)
**Impact**: VERY HIGH -- dungeon events are the largest untranslated content block
**Risk**: LOW (standard type-2 MSG, existing pipeline handles them)
**Complexity**: ~3,950 dialogue lines across 34 resources
**Dependencies**: None (pipeline ready)

**Tier 1 resources by dialogue line count** (translate in this order):

| Resource | Lines | Content Area |
|----------|-------|-------------|
| R2659 | 439 | Late-game events |
| R1937 | 202 | Dungeon event |
| R1954 | 196 | Dungeon event |
| R1926 | 193 | Dungeon event |
| R1955 | 173 | Dungeon event |
| R1914 | 146 | Dungeon event |
| R1944 | 137 | Dungeon event |
| R1932 | 132 | Dungeon event |
| R1938 | 127 | Dungeon event |
| R1945 | 118 | Dungeon event |
| R1924 | 116 | Dungeon event |
| R2165 | 122 | Late-game |
| R2168 | 103 | Late-game |
| R2211 | 102 | Late-game |
| R2021 | 94 | Dungeon event |
| R1919 | 90 | Dungeon event |
| R1918 | 87 | Dungeon event |
| R1951 | 81 | Dungeon event |
| R1949 | 74 | Dungeon event |
| R1921 | 66 | Dungeon event |
| R735 | 64 | NPC/shop scene |
| R2002 | 64 | Dungeon event |
| R1917 | 62 | Dungeon event |
| R1920 | 61 | Dungeon event |
| R1943 | 59 | Dungeon event |
| R1928 | 58 | Dungeon event |
| R753 | 55 | NPC/shop scene |
| R1916 | 51 | Dungeon event |
| + 6 more | 50-80 each | Various |

**Workflow per resource**:
1. Extract glyph stream from `extracted/packdata_raw/{RNUM}_type02.raw`
2. Decode using `data/msg_glyph_map.json`
3. Translate Japanese to English (use `data/guide_full_text.txt` for cross-reference)
4. Add entries to new batch file(s) in `data/type2_translated/`
5. Build pipeline auto-discovers

**Note on high-msg-count resources** (R2659=6276 msgs, R2168=2699 msgs, R2211=3032 msgs): These have very high msg_count but most are binary/structural data. Only the dialogue lines need translation. The batch files should include [DATA] tags for non-dialogue entries to skip them.

---

### MT-5. Translate R39 Sequential Section (558 Equipment Names/Descriptions)
**Impact**: HIGH -- equipment names and descriptions in menus
**Risk**: MEDIUM (sequential format is different from OT-indexed)
**Complexity**: 558 messages
**Dependencies**: MT-2 (R39 injector fix) must be done first

**Action**:
1. After MT-2 fixes the injector, extract the 558 messages from bytes 2720-26090 (14 sequential data sections)
2. These are equipment names and descriptions -- cross-reference with `data/guide_full_text.txt` and Busin 1 US terminology
3. The injector must handle the sequential sections (bytes 2720+) separately from the OT-indexed section
4. Use fixed-size in-place replacement within each sequential section

---

### MT-6. Translate R2129 (Type-15, 327KB) and R1186 (Type-20, 500KB)
**Impact**: MEDIUM (variant MSG resources with likely significant text)
**Risk**: MEDIUM (same format as R39/R34 but larger, need format verification)
**Complexity**: Unknown message count -- need extraction first
**Dependencies**: R39 fix (MT-2) establishes the type-15 handling pattern

**Action**:
1. Analyze `extracted/packdata_raw/2129_type15.raw` (327KB) -- extract sub-header, OT, glyph stream
2. Analyze `extracted/packdata_raw/1186_type20.raw` (500KB) -- same approach
3. Decode, translate, inject using the same approach as R39

---

### MT-7. Wire EXE Patching Into ISO Build (GAP-B1)
**Impact**: HIGH -- unblocks all EXE patches (save names, SJIS strings, future glyph table patches)
**Risk**: MEDIUM
**Complexity**: ~30 lines added to build_v9.py
**Dependencies**: None

**Problem**: Patched EXE variants exist in `build/` (SLPM_653.78_patched, _v2, _v3) but are NOT integrated into the ISO build. All EXE patches (QW-6, QW-7, QW-8, and future HT tasks) are useless until this is done.

**Action**: Add a new Step 8.5 to `build/build_v9.py` (between current Steps 8 and the final print):
```python
# ===== STEP 8.5: Patch EXE into ISO =====
print("\n=== Step 8.5: Patch EXE ===")
exe_path = 'build/SLPM_653.78_patched'
if os.path.exists(exe_path):
    exe_data = open(exe_path, 'rb').read()
    with open('build/BUSIN0_EN_v9.iso', 'r+b') as iso:
        # Find SLPM_653.78 in root directory (same approach as PACKDATA)
        iso.seek(root_lba * SECTOR)
        root_dir = iso.read(root_size)
        pos = 0
        while pos < len(root_dir):
            rec_len = root_dir[pos]
            if rec_len == 0: break
            name_len = root_dir[pos + 32]
            name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
            if 'SLPM' in name:
                exe_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
                # Update file size
                iso.seek(root_lba * SECTOR + pos + 10)
                iso.write(struct.pack('<I', len(exe_data)))
                iso.write(struct.pack('>I', len(exe_data)))
                # Write EXE data
                iso.seek(exe_lba * SECTOR)
                iso.write(exe_data)
                print(f"  EXE patched: {len(exe_data):,} bytes at LBA {exe_lba}")
                break
            pos += rec_len
```

**Note**: The `root_lba` and `root_size` variables are currently local to the PACKDATA patching block. Refactor Step 8 to make them available to Step 8.5, or re-parse the PVD.

---

### MT-8. Translate Tier 2 Dungeon Events (~62 Resources, ~2,000 Lines)
**Impact**: MEDIUM
**Risk**: LOW
**Complexity**: ~2,000 lines across 62 resources (20-49 dialogue lines each)
**Dependencies**: None

These are the R1960-R2026 range resources plus various R700-R900 NPC scenes with 20-49 dialogue lines each. Same workflow as MT-4 but lower priority.

---

## 3. Hard Tasks (Significant Engineering Needed)

### HT-1. EXE Menu Label Composite Glyphs (Table 2C)
**Impact**: HIGH -- all menu options show kanji
**Risk**: HIGH (requires font tile replacement in texture atlas)
**Complexity**: ~380 translatable items, 139 unmapped glyph IDs, texture editing pipeline
**Dependencies**: 139 glyph IDs must be mapped first; PSMT4 or PSMT8 texture editing for font tiles

**Problem**: Menu labels are NOT multi-character strings. They are composite glyphs -- each glyph ID (480+) represents an entire pre-rendered Japanese word as a single font tile. Translation requires REPLACING THE FONT TEXTURE TILES for these glyph IDs with English text rendered at the same pixel dimensions.

**Structure**: 106 records at EXE 0x3C3000-0x3C5300, each 56-byte struct with icon glyph + 2 label glyphs + float positioning data.

**Approach**:
1. Map all 94 unmapped glyph IDs in the 480-930 range (add to `data/msg_glyph_map.json`)
2. Identify which font texture atlas contains glyphs 480+ (likely R1272 or a separate atlas loaded at runtime)
3. For each menu label (2 kanji = 1 concept), render English equivalent text (1-8 chars) into the same tile dimensions
4. Replace tiles in the font atlas
5. Build and test

**Alternative approach** (if engine supports it): The 56-byte struct has space for glyph references at specific offsets. If the engine can render standard ASCII glyphs in menu positions, simply replace the composite glyph IDs with sequences of ASCII glyph IDs. This requires understanding the struct format and whether multiple small glyphs can replace a single composite glyph.

**Key unknowns**:
- Which texture resource contains composite glyphs 480+
- Whether the rendering engine supports variable-length glyph sequences in menu structs (probably not -- struct is fixed-size)

---

### HT-2. Name Entry Keyboard Restructuring (Tables 2A + 2B + 2D + 2E)
**Impact**: CRITICAL -- players cannot type English names
**Risk**: HIGH (complex EXE patching + texture editing)
**Complexity**: ~300 lines of EXE binary patching + PSMT4 texture editing
**Dependencies**: PSMT4 deswizzle tool (not yet implemented), PCSX2 texture dump of name entry screen

**Components**:

**A. Character Grid (Table 2A, EXE 0x3C9BF0-0x3C9DA0)**:
- 38 entries, 12-byte records (primary glyph + 5 alternates for different pages)
- Replace kana glyph IDs with A-Z, a-z, 0-9, space, backspace
- For English: Page 1 = A-Z, Page 2 = a-z, Page 3 = 0-9 + symbols
- ASCII glyph IDs: a=65, b=66, ..., z=90 (using char_code - 0x20 formula)

**B. Kana Display Grid (Table 2B, EXE 0x3C83C0-0x3C93A0)**:
- 81 groups of 4-byte records with FFFE/FFFF separators
- Groups 0-28: kana characters (replace with Latin layout)
- Groups 29-80: attribute/status labels (replace with English equivalents, need 45 unmapped glyph IDs)

**C. Kana Mapping Table (Table 2D, EXE 0x3C5B32-0x3C6186)**:
- Paired glyph ID lookup for input conversion
- Reprogram to map button presses to A-Z

**D. Tab Labels (Table 2E, EXE 0x3C9DA0-0x3C9DFC)**:
- Glyph IDs 6400-6412 reference bitmap font in R1189
- Tab labels: katakana, hiragana, alphanumeric, symbols, confirm, male/female names
- Replace with: "ABC", "abc", "123", "Sym", "OK", "M", "F"
- Requires editing R1189's 512x256 PSMT4 texture atlas (or R1188's 1024x1024 PSMT4 atlas)

**E. R1188 UI Texture (1024x1024 PSMT4)**:
- Contains tab labels, buttons, borders, title bar, instruction text
- File: `extracted/packdata_resources/1188_type01.bin`
- Pixel data at offset 0xC00 (524,288 bytes)
- Needs PSMT4 deswizzle/reswizzle

**F. R1189 Character Grid Font (512x256 PSMT4)**:
- Contains the actual keyboard character glyphs
- File: `extracted/packdata_resources/1189_type02.bin`
- Pixel data at offset 0x0E0 (65,536 bytes)

**PSMT4 deswizzle**: Not yet implemented. Different block/column tables from PSMT8. Need to implement based on PCSX2 GSTables.cpp PSMT4 tables.

**Recommended phased approach**:
1. First: Get PCSX2 texture dump of name entry screen (provides deswizzled reference)
2. Implement PSMT4 deswizzle in `tools/psmt4_deswizzle.py` (based on existing psmt8_deswizzle.py)
3. Edit R1188 texture: replace Japanese tab labels with English
4. Edit R1189 texture: ensure Latin characters are present in grid
5. Patch EXE tables 2A, 2B, 2D, 2E to reference English characters and tabs

**EXE patch points summary**:
| Address (file) | Content | Action |
|----------------|---------|--------|
| 0x3C83C0-0x3C93A0 | Kana grid groups | Replace with Latin layout |
| 0x3C9BF0-0x3C9DA0 | Name entry grid | A-Z, a-z, 0-9 |
| 0x3C9DA0-0x3C9DFC | Tab glyph IDs | Keep 6400+ or remap |
| 0x3C5B32-0x3C6186 | Input mapping | Button -> ASCII |
| 0x3C9C00 | Packed char grid | 77 entries, update |

**Code references**: 7 MIPS blocks at VA 0x2FB094-0x2FB4C4 reference glyph table at VA 0x4C9D20.

---

### HT-3. EXE Font Width Table Fix (M13 Reopening)
**Impact**: HIGH -- needed for English text to display at correct widths
**Risk**: HIGH (previously reverted because it broke Japanese stat labels)
**Complexity**: ~50 lines but requires all Japanese menu labels to be translated first
**Dependencies**: HT-1 (menu labels translated) OR a selective width patch that only changes positions used exclusively by English text

**Problem**: The EXE font width table at (address TBD) covers ALL glyphs 0-247. Changing widths for ASCII positions (0-94) also changes widths for Japanese glyphs that share those glyph ID positions. This broke stat labels.

**Fix options**:
A. Translate all Japanese labels first (HT-1), then apply width patch -- no more Japanese glyphs to break
B. Create a selective width patch that identifies which glyph positions are EXCLUSIVELY English and only patches those
C. Investigate whether the game has separate width tables for different font contexts

---

### HT-4. Equipment Type Label Textures (Table 2J)
**Impact**: LOW (12 labels)
**Risk**: MEDIUM
**Complexity**: Find source texture + edit
**Dependencies**: Identify which PACKDATA resource contains glyph IDs 2036-2047

**Problem**: 12 equipment type labels (sword, axe, staff, armor, shield, helmet, accessory, etc.) use glyph IDs 2036-2047 which reference a separate texture, not the main MSG font atlas.

**Action**: Find the texture resource, decode it, replace Japanese labels with English, re-encode.

---

### HT-5. Text Truncation / Display Box Limit (M14)
**Impact**: CRITICAL -- #1 blocker for translation quality
**Risk**: HIGH (requires EXE reverse engineering)
**Complexity**: Unknown -- need to find renderer limits in MIPS code
**Dependencies**: Deep EXE RE

**Current workarounds**: (A) Shorter translations, (B) FFD2 page breaks. Neither is ideal.

**Proper fix**: Find the text renderer's pixel/character limit in the EXE and increase it. This likely involves:
1. Finding the text rendering function (follows DISPLAY_TEXT opcode 0x0004 handling)
2. Identifying the max_chars or max_pixels constant
3. Patching to allow more text per display box
4. May also need to adjust line spacing or box dimensions

---

## 4. Deferred / Skip

### SKIP-1. Demo Disc Screens (R2118-R2124)
**Reason**: These are demo disc disclaimer/advertising screens left over in the retail build. Players will never see them. PSMT8 deswizzle is solved if we ever want to edit them, but there is no gameplay reason to translate them.

### SKIP-2. Battle Debug Strings (EXE Table 2I, 161 strings)
**Reason**: TTY debug output at EXE 0x3EE9D0-0x3F3500. Invisible to players on retail hardware.

### SKIP-3. Developer Debug Strings (EXE Table 2L, 5 of 7)
**Reason**: "Matsuno game boot!!", "Q is Over!!!", etc. -- developer messages only visible during debugging.

### SKIP-4. Binary/Event Data Resources (109 type-02 with 0 dialogue lines)
**Reason**: These have MSG markers but contain only binary/structural data. No translatable text.

### SKIP-5. R1118/R1126/R1134/R1148
**Reason**: Recon confirmed these are event script data / stat tables, NOT dialogue. The FFFE counts (22/171/110/181) were line breaks within data structures, not dialogue lines.

### SKIP-6. Ending Scene Text (R2361)
**Reason**: R2361 is a scene container with background artwork only. The ending narration text location is unidentified. Defer until endgame testing reveals which resources are loaded during ending sequence. Lower priority (endgame content, requires PCSX2 gameplay capture).

### SKIP-7. Type-01 Binary/3D Resources (~1,562 resources)
**Reason**: These are 3D models, textures, and binary data that happen to share type_code=1 but contain no translatable text.

### SKIP-8. Kana Mapping Table (Table 2D)
**Reason**: Only needed if name entry keyboard is fully reworked (HT-2). Defer until then.

### SKIP-9. R2123/R2124 (PSMT4 Demo Resources)
**Reason**: Demo disc resources in PSMT4 format. No PSMT4 deswizzle exists and these are lowest priority.

---

## 5. Recommended Execution Order

### Phase 1: Bug Fixes and Wiring (Day 1)
```
1. QW-4  Move /tmp/inject_r39.py into repo          [5 min]
2. QW-2  Wire chunk_r37_extra.json (111 translations) [5 min]
3. QW-3  Stop patching R1053/R1908                    [10 min]
4. QW-1  Fix consolidation bug (368 lost translations) [30-60 min]
5. QW-5  Add R1350 translation                        [5 min]
```
**Build and test ISO after Phase 1** -- these fixes alone should improve the current build significantly.

### Phase 2: Intro Narration (Day 1-2)
```
6. MT-1  Map ~50 intro narration glyphs               [2-4 hours]
7. MT-1  Translate R1193/R1194 intro text              [2-3 hours]
```
**Build and test** -- intro should now display in English.

### Phase 3: R39 Equipment Fix (Day 2-3)
```
8. MT-2  Write new R39 injector (fixed-size in-place)  [3-4 hours]
```
**Build and test** -- tavern should no longer softlock, equipment menus partially English.

### Phase 4: EXE Pipeline (Day 3)
```
9. MT-7  Wire EXE patching into ISO build              [1-2 hours]
10. QW-6  Patch save slot names                        [30 min]
11. QW-7  Patch 2 player-visible SJIS strings          [30 min]
12. QW-8  Patch NPC names                              [30 min]
```
**Build and test** -- EXE patches now take effect.

### Phase 5: Bulk Translation (Day 3-7)
```
13. MT-4  Translate top 10 dungeon event resources     [2-3 days]
14. MT-5  Translate R39 sequential section (558 msgs)  [1 day]
15. MT-3  Map FE:xx glyphs, translate R1163-R1173      [1 day]
16. MT-8  Translate Tier 2 events (~62 resources)       [2-3 days]
```

### Phase 6: Hard Engineering (Week 2+)
```
17. HT-2  Name entry keyboard (PSMT4 deswizzle first)  [3-5 days]
18. HT-1  Menu label composite glyphs                   [3-5 days]
19. HT-3  Font width table fix                          [1-2 days, after HT-1]
20. HT-5  Text truncation / display box fix             [Unknown, EXE RE]
21. HT-4  Equipment type label textures                  [1-2 days]
22. MT-6  Translate R2129/R1186 variant resources         [1-2 days]
```

---

## 6. Build Pipeline Changes

### 6.1 Changes to build_v9.py

**A. Step 1 post-processing** (after line 16): Remove unsafe resources
```python
# After v2 pipeline, remove unsafe patched resources
for unsafe_r, tc in [(1053, '03'), (1908, '06')]:
    f = f'build/packdata_resources/{unsafe_r:04d}_type{tc}.raw'
    if os.path.exists(f):
        os.remove(f)
        print(f"  Removed unsafe R{unsafe_r}")
```

**B. Step 2 chunk loading** (line 34): Add chunk_r37_extra.json
```python
for fix in ['chunk_r38_fix.json', 'chunk_r43_fix.json', 'chunk_r37_extra.json']:
```

**C. Step 3 R39 path** (line 107): Update path
```python
os.system('PYTHONIOENCODING=utf-8 python build/inject_r39.py 2>/dev/null')
```
(After MT-2 is complete, this becomes `build/inject_r39_v2.py`)

**D. New Step 8.5: EXE patching** (after line 236): See MT-7 above for full code.

**E. Future: Dynamic chunk loading** (Step 1/Step 2): Replace `range(10)` with glob-based discovery:
```python
chunk_files = sorted(glob.glob('data/translate_chunks/chunk_*_translated.json'))
chunk_files += sorted(glob.glob('data/translate_chunks/chunk_r*_fix.json'))
chunk_files += sorted(glob.glob('data/translate_chunks/chunk_r*_extra.json'))
```
This eliminates the need to manually add new chunk files.

### 6.2 New Build Steps Needed (Future)

**Texture Replacement Pipeline** (GAP-B2): For name entry font (HT-2) and any texture-based labels:
1. New step between Steps 6 and 7
2. Read original resource from `extracted/packdata_raw/`
3. Deswizzle PSMT4/PSMT8 pixel data
4. Replace pixel regions with pre-rendered English text
5. Reswizzle
6. Write to `build/packdata_resources/`

**EXE Binary Patch Accumulator**: For all EXE table patches (QW-6/7/8, HT-1/2/3):
1. Start from `extracted/SLPM_653.78`
2. Apply all binary patches (save names, SJIS strings, NPC names, glyph IDs, width table)
3. Write to `build/SLPM_653.78_patched`
4. Step 8.5 injects this into ISO

### 6.3 Files to Create

| File | Purpose |
|------|---------|
| `build/inject_r39_v2.py` | Fixed R39 injector (replaces /tmp/inject_r39.py) |
| `build/patch_exe.py` | EXE binary patch accumulator |
| `tools/psmt4_deswizzle.py` | PSMT4 texture deswizzle/reswizzle |
| `data/type2_translated/batch_intro_narration.json` | R1193/R1194 translations |
| `data/type2_translated/batch_r1163.json` | R1163-R1173 translations |
| `data/type2_translated/batch_dungeon_*.json` | Dungeon event translations |
| `data/type2_translated/batch_r39_sequential.json` | R39 equipment names (if using batch format) |

### 6.4 Summary of All Bugs to Fix

| ID | Description | Location | Fix |
|----|-------------|----------|-----|
| BUG-B1 | chunk_r37_extra.json never loaded | build_v9.py:34 | Add to fix file list |
| BUG-B2 | R1053/R1908 still patched despite unsafe | build_full_english_v2.py | Add exclusion |
| BUG-B3 | inject_r39.py at /tmp/ | build_v9.py:107 | Move to build/ |
| BUG-B4 | No word wrapping in type-2 encoder | build_v9.py:161-166 | Port wrapping from standalone tools |
| BUG-C1 | 368 translations lost in consolidation | consolidation script TBD | Fix merge logic |
| BUG-R39a | stream_end clips at payload_end | build_full_english_v2.py | Parse to byte 2701 |
| BUG-R39b | Group 90 boundary truncation | build_full_english_v2.py | Don't truncate at payload_end |
| BUG-R39c | OT count 91 instead of 97 | build_full_english_v2.py | Preserve original count |
| BUG-R39d | OT offset base wrong by 224 bytes | build_full_english_v2.py | Use byte 240 as base |
| GAP-B1 | No EXE patching in ISO build | build_v9.py | Add Step 8.5 |
| GAP-B2 | No texture replacement pipeline | build_v9.py | New step (future) |

---

## Appendix: Key File Paths

### Build Pipeline
- `build/build_v9.py` -- main build orchestrator
- `build/build_full_english_v2.py` -- type-1 sub-pipeline
- `build/rebuild_packdata.py` -- PACKDATA.DIG reassembly
- `tools/patch_section1_offsets.py` -- Section 1 opcode patcher

### Translation Data
- `data/type2_translated/batch_*.json` -- type-2 translations (auto-discovered)
- `data/translate_chunks/chunk_*_translated.json` -- type-1 translations
- `data/translate_chunks/chunk_r37_extra.json` -- ORPHANED, needs wiring
- `data/msg_glyph_map.json` -- glyph ID to character mappings
- `data/english_glyph_table.json` -- character to glyph ID encoding table
- `data/guide_full_text.txt` -- English walkthrough reference

### Source Resources
- `extracted/packdata_raw/*.raw` -- original PACKDATA resources (CORRECT source)
- `extracted/packdata_resources/*.bin` -- alternative layout (DO NOT use for type-2 parsing)
- `extracted/SLPM_653.78` -- original game executable

### Tools
- `tools/psmt8_deswizzle.py` -- PSMT8 deswizzle/reswizzle (WORKING)
- `tools/analyze_font_entry.py` -- font glyph analysis
- `tools/generate_font_atlas.py` -- English font atlas generator

### Build Output
- `build/packdata_resources/` -- patched resources for PACKDATA rebuild
- `build/patched_type2/` -- intermediate type-2 injection output
- `build/PACKDATA_v3.DIG` -- rebuilt PACKDATA
- `build/BUSIN0_EN_v9.iso` -- final ISO
- `build/SLPM_653.78_patched` -- patched EXE (NOT yet integrated into ISO)
