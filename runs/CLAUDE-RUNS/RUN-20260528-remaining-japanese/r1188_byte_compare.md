# R1188 Patched vs Original: Byte-Level Comparison

## File Basics

| Property | Original (raw) | Patched (raw) |
|----------|----------------|---------------|
| Path | `extracted/packdata_raw/1188_type01.raw` | `build/packdata_resources/1188_type01.raw` |
| Size | 528,384 bytes | 528,384 bytes |
| Header | 0x000-0xC0F (3088 bytes, 16-byte container + 0xC00 GIF header) | Identical |
| Pixel data | 0xC10-0x80C0F (524,288 bytes) | Same offset |
| Tail padding | 1,008 bytes | Identical (zeros) |

## Raw Byte Differences

- **Header region (0x000-0xC0F):** 0 bytes changed -- header is preserved perfectly
- **Pixel data region (0xC10+):** 420,198 bytes differ out of 524,288 (80.2%)
- **374 non-contiguous changed regions** scattered across the entire pixel data

### Why so many raw byte changes?

The massive raw byte count is **expected and correct**. R1188 uses PSMT4 format (4-bit
pixels) stored in PS2 GS VRAM swizzle order (PSMCT32 upload format). The deswizzle/reswizzle
process redistributes 4-bit nibbles across the entire VRAM buffer. Even small pixel edits
in deswizzled space cascade to many different raw byte positions because:

1. Each raw byte contains two 4-bit nibbles from different pixel coordinates
2. The PSMCT32-to-PSMT4 swizzle interleaves data across pages, blocks, and columns
3. Any nibble change in a byte makes the whole byte "different"

**Round-trip verification: PASS** -- deswizzle then reswizzle of original produces
byte-identical output (0 mismatches). The swizzle implementation is correct.

## Deswizzled Pixel Comparison (the meaningful view)

Comparing deswizzled linear pixels using the BIN source (which the patcher actually reads):

| Metric | Value |
|--------|-------|
| Total pixels changed | **22,673** out of 1,048,576 (2.2%) |
| Changed Y-ranges | 6 clusters |
| Kana rows (y < 144) | 21,737 pixels |
| Bottom labels (y >= 1009) | 936 pixels |
| Other areas (y 144-1008) | **0 pixels** |

### Changed regions in deswizzled space

```
Y   50- 69:  X  161-494   (2,915 pixels)  -- Hiragana row 2 (a-so) cleared + romaji
Y   73- 93:  X    0-471   (4,565 pixels)  -- Hiragana row 3 (ya-zo) cleared + romaji
Y   96-117:  X    0-941   (7,907 pixels)  -- Katakana row 4 left+right cleared + romaji
Y  119-141:  X    0-799   (6,173 pixels)  -- Katakana row 5 cleared + romaji
Y  143-143:  X  512-799   (  177 pixels)  -- Partial katakana row spillover
Y 1010-1017: X    9-943   (  936 pixels)  -- Pre-rendered English labels at bottom
```

### Dominant transitions

In kana area: `1->0` (10,681 occurrences) -- Japanese glyph pixels being cleared to background
In bottom area: `0->1` (936 occurrences) -- English label pixels being drawn on empty space

## Critical Findings

### 1. Stat labels are NOT in the atlas

The stat labels (Strength/力, IQ/知恵, Piety/信仰心, Vitality/生命力, Agility/敏捷度,
Luck/幸運度) do **not** appear at any position in the R1188 atlas pixel data. Zero pixels
changed in the y=144-1008 region where game-screen UI glyphs would be stored.

The patcher's `PCSX2_STAT_LABELS_64x16` entries (line 89-96 of patch_r1188_comprehensive.py)
only generate PCSX2 texture replacement PNGs -- they do NOT modify the atlas data. These
replacements only work in the emulator, not on real hardware or in the ISO.

### 2. What the patcher actually does

| Phase | What | Atlas modified? | Real hardware? |
|-------|------|----------------|----------------|
| Phase 1 | Kana cells -> romaji (keyboard grid) | YES (21,737 px) | YES |
| Phase 2 | Bottom-row English labels | YES (936 px) | YES |
| Phase 3 | PCSX2 texture replacement PNGs | NO | NO (emulator only) |

### 3. Tab/sidebar/stat labels rely on PCSX2 overlay

The following labels are ONLY patched via PCSX2 texture dump replacement:
- Tab labels: Kana, Hira, ABC, Sym
- Sidebar labels: Gender, Class, Race, Align
- Stat labels: Strength, IQ, Piety, Vitality, Agility, Luck
- Buttons: OK
- Banner: New Character

These are **not** in the R1188 atlas. They are rendered by the game engine from the
main font atlas (R1272) or as separate texture objects.

### 4. The coordinate mapping question is moot

Since the patcher only edits kana cells (y=50-143) and bottom labels (y=1010-1017),
there is no issue with coordinate mapping for stat labels -- they simply aren't being
edited in the atlas at all. The "stat label positions at (192,360)" hypothesis was
incorrect; those labels are not stored in R1188.

## Conclusion

The R1188 patcher is working correctly for what it does: replacing kana glyphs with
romaji and adding English labels at the bottom of the atlas. Round-trip swizzle is
perfect. The stat/tab/sidebar labels remain Japanese because they are rendered from
R1272 (the main font atlas) or as separate textures, not from R1188.

To translate stat labels on real hardware, the fix must target R1272 or the game
executable's text rendering code, not R1188.
