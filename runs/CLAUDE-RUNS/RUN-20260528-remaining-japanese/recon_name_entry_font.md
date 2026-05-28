# Recon: Name Entry Screen Bitmap Font (R1188 / R1189)

## Summary

R1188 (type01, 527,360 bytes) is the name entry screen's full UI texture atlas (1024x1024 PSMT4).
R1189 (type02, 65,760 bytes) is a secondary 512x256 PSMT4 texture (likely the character grid font or overlay).
The tab labels (katakana, hiragana, alphanumeric, symbols, confirm, male names, female names) use glyph IDs 6400-6412 which are pre-rendered bitmap glyphs baked into R1188's texture atlas -- not composed from individual font characters.

---

## R1188 (Resource ID 1188, TOC ID 0x04A4, type01)

### Binary Format
- **Total size:** 527,360 bytes
- **Header:** 16 bytes at 0x000 (uint32 count=17, uint32 count=17)
- **GS Setup:** 17 identical 0x50-byte GIFtag+A+D blocks at 0x010-0x55F
  - Each block: GIFtag (NLOOP=4, PACKED, A+D) + 4 register writes:
    - CLAMP_1 = 0x05 (clamp UV)
    - MIPTBP1_1 = 0x0080001000020000
    - TEX1_1 = 0x00 (bilinear off)
    - TEX0_1: TBP0=0, TBW=16, PSM=PSMT4, **1024x1024**, CLD=1
- **Sprite Metadata:** 17 x 20-byte entries at 0x560-0x6B3 (IDs 1-16 + extra ID 9)
  - Format: 8-byte marker (0000 FFFFFFFF) + uint16 entry_id + uint16 flags(0x0101) + uint32 pad + uint16 w(1024) + uint16 h(1024)
- **UV/Rect Table:** 17 x 16-byte records at 0x6B4-0x7C3
  - Record 0 (header): total_hdr_size=332, atlas=512x256, data_at=2048
  - Records 1-16: offsets at stride 48 (316, 364, 412, ..., 1036), each 8x2 pixels
- **Zero Padding:** 0x7C4-0x83F
- **Additional Metadata:** 0x840-0xBFF (sprite positioning / rendering data)
- **Pixel Data:** 0xC00-end = 524,288 bytes = exactly 1024x1024 PSMT4

### Atlas Contents
The 1024x1024 texture contains ALL name entry UI graphics:
- Tab labels: katakana, hiragana, alphanumeric, symbols, confirm, male/female names
- Button backgrounds, borders, cursor, selection highlights
- The ornate border/frame around the character grid
- Title bar "shinki touroku" (new registration)
- Instruction text at top
- All rendered at various sizes, pre-composited

### PSMT4 Swizzling
Standard PS2 GS PSMT4 memory layout applies:
- Page: 128x128 pixels = 8192 bytes
- Block: 32x16 pixels = 256 bytes
- Column: 32x4 pixels = 64 bytes
- Full deswizzle needed for correct rendering (paged render shows rough layout but within-page scrambling)

---

## R1189 (Resource ID 1189, TOC ID 0x04A5, type02)

### Binary Format
- **Total size:** 65,760 bytes
- **Type02 Header:** 16 bytes at 0x000 (count=1, offset=0x58, flags=0x010100, pad=0)
- **Sub-header:** 16 bytes at 0x010 (val=1, val=2, pad=0)
- **GS Setup Block:** 0x020-0x06F (same structure as R1188 but TEX0 differs)
  - TEX0: TBP0=0, TBW=8, PSM=PSMT4, **512x256**, CLD=1
- **Image Descriptor:** 0x070-0x09F (width/height metadata)
- **CLUT Palette:** 0x0A0-0x0DF (64 bytes, 16 colors RGBA)
  - Color 0-7: near-white with moderate alpha (0xBF)
  - Color 8-15: various colors (pinkish/bluish tones) -- these are for the character grid font rendering
- **Pixel Data:** 0x0E0-end = 65,536 bytes = exactly 512x256 PSMT4

### Atlas Contents
The 512x256 texture contains the **character grid glyphs** used on the name entry keyboard:
- Hiragana syllabary
- Katakana syllabary
- Latin alphabet (A-Z, a-z)
- Numbers (0-9)
- Special symbols/punctuation
- The actual characters that appear in the selection grid

---

## EXE References to Glyph IDs 6400+

### Glyph ID Table (EXE file offset 0x3C9DA0, vaddr 0x4C9D20)

The name entry screen glyph table is at EXE file offset 0x3C9D60, structured as:

```
Offset    Content
0x3C9D60  Control IDs: [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 114]
          (13 entries -- grid navigation/control codes for cursor, backspace, etc.)

0x3C9DA0  Tab label glyph IDs (group 1): [6400, 6401, 6402, 6403, 6404]
          Separated by 0xFFFFFFFF padding from next group
0x3C9DEC  Tab label glyph IDs (group 2): [6405, 6406, 6407, 6408, 6409]
0x3C9E18  Tab label glyph IDs (group 3): [6410, 6411, 6412]
          Total: 13 glyph IDs in range 0x1900-0x190C

0x3C9E50  Additional glyph IDs (range 0x1A00): [6656-6668] (13 entries)
0x3C9F00  Additional glyph IDs (range 0x1B00): [6912-6923] (12 entries)
```

### Mapping to Tab Labels

Based on the screenshot and table structure (5 + 5 + 3 grouping, 7 labels):
- **Group 1 (6400-6404):** katakana, hiragana, alphanumeric, symbols -- 4 tabs on the right side
  - Likely: 6400=katakana, 6401=hiragana, 6402=alphanumeric, 6403=symbols, 6404=possibly "name entry" mode label
- **Group 2 (6405-6409):** Variants or states of the above (highlighted/selected versions?)
- **Group 3 (6410-6412):** confirm, male names, female names
- **Ranges 0x1A00 and 0x1B00:** Likely additional UI elements (text prompts, status indicators)

### Code References

The glyph table at vaddr 0x4C9D20 is referenced from **7 nearly identical code blocks** at:
- vaddr 0x2FB094 (file 0x1FB114)
- vaddr 0x2FB130 (file 0x1FB1B0)
- vaddr 0x2FB1E4 (file 0x1FB264)
- vaddr 0x2FB294 (file 0x1FB314)
- vaddr 0x2FB354 (file 0x1FB3D4)
- vaddr 0x2FB404 (file 0x1FB484)
- vaddr 0x2FB4C4 (file 0x1FB544)

Each reference follows the same MIPS pattern:
```mips
lui   r3, 0x004D          # load upper bits of table address
addiu r3, r3, 0x9D20      # form full address 0x4C9D20
sll   r4, r4, 4           # index * 16 stride
addu  r3, r3, r4          # r3 = &table[index]
lw    r4, 0(r3)           # load glyph ID
```

The table start (0x3C9D60) is also referenced at:
- vaddr 0x2F268C (file 0x1F270C) -- navigation/control code setup
- vaddr 0x2FAFC0 (file 0x1FB040) -- initialization

### Character Grid Table (EXE offset 0x3C9C00)

Before the glyph table, at offset 0x3C9C00, there's a **packed character grid** with 77 entries.
Each 32-bit entry packs two 16-bit glyph IDs (low=one character, high=another):
- These map to the kana/latin character grids shown in the name entry keyboard
- Three columns of entries correspond to the three character sets (katakana, hiragana, alpha/symbols)

---

## PCSX2 Texture Dumps

### Relevant dumps found:
- **r24x24 textures** (20+ dumps): Individual glyph renders at 24x24 -- possibly character grid cells
- **r48x20 textures**: Small button/tab elements
- **r96x36 textures**: Button backgrounds (rounded rectangle shape)
- **r64x64 textures**: Spell effect / UI element sprites
- **r216x24 textures**: Dialogue text strips (not name entry related)
- **r10x16 textures**: Small individual character renders

No direct 1024x1024 or 512x256 dump matching R1188/R1189 was found in the dump set -- the name entry screen may not have been visited during the dump session.

---

## Replacement Strategy

### Option A: Texture Editing (Recommended)
**Replace the pre-rendered tab labels directly in R1188's pixel data.**

1. **Extract and deswizzle** R1188's 1024x1024 PSMT4 texture
2. **Locate the tab label regions** using the UV/rect table at 0x6B4:
   - 16 sprite rectangles at stride-48 offsets (316, 364, 412... 1036)
   - Each region is small (8x2 in the rect table, but actual rendered size may differ)
3. **Render English labels** at matching pixel dimensions:
   - "Kana" / "ABC" / "Sym" / "OK" / "M Name" / "F Name"
   - Or abbreviated: "Kata" / "Hira" / "Alpha" / "Sym" / "Done" / "M" / "F"
4. **Re-swizzle and inject** the modified texture back into PACKDATA.DIG

**Pros:** Direct visual replacement, no code changes needed.
**Cons:** PSMT4 deswizzle/reswizzle complexity; need to locate exact pixel regions in the scrambled data; font rendering must match the game's aesthetic.

### Option B: Glyph ID Remapping (Alternative)
**Change the glyph IDs in the EXE table from 6400+ to standard font atlas glyph IDs.**

1. **Patch EXE table at 0x3C9DA0:** Replace glyph IDs 6400-6412 with IDs from the main R1272 font atlas that spell out English equivalents
2. **Problem:** The main font atlas has individual 12x12 glyphs; the tab labels are pre-rendered at larger sizes. Remapping would show tiny characters unless the rendering code also handles sizing.
3. **Would also need** to change the code at 0x2FB094-0x2FB4C4 if the rendering path for glyph IDs 6400+ differs from standard glyphs.

**Pros:** Simple binary patch, no texture editing needed.
**Cons:** Size mismatch (12x12 glyphs vs. larger tab labels), may look wrong.

### Option C: Hybrid Approach
**Render English text into R1189's 512x256 atlas and adjust glyph IDs.**

If R1189 contains the name entry character grid font, and the tab labels pull from a specific region of this atlas, then:
1. Modify R1189 to include English tab label glyphs in the appropriate atlas positions
2. The glyph ID mapping in the EXE would still point to the same IDs, which now show English text

### Recommended Path Forward

**Option A (texture editing of R1188)** is the most reliable approach:
1. Capture the name entry screen in PCSX2 with texture replacement debugging enabled to identify the exact texture regions
2. Use PCSX2's texture dump feature while on the name entry screen to get the deswizzled texture
3. Edit the deswizzled texture with English labels
4. Re-import using a PSMT4 reswizzle tool

**Key unknowns to resolve:**
- Exact pixel locations of each tab label within the 1024x1024 atlas (need proper deswizzle or PCSX2 dump)
- Whether the GS setup in R1188's header needs updating for modified content
- Whether the 17 GS blocks at 0x010-0x55F correspond to the 17 sprite metadata entries (likely animation frames or tab states)
- Relationship between glyph IDs 6400-6412 and the UV rect table

---

## File Locations

| Item | Path |
|------|------|
| R1188 extracted | `extracted/packdata_resources/1188_type01.bin` |
| R1189 extracted | `extracted/packdata_resources/1189_type02.bin` |
| R1272 main font | `extracted/packdata_resources/1272_type01.bin` |
| Game EXE | `extracted/SLPM_653.78` |
| Name entry screenshots | `NameEntryEuropean.png`, `NameEntryHiraganamode.png` |
| Font analysis tools | `tools/analyze_font_entry.py`, `tools/find_font_data.py` |
| Rendered atlas dumps | `dumps/name_entry_font/r1188_paged_inv_1024x1024.png`, etc. |
| PCSX2 texture dumps | `build/pcsx2_dumps/` (411 files) |

## EXE Patch Points Summary

| Address (file) | Address (vaddr) | Content | Purpose |
|----------------|-----------------|---------|---------|
| 0x3C9DA0 | 0x4C9D20 | uint32[5]: 6400-6404 | Tab label glyph IDs group 1 |
| 0x3C9DEC | 0x4C9D6C | uint32[5]: 6405-6409 | Tab label glyph IDs group 2 |
| 0x3C9E18 | 0x4C9D98 | uint32[3]: 6410-6412 | Tab label glyph IDs group 3 |
| 0x3C9D60 | 0x4C9CE0 | uint32[13]: ctrl IDs | Grid navigation control codes |
| 0x3C9C00 | 0x4C9B80 | packed uint16 pairs x77 | Character grid layout |
| 0x1FB114 | 0x2FB094 | MIPS code | First of 7 references to glyph table |
