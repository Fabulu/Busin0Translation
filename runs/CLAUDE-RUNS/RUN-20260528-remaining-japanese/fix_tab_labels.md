# Fix Tab Labels: Name Entry Screen (カナ, かな, 英数, 記号, 決定)

**Date**: 2026-05-28

---

## Verdict: Tab Labels Are NOT Inline Glyph IDs in R39

The initial hypothesis was wrong. The name entry tab labels are **pre-baked bitmap sprites in R1188** (1024x1024 PSMT4 atlas), not R39 inline glyph IDs.

---

## How Tab Labels Actually Work

### 1. EXE Table 2E (file offset 0x3C9DA0) stores glyph IDs 6400-6412

These are LE uint32 values in the EXE, NOT in R39:

| EXE Offset | Glyph ID | Label |
|------------|----------|-------|
| 0x3C9DA0 | 6400 (0x1900) | **カナ** (Katakana) |
| 0x3C9DA4 | 6401 (0x1901) | **かな** (Hiragana) |
| 0x3C9DA8 | 6402 (0x1902) | **英数** (Alphanumeric) |
| 0x3C9DAC | 6403 (0x1903) | **記号** (Symbols) |
| 0x3C9DB0 | 6404 (0x1904) | (unused 5th slot) |
| 0x3C9DEC | 6405 (0x1905) | **決定** (Confirm/OK) |
| 0x3C9DF0 | 6406 (0x1906) | 男名 (Male Name) |
| 0x3C9DF4 | 6407 (0x1907) | 女名 (Female Name) |
| 0x3C9DF8 | 6408 (0x1908) | 1文字消す (Delete char) |
| 0x3C9DFC | 6409 (0x1909) | 全消去 (Clear all) |

### 2. Rendering pipeline

```
EXE Table 2E (glyph IDs 6400+)
  -> render_glyph_sprite (VA 0x494350)
    -> BSS page table (VA 0x4DB100 + group*8)
      -> cell data at EXE 0x3D9B90 (U, V, W per glyph)
        -> GS draws sprite from R1188's 1024x1024 PSMT4 atlas
```

### 3. Cell data (EXE file 0x3D9B90, 8 bytes per entry)

| Label | EXE Offset | V (tile index) | Dimensions |
|-------|-----------|----------------|------------|
| カナ (Kana) | 0x3D9B91 | 60 | 48x20 |
| かな (Hira) | 0x3D9B99 | 61 | 48x20 |
| 英数 (ABC)  | 0x3D9BA1 | 62 | 48x20 |
| 記号 (Sym)  | 0x3D9BA9 | 63 | 48x20 |
| 決定 (OK)   | 0x3D9BB9 | 65 | 40x24 |
| 男名 (M.Name) | 0x3D9BC1 | 66 | unknown |
| 女名 (F.Name) | 0x3D9BC9 | 67 | unknown |

### 4. R39 search results

Searched R39 (0039_type15.raw, 26624 bytes) for glyph IDs 0x1900-0x190C as BE uint16. All 17 hits for `19 00` were at **odd offsets** -- they are fragments of other glyph sequences (e.g., `01 19 00 71` = glyphs 0x0119, 0x0071), NOT tab label references.

**R39 does NOT contain tab label glyph IDs.**

---

## Fix Options (Ranked)

### Option A: PCSX2 Texture Replacement (WORKING NOW)

Already implemented in `tools/patch_r1188_direct.py`. Generates replacement PNGs for PCSX2's texture replacement feature.

- **Output**: `build/pcsx2_texture_replacements/`
- **Coverage**: 5 of 5 visible tabs (カナ, かな, 英数, 記号, 決定)
- **Gaps**: 男名, 女名, 1文字消す, 全消去 not captured from PCSX2 dumps
- **Limitation**: PCSX2-only, does not modify the ISO

### Option B: Edit R1188 Atlas Pixels (BLOCKED)

Replace the Japanese bitmap sprites with English text directly in the 1024x1024 PSMT4 atlas.

- **Blocker**: The tab label pixel positions within the atlas are unknown. The V tile indices (60-72) map to VRAM page addresses set at runtime. Without a PCSX2 save state or debugger trace to read the BSS table at VA 0x4DB100, the exact pixel coordinates cannot be determined.
- **Approach if unblocked**:
  1. Read BSS table from PCSX2 save state to get TBP0 values
  2. Calculate pixel coords from TBP0 + UV
  3. Render English labels at those positions in the deswizzled atlas
  4. Re-swizzle and inject into PACKDATA.DIG

### Option C: Patch EXE Cell Data V Bytes

Redirect V tile indices to point to atlas rows containing pre-rendered English labels.

- **EXE patch points**: 0x3D9B91, 0x3D9B99, 0x3D9BA1, 0x3D9BA9, 0x3D9BB9
- **Blocker**: Same as Option B -- need to know the tile-to-pixel mapping to find valid V values that land on English content

### Option D: Re-dump PCSX2 Textures for Missing Labels

Re-run PCSX2 texture dump while navigating all name entry states to capture the missing content hashes for 男名, 女名, etc. This would complete Option A coverage.

---

## Key Files

| Item | Path |
|------|------|
| R1188 raw resource | `extracted/packdata_raw/1188_type01.raw` |
| R1188 patcher | `tools/patch_r1188_direct.py` |
| PCSX2 replacement PNGs | `build/pcsx2_texture_replacements/` |
| EXE (original) | `extracted/SLPM_653.78` |
| Prior R1188 tab analysis | `runs/.../r1188_tab_editor.md` |
| Prior name entry analysis | `runs/.../analysis_name_entry.md` |
| Prior atlas search | `runs/.../find_tab_label_atlas.md` |
| PCSX2 tab label dumps | `runs/.../tab_alpha_*.png` |

---

## Summary

The tab labels are **bitmap sprites baked into R1188**, referenced by glyph IDs 6400+ stored in the **EXE** (not R39). R39 contains no tab label data. The fix requires either (a) PCSX2 texture replacement (already working for 5/9 labels), or (b) determining the tab sprites' pixel positions in R1188 via runtime tracing to edit the atlas directly.
