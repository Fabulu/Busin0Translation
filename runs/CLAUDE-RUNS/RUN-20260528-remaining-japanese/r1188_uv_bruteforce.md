# R1188 UV Metadata Brute-Force Analysis

**Date**: 2026-05-28

---

## CRITICAL FINDING: Previous Analysis Was Wrong

The previous analysis (in `r1188_sprite_metadata.md`) claimed:

- VA 0x494350 = "render_bitmap_glyph" function
- BSS table at 0x4EB100 = per-group glyph UV lookup table
- R1188 offset 0xA60-0xBFF = "per-glyph rendering metadata (UV data, dimensions)"

**All of these are WRONG.** The function at 0x494350 is an event/animation system,
not a glyph renderer. The "BSS table" at 0x4DB100 (note: address was wrong too)
contains event/scene identifiers like "KYO_01", "EV01_01", "ARD_01" -- not glyph
UV coordinates. The R1188 0xA60-0xBFF region is NOT per-glyph UV metadata.

---

## What We Verified

### EXE Event Table (NOT Glyph UV)

The table at VA 0x4DB100 has 32 groups, each 8 bytes:

```
Group[g]:
  +0: uint32 texpage/type_id (0-9)
  +4: uint32 pointer to entry array
```

Each entry array contains 8-byte records:

```
Entry[i]:
  byte[0]: column index (0-2)
  byte[1]: row index (60-105)
  byte[2]: size/type (always 0x64 = 100)
  byte[3]: flag (0 or 1)
  bytes[4-7]: pointer to ASCII name string (e.g., "EV01_01", "ARD_01", "KYO_01")
```

This is clearly an event/animation system, not a glyph rendering system.

### Function at 0x494350

```c
// NOT render_bitmap_glyph -- actually triggers events/animations
void trigger_event(uint16 event_id) {
    if (!check_loaded(event_id)) return;
    
    uint8 group = event_id >> 8;
    uint8 index = event_id & 0xFF;
    
    uint32 type = *(uint32*)(0x4DB100 + group*8);     // type/texpage
    uint32 base = *(uint32*)(0x4DB104 + group*8);      // entry array pointer
    
    uint8* entry = base + index * 8;
    uint8 col = entry[0];       // column
    uint8 row = entry[1];       // row  
    uint8 flags = entry[2];     // flags (0x64)
    
    uint32 packed = col | (row << 8) | (type << 16);
    call_handler(packed, flags);   // VA 0x474D30
}
```

---

## R1188 Header Structure (Corrected)

| Offset Range  | Size    | Content |
|---------------|---------|---------|
| 0x000-0x00F   | 16B     | Container header: `{0, 527360, 16, 0}` |
| 0x010-0x01F   | 16B     | Sub-resource counts: `{17, 17, 0, 0}` |
| 0x020-0x56F   | 0x550   | 17 GIF A+D packets (80 bytes each) -- GS texture setup |
| 0x570-0x6B3   | 0x144   | 17 sprite descriptors (20 bytes each) + 1 duplicate |
| 0x6B4-0x6C3   | 16B     | Duplicate descriptor (ID 9 repeated) |
| 0x6C4-0x6D7   | 20B     | Sub-sprite table header |
| 0x6D8-0x7D7   | 0x100   | 16 sub-sprite offset entries (16 bytes each) |
| 0x7D8-0x83F   | 0x68    | Zero padding |
| 0x840-0xBFF   | 0x3C0   | **UNIDENTIFIED** -- 960 bytes, NOT CLUTs, NOT UV data |
| 0xC00-0x80BFF | 524,288B| PSMT4 pixel data (1024x1024 @ 4bpp) |
| 0x80C00-0x80FFF| 1,024B | CLUT region (4 non-zero PSMCT16 entries at start) |

---

## Brute-Force Analysis of 0x840-0xBFF (960 bytes)

### Data Structure Pattern

The 960 bytes are organized in 9 non-zero groups separated by zero padding:

| Group | File Offset | Size | 8-byte entries |
|-------|-------------|------|----------------|
| 0 | 0x0850-0x086F | 32B | 4 |
| 1 | 0x0890-0x090F | 128B | 16 |
| 2 | 0x0930-0x096F | 64B | 8 |
| 3 | 0x0990-0xA00F | 128B | 16 |
| 4 | 0x0A30-0x0A7F | 80B | 10 |
| 5 | 0x0A90-0x0B0F | 128B | 16 |
| 6 | 0x0B30-0x0B6F | 64B | 8 |
| 7 | 0x0B90-0x0BCF | 64B | 8 |
| 8 | 0x0BF0-0x0BFF | 16B | 2 |

Total non-zero data: 704 bytes (88 eight-byte entries).
Zero padding between groups: 256 bytes total.

### Interpretations Tested

#### a. 8-byte stride: U(1), V(1), flags(2), pad(4) -- FAILED

52 entries over 416 bytes. Values don't map to valid atlas positions.
U values include 0, 8, 16, 49, 128, 240 -- no consistent grid pattern.
V values include 0, 1, 14, 15, 16, 48, 240 -- chaotic distribution.

#### b. 4-byte stride: U(1), V(1), W(1), H(1) -- FAILED

104 entries over 416 bytes. No clean coordinate patterns.
Many values >128 which exceeds reasonable glyph dimensions.

#### c. GS UV 10.4 fixed point (uint32 LE, U[13:0], V[29:16]) -- FAILED

Pixel values include 256, 512, 768, 771 -- some plausible, but many exceed
the 1024x1024 atlas (e.g., 1536, 3600, 4335). No consistent 24-pixel grid alignment.

#### d. uint16 LE pairs -- FAILED

Values are too large and irregular for any coordinate interpretation.
Examples: 4096, 12337, 57344, 61440.

#### e. uint16 Big-Endian pairs -- PARTIALLY INTERESTING

Some early values (17, 24, 15, 10) resemble glyph advance widths,
but subsequent values (225, 241, 88, 233, 4137, 24601) break the pattern.

#### f. GIF tag interpretation -- FAILED

NLOOP values (264, 4096, 6912, 4352) are unreasonably large.
No valid GIF tag structure detected.

#### g. PSMCT16 CLUT interpretation -- FAILED

Decoded as 16-color CLUTs, the colors are not grayscale (expected for a
font atlas) and show chaotic R/G/B values with no sensible pattern.

#### h. Nibble-packed data -- NOT TESTED CONCLUSIVELY

Data could potentially be 4-bit packed, but no clear structure emerged.

### Cross-Group Correlation

The three 128-byte groups (1, 3, 5) at offsets 0x890, 0x990, 0xA90 were compared:
- No byte-shift or nibble-shift relationship found
- Each group has different data patterns
- Sub-block analysis (4x32-byte) shows no consistent positional structure

### Density Map

```
0x0840: ..####....######
0x08C0: ##########....##
0x0940: ######....######
0x09C0: ##########....##
0x0A40: ########..######
0x0AC0: ##########....##
0x0B40: ######....######
0x0BC0: ##....##
```

(Each character = 8 bytes, `.` = zero, `#` = data)

---

## What the 0x840-0xBFF Data Might Be

Since it is NOT:
- Per-glyph UV coordinates (those would be in the EXE or computed at runtime)
- CLUT palettes (the real CLUT is at 0x80C00)
- GIF tags or GS register packets
- Direct pixel data

Possible remaining interpretations:
1. **Pre-computed GS sprite display lists** for fixed UI elements
2. **Animation keyframe data** for texture/sprite transitions
3. **VIF/DMA chain fragments** that control texture upload sequences
4. **Compressed coordinate data** using a game-specific encoding
5. **The data may simply be unused padding** or legacy data from development

---

## Implications for Translation

The fact that per-glyph UV data is NOT in R1188 means:

1. The game computes atlas-to-pixel mapping through a different code path
   (not the 0x494350 function previously identified)
2. To change which glyph is drawn for a given character code, we need to
   find the ACTUAL text rendering function (separate from this event system)
3. The 0x840-0xBFF region can likely be ignored for translation purposes
4. The real glyph UV system needs to be found by tracing the MSG text
   rendering code path, not the event/animation system

### Next Steps

1. Find the actual text rendering function by searching for code that:
   - Reads MSG glyph indices (the 0x00XX values from type-2 messages)
   - Computes pixel coordinates from atlas grid position
   - Issues GS sprite draw commands
2. The text rendering path likely uses TEX0 TBP0 offsets and simple
   arithmetic (cell_x * 24, cell_y * 24) rather than a lookup table
3. The R1188 atlas can be modified directly (replace Japanese glyphs
   with English ones in the pixel data) without touching the header
