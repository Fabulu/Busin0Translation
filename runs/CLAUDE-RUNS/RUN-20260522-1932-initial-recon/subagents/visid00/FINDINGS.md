# Visual Identification: Sheet 00 (Glyphs 0-99)

**Date:** 2026-05-22
**Status:** Complete
**Input:** `dumps/glyph_sheets/sheet_00_glyphs_0000-0099.png`
**Output:** `data/visual_id_sheet0.json`

---

## Key Finding: Glyphs 0-93 are ASCII characters (confirmed by EXE data)

The first 100 glyphs in the font atlas are NOT Japanese characters. They are ASCII/Latin characters, as confirmed by the 84-entry ASCII glyph index lookup table found at EXE file offset 0x3C0870 (RAM 0x004C07F0), documented in `recon20-glyph-table/FINDINGS.md`.

### Source of Truth

The mapping is derived from the **EXE binary's ASCII lookup table**, not from visual OCR. The individual glyph images are only 12x12 pixels (rendered at 64x64) and extremely difficult to distinguish visually. The EXE table provides a definitive mapping.

### Coverage Summary

| Range | Count | Content | Confidence |
|-------|-------|---------|------------|
| 0 | 1 | Null/padding (most frequent token at 66.55%) | HIGH (from frequency analysis) |
| 1 | 1 | Space character | HIGH (from EXE table) |
| 2-4 | 3 | Reserved/unknown (skipped in ASCII table) | MEDIUM |
| 5-10 | 6 | `! " # $ % &` | HIGH (from EXE table) |
| 11-12 | 2 | Reserved/unknown (skipped in ASCII table) | MEDIUM |
| 13-30 | 18 | `' ( ) * + , - . / 0-8` | HIGH (from EXE table) |
| 31-32 | 2 | Reserved/unknown (skipped in ASCII table) | MEDIUM |
| 33-93 | 61 | `9 : ; < = > ? @ A-Z [ \ ] ^ _ ` `` a-n` (skip 87-88) `o p q r s` | HIGH (from EXE table) |
| 87-88 | 2 | Reserved/unknown (skipped in ASCII table) | MEDIUM |
| 94-99 | 6 | Likely `t u v w x y` (continuation of ASCII) | LOW (not in EXE table) |

### Skipped Glyph Indices

The following glyph indices are NOT in the 84-entry ASCII lookup table:
- **0**: Null/padding character (used as stream padding, most frequent token)
- **2, 3, 4**: Unknown purpose -- may be control codes or icons
- **11, 12**: Unknown purpose -- gap between `&` (10) and `'` (13)
- **31, 32**: Unknown purpose -- gap between `8` (30) and `9` (33)
- **87, 88**: Unknown purpose -- gap between `n` (86) and `o` (89)

These gaps suggest the font atlas reserves certain slots for non-ASCII purposes (control codes, cursor icons, special markers, etc.).

### Glyph Sheet Observations

- **Rows 0-5 (glyphs 0-59):** Visible character shapes in the sheet image, consistent with ASCII punctuation, digits, and uppercase letters
- **Rows 6-9 (glyphs 60-99):** Appear much darker/sparser in the glyph sheet. The individual glyph PNGs do contain pixel data (T-s are thin single-pixel strokes at 12x12), but the sheet rendering makes them appear blank. This is likely because lowercase letters and late-alphabet uppercase have thinner strokes that don't show well at the sheet's zoom level.

### Confidence: 78/100 identified with HIGH confidence

- 78 glyphs confirmed from EXE ASCII table (indices 1, 5-10, 13-30, 33-86 excluding 87-88, 89-93)
- 9 glyphs marked as reserved/unknown (indices 0, 2-4, 11-12, 31-32, 87-88)
- 6 glyphs tentatively identified as t-y (indices 94-99, LOW confidence)

### Relation to Japanese Content

Glyph 94 is hypothesized in `GLYPH_MAPPING_PLAN.md` as the potential start of the Japanese character block (first non-ASCII glyph). If indices 94-99 are indeed `t`-`y`, then Japanese content likely starts at around glyph 100 or later. The Japanese glyph mapping lives in BSS RAM at 0x5191F0, loaded from game resources at runtime, and is not present in the EXE.
