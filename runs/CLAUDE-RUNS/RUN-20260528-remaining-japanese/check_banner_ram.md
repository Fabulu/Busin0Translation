# Banner RAM Check: v27 Savestate Analysis

**Date**: 2026-05-28  
**Savestate**: RAMdumps/27-1.p2s (PCSX2 v2.6.3)  
**ISO**: build/BUSIN0_EN_v27.iso

---

## 1. EXE Patch Status: WORKING

The patched EXE glyph IDs are correctly present in RAM at the expected virtual addresses.

| Record | File Offset | VA (RAM) | Old Glyph IDs | New Glyph IDs | RAM Status |
|--------|------------|----------|---------------|---------------|------------|
| rec1 | 0x3C33F0 | 0x4C3370 | 719, 720 | 46(N), 69(e) | PATCHED (correct) |
| rec2 | 0x3C3428 | 0x4C33A8 | 721, 722 | 87(w), 0(space) | PATCHED (correct) |
| rec3 | 0x3C3268 | 0x4C31E8 | 705, 706 | 50(R), 69(e) | PATCHED (correct) |
| rec4 | 0x3C32A0 | 0x4C3220 | 707, 708 | 71(g), 14(.) | PATCHED (correct) |

No old glyph IDs (705-722) remain in ANY of the 4 records. All u16 positions that originally had old values were successfully replaced. The 8-byte record patterns (0,719,0,720 etc.) are completely absent from RAM.

## 2. Patched EXE File: CORRECT

`build/SLPM_653.78_patched` has all 4 banner records properly patched. Build log confirms:
```
OK   0x3C33F0: new -> Ne (5 u16 values patched)
OK   0x3C3428: reg -> w_ (5 u16 values patched)
OK   0x3C3268: reg -> Re (6 u16 values patched)
OK   0x3C32A0: reg -> g. (6 u16 values patched)
```

## 3. ISO Injection: CORRECT

- `build/BUSIN0_EN_v27.iso` has the patched EXE at the correct LBA
- PACKDATA.DIG in the ISO contains the English R1272 font atlas (verified byte-for-byte match)
- R1272 TOC entry: sector_offset=211364, sector_count=41, type_code=1

## 4. Font Atlas Glyph Table: CORRECT

All ASCII glyph positions have rendered pixel data in `english_font_atlas.bin`:

| Glyph ID | Character | Nonzero Pixels | Status |
|----------|-----------|---------------|--------|
| 46 | N | 142 | HAS PIXELS |
| 69 | e | 142 | HAS PIXELS |
| 87 | w | 141 | HAS PIXELS |
| 50 | R | 144 | HAS PIXELS |
| 14 | . | 143 | HAS PIXELS |
| 71 | g | 144 | HAS PIXELS |

## 5. ROOT CAUSE: The Banner Is NOT Rendered From These Records

**The EXE patch is working perfectly. The problem is that the records we patched do NOT control the banner.**

Evidence:

1. **Japanese atlas glyph positions 46, 69, 87, 71 are BLANK** (0 non-white pixels). If the banner rendering read from these glyph IDs using the JP atlas, it would show blank space -- but the screenshot shows full kanji. Therefore, the banner rendering does NOT use these glyph IDs.

2. **The original glyph IDs 719/720 (for kanji) are also NOT what the banner reads.** These are R1272 font atlas tile references for the sidebar/label system, not the banner system.

3. **The banner is rendered as a 120x24px composite at GS page 0x2214** (per chargen_source_map.md). This is likely a pre-rendered texture or uses a completely different rendering path than the 12x12 glyph tile system.

4. **Font atlas in RAM**: The Japanese R1272 font atlas pixel data IS in RAM (confirmed at 0x4AF678 for pixel row 3). The English atlas pixel data (row 50 signature) is NOT found in eeMemory. However, this is likely because:
   - The atlas was DMA'd directly to GS VRAM and is no longer in eeMemory
   - Or the font atlas may be swizzled differently in memory vs. file

## 6. What Do The Patched Records Actually Control?

The 4 records at 0x3C3268-0x3C3428 are part of a large table of 56-byte menu struct records (from 0x3C3000 to 0x3C3FF8+). Each record has:
- Byte 2: menu item ID (e.g., 618, 624, 625)
- Bytes 4-24: float parameters (position, scale)
- Bytes 26+: glyph ID references

These records likely control **sidebar labels** or **menu option labels** on OTHER screens, not the red banner title. The chargen_source_map.md already documents them as sidebar field labels (Name, Race, Gender, etc.) at nearby offsets.

## 7. Conclusion

| Component | Status |
|-----------|--------|
| patch_exe.py PATCH 4 | Working correctly |
| EXE in ISO | Correctly injected |
| EXE in RAM | Has patched data |
| English font atlas in PACKDATA | Correctly injected |
| Banner still Japanese | YES -- because these records don't control the banner |

## 8. How To Fix The Banner

The banner "new reg." rendering at GS page 0x2214 must be addressed through one of:

1. **Find the ACTUAL banner rendering code** -- trace the GS register writes that draw the 120x24px banner texture to identify what data source it uses. This requires deeper EXE reverse engineering.

2. **PCSX2 texture replacement** -- a tex replacement PNG already exists (per chargen_source_map.md). This is emulator-only but works immediately.

3. **R1188 bitmap approach** -- if the banner uses R1188 sprites (like the tab buttons do), patch the R1188 atlas pixel data at the correct UV coordinates.

4. **GS VRAM injection** -- write English text pixels directly into the GS texture page at upload time (requires finding the DMA/GIF packet that uploads the banner texture).

The next step should be identifying WHERE in the code the 120x24px banner texture originates. A GS register trace or VIF/GIF DMA packet analysis would reveal the source resource.
