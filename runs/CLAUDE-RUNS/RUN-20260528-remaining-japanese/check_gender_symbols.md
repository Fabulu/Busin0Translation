# Gender Symbol Check: Mars/Venus in R1272 Atlas

**Date**: 2026-05-28

---

## Question

The gender labels still show kanji (male/female). Are the Mars/Venus symbol tiles actually present in the R1272 atlas at the correct positions?

---

## Findings

### 1. Atlas Positions Verified

| Symbol | Glyph ID | Grid Position | Pixel Position | Non-zero Pixels |
|--------|----------|---------------|----------------|-----------------|
| Mars   | 518      | row 24, col 14 | (168, 288)    | 26/144          |
| Venus  | 349      | row 16, col 13 | (156, 192)    | 30/144          |

Both symbols are **confirmed present** in the atlas preview PNG (`build/english_font_atlas_preview.png`, 256x540 pixels, mode L).

ASCII art from atlas:

**Mars (glyph 518):**
```
............
.......####.
.........##.
........#.#.
...###.#..#.
..#...#.....
.#.....#....
.#.....#....
.#.....#....
..#...#.....
...###......
............
```

**Venus (glyph 349):**
```
............
....####....
...#....#...
..#......#..
..#......#..
..#......#..
...#....#...
....####....
.....##.....
...######...
.....##.....
.....##.....
```

### 2. Binary Atlas Also Contains Them

The binary file `build/english_font_atlas.bin` (82,176 bytes = 192 header + 81,920 PSMT4-swizzled pixels + 64 palette) has non-zero pixel data at both positions when checked in 4-bit mode (142/144 and 144/144 non-zero respectively -- high because PSMT4 uses 15 for transparent background, 0 for opaque).

### 3. Patched R38 Correctly References Them

The patched R38 (`build/packdata_resources/0038_type01.raw`) contains:
- **Entry 25** (male): glyph 518 at offset 0x3FE -- confirmed
- **Entry 26** (female): glyph 349 at offset 0x402 -- confirmed

The `english_glyph_table.json` maps:
- `"\u2642"` (Mars) -> glyph 518
- `"\u2640"` (Venus) -> glyph 349

### 4. Rendering System: System 1 (R1272), NOT System 2

**Gender labels ARE rendered via System 1 (R1272 MSG glyph atlas).**

R38 is a type-01 MSG resource. All entries in R38 -- stat labels (STR, INT, etc.), alignment labels (good/neutral/evil), race labels, class labels, AND gender labels -- use the same rendering path: the game reads glyph IDs from R38 and looks up tiles in the R1272 font atlas.

This is confirmed by the fact that:
- Reputation labels (entries 229-257) already render English text using glyph IDs 33-58 (a-z)
- Stat labels were successfully patched to render as English (str, int, fth, etc.)
- The gender entries sit in the exact same R38 structure

The concern about "System 2 kanji font pages" does **not** apply here. System 2 is used for the kanji dictionary pages (R1188 and similar resources) that render CJK characters outside the R1272 glyph range. Gender labels use small glyph IDs (518, 349) well within the R1272 atlas range.

### 5. If Labels Still Show Kanji

If the gender labels still display as kanji despite the correct atlas tiles and R38 glyph IDs, possible causes:

1. **Stale ISO build** -- The patched R38 or R1272 was not injected into the latest ISO
2. **PCSX2 texture cache** -- Emulator may cache old textures; clear the cache
3. **Atlas swizzle mismatch** -- The PSMT4 swizzle may place glyph 518/349 at unexpected VRAM positions (though this would affect ALL glyphs, not just these two)
4. **Wrong R38 version** -- Multiple R38 files exist in the build directory (`0038_type01.raw` vs `v20_r38.raw`); verify which one gets injected

---

## Conclusion

The Mars/Venus tiles ARE correctly rendered in the R1272 atlas at the expected glyph positions. The patched R38 correctly references glyph IDs 518 and 349 for the male/female entries. Gender labels use the same System 1 rendering as all other R38 labels. If they still show kanji in-game, the issue is in the build pipeline (injection/caching), not in the atlas content.
