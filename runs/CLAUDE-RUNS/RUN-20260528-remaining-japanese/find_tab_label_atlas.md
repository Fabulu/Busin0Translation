# Finding the Tab Label Atlas (Name Entry / CharGen Screen)

**Date**: 2026-05-28

## PCSX2 Dump Evidence

All name entry / character creation tab labels come from a **single VRAM region at page 0x2214**. PCSX2 captured 208 unique textures from this page during gameplay, including:

| CLUT Hash | Count | Size(s) | Content |
|-----------|-------|---------|---------|
| 2396a88fd6b4cb36 | 117 | 16x16 | Character grid tiles (kana glyphs) |
| 3cb39bf7659ef15f | 16 | 48x20, 64x16, 40x24 | **Tab labels**: カナ, かな, 英数, 記号, 性別, 種族, 職業, 幸運度, 敏捷度, etc. |
| 8cef486a60d73b78 | 16 | 64x64 | Background panels |
| 5426a3daf294bef2 | 12 | 64x64 | Background panels (variant) |
| e5121c8caf7d1dd | 10 | 10x16 | Small character glyphs |
| 83b395554335bd47 | 10 | 10x16, 8x16 | Small character glyphs (variant) |
| 73d6533c7af7f8fd | 4 | 128x160, 176x24, 128x32, 0x32 | Large UI panels and title bar |
| Others | 23 | Various | Arrows, icons, misc UI |

All content is in the **alpha channel** (RGB=white, alpha 0-128). The text is rendered as white glyphs with alpha for anti-aliasing.

A nearby page at **0x2254** contains status screen labels (already translated: "Class&Parameter", "Status", "Attribute", "Race", "Level").

## PACKDATA Resource Identification

### Only Two 256x256 PSMT4 Resources Exist

A comprehensive scan of all 2883 PACKDATA resources found exactly **two** type-01 resources with TEX0 configured as 256x256 PSMT4 (PSM=20, TW=8, TH=8):

| Resource | Raw Size | Header | Pixels | TEX0 Blocks | Content |
|----------|----------|--------|--------|-------------|---------|
| **R2124** | 34,816B | 1,040B | 32,768B | 6 CLUTs | Town district UI atlas (フォブール地区, ボローラ地区, etc.) |
| **R2548** | 36,864B | 2,112B | 32,768B | 16 CLUTs | Generic UI toolkit atlas (numbered grid tiles, arrows, curved borders, gradient panels) |

Both use TEX0 = `0x2010000621410000`: TBP0=0, TBW=4 (256px), PSM=20 (PSMT4), 256x256.

**Neither R2124 nor R2548 contains the tab labels.** R2124 is for the town/area selection screen. R2548 is a generic UI element atlas.

### R1188 Is the Source

The tab labels are part of **R1188** (type-01, 528,384 bytes raw), which stores a **1024x1024 PSMT4** texture atlas. Evidence:

1. **Existing analysis** (analysis_name_entry.md) confirms tab label glyph IDs 6400-6412 are resolved from R1188 via a BSS lookup table at VA 0x4EBBEC
2. **VRAM layout**: R1188 occupies 2048 TBP0 units (1024x1024 PSMT4 = 64 pages x 32 units). If R1188 base is ~0x1A14, it spans to ~0x2213, and the UI overlay atlas at page 0x2214 sits immediately after it
3. **The game re-configures TEX0** at runtime to read sub-regions of R1188's VRAM with different TBP0/TBW settings
4. **17 GS register blocks** in R1188's header (17 TEX0 configurations) correspond to different rendering states for UI elements

### R1188 File Layout

| Offset | Size | Content |
|--------|------|---------|
| 0x000-0x00F | 16B | File header: `{0, 527360, 16, 0}` |
| 0x010-0x01F | 16B | GIFtag: NLOOP=17, FLG=0 (A+D), NREG=16 |
| 0x020-0x56F | 1360B | 17 x 5 A+D register blocks (TEX0_1, CLAMP_1, MIPTBP1_1, TEX2_1, A+D) |
| 0x570-0xBFF | 1680B | Sprite metadata, index tables, CLUT palette data |
| 0xC00-0x80BFF | 524,288B | 1024x1024 PSMT4 pixel data |
| 0x80C00-0x80FFF | 1024B | CLUT palette block |

## Deswizzle Status

**R1188 has NOT been successfully deswizzled.** All attempts with the VRAM simulation deswizzler (psmt4_deswizzle.py) using dbw_ct32 values of 64, 128, 256, 512, and 1024 produced garbled output. This suggests:

1. R1188 may use a **non-standard DMA upload** method (e.g., DMA chain with multiple transfers at different VRAM positions)
2. The pixel data may not be uploaded as a contiguous PSMCT32 block
3. The game code may split the upload into multiple BITBLTBUF/TRXREG operations

**The correct deswizzle requires reverse-engineering the EXE code** at the R1188 upload function to determine the exact DMA transfer parameters.

## Successfully Decoded Textures

| Resource | Description | Deswizzle Params |
|----------|-------------|-----------------|
| R2124 | Town district UI atlas (256x256 PSMT4) | hdr=0x410, dbw_ct32=128 |
| R2548 | Generic UI toolkit (256x256 PSMT4) | hdr=0x6D0, dbw_ct32=128 |
| R1272 | Main font atlas (256x512 PSMT4) | Previously decoded |

## Next Steps

1. **Reverse-engineer R1188 upload code** in the EXE to find the DMA transfer parameters (BITBLTBUF DBW, transfer dimensions)
2. **Alternative**: Use PCSX2's VRAM viewer/dumper to capture R1188's 1024x1024 texture directly from VRAM after loading
3. **Alternative**: Use PCSX2 texture replacement feature to inject modified textures at the CLUT hash `3cb39bf7659ef15f` without needing to edit R1188's raw data

## Key Files

- Tab label PCSX2 dumps: `build/pcsx2_dumps/*3cb39bf7659ef15f*`
- R1188 raw: `extracted/packdata_raw/1188_type01.raw`
- R2124 decoded: `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/R2548_h06D0_d128_2x.png`
- Deswizzle tool: `tools/psmt4_deswizzle.py`
- Name entry analysis: `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/analysis_name_entry.md`
