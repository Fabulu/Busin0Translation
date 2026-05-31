# R1188 Sidebar Label Editor: Implementation Report

**Date**: 2026-05-28
**Script**: `tools/patch_r1188_overwrite.py` (Phase 3 added)

---

## Summary

Added sidebar kanji replacement to `patch_r1188_overwrite.py` as Phase 3. Six kanji
used in chargen sidebar labels are overwritten with English abbreviations in the
deswizzled R1188 atlas (1024x1024, PSMT4, dbw=512).

---

## Sidebar Labels and Their Kanji

| Label | Japanese | Kanji 1 | Kanji 2 | Combined Meaning |
|-------|----------|---------|---------|-----------------|
| Gender | 性別 | 性 (sei) | 別 (betsu) | Sex/distinction |
| Race | 種族 | 種 (shu) | 族 (zoku) | Seed/clan |
| Alignment | 属性 | 属 (zoku) | 性 (sei) | Belong/nature |
| Class | 職業 | 職 (shoku) | 業 (gyou) | Job/work |
| Personality | 性格 | 性 (sei) | 格 (kaku) | Nature/character |

---

## Kanji Found in Atlas (6 of 8)

| Kanji | Row | Col | Atlas Position (x, y) | Width | English Abbrev |
|-------|-----|-----|----------------------|-------|---------------|
| 性 | 19 | 20 | (473, 456) | 22x24 | "sx" |
| 種 | 18 | 9 | (209, 432) | 22x24 | "ra" |
| 族 | 18 | 10 | (233, 432) | 22x24 | "ce" |
| 属 | 37 | 5 | (113, 888) | 22x24 | "al" |
| 職 | 15 | 9 | (209, 360) | 22x24 | "cl" |
| 格 | 22 | 3 | (65, 528) | 22x24 | "pe" |

### Kanji NOT Found (2 of 8)

| Kanji | Used In | Notes |
|-------|---------|-------|
| 別 (betsu) | 性別 (Gender) | Not in left-half kanji grid rows 6-41; likely in right half (x=512+) or alternate atlas region |
| 業 (gyou) | 職業 (Class) | Same -- not in left-half kanji grid |

---

## Abbreviation Rationale

Each kanji cell is ~22px wide, which fits 2-3 English characters at font_size=14.
The abbreviations are chosen so that when the game composes 2-kanji labels, the
English fragments form recognizable abbreviated words:

| Label | Kanji Pair | English Pair | Result | Notes |
|-------|-----------|-------------|--------|-------|
| Gender | 性 + 別 | "sx" + ?? | "sx??" | 別 not patched (missing from grid) |
| Race | 種 + 族 | "ra" + "ce" | "race" | Perfect! |
| Alignment | 属 + 性 | "al" + "sx" | "alsx" | Readable abbreviation |
| Class | 職 + 業 | "cl" + ?? | "cl??" | 業 not patched (missing from grid) |
| Personality | 性 + 格 | "sx" + "pe" | "sxpe" | Acceptable |

### Shared Glyph Conflict

性 (sei) is used in THREE contexts:
- 性別 (gender): "sx" + 別
- 属性 (alignment): 属 + "sx"
- 性格 (personality): "sx" + 格

The abbreviation "sx" was chosen as the most compact representation of the
sex/gender concept that works reasonably in all three contexts.

---

## Implementation Details

### Changes to `tools/patch_r1188_overwrite.py`

1. Added `SIDEBAR_KANJI_CELLS` list with 6 entries (lines ~220-245)
2. Added Phase 3 in `main()` that calls `patch_cells(linear, SIDEBAR_KANJI_CELLS, font_size=14)`
3. Added sidebar debug image output (`R1188_patched_sidebar_kanji.png`)

### Build Integration

The script is called from `build/build_v9.py` Step 3.6 via `patch_r1188_direct.py`.
The overwrite script produces the same output file: `build/packdata_resources/1188_type01.raw`.
Both scripts write to the same output path, so the BUILD PIPELINE should run
`patch_r1188_overwrite.py` LAST (or consolidate both into one script) to ensure
all patches are present.

### Verification

- Round-trip verification: PASS (deswizzle -> edit -> reswizzle -> re-deswizzle matches)
- 2,663 pixel edits in Phase 3
- Debug images saved to `build/textures_to_edit/`

---

## Rendering Architecture Note

### TBW=16 vs TBW=4 Mapping Issue

The sidebar labels (性別, 種族, 属性, 職業) are rendered by the game as **48x20 composite
sprites** via a TBW=4 sub-atlas view of R1188's VRAM. The deswizzled atlas uses TBW=16.

Modifying individual kanji in the TBW=16 deswizzled view changes the underlying VRAM
bytes. However, the PSMT4 block/column swizzle tables mean the same byte offset maps to
DIFFERENT visual positions under TBW=4 vs TBW=16. Therefore:

- Editing kanji cells in the TBW=16 grid **WILL** affect the raw VRAM bytes
- Those bytes **MAY NOT** correspond to the same visual position in the TBW=4 composite
- The PCSX2 texture replacement approach (already implemented in `patch_r1188_direct.py`)
  is the **proven reliable method** for sidebar labels

### When These Edits Help

The TBW=16 kanji edits are useful for:
1. Any screen that renders individual kanji via the R1188 cell data system (TBW=16)
2. The R38 MSG rendering path if it resolves to R1188 cell data instead of R1272
3. As a secondary/fallback when PCSX2 texture replacement is not available

---

## Existing PCSX2 Texture Replacement (Primary Path)

Already implemented in `tools/patch_r1188_direct.py` and `tools/patch_r1188_tabs.py`:

| PCSX2 Hash | Japanese | English Replacement |
|-----------|----------|-------------------|
| `16625baf9feaeafb` | 性別 | Gender |
| `88ff8b577084a2a8` | 職業 | Class |
| `9bec87b4031a7172` | 種族 | Race |
| `c89b469f7a152a6` | 属性 | Align |

These 48x20 PNG replacements are hash-matched by PCSX2 at runtime, completely replacing
the Japanese composite sprites with English labels. This is the primary and proven path.
