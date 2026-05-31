# R1272 Extended Font Atlas -- Render Verification

## File Sizes

| Item | Original | Patched |
|------|----------|---------|
| `.bin` (header+pixels+palette) | 65,792 B | 82,176 B |
| `.raw` (sub-header + .bin + pad) | 67,584 B (33 sectors) | 83,968 B (41 sectors) |
| Header | 192 B | 192 B (identical except TEX0) |
| Pixel data | 65,536 B (8 pages) | 81,920 B (10 pages) |
| Palette | 64 B | 64 B (identical) |

## TEX0 Register (offset 0x50 in header)

| Field | Original | Patched |
|-------|----------|---------|
| TEX0 raw | `0x2000000661410000` | `0x20000006A1410000` |
| TH | 9 (512px) | **10 (1024px)** |
| TW | 8 (256px) | 8 (256px) |
| PSM | 20 (PSMT4) | 20 (PSMT4) |
| TBW | 4 | 4 |

**generate_font_atlas.py** correctly patches TH from 9 to 10 when `ATLAS_H > 512`.

## Pipeline Preservation

Both injection pipelines (`build_full_english_v2.py` STEP 3, `full_patch_pipeline.py` STEP 1)
copy `english_font_atlas.bin` verbatim as the resource payload. They update only the
sub-header `payload_size` field (to `len(font_data)` = 82,176). The TEX0 TH=10 patch
is preserved through the entire pipeline.

The PACKDATA.DIG TOC correctly records 41 sectors for R1272 (vs 33 original).

## DMA Upload Analysis

The 192-byte GIF header contains:
- 1 GIF PACKED tag (NLOOP=4, NREG=1) with 4 A+D writes:
  - CLAMP_1, MIPTBP1_1, TEX1_1, TEX0_1
- NO BITBLTBUF, TRXPOS, TRXREG, or TRXDIR registers

This means the game engine handles pixel upload to GS VRAM using its own code,
not via an inline GIF transfer packet. The engine reads `payload_size` from the
16-byte sub-header to know how much data to process.

**Key finding:** Since the header does not embed transfer dimensions, the engine
must derive the upload size from either:
1. `payload_size` (sub-header field, correctly set to 82,176)
2. TEX0 TW/TH fields (patched to 256x1024)
3. A hardcoded constant (would break us)

No hardcoded transfer sizes were found in the EXE patches (`patch_exe.py`).

## Glyph Position Analysis

### Stat labels (confirmed SAFE -- all within 512px)

| Glyph | Row | Y range | Status |
|-------|-----|---------|--------|
| 346 | 16 | 192-204 | Within 512px |
| 535 | 25 | 300-312 | Within 512px |
| 621 | 29 | 348-360 | Within 512px |
| 669 | 31 | 372-384 | Within 512px |

### Menu tiles beyond 512px (47 of 256 tiles)

Glyphs 882-931 span rows 42-44 (y=504-540). If only 512px uploads, these
would be partially or fully missing:

- **Row 42 (y=504-516, partially outside):** misc(882), church(883-884),
  temple(885-886), floor(887-888), rank up(889-890), cure(891-892),
  rank(893-894), like(895-896), hate(897-898), accept(902)
- **Row 43 (y=516-528, fully outside):** accept(903), trade(904-905),
  train(906-907), sorry(908-909), sort(910-911), check(912-913)
- **Row 44 (y=528-540, fully outside):** relics(914-915), ruins(916-917),
  ancient(918-919), loyal(920-921), real(922), war(923), ?(924),
  info(925), reward(926-927), config(928-929), quit(930-931)

### Menu tiles within 512px (209 of 256 tiles)

All glyphs <= 881 are within the first 512 rows. This includes the majority
of menu labels (HP, MP, STR, INT, equip, item, spell, etc.).

## Verdict

**LIKELY SAFE, but with a caveat.**

1. TEX0 TH is correctly patched to 10 (1024px). The GS will sample
   UV coordinates correctly across the full atlas height.

2. The sub-header `payload_size` is correctly set. The TOC sector count
   is correctly set to 41.

3. There are NO inline BITBLTBUF/TRXREG registers in the header that
   would limit the transfer. The engine controls the upload.

4. **Risk:** If the engine has a hardcoded upload size (e.g., always uploads
   exactly 65,536 bytes for type-01 resources, ignoring payload_size), then
   the 47 menu tiles at y>504 would not reach VRAM. This cannot be verified
   without EXE disassembly of the texture loader or runtime testing.

5. **Mitigation:** The most critical translations (stat labels, common menu
   items) are all within the first 512 rows. The 47 at-risk tiles are
   secondary labels (church, temple, trade, config, quit, etc.) that appear
   less frequently.

6. **Recommended test:** Boot the patched ISO and navigate to a screen that
   uses one of the at-risk labels (e.g., the church/temple menu or config
   screen). If the label renders correctly, the extended atlas is working.
   If it shows garbage or blank tiles, the engine is capping the upload at
   512px and we need to either compact the atlas layout or patch the engine.
