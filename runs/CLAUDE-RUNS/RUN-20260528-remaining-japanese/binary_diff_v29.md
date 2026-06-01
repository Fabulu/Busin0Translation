# Binary Diff: v29 ISO vs Original Japanese ISO

## File Info
- **Original**: `Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso` (1,274,544,128 bytes)
- **Patched**:  `build/BUSIN0_EN_v29.iso` (1,274,544,128 bytes, same size)
- **Total sectors**: 622,336
- **Sectors that differ**: 406,784 (65.4% of ISO)
- **Contiguous diff ranges**: 237

## R38 (System/UI MSG) - NOT PATCHED

| Property | Original | Patched | Match? |
|----------|----------|---------|--------|
| TOC sector_offset | 68 | 68 | YES |
| TOC sector_count | 4 | 4 | YES |
| Absolute LBA | 16097 | 16097 | YES |
| Data content | (8192 bytes) | (8192 bytes) | **IDENTICAL** |

**First 20 glyph IDs from stream 0 (BOTH ISOs):**
```
[5, 0, 0, 0, 8, 0, 0, 0, 32768, 0, 4, 64, 52, 0, 0, 0, 0, 0, 0, 0]
```

**Verdict: R38 is COMPLETELY UNPATCHED.** The data is byte-for-byte identical.
R38 falls in the untouched gap between diff ranges (sectors 16046-17953).

## R1272 (Font Texture) - NOT PATCHED

| Property | Original | Patched | Match? |
|----------|----------|---------|--------|
| TOC sector_offset | 61462 | 61472 | NO (shifted +10) |
| TOC sector_count | 70 | 70 | YES |
| Absolute LBA | 77491 | 77501 | shifted |
| Data content | (143,360 bytes) | (143,360 bytes) | **IDENTICAL** |

First 100 bytes of pixel data: identical in both ISOs.

**Verdict: R1272 is COMPLETELY UNPATCHED.** The TOC offset shifted because earlier
resources grew, but the actual font texture data is byte-for-byte identical to the
original Japanese font.

## EXE (SLPM_653.78) - PATCHED (minimally)

| Property | Value |
|----------|-------|
| LBA | 457143 |
| Size | 4,185,776 bytes |
| Bytes changed | **210** |
| Patch range | 0x3c3282 - 0x3fc7a3 |

The 210 changed bytes are glyph ID replacements in hardcoded UI strings:
- Original JP glyph IDs: 0x02c1, 0x02c2, 0x02c3, 0x02c4, 0x02cf, 0x02d0...
- Patched EN glyph IDs: 0x0032, 0x0045, 0x0047, 0x000e, 0x002e, 0x0045...

These are the EXE-embedded text strings (menu labels etc.) that were patched
from Japanese glyph IDs to English glyph IDs.

## PACKDATA Resource Changes Summary

| Category | Count |
|----------|-------|
| TOC entries that differ | 1,350 |
| Resources with SIZE changes | 665 |
| Resources with CONTENT changes (same size) | 20 |
| Resources shifted but content identical | 628 |

The 665 size-changed resources are the MSG files that grew when English text
(which uses more glyph entries) replaced Japanese text. The 20 content-changed
resources include small metadata/index files. The 628 shifted-but-identical
resources are untouched data (like R1272) that simply moved because earlier
resources grew.

## Key Conclusions

1. **R38 patching FAILED or was never attempted.** The build pipeline does not
   touch R38 at all. Whatever system/UI text R38 contains is still 100% Japanese.

2. **R1272 (font texture) was never replaced.** The English font glyphs are NOT
   in the ISO. The game is still rendering with the original Japanese font bitmap.
   Any English text that appears must be using glyph slots that happened to already
   contain Latin characters in the Japanese font.

3. **The EXE patch is minimal** - only 210 bytes changed, all glyph ID swaps in
   hardcoded strings.

4. **The bulk of changes** are in MSG resources (665 grew in size), which is the
   12,725+ type-2 message injections working correctly.

5. **The remaining Japanese text** on screen comes from:
   - R38 (system/UI messages) being completely unpatched
   - R1272 (font texture) being the original Japanese font
   - Any MSG resources not in the 665 that changed
