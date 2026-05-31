# R1188 Tab Label Editor: Analysis and Implementation Status

**Date**: 2026-05-28

---

## 1. Task Summary

Replace Japanese tab labels on the name entry screen with English equivalents:
- カナ -> "Kana"
- かな -> "Hira"
- 英数 -> "ABC"
- 記号 -> "Sym"
- 決定 -> "OK"
- 男名 -> "M.Name"
- 女名 -> "F.Name"

---

## 2. How the Tab Labels Work

### Source: R1188 PSMT4 Atlas (1024x1024, 4bpp)

Tab labels are **pre-baked bitmap sprites** stored in the R1188 atlas. Each label is
a single glyph ID (6400-6409) rendered as ONE sprite by `render_glyph_sprite` at
EXE VA 0x494350.

### Glyph ID Table (EXE Table 2E at file 0x3C9DA0)

| Glyph ID | Group:Index | Japanese | English | PCSX2 Size | PCSX2 Content Hash |
|----------|-------------|----------|---------|-----------|--------------------|
| 6400     | 0x19:0x00   | カナ      | Kana    | 48x20     | `1f839869fab251d`  |
| 6401     | 0x19:0x01   | かな      | Hira    | 48x20     | `9677cb23da53ff88` |
| 6402     | 0x19:0x02   | 英数      | ABC     | 48x20     | `6f1fb24fad5cd1a`  |
| 6403     | 0x19:0x03   | 記号      | Sym     | 48x20     | `19a39fbc8a08d7ec` |
| 6404     | 0x19:0x04   | (unused) | --      | --        | --                 |
| 6405     | 0x19:0x05   | 決定      | OK      | 40x24     | `d09a04bdfaf715bc` |
| 6406     | 0x19:0x06   | 男名      | M.Name  | not captured | unknown         |
| 6407     | 0x19:0x07   | 女名      | F.Name  | not captured | unknown         |
| 6408     | 0x19:0x08   | 1文字消す  | Delete  | not captured | unknown         |
| 6409     | 0x19:0x09   | 全削除    | Clear   | not captured | unknown         |

### Cell Data (EXE file 0x3D9B90, 8 bytes per entry)

Each glyph has a cell record: `U(1) V(1) W(1) flag(1) ptr(4)`

| Glyph | U | V  | W   | Flag | Note |
|-------|---|-----|-----|------|------|
| 6400  | 0 | 60  | 100 | 0    | Katakana tab |
| 6401  | 0 | 61  | 100 | 0    | Hiragana tab |
| 6402  | 0 | 62  | 100 | 0    | Alphanumeric tab |
| 6403  | 0 | 63  | 100 | 0    | Symbols tab |
| 6404  | 0 | 64  | 100 | 0    | 5th tab slot |
| 6405  | 0 | 65  | 100 | 0    | Confirm (OK) |
| 6406  | 0 | 66  | 100 | 0    | Male Name |
| 6407  | 0 | 67  | 100 | 1    | Female Name |
| 6408  | 0 | 68  | 100 | 1    | Delete character |
| 6409  | 0 | 69  | 100 | 1    | Clear all |
| 6410  | 0 | 70  | 100 | 0    | Sidebar label 1 |
| 6411  | 0 | 71  | 100 | 1    | Sidebar label 2 |
| 6412  | 0 | 72  | 100 | 0    | Sidebar label 3 |

The V values (60-72) are tile indices into the atlas, but the tile-to-pixel mapping
involves GS VRAM page addressing (TBP0) that is populated at runtime into BSS tables.
The exact pixel positions in the deswizzled atlas could NOT be determined by static
analysis.

### Rendering Pipeline

```
EXE Table 2E (glyph IDs 6400+)
  -> render_glyph_sprite (VA 0x494350)
    -> BSS page table (VA 0x4DB100 + group*8)
      -> cell data (U, V, W from BSS-referenced table)
        -> GS draw sprite at UV coords in 1024x1024 PSMT4 atlas
```

The BSS page table is populated when R1188 is loaded. The per-glyph UV coordinates
come from R1188's sprite metadata (file offsets 0x574-0x6B3, 0x6C4-0x7C4).

---

## 3. Why Direct Atlas Editing Failed

### Problem: CLUT (palette) mapping is unknown

The R1188 atlas stores 4-bit palette INDICES (0-15). The CLUT maps these indices
to RGBA colors. The PCSX2 texture dumps show the FINAL rendered pixels (after CLUT
lookup), but the relationship between dump alpha values and atlas index values is
non-trivial:

- Atlas pixel values: 0, 17, 34, 51, ..., 255 (= index * 17 in grayscale)
- PCSX2 dump alpha values: 0, 11, 19, 28, 36, 44, 52, 60, 69, 77, 85, 93, 102, 110, 118, 128

The CLUT is NOT stored in R1188's file (the CLUT area at file offsets 0x800-0xBFF
is zeroed out). It is loaded separately by the game engine. Without the CLUT, we
cannot match PCSX2 dump pixels to atlas index values.

### Approaches tried and results

| Approach | Result |
|----------|--------|
| Direct y=60 in 1024-wide atlas | Shows button icons (X, O, arrows), NOT tab labels |
| TBW=4 page rearrangement | Same content as TBW=16 for x<128 |
| V*tile_h pixel mapping (h=10,12,14,16) | All land on kanji grid, NOT tab labels |
| PSMT4 block coordinate remapping | Produced garbage, block swizzle is more complex |
| Pixel pattern matching (binary mask) | 0 matches - CLUT changes shape |
| Normalized cross-correlation | 0 matches above 0.5 - CLUT inverts/permutes intensities |

### Root cause

The tab label sprites exist at specific VRAM addresses determined by TBP0 values in
the BSS page table. These TBP0 values are set at runtime when R1188 is loaded into
GS VRAM. Without runtime tracing (PCSX2 debugger or save state memory analysis), the
exact atlas pixel positions cannot be determined from static analysis alone.

---

## 4. Working Solution: PCSX2 Texture Replacement

### Already implemented in `tools/patch_r1188_direct.py`

The patcher generates 16 PCSX2 texture replacement PNGs:

| Category | Count | Dimensions | CLUT Hash |
|----------|-------|-----------|-----------|
| Tab labels | 8 | 48x20 | `3cb39bf7659ef15f` |
| Buttons | 1 | 40x24 | `3cb39bf7659ef15f` |
| Title | 1 | 120x24 | `e786e0650b284c64` |
| Stat labels | 6 | 64x16 | `3cb39bf7659ef15f` |

Files are output to: `build/pcsx2_texture_replacements/`

Format: `{content_hash}-{clut_hash}-r{W}x{H}-{gs_page}.png`

### Coverage gaps

The following labels have NO PCSX2 dumps and thus no replacement PNGs:

| Label | Glyph ID | Status |
|-------|----------|--------|
| 男名 (M.Name) | 6406 | NOT CAPTURED - needs PCSX2 re-dump with name entry screen active |
| 女名 (F.Name) | 6407 | NOT CAPTURED - same |
| 1文字消す (Delete) | 6408 | NOT CAPTURED |
| 全削除 (Clear) | 6409 | NOT CAPTURED |

These labels appear on the name entry screen but were apparently not rendered during
the PCSX2 texture dump session.

### PCSX2 setup instructions

1. Copy files from `build/pcsx2_texture_replacements/` to:
   `PCSX2/textures/SLPM-65378/replacements/`
2. Enable "Load Textures" in PCSX2 Graphics settings
3. English labels appear in-game for all captured textures

---

## 5. Future Work: ISO-Level Fix Options

### Option A: Runtime VRAM tracing (RECOMMENDED)

1. Load PCSX2 save state at the name entry screen
2. Use PCSX2 debugger to read BSS table at VA 0x4DB100 + 0x19*8
3. Extract TBP0 and cell_ptr values for glyph group 0x19
4. Compute pixel positions from TBP0 + UV coordinates
5. Edit those pixel positions in the deswizzled atlas
6. Re-swizzle and inject

### Option B: Patch EXE cell data V bytes

Redirect the V tile indices to point to atlas rows where English labels
have already been rendered (y=1009-1020 in the deswizzled atlas by
`patch_r1188_direct.py`).

EXE patch points (file offsets):

| Label | Offset | Current V | Change to |
|-------|--------|-----------|-----------|
| Kana  | 0x3D9B91 | 60 | TBD |
| Hira  | 0x3D9B99 | 61 | TBD |
| ABC   | 0x3D9BA1 | 62 | TBD |
| Sym   | 0x3D9BA9 | 63 | TBD |
| OK    | 0x3D9BB9 | 65 | TBD |
| M.Name| 0x3D9BC1 | 66 | TBD |
| F.Name| 0x3D9BC9 | 67 | TBD |

**Requires**: Understanding the tile-index-to-pixel mapping (TBP0-dependent).
The English labels at y=1009 would need a corresponding V tile index that maps
to y=1009 via the same TBP0 addressing. This may not be possible if the TBP0
page doesn't cover y=1009.

### Option C: Re-dump PCSX2 textures

Re-run PCSX2 with full texture dumping while navigating all name entry screen
states (including clicking M.Name and F.Name buttons). This would capture the
missing content hashes for the 4 uncaptured labels.

---

## 6. File References

| Item | Path |
|------|------|
| R1188 patcher (PCSX2 + direct) | `tools/patch_r1188_direct.py` |
| R1188 patcher (PCSX2 only) | `tools/patch_r1188_tabs.py` |
| PCSX2 replacement PNGs | `build/pcsx2_texture_replacements/` |
| R1188 raw resource | `extracted/packdata_raw/1188_type01.raw` |
| Deswizzled atlas | `build/textures_to_edit/R1188_CORRECT_dbw512.png` |
| PCSX2 texture dumps | `build/pcsx2_dumps/` |
| Build pipeline | `build/build_full_english_v2.py` |
| EXE | `extracted/SLPM_653.78` |
| Prior analysis | `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/r1188_tab_redirect.md` |
| Prior debug notes | `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/debug_name_entry_tabs.md` |
