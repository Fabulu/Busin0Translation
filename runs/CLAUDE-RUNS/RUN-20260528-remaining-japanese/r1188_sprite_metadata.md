# R1188 Sprite Metadata: Full Decode

**Date**: 2026-05-28

---

## Critical Finding: Tab Labels Are NOT Pre-Composed Bitmaps

The R1188 atlas (1024x1024 PSMT4) is a **character grid containing individual glyphs**,
NOT pre-rendered multi-character tab labels. The tab labels visible in PCSX2 dumps
(e.g., "性別" at 48x20, "力" at 64x16) are **composed at runtime** by the EXE drawing
individual characters from R1188 side by side.

Evidence:
- Visual inspection of the deswizzled atlas (`R1188_CORRECT_dbw512.png`) shows only
  individual characters arranged in a grid: digits, letters, hiragana, katakana, kanji
- No multi-character pre-composed labels exist anywhere in the 1024x1024 atlas
- NCC pattern matching of PCSX2 48x20 tab dumps against the atlas found zero matches
- The PCSX2 captures are the result of sequential GS sprite draw calls, each drawing
  one character, which PCSX2 captures as a combined source texture region

---

## R1188 Header Structure (0x000-0xBFF)

| Offset Range  | Size    | Content |
|---------------|---------|---------|
| 0x000-0x00F   | 16B     | Container header: `{0, 527360, 16, 0}` (pad, total_size, sub_count=16, pad) |
| 0x010-0x55F   | 0x550   | 17 GIF A+D blocks (0x50=80 bytes each), all with TEX0=0 (patched at runtime) |
| 0x560-0x6B3   | 0x154   | 18 sprite descriptor entries (20 bytes each) - see below |
| 0x6B4-0x7C3   | 0x110   | 18 index/offset records (16 bytes each) - CLUT pointers, not UV data |
| 0x7C4-0x83F   | 0x7C    | Zero padding |
| 0x840-0xA5F   | 0x220   | 17 PSMCT16 CLUTs (32 bytes = 16 colors x 2 bytes each) |
| 0xA60-0xBFF   | 0x1A0   | Per-glyph rendering metadata (UV data, dimensions) - 416 bytes |
| 0xC00-end     | 524,288B| 1024x1024 PSMT4 pixel data |

### Sprite Descriptor (20 bytes each, 18 entries at 0x560)

```
struct sprite_descriptor {
    uint32 marker;        // 0x00000000 or padding
    uint32 sentinel;      // 0xFFFFFFFF  
    uint16 entry_id;      // 0-16 (one duplicate: ID 9 appears twice)
    uint16 flags;         // 0x0101 (always)
    uint32 padding;       // 0x00000000
    uint16 atlas_w;       // 0x0400 = 1024 (full atlas width in pixels)
    uint16 atlas_h;       // 0x0400 = 1024 (full atlas height)
};
```

All 18 entries reference the full 1024x1024 atlas. These are sub-texture definitions
that pair with the 17 different CLUTs (each sub-texture uses a different CLUT for
different visual states: normal, highlighted, selected, etc.).

### Index/Offset Records (16 bytes each, 18 entries at 0x6B4)

Entry 0 is a header: `{total=332, 0, atlas_w=512, atlas_h=256, data_offset=2048}`.
Entries 1-17 contain file-internal offsets to the GIF A+D blocks (stride 48):
316, 364, 412, 460, 508, 556, 604, 652, 700, 748, 796, 844, 892, 940, 988, 1036.
These are NOT UV coordinates; they are pointers into the header structure.

### CLUT Palettes (32 bytes each, 17 CLUTs at 0x840)

PSMCT16 format: each color is 2 bytes, `ABBBBBGGGGGRRRRR` (1+5+5+5 bits).
The 17 CLUTs provide different color mappings for the same pixel indices:
- CLUTs for normal/hover/selected tab states
- CLUTs for different UI element types (buttons, backgrounds, text)
- All CLUTs are NON-grayscale (complex color values, not simple index ramps)

---

## Glyph ID Resolution (EXE Code Analysis)

### VA 0x494350: render_bitmap_glyph(glyph_id)

```c
void render_bitmap_glyph(uint16 glyph_id) {
    if (!check_glyph_loaded(glyph_id)) return NULL;
    
    uint8 group = glyph_id >> 8;     // 0x19 = 25 for tab labels
    uint8 index = glyph_id & 0xFF;   // 0x00-0x0C for each label char
    
    // BSS table at 0x4EB100: stride 8 per group
    uint32 texpage = *(uint32*)(0x4EB100 + group*8);  
    uint32 uv_base = *(uint32*)(0x4EB104 + group*8);  // pointer to UV array
    
    // Per-glyph UV data: 8 bytes per glyph
    uint8* glyph_data = uv_base + index * 8;
    uint8 U = glyph_data[0];     // U coordinate (0-255)
    uint8 V = glyph_data[1];     // V coordinate (0-255)
    uint8 flags = glyph_data[2]; // rendering flags
    
    // Pack and draw
    uint32 packed = U | (V << 8) | (texpage << 16);
    gs_draw_sprite(packed, flags);  // VA 0x474D30
}
```

Key points:
- U,V are byte values (0-255) within a **256x256 sub-atlas window**
- `texpage` selects which 256x256 region of VRAM to read from
- The sub-atlas window is created by the EXE setting TEX0 with TBW=4, TW=8, TH=8
  and a specific TBP0 offset within R1188's VRAM footprint

### Tab Label Glyph IDs (EXE Table 2E at file 0x3C9DA0)

| Glyph ID | Group:Index | Japanese Label | English | PCSX2 Size |
|----------|-------------|----------------|---------|------------|
| 6400     | 0x19:0x00   | カナ            | Kana    | Part of 48x20 composite |
| 6401     | 0x19:0x01   | かな            | Hira    | Part of 48x20 composite |
| 6402     | 0x19:0x02   | 英数            | ABC     | Part of 48x20 composite |
| 6403     | 0x19:0x03   | 記号            | Sym     | Part of 48x20 composite |
| 6404     | 0x19:0x04   | (unused?)       | --      | -- |
| 6405     | 0x19:0x05   | 決定            | OK      | Part of 48x20 composite |
| 6406     | 0x19:0x06   | 男名            | M.Name  | Part of 48x20 composite |
| 6407     | 0x19:0x07   | 女名            | F.Name  | Part of 48x20 composite |
| 6408     | 0x19:0x08   | 1文字消す       | Delete  | Wider composite |
| 6409     | 0x19:0x09   | 全消去          | Clear   | Wider composite |
| 6410-12  | 0x19:0x0A-C | Extra labels   | TBD     | -- |

Each glyph ID resolves to a SINGLE character in the atlas. The "48x20" PCSX2
captures span 2-3 adjacent character cells because the game draws them sequentially.

---

## VRAM Geometry: 1024x1024 vs 256x256

The R1188 pixel data is uploaded as 1024x1024 PSMT4 (TBW=16, via PSMCT32 at DBW=512).
But for rendering, the game reconfigures TEX0 to read with:
- TBW=4 (256 pixels per row)
- TW=8, TH=8 (256x256 texture window)
- TBP0 = base + offset (selects one of 16 possible 256x256 sub-regions)

The mapping between 256x256 sub-regions (TBW=4) and 1024x1024 positions (TBW=16):

| Sub-Region | TBP0 Offset | 1024x1024 Pages | Pixel Area |
|-----------|-------------|-----------------|------------|
| 0 | +0    | (0,0)(1,0)(2,0)(3,0) | x=0-511, y=0-127 |
| 1 | +128  | (4,0)(5,0)(6,0)(7,0) | x=512-1023, y=0-127 |
| 2 | +256  | (0,1)(1,1)(2,1)(3,1) | x=0-511, y=128-255 |
| 3 | +384  | (4,1)(5,1)(6,1)(7,1) | x=512-1023, y=128-255 |
| ... | ... | ... | ... |
| 15 | +1920 | (4,7)(5,7)(6,7)(7,7) | x=512-1023, y=896-1023 |

**IMPORTANT**: The pixel mapping within each page is NOT a simple spatial rearrangement.
The PSMT4 block/column swizzle tables produce a complex reordering within each 128x128
page when TBW changes. The sub-region tiles extracted with TBW=4 appear "scrambled"
relative to the TBW=16 deswizzled atlas.

---

## Character Grid Layout in Deswizzled Atlas

The 1024x1024 atlas contains a character grid visible in `R1188_CORRECT_dbw512.png`:

| Row Range | Content |
|-----------|---------|
| y=0-23    | Digits 0-9, punctuation :;<=>?, space, A B C D E F G H I |
| y=24-47   | (C) a-s, symbols, arrows, XOX |
| y=48-71   | Hiragana: あいうえおかきくけこさしすせ... |
| y=72-95   | More hiragana: やゆよらりるれろわをん, voiced: がぎぐげご... |
| y=96-119  | Katakana: アイウエオカキクケコサシスセソタチ... |
| y=120-143 | More katakana: ラリルレロワヲン, voiced: ガギグゲゴザジズゼゾ... |
| y=144-167 | Kanji row 1: ヴ引何岸宮去橋険故向行今次者人静騒達渡悲負 |
| y=168-191 | Kanji row 2: 街楽換歓関期気客強近金掲軽迎見言限後交困差 |
| y=192-215 | Kanji row 3: 紹上乗場常情信盛前相他台大段男知置柱調鉄店 |
| y=216-239 | Kanji row 4: 頻理立連脇長髪成告落容薬味物美転跳帯先女書 |
| y=240-263 | Kanji row 5: 念命拾様生最**記**憶**力**存在感薄会忘顔天才不**幸**横 |
| y=264-287 | Kanji row 6: 騎許景肩光広刻国査罪司士始子思紙至視床草触 |
| y=288-311 | More kanji rows continuing... |
| ... | ... |
| x=496-511 | 16-pixel vertical gap |
| x=512-1023 | Right half: more characters (letters, katakana variants, kanji) |

Cell dimensions: approximately 24x24 pixels per character, ~21 columns on the left
half (x=0-495) and similar on the right half (x=512-1023).

---

## Approach for English Translation

### Option A: Edit individual character glyphs in the atlas (RECOMMENDED)

Since tab labels are composed from individual characters, we need to:
1. Identify which character positions in the 1024x1024 grid correspond to each
   glyph ID used by the tab labels (6400+)
2. The character grid is shared with the keyboard display -- modifying a character
   affects both the keyboard grid AND any tab label that uses it
3. For latin letters: the atlas already contains A-Z, a-z at rows 0-47
4. For tab labels: we can't change "性" to "G" without affecting the keyboard grid

### Option B: Redirect UV coordinates in BSS (BEST)

1. Find unused character positions in the atlas grid
2. Render English label characters at those positions (one char per cell)
3. Patch the per-glyph UV data (U,V bytes at BSS 0x4EB104+group*8 -> base+index*8)
   to point to the new character positions
4. This requires either: patching the R1188 header data at 0xA60-0xBFF that populates
   BSS, OR patching the EXE code that populates BSS

### Option C: Replace glyph IDs in Table 2E with existing latin glyph IDs

1. The atlas already has A-Z, a-z at known grid positions
2. If we can find the glyph IDs for those existing latin characters, we can replace
   the entries in Table 2E (file 0x3C9DA0) to draw "O K" instead of "決定"
3. This requires: mapping atlas grid positions to glyph IDs

### Option D: EXE code patch to render text strings instead of bitmap glyphs

Replace the single `jal 0x494350` call at VA 0x2FB0B0 with a custom routine that:
1. Checks if the glyph ID is in the tab label range (0x1900-0x190C)
2. If so, renders a multi-character English string using the main text renderer
3. This is the most flexible but requires the most EXE code space

---

## Per-Glyph UV Data Location

The per-glyph UV data that feeds BSS[0x4EB104] is stored in R1188 at offset 0xA60-0xBFF
(416 bytes). This data is loaded by the texture management system (VA 0x493930 state
machine) and copied into BSS tables when R1188 is acquired.

The exact structure of the 0xA60-0xBFF data is not fully decoded. It contains:
- Per-glyph U,V byte coordinates for each glyph group
- Glyph dimensions or stride info
- Possibly multiple tables for different groups (25-36, 114)

To fully map glyph IDs to pixel positions, you would need to either:
1. Run R1188 through PCSX2 with memory breakpoints on BSS 0x4EB100-0x4EB1FF
2. Or trace the state machine at VA 0x4939C0 through all its states to understand
   how it parses the 0xA60-0xBFF data

---

## Key Files

| Item | Path |
|------|------|
| R1188 raw | `extracted/packdata_raw/1188_type01.raw` |
| Deswizzled atlas | `build/textures_to_edit/R1188_CORRECT_dbw512.png` |
| PCSX2 tab dumps | `build/pcsx2_dumps/*3cb39bf7659ef15f*r48x20*` |
| PCSX2 stat dumps | `build/pcsx2_dumps/*3cb39bf7659ef15f*r64x16*` |
| EXE glyph table | EXE file offset 0x3C9DA0 (VA 0x4C9D20), Table 2E |
| EXE group table | EXE file offset 0x3C9D60 (VA 0x4C9CE0), groups 25-36,114 |
| Glyph renderer | EXE VA 0x494350 (file 0x3943D0) |
| GS draw sprite | EXE VA 0x474D30 |
| BSS glyph UV table | VA 0x4EB100 (runtime, stride 8 per group) |
| BSS glyph group table | VA 0x4EBBE0-0x4EBBEC (runtime, stride 16 per group) |
| R1188 UV data | R1188 file offset 0xA60-0xBFF (416 bytes, parsed at load time) |
| Tab label caller | EXE VA 0x2FB094 (file 0x1FB114) |
| R1188 loader init | EXE VA 0x2FAFD0 -> calls 0x493F20 to register groups |
