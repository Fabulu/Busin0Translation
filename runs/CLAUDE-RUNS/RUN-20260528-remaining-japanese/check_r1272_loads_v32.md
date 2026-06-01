# R1272 Load Verification -- Save State 32-1

## Result: R1272 IS LOADED AND WORKING

The 67,584-byte R1272 (reverted to original size) loads correctly in build v32.

---

## Evidence

### 1. Screenshot Proof (definitive)
Save state `32-1.p2s` screenshot shows the name entry screen with:
- **"Enter your name."** rendered in English (our translated MSG text)
- Latin alphabet grid (A-Z, a-z) rendered from our English font atlas
- "Name" and "Level" labels visible in English
- "BABA" typed as character name

The English text could only render if R1272 (our font atlas) was successfully
loaded from PACKDATA and transferred to GS VRAM.

### 2. Translated MSG Data in EE RAM
Found `"Enter your name."` as 16-bit glyph indices at EE address `0x12B0F53`:
```
0x12b0f53: 25004e00540045005200000059004f00  (E.n.t.e.r. .y.o.)
0x12b0f63: 5500520000004e0041004d0045000eff  (u.r. .n.a.m.e...)
```
Immediately followed by `"Select Gender"` glyph indices at `0x12b0f73`:
```
0x12b0f73: 330045004c004500430054000000      (S.e.l.e.c.t. .)
0x12b0f83: 470045004e004400450052000effff    (G.e.n.d.e.r....)
```
This confirms the patched PACKDATA MSG resources are loaded.

### 3. R1272 File NOT in EE RAM (expected)
- R1272 raw file header (`00000000000101001000000000000000`) -- not found
- R1272 GS header / TEX0 value (`0x2000000661410000`) -- not found
- This is **normal PS2 behavior**: the game loaded R1272, sent the texture
  data to GS VRAM via DMA, then freed/reused the EE memory buffer.

### 4. VRAM Analysis
- GS VRAM (4 MB) contains active texture data across pages 64-495
- Pages 0-63 are empty (VRAM offset 0x0 - 0x7FFFF)
- Font texture TBP0=0x0000 (from R1272 TEX0 register) corresponds to page 0,
  but the actual VRAM storage uses PS2 block swizzling -- raw byte comparison
  is not feasible without full deswizzle
- The fact that English glyphs render correctly on screen proves the font
  texture data in VRAM is from our English atlas, not the original Japanese

### 5. File Size Confirmation
- `r1272_from_iso.bin`: 67,584 bytes (original size, as extracted from patched ISO)
- `english_font_atlas.bin`: 65,792 bytes (our atlas payload without 16-byte sub-header)
- 67,584 = 16 (sub-header) + 65,792 (GS header + pixel data) + 1,776 (trailing padding)
- Pixel data differs 11.1% between JP and EN (7,272 / 65,600 bytes)

---

## R1272 Format Summary
```
Offset   Size     Content
0        16       PACKDATA sub-header (resource type/flags)
16       192      GS register setup (GIFtag + A+D pairs)
                    TEX0_1: TBP0=0x0, TBW=4, PSM=PSMT4(20), 256x512
208+     65,536   Pixel data (PSMT4, 4bpp, 256x512)
65,744+  1,840    Trailing padding/alignment
```

## Conclusion

**R1272 loads without rejection when kept at 67,584 bytes (original size).**
The game's PACKDATA loader accepted the file, parsed the GS header, transferred
the font texture to VRAM, and English text renders correctly on screen.

The previous rejection was caused by enlarging R1272 beyond 67,584 bytes,
which violated the PACKDATA TOC size constraint. The revert to original size
resolved the issue completely.
