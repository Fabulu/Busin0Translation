# BUSIN 0: Wizardry Alternative Neo -- Fan Translation Architecture Plan

**Created:** 2026-05-22
**Status:** Ready for implementation
**Game:** BUSIN 0: Wizardry Alternative Neo (PS2, SLPM-65378, 2003, Racjin)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [File Inventory](#2-file-inventory)
3. [Phase 1: PACKDATA.DIG Extractor](#3-phase-1-packdatadig-extractor)
4. [Phase 2: Resource Classification](#4-phase-2-resource-classification)
5. [Phase 3: Font Analysis](#5-phase-3-font-analysis)
6. [Phase 4: Text Extraction](#6-phase-4-text-extraction)
7. [Phase 5: Translation Pipeline](#7-phase-5-translation-pipeline)
8. [Phase 6: Text Reinsertion](#8-phase-6-text-reinsertion)
9. [Phase 7: Font Modification](#9-phase-7-font-modification)
10. [Phase 8: ISO Rebuild](#10-phase-8-iso-rebuild)
11. [Implementation Priority and Parallelism](#11-implementation-priority-and-parallelism)
12. [Risk Register](#12-risk-register)
13. [Reference Data](#13-reference-data)

---

## 1. Project Overview

### Objective
Produce an English-language xdelta patch for BUSIN 0: Wizardry Alternative Neo (PS2 ISO, SLPM-65378). The patch replaces all Japanese text with English, using a custom Latin font atlas, while preserving all game logic.

### Key Advantages
- **No compression** anywhere in PACKDATA.DIG -- all data is raw and directly editable
- **Flat TOC** at byte 0 of PACKDATA.DIG -- fully decoded, simple 12-byte entries
- **Glyph-index MSG format** -- well-understood from BUSIN 1 analysis, no pointers to recalculate
- **~200,000-word English guide PDF** already provides translations for virtually all game content
- **BUSIN 1 English release** on the same engine serves as a Rosetta Stone

### Critical Constraint
The MSG format uses **glyph indices** (uint16 BE, range 0x0000-0x035A), not character codes. Translation requires:
1. Creating a new font atlas with Latin characters mapped to glyph indices
2. Building a glyph-index-to-English-character mapping table
3. Re-encoding all translated text as glyph-index streams

---

## 2. File Inventory

### Source Files (from ISO extraction)

| File | Path | Size | Role |
|------|------|------|------|
| PACKDATA.DIG | `extracted/PACKDATA.DIG` | 839,661,568 B | Main data archive (all game assets) |
| SLPM_653.78 | `extracted/SLPM_653.78` | 4,185,776 B | PS2 executable (ELF) |
| BSN2_0.DSI | `extracted/BSN2_0.DSI` | ~60 MB | Secondary data archive (MPEG video + data) |
| TEMP1.LZH | `extracted/TEMP1.LZH` | ~319 MB | LZH compressed data |

### Reference Files

| File | Path | Role |
|------|------|------|
| ENGLISH GUIDE.pdf | `ENGLISH GUIDE.pdf` (460 MB) | Complete English translations |
| Guide text dump | `dumps/guide_full.txt` (1 MB) | Extracted guide text |
| BUSIN 1 ISO | `extracted_busin1/` | English PS2 release of predecessor |
| BUSIN 1 EXE | `extracted_busin1/SLUS_202.59` | English EXE with debug labels |
| BUSIN 1 MSG files | `extracted_busin1/IMAGE/EVENT/*.MSG` | Reference MSG format samples |

### Existing Tool Scripts

| Script | Path | Status |
|--------|------|--------|
| parse_packdata_toc.py | `tools/parse_packdata_toc.py` | Working -- TOC parser/analyzer |
| scan_packdata_sjis.py | `tools/scan_packdata_sjis.py` | Working -- Shift-JIS text scanner |
| find_font_data.py | `tools/find_font_data.py` | Working -- font data locator |
| scan_exe_strings.py | `tools/scan_exe_strings.py` | Working -- EXE string extractor |
| scan_magic_numbers.py | `tools/scan_magic_numbers.py` | Working -- magic number scanner |

---

## 3. Phase 1: PACKDATA.DIG Extractor

### Objective
Extract all 2,881 data resources from PACKDATA.DIG as individual files, using the decoded TOC.

### PACKDATA.DIG Format Summary

```
File size: 839,661,568 bytes = 409,991 sectors of 2048 bytes
TOC: 2,883 entries x 12 bytes at file offset 0x00000000
  - 2,881 valid data entries
  - 2 structural outlier entries (indices 1370 and 2100)

TOC Entry (12 bytes, little-endian):
  uint32 sector_offset   -- multiply by 2048 for byte offset
  uint32 sector_count    -- multiply by 2048 for byte size (sector-padded)
  uint32 type_code       -- resource type (1,2,3,4,6,7,8,9,10,11,12,13,15,20,44)

Resource Sub-Header (16 bytes at start of each resource, little-endian):
  uint32 zero            -- always 0x00000000
  uint32 payload_size    -- actual data size in bytes (< sector_count * 2048)
  uint32 stride          -- equals type_code * 16 (0x10)
  uint32 zero            -- always 0x00000000

Data region: sectors 0x7D (byte 0x3E800) through 0x64187 (EOF)
Header region: sectors 0x00-0x7C (256,000 bytes) -- PS2 init data, CLUTs, GS configs
```

### Outlier Entry Detection

Entries at indices 1370 and 2100 are structural markers, NOT data:
- Entry 1370: `A=0x55, B=0x28, C=4` -- A+B = 0x7D = first data sector
- Entry 2100: `A=0x11, B=0x44, C=4` -- A+B = 0x55 = entry 1370's A

Detection rule: an entry is an outlier if `entry[i].sector_offset + entry[i].sector_count != entry[i+1].sector_offset` AND the entry's sector_offset < 0x7D (i.e., it points into the header region, not the data region).

### Script: `tools/extract_packdata.py`

**Purpose:** Extract all resources from PACKDATA.DIG into individual files.

**Input:** `extracted/PACKDATA.DIG`
**Output:** `extracted/packdata_resources/NNNN_typeNN.bin` (one file per resource)
**Also output:** `extracted/packdata_resources/manifest.json` (metadata for all entries)

**Key Logic:**

```python
import struct, os, json

INPUT = "extracted/PACKDATA.DIG"
OUTDIR = "extracted/packdata_resources"
SECTOR = 2048

def parse_toc(f):
    """Read all 2883 TOC entries from offset 0."""
    entries = []
    for i in range(2883):
        data = f.read(12)
        sec_off, sec_cnt, type_code = struct.unpack("<III", data)
        entries.append({
            "index": i,
            "sector_offset": sec_off,
            "sector_count": sec_cnt,
            "type_code": type_code,
            "byte_offset": sec_off * SECTOR,
            "byte_size_padded": sec_cnt * SECTOR,
        })
    return entries

def is_outlier(entry):
    """Outlier entries point into header region (sector < 0x7D)."""
    return entry["sector_offset"] < 0x7D and entry["index"] > 0

def extract_entry(f, entry, outdir):
    """Extract one resource, reading actual payload size from sub-header."""
    f.seek(entry["byte_offset"])
    sub_header = f.read(16)
    zero1, payload_size, stride, zero2 = struct.unpack("<IIII", sub_header)
    
    # Sanity check
    assert zero1 == 0, f"Entry {entry['index']}: sub-header word 0 != 0"
    assert payload_size <= entry["byte_size_padded"] - 16, \
        f"Entry {entry['index']}: payload_size {payload_size} > available"
    
    payload = f.read(payload_size)
    
    filename = f"{entry['index']:04d}_type{entry['type_code']:02d}.bin"
    filepath = os.path.join(outdir, filename)
    with open(filepath, "wb") as out:
        out.write(payload)
    
    entry["payload_size"] = payload_size
    entry["filename"] = filename
    return entry

# Main: parse TOC, skip outliers, extract all valid entries
# Write manifest.json with all metadata
```

**Testing:**
1. Verify extracted file count = 2,881
2. Verify `sum(payload_sizes) < file_size`
3. Spot-check 10 resources: re-read from DIG at offset, compare to extracted file
4. Verify type_code distribution matches recon findings
5. Check that outlier entries 1370 and 2100 are correctly skipped

### Script: `tools/extract_packdata_raw.py`

**Purpose:** Alternative extractor that preserves the sub-header and full sector-padded data (useful for rebuilding later).

**Output:** `extracted/packdata_raw/NNNN_typeNN.raw` (with 16-byte sub-header + padding)

This is needed for Phase 8 (ISO rebuild) -- the repacker needs to know the exact sector-aligned sizes.

---

## 4. Phase 2: Resource Classification

### Objective
Scan all 2,881 extracted resources to identify which contain text (MSG-like structures, Shift-JIS strings, or other translatable data).

### Script: `tools/classify_resources.py`

**Purpose:** Analyze each extracted resource and classify by content type.

**Input:** `extracted/packdata_resources/` (all .bin files) + `manifest.json`
**Output:** `dumps/resource_classification.json`

**Key Logic:**

```python
# For each resource file:

def classify(data, type_code):
    """Return a classification dict with detected content types."""
    result = {
        "has_sjis": False,
        "has_msg_structure": False,
        "has_floats": False,
        "has_tmx": False,
        "has_riff": False,
        "has_vag": False,
        "has_text_indices": [],
        "magic_bytes": data[:4].hex() if len(data) >= 4 else "",
    }
    
    # 1. Check for MSG structure: scan for FFFF/FFFE as big-endian uint16
    #    MSG files are streams of BE uint16 with FFFF separators
    ffff_count = 0
    fffe_count = 0
    for i in range(0, len(data) - 1, 2):
        word = (data[i] << 8) | data[i+1]  # big-endian
        if word == 0xFFFF:
            ffff_count += 1
        elif word == 0xFFFE:
            fffe_count += 1
    if ffff_count >= 5 and fffe_count >= 3:
        result["has_msg_structure"] = True
        result["msg_count"] = ffff_count
        result["linebreak_count"] = fffe_count
    
    # 2. Check for Shift-JIS text (lead bytes 0x81-0x9F, 0xE0-0xEF)
    sjis_pairs = 0
    for i in range(len(data) - 1):
        lead = data[i]
        trail = data[i+1]
        if (0x81 <= lead <= 0x9F or 0xE0 <= lead <= 0xEF):
            if (0x40 <= trail <= 0x7E or 0x80 <= trail <= 0xFC):
                sjis_pairs += 1
    if sjis_pairs >= 10:
        result["has_sjis"] = True
        result["sjis_pair_count"] = sjis_pairs
    
    # 3. Check for known magic bytes
    if data[:4] == b"TMX0" or data[:4] == b"TMX\x00":
        result["has_tmx"] = True
    if data[:4] == b"RIFF":
        result["has_riff"] = True
    if data[:4] == b"VAGp":
        result["has_vag"] = True
    if data[:4] == bytes([0x12, 0x12, 0x12, 0x12]):
        result["has_tmz_compressed"] = True
    
    # 4. Check for IEEE 754 floats (3D model indicator)
    float_count = 0
    for i in range(0, min(len(data), 1024) - 3, 4):
        val = struct.unpack("<f", data[i:i+4])[0]
        if 0.001 < abs(val) < 10000.0 and val == val:  # not NaN
            float_count += 1
    if float_count > 50:
        result["has_floats"] = True
    
    return result
```

**Classification Categories (expected):**

| Type Code | Likely Content | Detection Method |
|-----------|---------------|------------------|
| 1 | Small data (palettes, configs, single records) | Size = 1 sector |
| 2 | Text/script data (MSG-like) | FFFF/FFFE scan, SJIS scan |
| 3 | Audio (RIFF/WAV) | RIFF magic |
| 4 | Structured data tables (items, stats, spells) | Repeating struct patterns |
| 6-9 | 3D models, maps, geometry | Float patterns, VIF/GIF tags |
| 10 | Large structured data | Mixed content |
| 11 | Very large resources (~2 MB) | Likely textures or map data |
| 12-13 | Medium resources | Various |
| 15 | Medium resources | Various |
| 20 | Multi-resource containers (font?) | Sub-entry structure |
| 44 | Rare type | Unknown |

### Script: `tools/scan_sjis_regions.py`

**Purpose:** Deeper Shift-JIS scan of resources that contain text -- extract the actual character sequences and decode them.

**Input:** Resources flagged as `has_sjis == True` or `has_msg_structure == True`
**Output:** `dumps/sjis_text_dump.txt` (human-readable text per resource)

**Key Logic:**
- For MSG-structured resources: split on FFFF, decode glyph indices (not SJIS -- these are glyph IDs)
- For SJIS resources: extract contiguous runs of valid SJIS bytes, decode with `codecs.decode(bytes, 'shift_jis')`
- Record the byte offset, resource index, and decoded text for each string

### Testing
1. Cross-reference results with the known Shift-JIS regions at ~64, 400, 416, 464, 640, 656, 784 MB
2. Verify that the Shift-JIS scanner finds text in those approximate byte ranges
3. Manually inspect 5 MSG-structured resources to confirm they match the MSG format spec
4. Verify no false positives (e.g., float data misidentified as text)

---

## 5. Phase 3: Font Analysis

### Objective
Locate the font atlas in PACKDATA.DIG, extract it, determine the glyph layout, and build a complete glyph-index-to-character mapping.

### Critical Background

The game uses a **glyph-index encoding** in MSG files. Each uint16 BE value (0x0000-0x035A) maps to a tile position in a font texture atlas. The font atlas is NOT a TIM2 file (no TIM2 headers found anywhere in PACKDATA.DIG). It is stored in a custom format, likely within a type=20 resource.

**Candidate resources for the font:**
- **Entry 34** (type=20, 68 KB, 16 sub-entries) -- HIGHEST PRIORITY. Type 20 is rare and this is a multi-resource container consistent with a font atlas + metadata.
- **Entry 26** (type=10, 326 KB) -- large, unusual type
- **Entry 30** (type=2, 806 KB) -- largest type-2 entry

### Script: `tools/analyze_font_entry.py`

**Purpose:** Deep binary analysis of candidate font entries, especially entry 34.

**Input:** `extracted/packdata_resources/0034_type20.bin`
**Output:** `dumps/font_analysis_detailed.txt`, `dumps/font_atlas_raw.bin`

**Key Logic:**

```python
# 1. Parse the sub-entry structure within the resource
#    The 16-byte sub-header at offset 0 gives: (0, payload_size, stride=0x140, 0)
#    stride = type_code * 16 = 20 * 16 = 320 = 0x140
#    This stride may indicate 320-byte sub-entries, or 20 logical sub-resources

# 2. Scan for palette data (sequences of ABGR1555 uint16 values)
#    PS2 font textures typically use 4bpp or 8bpp indexed color
#    Look for 16-entry or 256-entry CLUT data (grayscale ramp)

# 3. Scan for bitmap data:
#    - Font glyphs are typically arranged in a grid
#    - Common glyph sizes: 12x12, 14x14, 16x16, 18x18, 20x20
#    - For 858 glyphs at 16x16, 4bpp: 858 * 16 * 16 / 2 = 109,824 bytes (~107 KB)
#    - For 858 glyphs at 12x12, 4bpp: 858 * 12 * 12 / 2 = 61,776 bytes (~60 KB)
#    - 68 KB entry could hold ~858 glyphs at ~12x12 4bpp

# 4. Try rendering the data as a bitmap at various widths/bpp:
#    - Write raw pixels to a BMP or PNG file
#    - Try widths: 128, 256, 512 pixels
#    - Try bpp: 4 (indexed), 8 (indexed), 1 (monochrome)

# 5. Check for a width table:
#    - Variable-width fonts need a byte-per-glyph width table
#    - Look for a sequence of ~858 bytes where each value is 4-20
#    - This might be at the end of the font resource or in a companion resource

def try_render_bitmap(data, width, bpp, filename):
    """Render raw pixel data as a grayscale image."""
    from PIL import Image
    if bpp == 4:
        pixels = []
        for byte in data:
            pixels.append((byte & 0x0F) * 17)  # scale 0-15 to 0-255
            pixels.append((byte >> 4) * 17)
        height = len(pixels) // width
        img = Image.new("L", (width, height))
        img.putdata(pixels[:width * height])
        img.save(filename)
    elif bpp == 8:
        height = len(data) // width
        img = Image.new("L", (width, height))
        img.putdata(list(data[:width * height]))
        img.save(filename)
```

### Script: `tools/dump_glyph_atlas.py`

**Purpose:** Once the font atlas is located, extract individual glyphs and attempt OCR or manual identification.

**Input:** Font atlas resource (identified by analyze_font_entry.py)
**Output:** `dumps/glyphs/glyph_NNNN.png` (individual glyph images), `dumps/glyph_map.json`

**Key Logic:**
- Parse the atlas into a grid of glyph cells
- Export each cell as a small PNG image
- For the first ~96 glyphs (if they cover ASCII range): attempt automated recognition
- Generate a template `glyph_map.json` mapping glyph index to character

### Alternative Approach: PCSX2 VRAM Dump

If the font atlas cannot be located statically:

1. Run the game in PCSX2 with the debugger enabled
2. At the main menu or dialogue screen, dump GS (Graphics Synthesizer) VRAM
3. The font texture will be visible as a grid of characters in VRAM
4. Use PCSX2's texture replacement feature to identify the GS texture page/block

### Script: `tools/build_glyph_table.py`

**Purpose:** Build the glyph-to-character mapping by cross-referencing MSG data with known text.

**Input:** MSG resource data + BUSIN 1 MSG files + guide translations
**Output:** `data/glyph_table.json`

**Key Logic:**

```python
# Strategy: Use frequency analysis + known text to deduce the mapping.
#
# 1. Parse all MSG resources from PACKDATA.DIG
# 2. Build frequency histogram of all glyph indices
# 3. The most frequent glyph is likely a common Japanese character:
#    - 0x0040 (248 occurrences in BUSIN 1 UEDA.MSG) -- likely の (no) or space
#    - 0x026A (199 occurrences) -- likely 。 (period)
#    - 0x026E (124 occurrences) -- likely 、 (comma)
# 4. For BUSIN 1: we have both the MSG files and the English game text
#    Compare glyph frequencies between JP MSG and known EN text to deduce mappings
# 5. Speaker name tags (011e 0247 ... 0148 ... 0149) contain character names
#    If we know character names (Vera, Erika, etc.), we can match glyph sequences
# 6. Cross-reference spell names: KRETA = specific glyph sequence in MSG
```

### Testing
1. Visual inspection of rendered font atlas (should show recognizable Japanese characters)
2. Glyph count should be ~858 (matching 0x0000-0x035A range)
3. Cross-validate glyph map by decoding a known dialogue passage and comparing to guide
4. The period glyph (0x026A) should appear at sentence boundaries

### Risks/Blockers
- **CRITICAL:** If the font is generated at runtime by the IPU (Image Processing Unit), there may be no static atlas to extract. The IPU library (`PsIIlibipu`) is present in the EXE. Mitigation: use PCSX2 VRAM dump approach.
- **MODERATE:** The font may be in a resource we haven't identified. Mitigation: scan ALL type=20 and type=4 resources for bitmap-like data patterns.
- **MODERATE:** PS2 GS texture swizzling. 4bpp and 8bpp indexed textures on PS2 use a non-linear pixel ordering. Must apply CSM1 unswizzle before the atlas is human-readable.

---

## 6. Phase 4: Text Extraction

### Objective
Extract all translatable text from PACKDATA.DIG into structured JSON/CSV files, covering dialogue, menus, items, spells, monster names, and all other text categories.

### Dependencies
- Phase 1 (extractor) -- need individual resource files
- Phase 2 (classification) -- need to know which resources contain text
- Phase 3 (font/glyph mapping) -- need glyph-to-character table to decode MSG data

### Text Categories

| Category | Format | Location (expected) | Encoding |
|----------|--------|---------------------|----------|
| Dialogue/Events | MSG format (glyph indices, BE uint16) | Type 2 resources | Glyph-index stream |
| Item names | Shift-JIS strings in data tables | Type 4 resources | Shift-JIS (direct) |
| Spell names | Shift-JIS strings in data tables | Type 4 resources | Shift-JIS (direct) |
| Monster names | Shift-JIS strings in data tables | Type 4 resources | Shift-JIS (direct) |
| Menu/UI text | Shift-JIS in EXE or resources | EXE + various | Shift-JIS or glyph |
| EXE strings | Shift-JIS debug/UI strings | SLPM_653.78 | Shift-JIS |

### Script: `tools/extract_msg_text.py`

**Purpose:** Parse MSG-format resources and extract all messages with control codes.

**Input:** All resources classified as `has_msg_structure == True`
**Output:** `data/extracted_text/msg_NNNN.json` per resource, `data/extracted_text/all_messages.json` (combined)

**Key Logic:**

```python
def parse_msg_resource(data, glyph_table):
    """Parse a MSG-format glyph-index stream into messages."""
    messages = []
    current_msg = {"tokens": [], "text": "", "control_codes": []}
    
    for i in range(0, len(data) - 1, 2):
        word = struct.unpack(">H", data[i:i+2])[0]  # big-endian uint16
        
        if word == 0xFFFF:
            # Message separator
            messages.append(current_msg)
            current_msg = {"tokens": [], "text": "", "control_codes": []}
        elif word == 0xFFFE:
            current_msg["tokens"].append({"type": "linebreak"})
            current_msg["text"] += "\n"
        elif 0xFFC0 <= word <= 0xFFFD:
            current_msg["tokens"].append({"type": "control", "code": word})
            current_msg["control_codes"].append(word)
        elif word == 0x0000 and all(data[j] == 0 for j in range(i, min(i+8, len(data)))):
            break  # trailing zero padding
        else:
            # Glyph index
            char = glyph_table.get(word, f"[{word:04X}]")
            current_msg["tokens"].append({"type": "glyph", "index": word, "char": char})
            current_msg["text"] += char
    
    if current_msg["tokens"]:
        messages.append(current_msg)
    
    return messages

# Output format per message:
# {
#   "resource_id": 1234,
#   "message_index": 0,
#   "original_text": "decoded Japanese text",
#   "tokens": [...],
#   "has_speaker_tag": true/false,
#   "speaker_glyphs": [0x011e, 0x0247, ...],
#   "byte_offset": 0,
#   "byte_length": 42
# }
```

### Script: `tools/extract_table_text.py`

**Purpose:** Extract Shift-JIS text from structured data tables (items, spells, monsters).

**Input:** Resources classified as `has_sjis == True` (likely type 4 resources)
**Output:** `data/extracted_text/tables_NNNN.json`

**Key Logic:**

```python
def extract_sjis_strings(data, min_length=2):
    """Extract all Shift-JIS encoded strings from binary data."""
    strings = []
    i = 0
    while i < len(data):
        # Try to read a SJIS string starting at offset i
        start = i
        chars = []
        while i < len(data):
            byte = data[i]
            if byte == 0x00:
                break  # null terminator
            if (0x81 <= byte <= 0x9F or 0xE0 <= byte <= 0xEF) and i + 1 < len(data):
                trail = data[i+1]
                if 0x40 <= trail <= 0x7E or 0x80 <= trail <= 0xFC:
                    chars.append(data[i:i+2])
                    i += 2
                    continue
            if 0x20 <= byte <= 0x7E:  # ASCII printable
                chars.append(bytes([byte]))
                i += 1
                continue
            if 0xA1 <= byte <= 0xDF:  # half-width katakana
                chars.append(bytes([byte]))
                i += 1
                continue
            break  # not a valid SJIS continuation
        
        if len(chars) >= min_length:
            raw = b"".join(chars)
            try:
                text = raw.decode("shift_jis")
                strings.append({
                    "offset": start,
                    "raw_hex": raw.hex(),
                    "text": text,
                    "length": len(raw),
                })
            except:
                pass
        i = max(i + 1, start + 1)
    
    return strings
```

### Script: `tools/extract_exe_strings.py`

**Purpose:** Extract all translatable strings from the PS2 executable.

**Input:** `extracted/SLPM_653.78`
**Output:** `data/extracted_text/exe_strings.json`

**Note:** The BUSIN 0 EXE contains 464 Shift-JIS debug strings (at 0x3EC910-0x3FC7F0). Many are developer debug messages, but some are player-facing:
- Menu labels, error messages, system prompts
- Format strings with `%d`, `%s` placeholders
- These need translation too

### Output Format (all extractors)

All extracted text files use a common JSON schema:

```json
{
  "source": "PACKDATA.DIG entry 1234",
  "format": "msg" | "sjis_table" | "exe_string",
  "entries": [
    {
      "id": "1234_msg_000",
      "original": "Japanese text here",
      "translation": "",
      "context": "dialogue / item_name / spell_name / menu / ...",
      "byte_offset": 0,
      "byte_length": 42,
      "max_bytes": 42,
      "notes": ""
    }
  ]
}
```

### Testing
1. Decode 10 known dialogue passages and compare to the English guide
2. Verify item names match known items (e.g., search for katana names)
3. Verify spell names match the 56 known spells
4. Count total extracted strings -- should be thousands for dialogue + hundreds for items
5. Verify no messages are truncated or have misaligned glyph pairs

---

## 7. Phase 5: Translation Pipeline

### Objective
Cross-reference extracted Japanese text with the English guide PDF to produce translated text for all game content.

### Dependencies
- Phase 4 (text extraction) -- need all extracted text with IDs
- English guide text dump (`dumps/guide_full.txt`)

### Script: `tools/build_glossary.py`

**Purpose:** Parse the English guide and build structured glossaries for all game terms.

**Input:** `dumps/guide_full.txt`
**Output:** `data/glossary.json`

**Key Logic:**

```python
# Parse the guide text to extract structured data:

glossary = {
    "spells": {
        # 56 spells (28 sorcery + 28 holy)
        "KRETA": {"level": 1, "type": "sorcery", "element": "fire", "target": "single"},
        "HEAL": {"level": 1, "type": "holy", "target": "single"},
        # ...
    },
    "classes": {
        "Fighter": {"abbrev": "FIG"},
        "Thief": {"abbrev": "THI"},
        # 16 total
    },
    "races": ["Human", "Elf", "Gnome", "Dwarf", "Hobbit"],
    "attributes": {
        "STR": "Strength", "INT": "Intelligence", "FTH": "Faith",
        "VIT": "Vitality", "AGI": "Agility", "LCK": "Luck",
    },
    "items": {
        # Hundreds of items with names, stats, categories
    },
    "monsters": {
        # All monster names with stats
    },
    "alleid_attacks": {
        # All cooperative attacks/defenses/supports
    },
    "personality_traits": [...],
    "npc_names": {
        # Character names: Vera, Erika, Iris, Konde, Lidi, etc.
    },
    "locations": {
        # Duhan, Karman's Labyrinth, etc.
    },
}
```

### Script: `tools/match_translations.py`

**Purpose:** Attempt to automatically match extracted Japanese text entries to English guide translations.

**Input:** `data/extracted_text/all_messages.json`, `data/glossary.json`
**Output:** `data/translation_draft.json`

**Key Logic:**

```python
# Matching strategies (in priority order):

# 1. EXACT STRUCTURAL MATCH:
#    Item/spell/monster data tables have fixed record sizes.
#    If we know the table order matches the guide order, map 1:1.

# 2. CONTEXT MATCH:
#    The guide is organized by dungeon floor (B1F-B11F).
#    MSG resources are likely organized similarly.
#    Match by floor/event number.

# 3. SPEAKER-NAME MATCH:
#    Messages with speaker tags (011e 0247) contain character names.
#    Decode the name glyphs, match to known NPC names, then match dialogue.

# 4. LENGTH/PATTERN MATCH:
#    Short strings (1-3 chars) in data tables are likely stat labels or menu items.
#    Match by positional context within the table.

# 5. MANUAL ANNOTATION:
#    For messages that can't be auto-matched, output them with context
#    for manual translation assignment.
```

### Script: `tools/translation_editor.py`

**Purpose:** Simple CLI or web-based editor for reviewing/editing translations.

**Input:** `data/translation_draft.json`
**Output:** `data/translation_final.json`

**Features:**
- Show original Japanese (decoded) and proposed English side by side
- Highlight length warnings (translation longer than original)
- Allow editing, adding notes, flagging uncertain translations
- Track completion percentage by category

### Text Length Management

**CRITICAL ISSUE:** English text is typically 30-50% longer than Japanese text. Mitigations:

1. **MSG format flexibility:** MSG files are flat streams with zero-padding at the end. If the total translated text for a resource is shorter than or equal to the original resource size, no problems arise. If longer, the resource must grow.

2. **Resource resizing:** Since PACKDATA.DIG uses sector-aligned resources, any resource can be expanded up to the next sector boundary without affecting other resources. Beyond that, the entire file must be rebuilt (Phase 8 handles this).

3. **Abbreviation strategy:** Use the guide's established abbreviations (OFE, DEF, EVA, ACC) for stat names. Use short names where possible.

4. **Text box capacity:** Japanese dialogue typically shows 3-4 lines of ~20 characters. English VWF (variable-width font) can fit more characters per line. Estimate ~30 English characters per line with VWF.

### Testing
1. Verify glossary completeness: all 56 spells, all 16 classes, all races present
2. Spot-check 20 auto-matched translations against the guide
3. Verify no duplicate translations (one Japanese string mapped to two different English strings)
4. Run length analysis: flag all translations where English byte count > Japanese byte count * 1.5

---

## 8. Phase 6: Text Reinsertion

### Objective
Insert translated English text back into PACKDATA.DIG resources, producing modified resource files ready for repacking.

### Dependencies
- Phase 3 (font/glyph mapping) -- need the English glyph-to-index mapping
- Phase 5 (translations) -- need finalized translation data
- Phase 7 (font modification) -- need the English font atlas installed first

### Encoding Strategy

Since the MSG format uses glyph indices (not character codes), we need an **English glyph table** that maps ASCII characters to glyph indices. There are two approaches:

**Approach A: Reuse existing glyph slots**
- Map English letters to glyph indices that previously held Japanese characters
- Example: Glyph 0x0041 (previously hiragana 'a') now holds the Latin 'A' bitmap
- The font atlas (Phase 7) is modified to place Latin glyphs at these positions
- Pro: minimal format changes. Con: must carefully choose which Japanese glyphs to replace.

**Approach B: Define a new mapping**
- Create a clean mapping: glyph 0x0000 = 'A', 0x0001 = 'B', ..., 0x005A = 'z', etc.
- Remap the entire font atlas accordingly
- Pro: clean, predictable. Con: more work, must update ALL text references.

**Recommended: Approach A** -- reuse the first ~128 glyph slots for ASCII characters (A-Z, a-z, 0-9, punctuation), keeping the remaining slots for any Japanese characters that must be preserved (e.g., spell names in katakana if desired).

### Script: `tools/encode_msg.py`

**Purpose:** Encode translated English text as glyph-index streams in MSG format.

**Input:** `data/translation_final.json`, `data/english_glyph_table.json`
**Output:** Modified resource files in `build/packdata_resources/`

**Key Logic:**

```python
def encode_message(text, control_tokens, en_glyph_table):
    """Encode an English message as a BE uint16 glyph-index stream."""
    output = bytearray()
    
    token_idx = 0
    for token in merged_token_stream:
        if token["type"] == "control":
            output += struct.pack(">H", token["code"])
        elif token["type"] == "linebreak":
            output += struct.pack(">H", 0xFFFE)
        elif token["type"] == "text":
            for char in token["text"]:
                glyph_idx = en_glyph_table.get(char)
                if glyph_idx is None:
                    raise ValueError(f"No glyph for character '{char}'")
                output += struct.pack(">H", glyph_idx)
    
    output += struct.pack(">H", 0xFFFF)  # message separator
    return output

def rebuild_msg_resource(original_data, messages, en_glyph_table):
    """Rebuild an entire MSG resource with translated messages."""
    output = bytearray()
    
    for msg in messages:
        encoded = encode_message(msg["translation"], msg["control_tokens"], en_glyph_table)
        output += encoded
    
    # Pad to original resource size (or larger if needed)
    original_size = len(original_data)
    if len(output) < original_size:
        output += b"\x00" * (original_size - len(output))
    
    return bytes(output)
```

### Script: `tools/patch_tables.py`

**Purpose:** Replace Shift-JIS strings in data tables (items, spells, monsters) with English text.

**Input:** Original table resources, `data/translation_final.json`
**Output:** Modified table resources in `build/packdata_resources/`

**Key Logic:**

```python
def patch_fixed_length_string(data, offset, new_text, max_length, encoding="ascii"):
    """Replace a fixed-length string field in a data table."""
    encoded = new_text.encode(encoding)
    if len(encoded) > max_length:
        # Truncate with ellipsis or abbreviate
        encoded = encoded[:max_length-1] + b"."
    # Pad with null bytes
    encoded = encoded.ljust(max_length, b"\x00")
    return data[:offset] + encoded + data[offset + max_length:]
```

**CRITICAL:** Table records have fixed-size string fields (e.g., item name = 16 bytes). English names must fit within these field sizes. If a name is too long, it must be abbreviated. The guide already uses abbreviated names for many items.

### Script: `tools/patch_exe_strings.py`

**Purpose:** Replace Shift-JIS strings in the PS2 executable with English text.

**Input:** `extracted/SLPM_653.78`, `data/translation_final.json`
**Output:** `build/SLPM_653.78`

**Key Logic:**
- Each EXE string occupies a fixed number of bytes at a known offset
- English replacement must be <= original byte length (cannot expand EXE strings without relocating code)
- Pad with null bytes after the English text
- Verify no MIPS code is accidentally modified

### Testing
1. Re-decode each modified MSG resource and verify the English text reads correctly
2. Verify all modified resources are the correct size (same or larger, sector-aligned)
3. Binary diff original vs modified: only text bytes should change, all control codes preserved
4. Verify EXE modifications don't corrupt code sections (check that modified offsets are in .data/.rodata, not .text)
5. Run the modified game in PCSX2 and verify text displays correctly

---

## 9. Phase 7: Font Modification

### Objective
Create an English font atlas with Latin characters, install it in PACKDATA.DIG, and update any font width/metric tables.

### Dependencies
- Phase 3 (font analysis) -- need to know exact font atlas format, dimensions, palette
- This phase can partially overlap with Phase 6

### Sub-tasks

#### 7A: Design the English Font

**Script:** `tools/generate_font_atlas.py`

**Purpose:** Generate a new font texture atlas with Latin characters.

**Input:** Font specification (glyph size, character set, typeface)
**Output:** `build/font_atlas.png`, `build/font_atlas.bin` (raw PS2 format)

**Key Logic:**

```python
from PIL import Image, ImageDraw, ImageFont

def generate_font_atlas(
    char_set,           # string of all characters to include
    glyph_width,        # pixels per glyph cell (e.g., 16)
    glyph_height,       # pixels per glyph cell (e.g., 16)
    cols,               # glyphs per row in atlas
    ttf_path,           # path to TTF font file
    ttf_size,           # font size in points
):
    """Generate a font atlas image with one glyph per cell."""
    rows = (len(char_set) + cols - 1) // cols
    atlas = Image.new("L", (cols * glyph_width, rows * glyph_height), 0)
    draw = ImageDraw.Draw(atlas)
    font = ImageFont.truetype(ttf_path, ttf_size)
    
    widths = {}
    for i, char in enumerate(char_set):
        col = i % cols
        row = i // cols
        x = col * glyph_width
        y = row * glyph_height
        
        # Center the glyph in the cell
        bbox = font.getbbox(char)
        char_w = bbox[2] - bbox[0]
        char_h = bbox[3] - bbox[1]
        draw.text((x + (glyph_width - char_w) // 2, y + (glyph_height - char_h) // 2 - bbox[1]),
                  char, fill=255, font=font)
        widths[char] = char_w
    
    return atlas, widths

# Character set (minimum):
ENGLISH_CHARSET = (
    " !\"#$%&'()*+,-./0123456789:;<=>?"
    "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_"
    "`abcdefghijklmnopqrstuvwxyz{|}~"
    "..."  # any additional symbols needed (arrows, hearts, etc.)
)
```

**Font Selection Considerations:**
- Use a pixel font or a TTF that renders cleanly at small sizes (12-16px)
- The font must be readable on a 480i NTSC display (PS2 output resolution)
- Consider fonts used by other PS2 fan translations for consistency
- Good candidates: Terminus, Unifont, Press Start 2P, or a custom pixel font

#### 7B: Convert to PS2 Texture Format

**Script:** `tools/convert_font_to_ps2.py`

**Purpose:** Convert the generated font atlas PNG to the PS2 texture format used by the game.

**Input:** `build/font_atlas.png`
**Output:** `build/font_atlas_ps2.bin`

**Key Logic:**

```python
def png_to_ps2_4bpp(image, palette):
    """Convert a grayscale image to PS2 4bpp indexed format with GS swizzling."""
    width, height = image.size
    pixels = list(image.getdata())
    
    # Quantize to 4-bit (16 levels)
    quantized = [min(p // 17, 15) for p in pixels]
    
    # Apply PS2 GS swizzle for 4bpp textures
    # (block-based reordering for GS memory layout)
    swizzled = apply_4bpp_swizzle(quantized, width, height)
    
    # Pack two pixels per byte (low nibble first)
    packed = bytearray()
    for i in range(0, len(swizzled), 2):
        lo = swizzled[i] & 0x0F
        hi = (swizzled[i+1] & 0x0F) << 4 if i+1 < len(swizzled) else 0
        packed.append(lo | hi)
    
    # Build palette (16 entries, ABGR1555 format)
    clut = bytearray()
    for level in range(16):
        gray = level * 2  # 5-bit value (0-31 range scaled from 0-15)
        entry = gray | (gray << 5) | (gray << 10) | (0x8000 if level > 0 else 0)
        clut += struct.pack("<H", entry)
    
    return clut + packed

def apply_4bpp_swizzle(pixels, width, height):
    """Apply PS2 GS CSM1 swizzle for 4bpp indexed textures."""
    # PS2 GS stores 4bpp textures in 32x16 blocks
    # Within each block, pixels are arranged in a specific Z-pattern
    # Reference: PS2 GS User's Manual, Chapter 8
    # ... (implementation of the CSM1 swizzle algorithm)
    pass
```

#### 7C: Build Width Table

**Script:** `tools/build_width_table.py`

**Purpose:** Generate a variable-width font (VWF) width table.

**Input:** `build/font_atlas.png`, character set definition
**Output:** `build/font_widths.bin`

**Key Logic:**

```python
def measure_glyph_widths(atlas_image, glyph_width, glyph_height, cols, char_count):
    """Measure the actual width of each rendered glyph in the atlas."""
    widths = []
    for i in range(char_count):
        col = i % cols
        row = i // cols
        x0 = col * glyph_width
        y0 = row * glyph_height
        
        # Find rightmost non-zero pixel column
        max_x = 0
        for y in range(y0, y0 + glyph_height):
            for x in range(x0 + glyph_width - 1, x0 - 1, -1):
                if atlas_image.getpixel((x, y)) > 0:
                    max_x = max(max_x, x - x0 + 1)
                    break
        
        widths.append(max_x + 1)  # +1 for spacing
    
    return widths
```

#### 7D: EXE Font Patch (if needed)

**Script:** `tools/patch_exe_font.py`

**Purpose:** Modify the PS2 executable to support VWF rendering (if the game uses fixed-width rendering).

**Input:** `extracted/SLPM_653.78`
**Output:** `build/SLPM_653.78` (patched)

**This is a conditional step.** Analysis needed:
1. Determine if the game already supports variable-width glyphs (check the FCD_event_font rendering code)
2. If fixed-width: patch the text rendering function to read per-glyph widths from a table
3. The width table can be stored in unused space in the EXE data section or in a modified PACKDATA resource

**MIPS patching approach:**
- Use Ghidra to find the font rendering function (look for GS texture coordinate calculations)
- The function likely has: `glyph_x = (glyph_index % cols) * glyph_width`
- For VWF: replace the fixed `glyph_width` multiply with a table lookup
- Alternatively: if the game already renders variable-width text (some PS2 JRPGs do), just update the width table values

### Testing
1. Visual test: load the modified font atlas in a TIM2 viewer, verify all Latin characters are readable
2. In PCSX2: run the game and verify the font renders correctly on screen
3. Width table test: verify that text wraps correctly at line boundaries
4. Stress test: display the longest translated string, verify no overflow

### Risks/Blockers
- **HIGH:** PS2 GS swizzle implementation must be pixel-perfect. Incorrect swizzling produces garbled textures. Mitigation: test with PCSX2's texture dump feature, compare.
- **MODERATE:** If the game's text renderer is hardcoded for fixed-width Japanese characters (all 16x16), VWF requires EXE patching. This is the most technically difficult step.
- **LOW:** Font readability at 480i. Test on an actual CRT or with PCSX2 in interlaced mode.

---

## 10. Phase 8: ISO Rebuild

### Objective
Rebuild PACKDATA.DIG with all modified resources, rebuild the ISO, and produce an xdelta patch.

### Dependencies
- All previous phases (all modified resources + EXE must be ready)

### Script: `tools/rebuild_packdata.py`

**Purpose:** Rebuild PACKDATA.DIG from modified resources.

**Input:** `build/packdata_resources/` (modified files), original `extracted/packdata_resources/` (unmodified files), `manifest.json`
**Output:** `build/PACKDATA.DIG`

**Key Logic:**

```python
def rebuild_packdata(manifest, modified_dir, original_dir, output_path):
    """Rebuild PACKDATA.DIG from individual resource files."""
    
    # 1. Read the manifest to get original TOC entries
    entries = manifest["entries"]
    
    # 2. For each entry, determine if it was modified
    #    Modified files are in modified_dir; unmodified are in original_dir
    
    # 3. Build new TOC and data region
    #    - Preserve the original header region (sectors 0x00-0x7C, 256,000 bytes)
    #    - For each data entry:
    #      a. Read the resource payload (modified or original)
    #      b. Prepend the 16-byte sub-header:
    #         (0x00000000, payload_size, type_code * 16, 0x00000000)
    #      c. Pad to sector boundary (2048 bytes)
    #      d. Record the new sector_offset and sector_count in the TOC
    
    SECTOR = 2048
    
    with open(output_path, "wb") as out:
        # Reserve space for header region
        header_region = read_original_header_region()  # first 0x3E800 bytes
        out.write(header_region)
        
        current_sector = 0x7D  # first data sector
        new_toc = []
        
        for entry in entries:
            if is_outlier(entry):
                # Preserve outlier entries as-is in TOC
                new_toc.append(entry)
                continue
            
            # Load payload
            modified_path = os.path.join(modified_dir, entry["filename"])
            original_path = os.path.join(original_dir, entry["filename"])
            
            if os.path.exists(modified_path):
                payload = open(modified_path, "rb").read()
            else:
                payload = open(original_path, "rb").read()
            
            # Build sub-header
            sub_header = struct.pack("<IIII",
                0x00000000,
                len(payload),
                entry["type_code"] * 16,
                0x00000000)
            
            # Calculate sector count
            total_size = 16 + len(payload)
            sector_count = (total_size + SECTOR - 1) // SECTOR
            
            # Write to output
            out.seek(current_sector * SECTOR)
            out.write(sub_header)
            out.write(payload)
            # Pad to sector boundary
            remainder = (16 + len(payload)) % SECTOR
            if remainder > 0:
                out.write(b"\x00" * (SECTOR - remainder))
            
            new_toc.append({
                "sector_offset": current_sector,
                "sector_count": sector_count,
                "type_code": entry["type_code"],
            })
            
            current_sector += sector_count
        
        # Write TOC at offset 0
        out.seek(0)
        for toc_entry in new_toc:
            out.write(struct.pack("<III",
                toc_entry["sector_offset"],
                toc_entry["sector_count"],
                toc_entry["type_code"]))
```

**CRITICAL:** The outlier entries (indices 1370 and 2100) encode the header region's sector layout. If the header region size changes, these must be updated. Since we preserve the original header region, they remain unchanged.

### Script: `tools/rebuild_iso.py`

**Purpose:** Rebuild the PS2 ISO from modified files.

**Input:** Original ISO, `build/PACKDATA.DIG`, `build/SLPM_653.78`
**Output:** `build/BUSIN0_EN.iso`

**Key Logic:**

```python
# Option A: Use mkisofs / genisoimage (recommended)
# PS2 ISOs use standard ISO9660 with specific parameters

import subprocess

def rebuild_iso(original_iso, modified_files, output_iso):
    """
    Approach:
    1. Extract ALL files from original ISO to a temp directory
    2. Replace modified files (PACKDATA.DIG, SLPM_653.78)
    3. Rebuild ISO with mkisofs using PS2-compatible settings
    """
    # Extract original
    extract_dir = "build/iso_staging"
    # Use 7z or pycdlib to extract
    
    # Copy modified files
    shutil.copy("build/PACKDATA.DIG", f"{extract_dir}/PACKDATA.DIG")
    shutil.copy("build/SLPM_653.78", f"{extract_dir}/SLPM_653.78")
    
    # Rebuild with mkisofs
    # PS2 requires: UDF bridge, specific sector size, no Joliet
    subprocess.run([
        "mkisofs",
        "-o", output_iso,
        "-dvd-video",  # or just use standard ISO9660
        "-V", "SLPM_65378",
        "-sysid", "PLAYSTATION",
        extract_dir
    ])

# Option B: Use pycdlib for more control
import pycdlib

def rebuild_iso_pycdlib(original_iso, modified_files, output_iso):
    iso = pycdlib.PyCdlib()
    iso.open(original_iso)
    
    for game_path, local_path in modified_files.items():
        with open(local_path, "rb") as f:
            data = f.read()
        iso.modify_file_in_place(
            BytesIO(data), len(data),
            iso_path=game_path
        )
    
    iso.write(output_iso)
    iso.close()
```

**Note on ISO rebuilding:** PS2 ISOs must preserve the exact SYSTEM.CNF boot configuration and the IOP module layout. The simplest approach is to use `pycdlib` to modify files in-place within the existing ISO structure, avoiding any boot issues.

### Script: `tools/create_patch.py`

**Purpose:** Generate an xdelta patch between original and modified ISOs.

**Input:** Original ISO, modified ISO
**Output:** `release/busin0_english_v1.0.xdelta`

**Key Logic:**

```python
import subprocess

def create_xdelta_patch(original_iso, modified_iso, patch_path):
    subprocess.run([
        "xdelta3",
        "-e",           # encode (create patch)
        "-f",           # force overwrite
        "-s", original_iso,   # source (original)
        modified_iso,         # target (modified)
        patch_path            # output patch
    ], check=True)
```

### Testing
1. **Rebuild verification:** After rebuilding PACKDATA.DIG, re-extract all resources and binary-diff against originals. Only text resources should differ.
2. **ISO verification:** Mount the rebuilt ISO and verify file sizes match expectations.
3. **Boot test:** Load the rebuilt ISO in PCSX2 and verify the game boots to the title screen.
4. **Gameplay test:** Play through the first dungeon floor, checking:
   - Menu text displays in English
   - Dialogue displays correctly with VWF
   - Item names, spell names, monster names are English
   - No crashes at event triggers
   - Save/load works correctly
5. **Patch verification:** Apply the xdelta patch to a clean ISO and verify the result matches the modified ISO byte-for-byte.

---

## 11. Implementation Priority and Parallelism

### Critical Path (must be sequential)

```
Phase 1 (Extract) --> Phase 2 (Classify) --> Phase 4 (Extract Text)
                                                    |
                                                    v
Phase 3 (Font) -----> Phase 7 (Font Mod) -----> Phase 6 (Reinsert) --> Phase 8 (Rebuild)
                                                    ^
                                                    |
                                          Phase 5 (Translate) 
```

### Recommended Build Order

| Order | Phase | Est. Effort | Can Parallelize With |
|-------|-------|-------------|---------------------|
| 1 | Phase 1: PACKDATA.DIG Extractor | 2-4 hours | Nothing (foundational) |
| 2 | Phase 2: Resource Classification | 2-4 hours | Nothing (needs Phase 1 output) |
| 3a | Phase 3: Font Analysis | 4-8 hours | Phase 5 (glossary building) |
| 3b | Phase 5: Build Glossary | 4-8 hours | Phase 3 |
| 4 | Phase 4: Text Extraction | 4-8 hours | Nothing (needs Phase 2 + Phase 3) |
| 5 | Phase 5: Translation Matching | 8-16 hours | Phase 7 |
| 6 | Phase 7: Font Modification | 8-24 hours | Phase 5 (translation matching) |
| 7 | Phase 6: Text Reinsertion | 4-8 hours | Nothing (needs Phase 5 + Phase 7) |
| 8 | Phase 8: ISO Rebuild | 2-4 hours | Nothing (final step) |

### First Milestone: "Proof of Life"

The fastest path to seeing English text in-game:

1. Extract PACKDATA.DIG (Phase 1) -- 2 hours
2. Find and classify MSG resources (Phase 2, partial) -- 2 hours
3. Locate font atlas (Phase 3, partial) -- 4 hours
4. Replace ONE Japanese glyph with a Latin "A" in the font atlas -- 2 hours
5. Find ONE short dialogue message, replace ONE glyph with the "A" glyph -- 1 hour
6. Rebuild PACKDATA.DIG with just that one change -- 2 hours
7. Test in PCSX2 -- 1 hour

**Total for proof-of-life: ~14 hours of work**

This milestone validates the entire pipeline end-to-end before investing in full translation.

---

## 12. Risk Register

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|------------|------------|
| R1 | Font atlas is IPU-generated at runtime, not stored statically | HIGH | LOW | Use PCSX2 VRAM dump. Alternatively, patch the IPU decompression output. |
| R2 | PS2 GS swizzle implementation is incorrect | HIGH | MEDIUM | Use Rainbow library's swizzle code as reference. Test with PCSX2 texture dump. |
| R3 | Text renderer is fixed-width only, VWF requires EXE patching | HIGH | MEDIUM | Compare with BUSIN 1 English EXE (which already has VWF). Port the VWF code. |
| R4 | English text too long for fixed-size table fields | MEDIUM | HIGH | Abbreviate aggressively. Guide already uses abbreviations. |
| R5 | MSG glyph-to-character mapping cannot be determined | HIGH | LOW | Use PCSX2 debugger to trace text rendering. Set breakpoint on font texture access. |
| R6 | BSN2_0.DSI or TEMP1.LZH contain additional text | MEDIUM | MEDIUM | Analyze these files in a follow-up phase. Currently out of scope. |
| R7 | EXE string patches break code alignment | MEDIUM | LOW | Only modify strings in .data/.rodata sections. Verify with Ghidra disassembly. |
| R8 | Game uses DMA-based resource loading with hardcoded sizes | MEDIUM | LOW | If resources change size, verify DMA chain integrity. The rebuilt TOC handles size changes. |
| R9 | Multiple font atlases for different contexts (battle vs dialogue vs menu) | MEDIUM | MEDIUM | FCD_event_font, FCD_battle_font, FCD_event_frame suggest 3+ font resources. Must modify all. |
| R10 | Outlier TOC entries are used by the game for address calculation | LOW | LOW | Preserve outlier entry values exactly as original. They encode header region layout. |

---

## 13. Reference Data

### PACKDATA.DIG TOC Constants

```python
SECTOR_SIZE = 2048
TOC_OFFSET = 0
TOC_ENTRY_SIZE = 12
TOC_ENTRY_COUNT = 2883
DATA_ENTRIES = 2881
OUTLIER_INDICES = [1370, 2100]
FIRST_DATA_SECTOR = 0x7D  # 125
HEADER_REGION_SIZE = 0x3E800  # 256,000 bytes = 125 sectors
```

### MSG Format Constants

```python
MSG_SEPARATOR = 0xFFFF
MSG_LINEBREAK = 0xFFFE
MSG_WAIT_LINEBREAK = 0xFFF9
MSG_PAGE_BREAK_1 = 0xFFD2
MSG_PAGE_BREAK_2 = 0xFFD3
MSG_PAGE_BREAK_3 = 0xFFD4
MSG_FORMAT_OFF = 0xFFE0
MSG_FORMAT_ON = 0xFFE1
MSG_SPEAKER_TAG = [0x011E, 0x0247]
MSG_TEXT_BEGIN = 0x0148
MSG_TEXT_END = 0x0149
MSG_CONTINUATION = [0x0145, 0x0146, 0x0147]
GLYPH_RANGE = (0x0000, 0x035A)  # 858 slots
```

### EXE Memory Map

```
ELF entry point: 0x00100008
Text segment VA: 0x00100000
Text segment file offset: 0x80
Text segment file size: 0x3FDC80 (4.0 MB)
Text segment mem size: 0x479800 (4.5 MB)
VA-to-file calculation: file_offset = VA - 0x00100000 + 0x80
                        equivalently: file_offset + 0x000FFF80 = VA

SJIS debug strings: file offsets 0x3EC910 - 0x3FC7F0
                    VA range: 0x004EC890 - 0x004FC770

Compiler: Metrowerks CodeWarrior MW MIPS C Compiler (2.4.1.01)
PS2 SDK: PsIIlibipu 2500, PsIIlibkernl2540
```

### Type Code Distribution

```
Type  Count  Typical Size      Likely Content
----  -----  ----------------  ---------------------------
  1   ~409   1 sector (2 KB)   Small data records, configs
  2    ~62   Variable          Text/MSG data, script data
  3      5   Variable          Audio (RIFF/WAV confirmed)
  4    ~20   Variable          Data tables (items, spells, stats)
  6      1   Variable          Unknown
  7    varies Variable         Large data blocks
  8    varies Variable         Unknown
  9    varies Variable         Large blocks (last entry = 682 KB)
 10      1   326 KB            Large structured data
 11    varies ~2 MB            Very large (textures? maps?)
 12    varies Variable         Unknown
 13    varies Variable         Unknown
 15      1   Variable          Unknown
 20      1   68 KB             Multi-resource container (FONT?)
 44      1   Variable          Rare/special
```

### File Paths (absolute, Windows)

```
Project root:     C:\Programmieren\wizardrytranslation\
ISO extract:      C:\Programmieren\wizardrytranslation\extracted\
BUSIN 1 extract:  C:\Programmieren\wizardrytranslation\extracted_busin1\
Tool scripts:     C:\Programmieren\wizardrytranslation\tools\
Data dumps:       C:\Programmieren\wizardrytranslation\dumps\
Build output:     C:\Programmieren\wizardrytranslation\build\        (to create)
Release output:   C:\Programmieren\wizardrytranslation\release\      (to create)
Translation data: C:\Programmieren\wizardrytranslation\data\         (to create)
Guide PDF:        C:\Programmieren\wizardrytranslation\ENGLISH GUIDE.pdf
```

### Known Shift-JIS Text Regions in PACKDATA.DIG

Approximate byte offsets where Shift-JIS text has been confirmed:
- ~64 MB (0x03E80000)
- ~400 MB (0x18F40000)
- ~416 MB (0x19A00000)
- ~464 MB (0x1CA80000)
- ~640 MB (0x27100000)
- ~656 MB (0x28F40000)
- ~784 MB (0x2EE00000)

These correspond to resource entries in the TOC that should be classified as text-containing in Phase 2.

### BUSIN 1 Debug Labels (official terminology from English EXE)

```
System names:     TextEvent, MessageDataLoadClose, BattleField, ItemSystem, WallEvent
Font resources:   FCD_event_font, FCD_battle_font, FCD_event_frame
Resource types:   FCD_wallevent, FCD_haikai, FCD_effect_mnist, FCD_game_common_effect
Battle system:    FCD_battle_common_effect, FCD_battle_weapon, FCD_battle_result
Other:            FCD_death, FCD_notice_data
Stats:            STRENGTH, IQ, FAITH, STAMINA, QUICK, LUCK, FEELING
Classes:          FIG SAM PAR NIN THI PRI BIS MAG
Statuses:         SLEEP, POISON, PARALYZED, PETRIFIED, STAN, DEAD, SILENCE, CHAOS
Item categories:  FLAIL, STAFF, HANDAXE, KATANA, CHOP, STARS, STONE
Armor types:      ARMOR, HELMET, GLOVE, SHIELD
Equipment tiers:  WEAK, NORMAL, STRONG
Accessory types:  SCROLL, CHARM, RING, BOOTS, MANTLE, RIBBON, SPECIAL
```

---

## Appendix A: Script Inventory (all scripts to be created)

| Script | Phase | Purpose |
|--------|-------|---------|
| `tools/extract_packdata.py` | 1 | Extract 2,881 resources from PACKDATA.DIG |
| `tools/extract_packdata_raw.py` | 1 | Extract with sub-headers and padding (for rebuild) |
| `tools/classify_resources.py` | 2 | Scan resources for text, textures, audio, etc. |
| `tools/scan_sjis_regions.py` | 2 | Deep Shift-JIS text scanner |
| `tools/analyze_font_entry.py` | 3 | Analyze candidate font resources |
| `tools/dump_glyph_atlas.py` | 3 | Extract individual glyph images |
| `tools/build_glyph_table.py` | 3 | Build glyph-to-character mapping |
| `tools/extract_msg_text.py` | 4 | Parse MSG-format resources |
| `tools/extract_table_text.py` | 4 | Extract Shift-JIS from data tables |
| `tools/extract_exe_strings.py` | 4 | Extract EXE strings (extends existing scan_exe_strings.py) |
| `tools/build_glossary.py` | 5 | Parse English guide into structured glossary |
| `tools/match_translations.py` | 5 | Auto-match Japanese text to English translations |
| `tools/translation_editor.py` | 5 | CLI editor for reviewing translations |
| `tools/encode_msg.py` | 6 | Encode English text as MSG glyph streams |
| `tools/patch_tables.py` | 6 | Patch data table strings |
| `tools/patch_exe_strings.py` | 6 | Patch EXE strings |
| `tools/generate_font_atlas.py` | 7 | Generate English font atlas image |
| `tools/convert_font_to_ps2.py` | 7 | Convert font to PS2 texture format |
| `tools/build_width_table.py` | 7 | Generate VWF width table |
| `tools/patch_exe_font.py` | 7 | EXE patches for VWF support (conditional) |
| `tools/rebuild_packdata.py` | 8 | Rebuild PACKDATA.DIG |
| `tools/rebuild_iso.py` | 8 | Rebuild PS2 ISO |
| `tools/create_patch.py` | 8 | Generate xdelta patch |

---

## Appendix B: Directory Structure (target)

```
wizardrytranslation/
  extracted/                    # Original ISO contents
    PACKDATA.DIG
    SLPM_653.78
    BSN2_0.DSI
    TEMP1.LZH
    ...
  extracted/packdata_resources/ # Phase 1 output (2,881 files)
    0000_type01.bin
    0001_type01.bin
    ...
    manifest.json
  extracted/packdata_raw/       # Phase 1 output (with sub-headers)
    0000_type01.raw
    ...
  extracted_busin1/             # BUSIN 1 reference
    IMAGE/EVENT/*.MSG
    IMAGE/EVENT/*.EVE
    SLUS_202.59
    ...
  data/                         # Translation data
    glyph_table.json            # Phase 3: glyph index -> Japanese character
    english_glyph_table.json    # Phase 7: ASCII character -> glyph index
    glossary.json               # Phase 5: structured game terminology
    extracted_text/             # Phase 4 output
      all_messages.json
      msg_NNNN.json
      tables_NNNN.json
      exe_strings.json
    translation_draft.json      # Phase 5: auto-matched translations
    translation_final.json      # Phase 5: reviewed translations
  build/                        # Build output
    packdata_resources/         # Modified resource files
    font_atlas.png              # English font atlas (preview)
    font_atlas_ps2.bin          # English font atlas (PS2 format)
    font_widths.bin             # VWF width table
    PACKDATA.DIG                # Rebuilt archive
    SLPM_653.78                 # Patched EXE
    BUSIN0_EN.iso               # Rebuilt ISO
  release/                      # Final deliverables
    busin0_english_v1.0.xdelta  # Patch file
    README.txt                  # Patch instructions
  tools/                        # All Python scripts
    extract_packdata.py
    classify_resources.py
    ...
  dumps/                        # Analysis output (existing)
    resource_classification.json
    font_analysis_detailed.txt
    sjis_text_dump.txt
    ...
  runs/                         # Run logs (existing)
```
