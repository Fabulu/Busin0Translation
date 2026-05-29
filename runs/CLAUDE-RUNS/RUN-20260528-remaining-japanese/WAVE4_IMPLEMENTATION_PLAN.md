# Wave 4 Implementation Plan

**Date**: 2026-05-28
**Author**: Architect agent
**Baseline**: Build v12+ (12,863 dialogue messages, R39 equipment, EXE patches)

---

## Overview

Three remaining tasks, in priority order:

| # | Task | Impact | Difficulty | Est. Time |
|---|------|--------|------------|-----------|
| W4-A | Font atlas tile replacement for menu buttons | HIGH (every menu screen) | MEDIUM | 3-4 hours |
| W4-B | Translate 46 remaining MSG dialogue resources | HIGH (dungeon events) | LOW (bulk) | 4-6 hours |
| W4-C | Name entry R1188 tab labels | LOW (cosmetic) | HARD | 2-3 hours |

---

## W4-A: Font Atlas Tile Replacement for Menu Buttons

### Problem

Menu buttons in the EXE use 56-byte structs (at file offset 0x3C3000-0x3C46F8). Each struct references exactly 2 glyph IDs from the R1272 font atlas. These glyph IDs (range 683-866) currently contain Japanese kanji bitmaps. To translate menus, we must replace those 12x12 pixel tiles in the font atlas with English text rendered as bitmaps.

The EXE struct format is fixed: it can only hold 2 glyph ID slots per button. We cannot add more characters. We must render the English word split across those 2 tiles (e.g., "tav" on tile 1, "ern" on tile 2).

### Architecture

```
data/menu_labels.csv          -- translation table (already exists, 106 records)
        |
        v
tools/render_menu_tiles.py    -- NEW: renders English text into 12x12 PSMT4 tiles
        |
        v
tools/generate_font_atlas.py  -- MODIFIED: also stamps menu tiles into glyph slots 683-866
        |
        v
build/english_font_atlas.bin  -- existing output (192-byte header + 65536 pixels + 64 palette)
        |
        v
build_v9.py Step 1            -- v2 pipeline injects atlas into R1272 (already works)
```

### Data Flow

1. `menu_labels.csv` has columns: `id, exe_offset, glyph_id_1, glyph_id_2, japanese, context, english, strategy`
2. For each non-skip row, split `english` into two halves for the two tiles
3. Render each half as a 12x12 pixel bitmap (4-bit indexed, palette index 0 = opaque text, 15 = transparent background)
4. Write the pixels into the correct positions in the 256x512 atlas

### Step-by-Step Implementation

#### File to create: `tools/render_menu_tiles.py`

```python
#!/usr/bin/env python3
"""
Render English menu labels into 12x12 font atlas tiles.

Reads data/menu_labels.csv and produces a dict of {glyph_id: pixel_data}
where pixel_data is a 144-byte array (12x12, one byte per pixel, values 0-15).

Palette convention (matching existing atlas):
  0  = fully opaque (glyph foreground / text color)
  15 = fully transparent (background)
"""
import csv
import os
import sys

from PIL import Image, ImageFont, ImageDraw

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CELL_W, CELL_H = 12, 12
CSV_PATH = os.path.join(BASE, "data", "menu_labels.csv")


def find_font():
    """Find a narrow pixel font suitable for 12x12 cells."""
    # At ~4px per character we can fit 3 chars per 12px tile
    # Consolas at size 9-10 works well; fallback to arial or default
    candidates = [
        ("C:/Windows/Fonts/consola.ttf", 9),
        ("C:/Windows/Fonts/arial.ttf", 9),
        ("C:/Windows/Fonts/cour.ttf", 9),
    ]
    for path, size in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def split_label(english: str, strategy: str) -> tuple:
    """Split an English label into (tile1_text, tile2_text).

    For 'abbrev' labels (<= 4 chars), the whole word goes on tile 1.
    For 'tile_pair' labels, the word is split roughly in half.
    """
    if strategy == "skip":
        return ("", "")
    if strategy == "abbrev" or len(english) <= 3:
        return (english, "")

    # Split at midpoint, preferring consonant clusters
    mid = len(english) // 2
    # Try to find a good split point (after a vowel, before a consonant)
    best = mid
    for offset in range(0, min(3, mid)):
        for candidate in [mid + offset, mid - offset]:
            if 0 < candidate < len(english):
                # Good split: after vowel or at syllable boundary
                best = candidate
                break
    return (english[:best], english[best:])


def render_tile(text: str, font) -> list:
    """Render text into a 12x12 pixel array.

    Returns list of 144 ints (0=opaque text, 15=transparent).
    Text is vertically centered and left-aligned within the cell.
    """
    pixels = [15] * (CELL_W * CELL_H)  # start fully transparent
    if not text:
        return pixels

    img = Image.new("L", (CELL_W, CELL_H), 0)  # black background
    draw = ImageDraw.Draw(img)

    bbox = font.getbbox(text)
    if not bbox:
        return pixels

    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    # Left-align, vertically center
    ox = -bbox[0]  # flush left
    oy = max(0, (CELL_H - th) // 2) - bbox[1]
    draw.text((ox, oy), text, fill=255, font=font)

    # Convert: white (255) = opaque (0), black (0) = transparent (15)
    raw = list(img.getdata())
    for i, val in enumerate(raw):
        pixels[i] = 15 - min(val * 15 // 255, 15)

    return pixels


def load_menu_tiles() -> dict:
    """Load CSV and render all menu tiles.

    Returns {glyph_id: [144 pixel values]} for all non-skip entries.
    """
    font = find_font()
    tiles = {}

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            strategy = row["strategy"].strip()
            if strategy == "skip":
                continue
            glyph_id_1 = int(row["glyph_id_1"])
            glyph_id_2 = int(row["glyph_id_2"])
            english = row["english"].strip()

            tile1_text, tile2_text = split_label(english, strategy)
            tiles[glyph_id_1] = render_tile(tile1_text, font)
            tiles[glyph_id_2] = render_tile(tile2_text, font)

    return tiles


if __name__ == "__main__":
    tiles = load_menu_tiles()
    print(f"Rendered {len(tiles)} menu tiles from {CSV_PATH}")
    # Debug: show a few
    for gid in sorted(tiles.keys())[:5]:
        non_bg = sum(1 for p in tiles[gid] if p != 15)
        print(f"  Glyph {gid}: {non_bg} foreground pixels")
```

#### File to modify: `tools/generate_font_atlas.py`

Add the following after the existing character rendering loop (after line ~66, before the "Convert to game's 4bpp format" section):

```python
# ---- MENU TILE INJECTION ----
# Render English menu labels into glyph slots 683-866
try:
    from render_menu_tiles import load_menu_tiles
    menu_tiles = load_menu_tiles()
    for glyph_id, tile_pixels in menu_tiles.items():
        col = glyph_id % COLS  # COLS = 21
        row = glyph_id // COLS
        x0 = col * CELL_W
        y0 = row * CELL_H
        if x0 + CELL_W > ATLAS_W or y0 + CELL_H > ATLAS_H:
            continue
        # Write pixels into the grayscale atlas image
        for dy in range(CELL_H):
            for dx in range(CELL_W):
                # tile_pixels uses game convention: 0=opaque, 15=transparent
                # atlas image uses: 0=black(bg), 255=white(char)
                game_val = tile_pixels[dy * CELL_W + dx]
                img_val = (15 - game_val) * 17  # 0->255, 15->0
                atlas.putpixel((x0 + dx, y0 + dy), img_val)
    print(f"  Injected {len(menu_tiles)} menu tiles into atlas")
except ImportError:
    print("  WARNING: render_menu_tiles not found, skipping menu tiles")
# ---- END MENU TILE INJECTION ----
```

**CRITICAL**: The existing `generate_font_atlas.py` does NOT use `psmt4_deswizzle.py` for swizzling. It writes pixels in a "linear page layout" (line 95-108). This is WRONG for the game -- the game expects PSMCT32-swizzled upload data. However, it has been working for the existing English characters (IDs 0-94), which means either:
- The v2 pipeline's Step 3 handles swizzle separately, OR
- The game accepts this format for some reason

**Action**: The implementer MUST verify by examining the existing `build/english_font_atlas.bin` output. If the current linear-page approach works in-game for existing characters, use the same approach for menu tiles. If not, replace the 4bpp conversion section with proper `swizzle_psmt4()` from `tools/psmt4_deswizzle.py`.

#### Verification checklist

1. Run `python tools/generate_font_atlas.py` -- should produce `build/english_font_atlas.bin` (65,792 bytes) and `build/english_font_atlas_preview.png`
2. Open `build/english_font_atlas_preview.png` -- visually confirm that:
   - ASCII characters (a-z, 0-9, symbols) are in rows 0-4 (glyph IDs 0-94)
   - Menu labels appear in rows 32-41 (glyph IDs 683-866)
   - Labels read correctly when two adjacent tiles are viewed side-by-side
3. Run `python build/build_v9.py` -- full build
4. Test in PCSX2: navigate to town hub, check that menu buttons show English labels

#### Known constraints

- Only **lowercase a-z** in the current atlas font. Menu labels in `menu_labels.csv` are already lowercase.
- Each tile is 12x12 pixels. At ~4px per character (Consolas 9pt), each tile fits 2-3 characters. Total label: 4-6 chars.
- Some labels in the CSV may need shortening if they overflow. The implementer should visually inspect each rendered tile.

#### Files involved

| File | Action | Path |
|------|--------|------|
| menu_labels.csv | READ (source of truth) | `data/menu_labels.csv` |
| render_menu_tiles.py | CREATE | `tools/render_menu_tiles.py` |
| generate_font_atlas.py | MODIFY (add menu tile injection) | `tools/generate_font_atlas.py` |
| psmt4_deswizzle.py | READ (may need swizzle_psmt4) | `tools/psmt4_deswizzle.py` |
| english_font_atlas.bin | OUTPUT (rebuilt) | `build/english_font_atlas.bin` |
| build_v9.py | NO CHANGE (already injects R1272) | `build/build_v9.py` |

---

## W4-B: Translate 46 Remaining MSG Dialogue Resources

### Problem

46 MSG-format type-02 resources remain untranslated. These are dungeon events, system text, and data tables. The existing pipeline (`build_v9.py` Step 4) already handles type-02 injection via auto-glob of `data/type2_translated/batch_*.json`. The work is purely translation + glyph mapping.

### Resource Priority

**Tier 1 -- Dungeon Events (29 resources, ~1,073 dialogue groups)**:
R680, R684, R686, R694, R698, R714, R716, R718, R730, R738, R754, R760, R776, R778, R802, R812, R822, R824, R826, R832, R834, R836, R842, R846, R854, R858, R890, R909, R911

**Tier 2 -- Large System Text (3 resources, ~1,360 groups)**:
R1067 (580 groups), R1095 (256 groups), R1103 (524 groups)

**Tier 3 -- Remaining (14 resources, ~1,341 groups)**:
R1054, R1055, R1358-R1362, R1365-R1367, R2158, R2217, R2218, R2219

### Workflow: Extract -> Translate -> Inject

#### Step 1: Extract all 46 resources

Use the existing extraction approach. For each resource, decode the glyph stream and produce a JSON file with Japanese text and empty English fields.

**File to create**: `tools/extract_untranslated.py`

```python
#!/usr/bin/env python3
"""
Extract untranslated MSG resources into batch JSON files for translation.

For each resource:
  1. Read the .raw file from extracted/packdata_raw/
  2. Parse FFFF-delimited glyph groups in the Section 2 stream
  3. Decode each glyph via msg_glyph_map.json
  4. Output JSON with {resource, msg_index, japanese, english: ""}

Usage:
    python tools/extract_untranslated.py
    # Outputs: data/type2_translated/batch_untrans_tierN.json
"""
import struct
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE, "extracted", "packdata_raw")
OUT_DIR = os.path.join(BASE, "data", "type2_translated")
GLYPH_MAP_PATH = os.path.join(BASE, "data", "msg_glyph_map.json")

# Load glyph map: {glyph_id_str: character}
glyph_map = json.load(open(GLYPH_MAP_PATH, encoding="utf-8"))
# Invert if needed (the map is {char: id} or {id_str: char})
# Check format:
sample_key = next(iter(glyph_map))
if sample_key.isdigit() or (len(sample_key) > 1 and sample_key[0].isdigit()):
    id_to_char = {int(k): v for k, v in glyph_map.items()}
else:
    id_to_char = {v: k for k, v in glyph_map.items()}


def parse_msg_groups(raw_data: bytes) -> list:
    """Parse FFFF-delimited glyph groups from a type-02 raw resource.

    Returns list of lists of glyph IDs (one list per group).
    """
    # Sub-header: 16 bytes (u32 x 4)
    if len(raw_data) < 16:
        return []
    payload_size = struct.unpack_from("<I", raw_data, 4)[0]

    # Find Section 2 glyph stream start
    # Section 1 is an offset table terminated by FFFF
    # The glyph stream starts after the offset table
    pos = 16
    # Skip Section 1 offset table entries (each is a LE u16)
    while pos + 2 <= len(raw_data):
        val = struct.unpack_from(">H", raw_data, pos)[0]
        if val == 0xFFFF:
            pos += 2
            break
        pos += 2

    # Now parse glyph groups (FFFF-delimited)
    groups = []
    current = []
    while pos + 2 <= len(raw_data):
        val = struct.unpack_from(">H", raw_data, pos)[0]
        pos += 2
        if val == 0xFFFF:
            if current:
                groups.append(current)
            current = []
        else:
            current.append(val)

    return groups


def decode_group(glyphs: list) -> str:
    """Decode a glyph list to a Japanese string."""
    chars = []
    for g in glyphs:
        if g == 0xFFFE:
            chars.append(" / ")  # line break marker
        elif 0xFB00 <= g <= 0xFBFF:
            chars.append(f"[FB:{g & 0xFF:02X}]")  # speaker tag
        elif 0xFFD0 <= g <= 0xFFD9:
            pass  # spacing control, skip
        elif g in id_to_char:
            chars.append(id_to_char[g])
        else:
            chars.append(f"[{g:04X}]")
    return "".join(chars)


TIER1 = [680, 684, 686, 694, 698, 714, 716, 718, 730, 738, 754, 760,
         776, 778, 802, 812, 822, 824, 826, 832, 834, 836, 842, 846,
         854, 858, 890, 909, 911]

TIER2 = [1067, 1095, 1103]

TIER3 = [1054, 1055, 1358, 1359, 1360, 1361, 1362, 1365, 1366, 1367,
         2158, 2217, 2218, 2219]


def extract_tier(resource_ids: list, tier_name: str):
    entries = []
    for r_id in resource_ids:
        raw_path = os.path.join(RAW_DIR, f"{r_id:04d}_type02.raw")
        if not os.path.isfile(raw_path):
            print(f"  WARNING: {raw_path} not found, skipping R{r_id}")
            continue
        raw_data = open(raw_path, "rb").read()
        groups = parse_msg_groups(raw_data)
        for mi, glyphs in enumerate(groups):
            japanese = decode_group(glyphs)
            entries.append({
                "resource": r_id,
                "msg_index": mi,
                "japanese": japanese,
                "english": ""
            })
        print(f"  R{r_id}: {len(groups)} groups extracted")

    out_path = os.path.join(OUT_DIR, f"batch_untrans_{tier_name}.json")
    json.dump(entries, open(out_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"  -> {out_path}: {len(entries)} entries")
    return entries


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    print("=== Extracting Tier 1 (dungeon events) ===")
    extract_tier(TIER1, "tier1")
    print("\n=== Extracting Tier 2 (large system text) ===")
    extract_tier(TIER2, "tier2")
    print("\n=== Extracting Tier 3 (remaining) ===")
    extract_tier(TIER3, "tier3")
```

#### Step 2: Translate

The translation agent should:

1. For each entry in the batch JSON, translate `japanese` to `english`.
2. Use `data/guide_full_text.txt` (Diablo1_reborn's 577-page guide) as the primary reference for context, proper nouns, and canonical terminology.
3. Use Busin 1 (Tale of the Forsaken Land) canonical terms: Kingdom of Duhan, Karman's Labyrinth, Fighter/Thief/Mage/Priest/Ninja/Samurai/Bishop, Bergran von Buren, Aurora, Automata, Spell Stones.
4. Respect the 18-char-per-line limit (current engine constraint). Use ` / ` to separate lines within a single dialogue group.
5. Mark non-text entries with `[DATA]`, `[BINARY]`, or `[LAYOUT]` prefix -- the pipeline skips these.

**Important**: Entries where `japanese` contains mostly `[XXXX]` unmapped glyphs need glyph mapping first. The translation agent should identify these and add them to `data/msg_glyph_map.json` using context clues from surrounding known characters and the guide.

#### Step 3: Inject (already handled)

Once batch files are populated with English text and saved to `data/type2_translated/`, the existing `build_v9.py` Step 4 auto-discovers them via `glob('data/type2_translated/batch_*.json')`. No pipeline changes needed.

#### Verification

1. After filling in translations, run `python build/build_v9.py`
2. The build log should show the new batch files being loaded and the increased resource count
3. Test in PCSX2: visit dungeon areas, trigger events, check dialogue

#### Files involved

| File | Action | Path |
|------|--------|------|
| extract_untranslated.py | CREATE | `tools/extract_untranslated.py` |
| batch_untrans_tier1.json | CREATE (then fill translations) | `data/type2_translated/batch_untrans_tier1.json` |
| batch_untrans_tier2.json | CREATE (then fill translations) | `data/type2_translated/batch_untrans_tier2.json` |
| batch_untrans_tier3.json | CREATE (then fill translations) | `data/type2_translated/batch_untrans_tier3.json` |
| msg_glyph_map.json | MODIFY (add unmapped glyphs) | `data/msg_glyph_map.json` |
| guide_full_text.txt | READ (reference) | `data/guide_full_text.txt` |
| build_v9.py | NO CHANGE | `build/build_v9.py` |

#### Parallelization strategy

The three tiers are independent. Three translation agents can work simultaneously:
- Agent A: Tier 1 (29 dungeon resources)
- Agent B: Tier 2 (3 large system resources -- R1067, R1095, R1103)
- Agent C: Tier 3 (14 smaller resources)

Each agent extracts, translates, and commits its batch file independently.

---

## W4-C: Name Entry R1188 Tab Labels (Optional)

### Problem

The character name entry screen has tab labels (kana, kana, alphanumeric, symbols, confirm, male names, female names) rendered as glyphs from the R1188/R1189 PSMT4 atlas. These use glyph IDs 6400+ with a custom bitmap format.

### Why this is lower priority

- The grid already has A-Z, a-z, 0-9 from R1189 using regular font glyph IDs
- Players CAN enter English names currently
- Only the tab labels at the top remain in Japanese
- This is cosmetic -- functional name entry works

### Approach (if pursued)

1. **Deswizzle R1188** using `psmt4_deswizzle.py` with parameters: width=1024, height=1024, header_size=2048, clut_size=2048 (already supported via `--test-r1188` flag)
2. **Identify tab label positions** in the deswizzled image -- look for the Japanese text blocks
3. **Overwrite with English labels** ("KANA", "kana", "A-Z", "SYMB", "OK", "MALE", "FEMALE") using the same pixel font
4. **Reswizzle** using `swizzle_psmt4()` and rebuild the raw resource
5. **Inject into PACKDATA** via the existing resource replacement mechanism

### Technical details

- R1188 raw file: `extracted/packdata_raw/1188_type01.raw` (527,360 bytes)
- Format: 2048-byte header + 524,288 pixel bytes (1024x1024 PSMT4) + 2048-byte CLUT
- The 7 tab labels correspond to EXE glyph IDs 6400-6412 at file offset 0x3C9DA0
- Runtime resolution: function at VA 0x494050 looks up BSS table at VA 0x4EBBEC

### Blockers

- Need PCSX2 texture dump during name entry screen to identify exact pixel positions of tab labels in the deswizzled atlas
- The R1188 resource structure has conflicting interpretations from recon agents (GS draw commands vs PSMT4 atlas) -- need definitive verification

### Files involved

| File | Action | Path |
|------|--------|------|
| 1188_type01.raw | READ + MODIFY | `extracted/packdata_raw/1188_type01.raw` |
| psmt4_deswizzle.py | USE (deswizzle + reswizzle) | `tools/psmt4_deswizzle.py` |
| patch_name_entry.py | CREATE | `tools/patch_name_entry.py` |
| build_v9.py | MODIFY (add Step 2.5 for R1188 injection) | `build/build_v9.py` |

---

## Build Pipeline Integration Summary

The final build pipeline order after all W4 tasks:

```
Step 1:  v2 pipeline (type-1 resources + R1272 font atlas injection)
         -- generate_font_atlas.py now includes menu tiles at IDs 683-866
Step 2:  Fix type-1 FFFF mismatches (R34, R35, R2124, R2654)
Step 2.5: [OPTIONAL] R1188 name entry atlas injection
Step 3:  R39 type-15 injection
Step 4:  Variable-size type-2 injection + Section 1 patching
         -- now auto-loads batch_untrans_tier{1,2,3}.json
Step 5:  R1193 manual inject
Step 6:  Merge and clean
Step 7:  Rebuild PACKDATA.DIG
Step 8:  Build ISO
Step 8.4: Patch EXE
Step 8.5: Inject patched EXE into ISO
```

No changes to `build_v9.py` are needed for W4-A or W4-B. Both feed into the existing pipeline through their respective input files (`build/english_font_atlas.bin` for menu tiles, `data/type2_translated/batch_*.json` for dialogue).

---

## Execution Order

1. **W4-A first** -- menu labels are the most visible remaining Japanese. One agent can complete this in a single session.
2. **W4-B in parallel** -- start the extraction script, then hand off batch files to translation agents. This can run alongside W4-A since they modify different files.
3. **W4-C last** -- only if W4-A and W4-B are complete and there is time remaining.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Font atlas swizzle format mismatch | MEDIUM | HIGH | Verify existing `english_font_atlas.bin` works in-game first. If the current linear-page approach is wrong, replace with proper `swizzle_psmt4()`. |
| Menu label text overflow (>3 chars per tile) | LOW | LOW | Menu labels in CSV are already vetted for length. Adjust splits if preview shows overflow. |
| Unmapped glyphs in dungeon dialogue | MEDIUM | MEDIUM | Use context inference + guide crossref (95%+ coverage already achieved for mapped resources). |
| R1188 format uncertainty | HIGH | LOW | This task is optional. Skip if format cannot be verified from PCSX2 dumps. |
| 18-char line limit causes truncation in new translations | MEDIUM | MEDIUM | Pre-wrap all translations at 18 chars with ` / ` separators. This is the same approach used for existing 12,863 messages. |

---

## Quick Reference: Key File Paths

```
C:/Programmieren/wizardrytranslation/
  data/
    menu_labels.csv                    -- menu button translation table
    english_glyph_table.json           -- ASCII char -> glyph ID (0-94)
    msg_glyph_map.json                 -- glyph ID -> Japanese char (1100+ entries)
    guide_full_text.txt                -- 577-page game guide reference
    type2_translated/
      batch_*.json                     -- all type-2 translations (auto-globbed)
  tools/
    generate_font_atlas.py             -- builds english_font_atlas.bin
    psmt4_deswizzle.py                 -- PSMT4 deswizzle/swizzle (round-trip verified)
    render_menu_tiles.py               -- NEW: renders menu label bitmaps
    extract_untranslated.py            -- NEW: extracts untranslated resources to JSON
  build/
    build_v9.py                        -- main build pipeline
    build_full_english_v2.py           -- v2 sub-pipeline (type-1 + font atlas)
    inject_r39_v2.py                   -- R39 equipment injector
    patch_exe.py                       -- EXE binary patcher
    rebuild_packdata.py                -- PACKDATA.DIG rebuilder
    english_font_atlas.bin             -- generated font atlas (65,792 bytes)
    BUSIN0_EN_v9.iso                   -- output ISO
  extracted/
    packdata_raw/                      -- original resources (.raw, with 16-byte sub-header)
    packdata_resources/                -- original resources (.bin, without sub-header)
    SLPM_653.78                        -- original EXE
```
