# Fix: Banner "New Reg." (was 新規登録)

## Problem

The chargen title banner "新規登録" (New Registration) was still showing Japanese kanji in v22 despite menu_labels.csv rows 11, 12, 18, 19 being configured to replace the font atlas tiles.

## Root Cause

**Glyph ID collision between banner tiles and stat label tiles.**

The banner uses R1272 font atlas glyph IDs via EXE menu struct records:

| Kanji | EXE Offset | Glyph IDs |
|-------|-----------|-----------|
| 新    | 0x3C33F0  | 719, 720  |
| 規    | 0x3C3428  | 721, 722  |
| 登    | 0x3C3268  | 705, 706  |
| 録    | 0x3C32A0  | 707, 708  |

The menu_labels.csv had rows that wrote English text ("new", " ", "reg", ".") to these glyph positions. However, **stat label entries** (`stat_719`, `stat_720`, `stat_721`) also wrote to glyphs 719-721 for the party status screen stat abbreviations (AGI, LCK). Since stat entries come later in the CSV, they overwrote the banner tiles:

- Glyph 719: banner wanted "new" -> stat overwrote with "i" (part of AGI)
- Glyph 720: banner wanted "" -> stat overwrote with "lc" (part of LCK)
- Glyph 721: banner wanted "" -> stat overwrote with "k" (part of LCK)

Result: banner showed garbled fragments instead of "new reg."

## Fix Applied

**EXE glyph ID patch** -- changed the glyph ID references in the 4 banner EXE records to point to ASCII letter glyph slots instead of kanji slots:

| Position | Was (kanji glyph IDs) | Now (ASCII glyph IDs) | Display |
|----------|----------------------|----------------------|---------|
| 1 (新)   | 719, 720             | 46(N), 69(e)         | Ne      |
| 2 (規)   | 721, 722             | 87(w), 0(space)      | w       |
| 3 (登)   | 705, 706             | 50(R), 69(e)         | Re      |
| 4 (録)   | 707, 708             | 71(g), 14(.)         | g.      |

Banner now reads: **"New Reg."**

## Files Modified

1. **`build/patch_exe.py`** -- Added PATCH 4: Banner Glyph IDs. Replaces all occurrences of old glyph IDs with new ASCII glyph IDs within each 56-byte menu struct record (5-6 u16 values per record).

2. **`data/menu_labels.csv`** -- Changed rows 11, 12, 18, 19 from `abbrev` strategy to `skip`. These rows no longer overwrite the font atlas tiles at glyph positions 705-708, 719-722, leaving them available for stat labels and other kanji usage.

3. **`build/build_full_english_v2.py`** -- Added STEP 6b: EXE patching. After PACKDATA.DIG is written to the ISO, the build now also runs `patch_exe.py` and injects the patched EXE (SLPM_653.78) into the ISO.

## Verification

- `patch_exe.py` tested: all 4 banner records patched (22 u16 values total)
- `render_menu_tiles.py` tested: 194 tiles rendered (down from 196, correct)
- Stat entries stat_719/720/721 now render without collision
- No other code references glyph IDs 705-708 in the english_glyph_table (confirmed empty slots)

## Side Effects

- The original kanji pixels at glyph positions 705-708 are now preserved in the font atlas (previously overwritten with "reg" / "."). If any game text uses these kanji, it will still display correctly.
- Stat labels for AGI (glyph 719="i") and LCK (glyphs 720="lc", 721="k") now render correctly without banner collision.
