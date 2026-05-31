# R1272 v11 Format Check

## Question
Did v11 use a different R1272 format that we broke in later builds?

## Answer: NO. The format is identical. The issue is NOT the R1272 format.

## Evidence

### R1272 sizes across all ISO versions

| Version | Sectors | field1 (payload size) | Atlas height |
|---------|---------|----------------------|-------------|
| v10-v23 | 33 | 0x10100 (65,792 bytes) | 256x512 (TH=9) |
| **v24-v26** | **41** | **0x14100 (82,176 bytes)** | **256x540/1024 (TH=10)** |
| Current | 41 | 0x14100 (82,176 bytes) | 256x540/1024 (TH=10) |

The atlas expansion (from 33 to 41 sectors) first appeared in **v24**.

### Sub-header structure (16 bytes, identical format in all versions)

```
Offset  Original/v11           Current build
0x00    00 00 00 00            00 00 00 00          (field0: always 0)
0x04    00 01 01 00            00 41 01 00          (field1: payload size LE)
0x08    10 00 00 00            10 00 00 00          (field2: always 16)
0x0C    00 00 00 00            00 00 00 00          (field3: always 0)
```

The build script (`build_full_english_v2.py` lines 184-193) correctly:
- Preserves field0, field2, field3 from original
- Updates field1 to new payload size
- Pads to sector boundary

### GS header comparison (v11 vs current atlas)

Only **1 byte** differs in the 192-byte GS header:
- Offset 0x53 (TEX0 register): v11=0x61, atlas=0xA1
- This is the TH field: v11 TH=9 (512px height), atlas TH=10 (1024px height)
- This change is correct and necessary for the taller atlas

### v11 pixel data

v11's R1272 has **16,037 pixel differences** vs original Japanese atlas (across 67,568 payload bytes), confirming English glyphs were rendered into it. But it stayed within the original 256x512 dimensions.

### What v11 ACTUALLY proves

v11 proves that **the R1272 sub-header + GS packet format works**. The format has NOT changed between v11 and the current build -- only the size grew.

The "positions 0-94 worked" means ASCII glyphs (space through tilde, mapped to glyph slots 0-94) rendered correctly. This is purely about the **glyph table mapping** and **message encoding**, not about the R1272 binary format.

## Conclusion

The R1272 format is NOT the cause of any remaining Japanese text. The format is the same as v11, just larger. The remaining Japanese text issue must be in one of:
1. Message resources that haven't been re-encoded (glyph indices still point to Japanese slots)
2. Hardcoded glyph indices in the EXE (SLPM_653.78)
3. Separate texture atlases for specific UI screens (R1188 tabs, etc.)

## Files examined
- `C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v11.iso` (R1272 extracted at LBA 16029)
- `C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1272_type01.raw` (original)
- `C:/Programmieren/wizardrytranslation/build/english_font_atlas.bin` (current atlas output)
- `C:/Programmieren/wizardrytranslation/build/packdata_resources/1272_type01.raw` (current modified)
- `C:/Programmieren/wizardrytranslation/tools/generate_font_atlas.py` (atlas generator)
- `C:/Programmieren/wizardrytranslation/build/build_full_english_v2.py` (build pipeline, R1272 injection at line 174)
