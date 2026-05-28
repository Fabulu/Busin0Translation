# Recon 18: MOJI (Font/Character) File Analysis

**Date:** 2026-05-22
**Status:** Complete
**Files analyzed:**
- `IMAGE/BATTLE/EFFECT/MOJI.MDT` (2,208 bytes)
- `IMAGE/BATTLE/EFFECT/MOJI.TMZ` (1,440 bytes)
- `IMAGE/BATTLE/EFFECT/MOJI1.MDT` (2,064 bytes)
- `IMAGE/BATTLE/EFFECT/MOJI1.TMZ` (1,440 bytes)
- `IMAGE/COCKPIT/BAR/BAR_00.TMX` (33,344 bytes) -- comparison
- `IMAGE/COCKPIT/GUILD/GUILD_00.TMX` (33,344 bytes) -- comparison

---

## Critical Finding: MOJI Files Are NOT the Main Font

Despite "MOJI" meaning "character/letter" in Japanese, these files are **battle effect sprites** (damage numbers, status text overlays), NOT the main game font used for dialogue/menus. Evidence:

1. Located under `IMAGE/BATTLE/EFFECT/` alongside `KIRARI.TMZ` (sparkle), `SWORD.TMZ`, `THUN.TMZ` (thunder), `WA_WA.TMZ` -- all battle visual effects
2. MDT files contain 3D vertex data (floating-point XYZ coordinates) for rendering billboard sprites in the 3D battle scene
3. The texture is tiny (1,440 bytes compressed) -- far too small for a full character set
4. The source texture is named `moji2.tim` -- likely just numbers 0-9 and a few status words ("MISS", "HIT", etc.)

The main game font (for dialogue, menus, item names) must be stored elsewhere.

---

## TMZ File Format

### Outer Container (Compression Wrapper)

```
Offset  Size  Value       Description
0x00    4     12 12 12 12  Magic/signature for compressed TMZ container
0x04    4     0x00000001   Unknown (version or count = 1)
0x08    4     0x00000020   Offset to data start (32 bytes)
0x0C    4     0x00000000   Padding
0x10    4     0x00000020   Duplicate offset or uncompressed offset
0x14-1F 12    zeros        Reserved
0x20    4     0x00000002   Number of images/sections
0x24    4     0x00000580   Data payload size (1,408 bytes)
```

### Inner TMX Texture (at offset 0x28)

The TMZ container wraps a **TMX** (not TMX0) texture format:

```
Offset  Size  Value       Description
0x28    4     "TMX\0"     TMX magic (note: NOT "TMX0")
0x2C    1     0x0A        Bits per pixel indicator? (could mean 4bpp indexed)
0x2D    1     0x02        Image type / format subtype
0x2E    2     0x0040      Width or buffer width (64)
0x30    2     0x0020      Width (32) or height
0x32    2     0x0014      Height (20) or format detail
0x34    4     0x000000B7  Data size or offset (183)
0x38    8     "USR REV\0" User/revision marker
0x40    10    "moji2.tim" Original source filename
```

### TMX vs TMX0 Format Difference

| Feature | TMZ inner (TMX) | BAR_00.TMX (TMX0) |
|---------|-----------------|---------------------|
| Magic | `TMX\0` (54 4D 58 00) | `TMX0` (54 4D 58 30) |
| Outer header | 0x28-byte wrapper with `12 12 12 12` magic | 8-byte header before TMX0 |
| Outer header bytes 0-7 | `02 00 00 00  40 82 00 00` (BAR) | `12 12 12 12  01 00 00 00` (TMZ) |
| Source filename | `moji2.tim` | `bar_00.tim` / `guild_00.tim` |
| Pixel data | Compressed (see below) | Uncompressed |

**BAR_00.TMX / GUILD_00.TMX outer header:**
```
0x00  02 00 00 00   -- Format version (2)
0x04  40 82 00 00   -- Total file size (0x8240 = 33,344 bytes)
0x08  "TMX0"        -- TMX version 0 magic
```

**TMX0 sub-header at offset 0x08:**
```
0x08  54 4D 58 30   "TMX0"
0x0C  00 00 00 00   Reserved
0x10  10 02 00 01   Format: 0x10=16bpp? 0x02=type, 0x00=?, 0x01=1 image
0x14  00 01         Width = 256
0x16  14 00         Height = 20 (or palette type)
```

### Palette Data (ABGR1555, 16-bit per entry)

Starting at offset 0x60 in TMZ, there are **10 palettes** of **16 colors** each (= 320 bytes, 4bpp indexed color). Palette entries use PS2 standard ABGR1555 format.

**Palette 0 (offset 0x60):** Grayscale ramp from black to white
```
[ 0] 0x0000  R= 0 G= 0 B= 0 A=0  (transparent black)
[ 1] 0x0441  R= 1 G= 2 B= 1 A=0
...
[15] 0x7FFF  R=31 G=31 B=31 A=0  (opaque white)
```

Each palette is a color ramp for different text colorations (e.g., normal damage, critical, healing, miss).

### Pixel Data (Compressed)

Starting at offset 0x1A0 (after 10 palettes), the remaining ~1,056 bytes contain **compressed pixel data**. The compression format appears to be a custom scheme (NOT standard LZ77/LZSS):

```
0x1A0: 00 10 11 00 00 00 00 00 00 00 00 00 00 00 00 00
0x1B0: 00 00 00 00 00 00 11 00 00 00 00 00 00 00 00 00
0x1C0: 00 42 13 01 ...
```

The data has a distinctive pattern: sparse early rows (mostly zeros = transparent), becoming denser, suggesting top-to-bottom scanline encoding of small glyph images. The heavy use of repeated `f3` bytes and `00` runs suggests a simple RLE or nibble-based compression.

### MOJI.TMZ and MOJI1.TMZ Are Identical

```
$ cmp MOJI.TMZ MOJI1.TMZ
(no output = files are byte-identical)
```

Both battle effect sets share the same texture atlas; only the MDT (geometry/animation) differs.

---

## MDT File Format (3D Model/Sprite Data)

The MDT files are **PS2 VU1 display list / 3D mesh data** for rendering textured quads in the battle scene. They are NOT font mapping tables.

### MDT Header (0x00-0x7F)

```
Offset  Size  Value       Description
0x00    4     0x00000001  Version or type
0x04    4     0x00000020  Header size or data offset
0x08    4     0x00000001  Number of meshes or objects
0x0C    4     0x00000010  Vertex stride or count (16)
0x10-1F 16    zeros       Reserved
0x20    4     0x00000000  Flags
0x24    4     0x00000090  Offset to geometry section (144)
0x28    4     0x00000000  Reserved
0x2C    4     0x00000820  Size of geometry data (MOJI: 2080 / MOJI1: 1936)
0x30-3F       floats      Transform matrix (identity-like: 1.0 values)
0x40-5F       floats      More transform/scale data
0x60-6F       flags/color  Color/blend settings (0xFFFF at 0x6A = white/full alpha)
0x78    4     0x00000860  Offset to secondary data
```

### Vertex Data (starts at ~0x80)

Contains floating-point vertex positions (XYZ + W) for textured quads:
- Each vertex is 16 bytes: X(float), Y(float), Z(float), W(float=1.0)
- Values like `0x41624630` = 14.15 (float), `0xC1A00000` = -20.0 (float)
- These define billboard rectangles positioned in 3D space around the battle camera

### UV Coordinate Data (starts at ~0x2C0 in MOJI.MDT)

After vertex positions, there are UV texture coordinates:
```
0x2E0: 00 ff 7e 3f  c2 c0 40 3c  bf be 3e 3f  fd fb 7b 3f
```
These are float pairs mapping vertices to texture atlas regions. Values range from ~0.0 to ~1.0, typical for normalized UV coordinates.

### Mesh/Strip Definitions (later in file)

The MDT contains multiple mesh sections with triangle strip indices:
```
0x790: 03 80 21 62  -- Tag: 0x21 triangles, 0x62 = 'b' (strip primitive?)
       1b 1a 19 19 1a 1b  -- Triangle strip vertex indices
       1b 1c 1a 1a 1c 1b  -- More strips
```

Vertex indices increment sequentially (0x00 through 0x27 = 40 vertices), consistent with a set of ~10 textured quads (damage numbers 0-9 plus status words).

### Tail Section (~0x830 in MOJI.MDT)

```
0x838: 00 00 00 11   -- Texture reference or state flags
0x844: 05 00 00 00   -- 5 animation frames or sub-objects
0x850: 01 00 49 00   -- MOJI: 0x49 = 73 items; MOJI1: 0x40 = 64 items
0x858: b6 03 04 6c   -- Display list command
0x860: 02 00 30 00   -- Render state
0x864: 90 04 00 00   -- Data offset (MOJI) / 00 04 00 00 (MOJI1)
0x874: 90 07 00 00   -- Data offset (MOJI) / 00 07 00 00 (MOJI1)
0x890: 30 00 00 00   -- MOJI: 0x30=48 / MOJI1: 0x31=49 (frame count?)
```

### Difference Between MOJI.MDT and MOJI1.MDT

- MOJI.MDT (2,208 bytes): 73 items, more vertex data, likely the main damage number set
- MOJI1.MDT (2,064 bytes): 64 items, uses a circle of vertices (trigonometric XY positions visible as sin/cos pairs), likely a radial/splash effect for damage display
- Both reference the same `moji2.tim` texture atlas

---

## TMX/TMX0 Format Summary (from BAR_00 / GUILD_00 comparison)

The TMX0 format used in `COCKPIT/` files is a standard **uncompressed PS2 TIM2-like texture**:

```
Outer header (8 bytes):
  0x00: uint32 format_version = 2
  0x04: uint32 total_file_size

TMX0 header (at offset 0x08):
  0x00: "TMX0" magic
  0x04: uint32 reserved = 0
  0x08: uint8  pixel_format (0x10 = 4bpp indexed?)
  0x09: uint8  type = 0x02
  0x0A: uint8  mipmaps = 0x00
  0x0B: uint8  image_count = 0x01
  0x0C: uint16 width (BAR: 256)
  0x0E: uint16 height_or_format
  0x10-0x1F: reserved/padding
  0x18: char[16] source_filename ("bar_00.tim")

Palette data follows header (multiple 16-color ABGR1555 CLUTs)
Pixel data follows palette
```

Both BAR_00.TMX and GUILD_00.TMX are 33,344 bytes and share identical palette structures in their first two CLUTs, suggesting they are UI element textures rendered with the same color scheme.

---

## Where Is the Main Game Font?

The MOJI files are battle-effect sprites (damage numbers), NOT the main font. The actual game font for dialogue, menus, and item text is likely:

1. **Embedded in the PS2 executable** (SLPM_653.78) -- common for Japanese PS2 games
2. **In a different texture file** not named "MOJI" -- possibly among the TMX files in `COCKPIT/` or another directory
3. **In PACKDATA.DIG** -- the main data archive might contain font textures not yet extracted
4. **Generated from a Shift-JIS character table** mapped to a large texture atlas (typical: 256x256 or 512x512 with 16x16 character cells = 256-1024 glyphs)

### Recommended Next Steps

- Search for larger TMX/TMZ files (>8KB) that could contain a full font atlas
- Examine the PS2 executable for embedded font data or font-loading code
- Look for files with names like `SYS_`, `MENU_`, `MSG_`, or `TEXT_` that might contain font resources
- Check if any TMX file contains a grid pattern consistent with a character atlas (e.g., 16 chars per row, 16 rows)

---

## File Format Quick Reference

| Extension | Full Name | Content | Compression |
|-----------|-----------|---------|-------------|
| `.TMX` | Texture Matrix eXtended | PS2 texture (TIM2 variant) | Uncompressed |
| `.TMZ` | Texture Matrix Zipped | PS2 texture (TIM2 variant) | Compressed (custom) |
| `.MDT` | Model DaTa | 3D mesh/sprite geometry | Uncompressed |

TMZ = TMX with compression wrapper. The `12 12 12 12` magic identifies the compressed container. Inside is a TMX texture with palette + compressed pixel data.
