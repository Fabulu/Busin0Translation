# REINSERTION PLAN: Busin 0 English Translation

**Consolidated from 10 recon agent findings**
**Date:** 2026-05-22

---

## Executive Summary

This plan covers the full pipeline from translated text to a playable English ISO. Six phases (A-F) transform English translations into glyph-index streams, patch them into MSG resources, rebuild PACKDATA.DIG, and produce an xdelta patch. A "proof of life" milestone is defined to validate the pipeline end-to-end with minimal effort.

### Key Facts from Recon

| Fact | Value |
|------|-------|
| Font atlas format | 256x512, 4bpp PSMT4 linear, 21x42 grid, 12x12 cells |
| Glyph encoding | BE uint16 glyph indices (0x0000-0x035A, 882 slots) |
| Alpha convention | INVERTED: 0=opaque, 15=transparent |
| Existing Latin chars | a-z at glyphs 33-58, digits at 16-25 |
| Missing for English | A-Z (26), apostrophe, period, comma, parens (~30 total) |
| Available slots | 80+ hiragana (112-191), 80+ katakana (193-272) |
| MSG resources | 1,700 type-1 entries in PACKDATA.DIG |
| Text expansion ratio | Average 2.12x, median 1.94x (English vs Japanese) |
| Sector alignment | 2048 bytes per sector, resources contiguous |
| Translation coverage | ~79% complete (791 of 1,168 messages + nested shop names) |
| Resources overflowing | 5 of 16 analyzed (36, 38, 43, 45, 49) |
| VWF in original game | NOT present -- fixed 12px width |
| Line width | 12-13 JP chars = 144-156px (standard dialogue) |
| Control codes | FFFF=end, FFFE=linebreak, FFD2-D4=page break, FF01=speaker |

---

## Phase A: Font Atlas Generation

**Goal:** Create a 256x512 4bpp font atlas with English glyphs and inject it into resource 1272.

**Dependencies:** None (can start immediately)
**Estimated complexity:** MEDIUM (2-3 days)
**Can run in parallel with:** Phase B (glyph mapping design)

### Scripts to Write

#### `tools/generate_font_atlas.py`

**Purpose:** Render all needed English glyphs into a 256x512 atlas image, then convert to the game's 4bpp linear format.

**Inputs:**
- TTF font file (recommended: MS Gothic `C:/Windows/Fonts/msgothic.ttc` or Consolas `C:/Windows/Fonts/consola.ttf`)
- Character set definition (95 printable ASCII + extras)
- Glyph slot assignment table (from Phase B)

**Outputs:**
- `build/font_atlas_preview.png` (human-readable preview)
- `build/font_atlas.bin` (65,536 bytes of raw 4bpp pixel data)

**Algorithm:**
```
1. Create 256x512 grayscale image (Pillow)
2. For each (character, slot_index) in assignment table:
   a. Compute cell position: x = (slot_index % 21) * 12, y = (slot_index // 21) * 12
   b. Render character centered in 12x12 cell using PIL ImageDraw.text()
   c. Apply 2-3 level anti-aliasing (the 16-level palette supports this)
3. Convert to 4bpp with INVERTED alpha:
   pixel_4bit = 15 - (pil_grayscale_value * 15 // 255)
   (0 = opaque white text, 15 = transparent background)
4. Pack: two pixels per byte, low nibble first
5. Format is LINEAR (no PS2 GS swizzle needed -- confirmed by recon)
6. Prepend the original 192-byte header from resource 1272 (GS register setup)
7. Append the original 64-byte palette (or generate: 16-entry grayscale CLUT)
```

**Critical details:**
- Keep the 21-column x 42-row grid and 12x12 cell size UNCHANGED (40+ div-by-21 patterns in EXE)
- Preserve the original resource 1272 header (192 bytes) and palette (64 bytes) exactly
- Only replace the pixel data region
- Font rendering: use Pillow `ImageFont.truetype()` at size 10-11px to fit within 12x12 cells
- Test candidate fonts: MS Gothic (clean CJK/Latin), Consolas (clear monospace), Terminus (bitmap)

#### `tools/inject_font_atlas.py`

**Purpose:** Replace the pixel data in resource 1272's extracted file with the new atlas.

**Inputs:**
- `build/font_atlas.bin` (new pixel data)
- `extracted/packdata_resources/1272_type*.bin` (original resource)

**Outputs:**
- `build/packdata_resources/1272_type*.bin` (patched resource)

**Algorithm:**
```
1. Read original resource 1272
2. Locate pixel data region (after 192-byte header, before 64-byte palette)
3. Replace pixel data with new atlas data
4. Verify total size unchanged
5. Write to build directory
```

### Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Wrong pixel format (swizzled vs linear) | HIGH | Recon confirmed linear; validate by round-tripping original atlas |
| Font too large/small for 12x12 cells | MEDIUM | Test multiple font sizes (9-12px); inspect preview PNG |
| Anti-aliasing looks bad on interlaced display | LOW | Test in PCSX2 with interlace mode; use 2-level AA max |
| Multiple font atlases exist (battle/event/menu) | MEDIUM | FCD_event_font, FCD_battle_font references suggest 3+; identify and patch all |

---

## Phase B: English Glyph Mapping

**Goal:** Define the complete character-to-glyph-index mapping for English text encoding.

**Dependencies:** None (design work, no code dependency)
**Estimated complexity:** LOW (1 day)
**Can run in parallel with:** Phase A

### Scripts to Write

#### `tools/build_english_glyph_table.py`

**Purpose:** Generate `data/english_glyph_table.json` mapping each ASCII character to a glyph slot index.

**Output format:**
```json
{
  " ": 0,
  "a": 33, "b": 34, ..., "z": 58,
  "0": 16, "1": 17, ..., "9": 25,
  "A": 112, "B": 113, ..., "Z": 137,
  "'": 138, "\"": 139, "(": 140, ")": 141,
  ";": 142, "+": 143, "=": 144, "#": 145,
  "?": 31, "!": 92, ",": 62, ".": 63,
  ":": 26, "/": 15, "-": 13, "%": 109, "~": 94
}
```

### Slot Assignment Strategy

**PRESERVE existing Latin mappings:**
- Space: slot 0 (already mapped)
- Lowercase a-z: slots 33-58 (already mapped and in atlas)
- Digits 0-9: slots 16-25 (fullwidth, reuse as-is or re-render)
- Existing punctuation: `?`=31, `!`=92, `,`=62, `.`=63, `:`=26, `/`=15, `-`=13, `%`=109, `~`=94

**REPURPOSE hiragana slots for new characters:**
- Uppercase A-Z: slots 112-137 (was hiragana a-row through n-row)
- Apostrophe `'`: slot 138
- Double quote `"`: slot 139
- Open paren `(`: slot 140
- Close paren `)`: slot 141
- Semicolon `;`: slot 142
- Plus `+`: slot 143
- Equals `=`: slot 144
- Hash `#`: slot 145
- Underscore `_`: slot 146
- Open bracket `[`: slot 147
- Close bracket `]`: slot 148

**Total: ~74 active slots out of 882 available.** This is well within capacity.

### Font-Sheet Variant Issue

Recon found that 29 glyph IDs render different kanji depending on which font sheet is loaded (resource-dependent mapping). For English reinsertion, this is NOT a problem because:
1. We are replacing ALL text with English
2. English characters use only slots 0-148, which are in the first font sheet
3. We will render the same English glyphs on ALL font sheets

However, if multiple atlas resources exist (battle font, event font, menu font), each must be patched with the same English glyphs in the same slots.

---

## Phase C: Translation Encoding

**Goal:** Convert each English translation string into a BE uint16 glyph-index stream with proper line wrapping and control codes.

**Dependencies:** Phase B (glyph table), Phase A partial (to know slot assignments)
**Estimated complexity:** HIGH (3-5 days)
**Can run in parallel with:** Phase A (font rendering)

### Scripts to Write

#### `tools/encode_msg.py`

**Purpose:** Master encoder -- takes translated text and produces binary MSG glyph streams.

**Inputs:**
- `data/english_glyph_table.json`
- `data/translations_*.json` (4 translation files)
- `data/full_decoded_text.json` (original messages with control codes)

**Outputs:**
- `build/encoded_resources/{resource_id}.bin` (one per MSG resource)

**Algorithm:**
```python
def encode_message(english_text, original_tokens, glyph_table, max_chars_per_line):
    output = bytearray()
    
    # Step 1: Extract control code tokens from original message
    # Preserve: FF01 (speaker tags), FFD2-D4 (page breaks), FFE0/E1 (format on/off)
    # These are positional -- keep them at message start/end as in original
    
    # Step 2: Word-wrap the English text
    lines = word_wrap(english_text, max_chars_per_line)
    
    # Step 3: Insert page breaks every 3 lines (matching game's 3-line dialogue box)
    paged_lines = insert_page_breaks(lines, lines_per_page=3)
    
    # Step 4: Encode each line
    for i, line in enumerate(paged_lines):
        if line == "PAGE_BREAK":
            output += struct.pack(">H", 0xFFFE)  # empty line = page advance
            continue
        for char in line:
            glyph_idx = glyph_table[char]
            output += struct.pack(">H", glyph_idx)
        if i < len(paged_lines) - 1:  # line break between lines, not after last
            output += struct.pack(">H", 0xFFFE)
    
    # Step 5: Append message terminator
    output += struct.pack(">H", 0xFFFF)
    return output
```

#### `tools/word_wrap.py`

**Purpose:** Word-wrap English text to fit within the game's dialogue box.

**Key parameters:**
- Standard dialogue: 12-13 characters per line at 12px fixed width (144-156px)
- Bulletin board (resource 46): 18-19 characters per line (228px)
- Dungeon text (resource 49): 16-18 characters per line (216px)
- Lines per page: 3 (before page break)

**Algorithm:**
```
1. Split text into words
2. Greedily fit words onto lines, respecting max_chars_per_line
3. Never break mid-word (unlike Japanese which can break anywhere)
4. After every 3 lines, insert a page break marker
5. Return list of lines with page break markers
```

**If VWF is implemented later (Phase E2 in exe-patching):**
- Replace character-count wrapping with pixel-width wrapping
- Use per-glyph width table: `line_width_px = sum(width_table[glyph] for glyph in line)`
- Max line width: ~240px (standard dialogue) or ~320px (bulletin board)
- This roughly doubles characters per line (from ~13 to ~26-30)

#### `tools/fill_translation_gaps.py`

**Purpose:** Generate translations for the ~21% of messages not yet translated.

**Coverage gaps (from recon):**

| Resource | Messages | Priority | Content |
|----------|----------|----------|---------|
| R38 | 177 msgs | CRITICAL | Stat labels, class names, personality traits |
| R43 | 26 msgs | MEDIUM | Tavern bartender dialogue |
| R45 tail | 28 msgs | MEDIUM | Edge-case shop dialogue, floor labels |
| R48 | 107 msgs | LOW | Shop tier names (mostly translated, needs struct fix) |
| R37 | 2 msgs | LOW | Name entry grid (cosmetic) |
| R720/1053/1908/2124 | 37 msgs | SKIP | Poorly decoded, likely not text |

**R38 strategy:** Most are 1-2 character labels (stat abbreviations, class names). Use standard Wizardry terminology from the guide and Busin 1 English EXE:
- Stats: STR, INT, FTH, VIT, AGI, LCK
- Classes: Fighter, Thief, Priest, Ninja, etc.
- Personality: Bold, Cautious, Intellectual, etc.

**R43 strategy:** 26 lines of bartender dialogue, all fully decoded Japanese. Translate directly.

**R48 strategy:** Wire existing nested translations from `translations_menus.json` into flat resource mapping.

### Control Code Preservation Rules

```
ALWAYS COPY FROM ORIGINAL:
  FF01 xx xx ... 0148    Speaker name tag (copy entire sequence verbatim)
  FFE0                   Format off
  FFE1                   Format on
  
RE-GENERATE BASED ON ENGLISH TEXT:
  FFFE                   Line break (new positions from word_wrap)
  FFD2/FFD3/FFD4         Page breaks (insert every 3 lines)
  FFF9                   Wait + line break (preserve if original had it)
  
ALWAYS PRESERVE AT END:
  FFFF                   Message separator
```

### Text Overflow Strategy

For the 5 resources that overflow their sector allocation:

| Resource | Overflow | Strategy |
|----------|----------|----------|
| R36 (+296 bytes) | SMALL | Shorten translations by ~148 chars total (UI labels are easy to abbreviate) |
| R38 (+5,606 bytes) | LARGE | Full PACKDATA rebuild handles this (Phase E) |
| R43 (+214 bytes) | SMALL | Shorten by ~107 chars or let rebuild handle it |
| R45 (+4,156 bytes) | LARGE | Full PACKDATA rebuild handles this |
| R49 (+3,114 bytes) | LARGE | Full PACKDATA rebuild handles this |

**Decision: Always do a full PACKDATA rebuild (Phase E).** This eliminates all overflow concerns. In-place patching is not worth the fragility -- the rebuild is straightforward and handles arbitrary size changes.

---

## Phase D: Resource Patching

**Goal:** Produce modified MSG resource files with English glyph streams replacing Japanese ones.

**Dependencies:** Phase C (encoded glyph streams)
**Estimated complexity:** MEDIUM (2-3 days)
**Cannot run in parallel with Phase C (sequential dependency)**

### Scripts to Write

#### `tools/patch_msg_resources.py`

**Purpose:** Replace text payloads in MSG resources, handling both Format A (with offset table) and Format B (flat stream) resources.

**Inputs:**
- `build/encoded_resources/*.bin` (encoded English streams from Phase C)
- `extracted/packdata_resources/*.bin` (original resources)
- `data/msg_header_analysis.json` (resource format metadata)

**Outputs:**
- `build/packdata_resources/{index}_type{tc}.bin` (patched resources)

**Algorithm for Format B resources (279 of 296 MSG resources -- flat stream, no offset table):**
```
1. Read original resource
2. Identify the glyph stream region (after any sequential table / config header)
3. Replace glyph stream with encoded English data
4. Update nothing else (no internal pointers to fix)
5. New payload = original_header_portion + new_glyph_stream
```

**Algorithm for Format A resources (17 of 296 -- with BE uint16 offset table):**
```
1. Read original resource
2. Parse offset table header: [msg_count, 0, offset_msg1, 0, offset_msg2, 0, ...]
3. Encode each message separately
4. Compute new offsets based on encoded message sizes
5. Rebuild offset table with new values
6. Concatenate: new_offset_table + all_encoded_messages
```

**Sub-header update:**
```
For each patched resource:
  new_payload_size = len(new_payload)
  sub_header = pack('<IIII', 0, new_payload_size, type_code * 16, 0)
```

**Sequential table fields (RISK):**
- Some resources have a sequential table with `field1` values that may be byte sizes
- If `field1` is a size, it must be updated when the glyph stream grows
- MITIGATION: Test with unmodified field1 values first; if rendering breaks, investigate

#### `tools/patch_font_resource.py`

**Purpose:** Replace the font atlas pixel data in resource 1272.

**Inputs:**
- `build/font_atlas.bin`
- `extracted/packdata_resources/1272_type*.bin`

**Outputs:**
- `build/packdata_resources/1272_type*.bin`

**This is a simple binary splice -- replace pixel data bytes, keep header and palette.**

### Non-MSG Patching (Lower Priority)

#### `tools/patch_exe_strings.py`

**Purpose:** Translate hardcoded SJIS strings in the EXE.

**Targets (from exe-patching recon):**
- Save slot labels at 0x3F9370+ (translate)
- Player-visible error/system messages (translate)
- Format strings with %d/%s (translate, PRESERVE format specifiers exactly)
- DO NOT touch FCD_ resource name strings (functional, not display text)
- DO NOT change memory card identifier

**Constraint:** English replacement must be <= original byte length. SJIS uses 2 bytes per JP char, ASCII uses 1 byte per EN char, so a 10-char JP string (20 bytes) has room for 19 ASCII chars + null.

#### `tools/patch_exe_glyph_table.py`

**Purpose:** Extend the 84-entry ASCII glyph lookup table at EXE offset 0x3C0870 to cover full printable ASCII (95 entries).

**Current state:** Maps ASCII 0x20-0x73 (space through 's') to glyph indices 1-93. Stops at 's' -- t-z and symbols missing.

**Required:** Extend to map ASCII 0x20-0x7E to the correct glyph indices from our English glyph table (Phase B).

---

## Phase E: PACKDATA.DIG Rebuild

**Goal:** Rebuild the entire PACKDATA.DIG file from modified and unmodified resources with updated TOC.

**Dependencies:** Phase D (all patched resources ready)
**Estimated complexity:** MEDIUM (2-3 days)
**Cannot run in parallel with Phase D**

### Scripts to Write

#### `tools/rebuild_packdata.py`

**Purpose:** Sequential rebuild of PACKDATA.DIG with new sector allocations.

**Inputs:**
- `build/packdata_resources/` (modified resources)
- `extracted/packdata_resources/` (unmodified resources, used as fallback)
- `extracted/packdata_resources/manifest.json` (original TOC metadata)

**Outputs:**
- `build/PACKDATA.DIG` (~839 MB, may be slightly larger/smaller than original)

**Algorithm:**
```python
SECTOR = 2048
TOC_ENTRIES = 2883
HEADER_SECTORS = 125
OUTLIER_INDICES = {1370, 2100}

def rebuild():
    # Phase 1: Compute new TOC
    running_sector = HEADER_SECTORS  # start at sector 125
    new_toc = []
    
    for i in range(TOC_ENTRIES):
        if i in OUTLIER_INDICES:
            new_toc.append(original_toc_entry[i])  # preserve exactly
            continue
        
        payload = load_payload(i)  # modified if exists, else original
        payload_size = len(payload)
        needed_sectors = ceil((16 + payload_size) / SECTOR)
        type_code = original_type_code[i]
        
        new_toc.append({
            'sector_offset': running_sector,
            'sector_count': needed_sectors,
            'type_code': type_code
        })
        running_sector += needed_sectors
    
    # Phase 2: Write file
    with open(output_path, 'wb') as f:
        # Write TOC (2883 x 12 bytes = 34,596 bytes)
        for entry in new_toc:
            f.write(pack('<III', entry['sector_offset'],
                         entry['sector_count'], entry['type_code']))
        
        # Pad TOC region to sector 125 (256,000 bytes)
        # Copy original header region data (bytes 34,596 to 256,000)
        f.write(original_header_padding)
        
        # Write each resource
        for i in range(TOC_ENTRIES):
            if i in OUTLIER_INDICES:
                continue
            
            payload = load_payload(i)
            sub_header = pack('<IIII', 0, len(payload),
                              original_type_code[i] * 16, original_zero2[i])
            
            block = sub_header + payload
            pad_len = (ceil(len(block) / SECTOR) * SECTOR) - len(block)
            f.write(block + b'\x00' * pad_len)
```

**Edge cases:**
1. **Outlier entries 1370, 2100:** Preserve original TOC bytes exactly (they encode header region layout)
2. **Sub-header zero2 field:** Most entries have 0, but entries 2880+ have value 64. Preserve original values.
3. **Non-text resources:** Copy payload byte-for-byte from original extraction
4. **Contiguity:** Resources are perfectly contiguous in original. Rebuild maintains this.

#### `tools/verify_packdata.py`

**Purpose:** Validate the rebuilt PACKDATA.DIG.

**Checks:**
1. TOC is parseable and all entries have valid sector_offset/count
2. Resources are contiguous (no gaps, no overlaps)
3. Each resource's sub-header payload_size matches actual data
4. Non-modified resources are byte-identical to originals
5. Modified resources decode back to expected English text
6. Total file size is reasonable (~839 MB +/- a few MB)

---

## Phase F: ISO Rebuild + Patch

**Goal:** Replace PACKDATA.DIG (and optionally SLPM_653.78) in the ISO and generate an xdelta patch.

**Dependencies:** Phase E (rebuilt PACKDATA.DIG), Phase D optional (patched EXE)
**Estimated complexity:** LOW (1 day)
**Cannot run in parallel with Phase E**

### Scripts to Write

#### `tools/rebuild_iso.py`

**Purpose:** Replace files in the PS2 ISO.

**Inputs:**
- Original ISO: `C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso`
- `build/PACKDATA.DIG` (rebuilt)
- `build/SLPM_653.78` (patched EXE, if applicable)

**Outputs:**
- `build/BUSIN0_EN.iso`

**Primary strategy: pycdlib `modify_file_in_place()`**

```python
import pycdlib
from io import BytesIO

def rebuild_iso(original_iso, modified_files, output_iso):
    iso = pycdlib.PyCdlib()
    iso.open(original_iso)
    
    for iso_path, local_path in modified_files.items():
        with open(local_path, 'rb') as f:
            data = f.read()
        iso.modify_file_in_place(
            BytesIO(data), len(data),
            iso_path=iso_path
        )
    
    iso.write(output_iso)
    iso.close()

# Usage:
rebuild_iso(
    original_iso="...iso",
    modified_files={
        "/PACKDATA.DIG;1": "build/PACKDATA.DIG",
        # "/SLPM_653.78;1": "build/SLPM_653.78",  # if EXE is patched
    },
    output_iso="build/BUSIN0_EN.iso"
)
```

**This approach preserves:**
- All ISO metadata, boot sectors, PS2 logo
- File LBAs for unmodified files
- SYSTEM.CNF boot configuration

**Fallback (if PACKDATA.DIG changes size):** Use `iso.rm_file()` + `iso.add_fp()` to replace with different-sized file. Then test thoroughly in PCSX2.

**Prerequisite check:** Install pycdlib (`pip install pycdlib`) and verify xdelta3 is available.

#### `tools/create_patch.py`

**Purpose:** Generate xdelta patch for distribution.

**Inputs:**
- Original ISO
- `build/BUSIN0_EN.iso`

**Outputs:**
- `release/busin0_english_v1.0.xdelta`

**Command:**
```bash
xdelta3 -e -f -s "original.iso" "build/BUSIN0_EN.iso" "release/busin0_english_v1.0.xdelta"
```

**If xdelta3 is not installed:** Download from https://github.com/jmacd/xdelta-gpl/releases and place in project root.

---

## Dependency Graph and Parallelism

```
Phase A (Font Atlas)  ----+
                          |
Phase B (Glyph Map)  ----+----> Phase C (Encoding) ----> Phase D (Patching) ----> Phase E (Rebuild) ----> Phase F (ISO)
                          |
Translation Gap Fill ----+
```

### What Can Run in Parallel

| Parallel Group | Phases | Notes |
|---------------|--------|-------|
| Group 1 | A + B + translation gap fill | All independent design/generation work |
| Group 2 | C (depends on A+B output) | Sequential after Group 1 |
| Group 3 | D (depends on C output) | Sequential after Group 2 |
| Group 4 | E (depends on D output) | Sequential after Group 3 |
| Group 5 | F (depends on E output) | Sequential after Group 4 |

### EXE Patching (Optional Enhancement Track)

EXE patching is a separate track that can proceed in parallel with the main pipeline. It has its own phases:

| EXE Phase | Content | Priority | Blocks Main Pipeline? |
|-----------|---------|----------|-----------------------|
| EXE-1: Glyph table extension | Extend ASCII lookup at 0x3C0870 | HIGH | NO (needed for ASCII input, not MSG display) |
| EXE-2: VWF implementation | Add variable-width font rendering | HIGH for quality | NO (fixed-width works, just ugly) |
| EXE-3: Name entry system | Replace kana grids with Latin alphabet | HIGH for UX | NO |
| EXE-4: String translation | Translate SJIS strings in EXE | MEDIUM | NO |
| EXE-5: Per-glyph properties | Update 133 property structs at 0x3C0E78 | MEDIUM | Maybe |

**Critical VWF insight:** Without VWF, the game displays 12-13 fixed-width English characters per dialogue line. This is barely usable. With VWF, ~26-35 characters fit per line. VWF is HIGH priority for playability but can be added after the initial proof-of-life.

---

## Estimated Timeline

| Phase | Effort | Cumulative |
|-------|--------|------------|
| Phase A: Font Atlas | 2-3 days | 2-3 days |
| Phase B: Glyph Map | 1 day (parallel with A) | 2-3 days |
| Phase C: Translation Encoding | 3-5 days | 5-8 days |
| Phase D: Resource Patching | 2-3 days | 7-11 days |
| Phase E: PACKDATA Rebuild | 2-3 days | 9-14 days |
| Phase F: ISO + Patch | 1 day | 10-15 days |
| **Total (main pipeline)** | **10-15 days** | |
| EXE VWF (parallel) | 5-10 days | Ongoing |

---

## "Proof of Life" Milestone

**Objective:** See ONE English sentence rendered in-game with the absolute minimum work.

### Steps (Minimal Path)

1. **Generate a minimal font atlas** (~2 hours)
   - Take the original resource 1272 atlas
   - Replace ONLY the glyphs at slots 112-137 with uppercase A-Z bitmaps
   - Leave all other glyphs untouched (lowercase a-z already work at 33-58)
   - Script: simplified version of `tools/generate_font_atlas.py`

2. **Encode ONE message** (~1 hour)
   - Pick Resource 42, Message 0 (Adventurer's Inn greeting -- short, fully translated)
   - Example: "Welcome to the Inn." = 19 characters, well within limits
   - Manually encode: W=134, e=37, l=44, c=35, o=47, m=45, e=37, ...
   - Each char becomes a BE uint16 glyph index
   - Append FFFF terminator

3. **Patch ONE resource** (~30 min)
   - Read extracted resource 42
   - Replace Message 0's glyph stream with the English encoding
   - Keep all other messages unchanged
   - Update sub-header payload_size if needed

4. **Inject into PACKDATA.DIG** (~30 min)
   - Since resource 42 fits in-place (231% padding), do a direct binary patch:
   - Seek to resource 42's byte offset in PACKDATA.DIG
   - Write new sub-header + payload + zero-pad to sector boundary
   - No TOC changes needed (size fits within existing allocation)

5. **Inject font atlas** (~30 min)
   - Same in-place approach for resource 1272
   - Replace pixel data region only

6. **Build ISO and test** (~30 min)
   - Use pycdlib to replace PACKDATA.DIG in the ISO
   - Boot in PCSX2, walk to the Inn, talk to the innkeeper
   - See "Welcome to the Inn." in English

**Total proof-of-life effort: ~5 hours**

### What This Validates

- Font atlas format is correct (glyphs render properly)
- Glyph slot assignments work (correct characters appear)
- MSG encoding is correct (game parser reads our data)
- PACKDATA in-place patching works
- ISO replacement works
- End-to-end pipeline is viable

### What This Does NOT Validate

- VWF (still fixed-width)
- Line wrapping across multiple lines
- Page breaks
- Control codes (speaker tags, etc.)
- Resources that overflow their sector allocation
- Full PACKDATA rebuild
- EXE patching

---

## Critical Risks (Consolidated)

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|------------|------------|
| 1 | Multiple font atlases need patching (battle/event/menu) | HIGH | HIGH | Identify all font resources via FCD_ references; patch each |
| 2 | Fixed-width 12px rendering makes English barely readable | HIGH | CERTAIN | Implement VWF (EXE Phase 2) as priority enhancement |
| 3 | Format A offset table rebuild breaks 17 resources | MEDIUM | CERTAIN | Carefully recompute offsets; test each Format A resource |
| 4 | Sequential table field1 is a size that needs updating | MEDIUM | UNKNOWN | Test with original values; investigate if rendering breaks |
| 5 | English text 2x expansion overflows 5 resources | LOW | CERTAIN | Full PACKDATA rebuild (Phase E) handles this |
| 6 | pycdlib cannot handle PS2 UDF quirks | MEDIUM | LOW | Fallback: Ps2IsoTools (C#) or manual sector patching |
| 7 | Glyph property structs (133 x 28 bytes) need updating | MEDIUM | LIKELY | Update float scales and atlas coordinates for new glyph positions |
| 8 | Name entry system unusable without EXE patching | HIGH | CERTAIN | EXE Phase 3; can defer if players use default names |
| 9 | 21% untranslated messages remain in Japanese | MEDIUM | CERTAIN | Fill gaps (Phase C script); R38 is critical, others are lower priority |
| 10 | xdelta3 not installed on build system | LOW | UNKNOWN | Download from GitHub releases; single binary, no installer |

---

## File Inventory (Scripts to Create)

| Script | Phase | Priority | Purpose |
|--------|-------|----------|---------|
| `tools/generate_font_atlas.py` | A | P0 | Render English glyphs into 256x512 4bpp atlas |
| `tools/inject_font_atlas.py` | A | P0 | Splice new atlas into resource 1272 |
| `tools/build_english_glyph_table.py` | B | P0 | Generate char-to-glyph-index JSON mapping |
| `tools/encode_msg.py` | C | P0 | Encode English text as BE uint16 glyph streams |
| `tools/word_wrap.py` | C | P0 | Word-wrap English text for dialogue boxes |
| `tools/fill_translation_gaps.py` | C | P1 | Translate remaining ~21% of messages |
| `tools/patch_msg_resources.py` | D | P0 | Replace glyph streams in MSG resources |
| `tools/patch_font_resource.py` | D | P0 | Replace font atlas in resource 1272 |
| `tools/patch_exe_strings.py` | D | P2 | Translate hardcoded EXE strings |
| `tools/patch_exe_glyph_table.py` | D | P1 | Extend ASCII glyph lookup in EXE |
| `tools/rebuild_packdata.py` | E | P0 | Full sequential rebuild with new TOC |
| `tools/verify_packdata.py` | E | P1 | Validate rebuilt PACKDATA.DIG |
| `tools/rebuild_iso.py` | F | P0 | Replace files in ISO via pycdlib |
| `tools/create_patch.py` | F | P0 | Generate xdelta patch |

**Priority key:** P0 = required for proof-of-life, P1 = required for full translation, P2 = enhancement

---

## Appendix: MSG Control Code Reference

```
0xFFFF  Message separator (end of message)
0xFFFE  Line break (explicit, game does NOT auto-wrap)
0xFFF9  Wait for input + line break
0xFFD2  Page break variant 1
0xFFD3  Page break variant 2
0xFFD4  Page break variant 3
0xFFE0  Format off (disable text formatting)
0xFFE1  Format on (enable text formatting)
0xFF01  Speaker tag start marker
0x0148  Text begin marker (after speaker name)
0x0149  Text end marker
0x0145  Continuation marker 1
0x0146  Continuation marker 2
0x0147  Continuation marker 3
```

## Appendix: Dialogue Box Dimensions

| Context | JP Chars/Line | Pixels Wide | EN Chars (12px) | EN Chars (VWF ~7px avg) |
|---------|--------------|-------------|-----------------|------------------------|
| Standard NPC dialogue | 12-13 | 144-156 | 12-13 | ~22-25 |
| Bulletin board (R46) | 18-19 | 216-228 | 18-19 | ~32-35 |
| Dungeon examination (R49) | 16-18 | 192-216 | 16-18 | ~28-32 |
| Lines visible per page | 3 | -- | 3 | 3 |

## Appendix: Resource Format Quick Reference

| Format | Count | Structure | Offset Table? |
|--------|-------|-----------|---------------|
| Format B (flat) | 279 | sequential_table + glyph_stream + FFFF separators | NO |
| Format A (indexed) | 17 | offset_table + glyph_stream | YES (BE uint16 offsets) |
