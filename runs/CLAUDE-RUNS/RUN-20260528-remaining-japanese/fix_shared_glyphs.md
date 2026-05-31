# Fix: Shared Glyph ID Conflicts in Font Atlas Stat Labels

**Date**: 2026-05-28
**Fix applied to**: `data/menu_labels.csv`
**No EXE patch needed**: The stat label glyph IDs are NOT in the EXE; they come from R38/R39/R44 resources.

---

## Problem

The `menu_labels.csv` stat label entries render English text into font atlas positions matching the original Japanese kanji glyph IDs. Three kanji glyph IDs are shared between multiple stat/attribute labels, causing rendering conflicts:

| Shared Glyph | Kanji | Context 1 | Context 2 | Context 3 |
|---|---|---|---|---|
| 346 | 力 (chikara) | STR (standalone) | VIT 3rd char (生命**力**) | |
| 590 | 度 (do) | AGI 3rd char (敏捷**度**) | LCK 3rd char (幸運**度**) | |
| 511 | 性 (sei) | Gender 1st char (**性**別) | Alignment 2nd char (属**性**) | Personality 1st char (**性**格) |

### Before fix (broken rendering via font atlas path)

| Label | Glyphs | Rendered | Problem |
|---|---|---|---|
| STR | [346] | "str" | OK |
| VIT | [718, 696, 346] | "vitstr" | WRONG - 346 renders "str" |
| AGI | [582, 719, 590] | "agi" | OK (590 already blank) |
| LCK | [720, 721, 590] | "lck" | OK (590 already blank) |
| Gender | [511, 512] | "gend" | OK-ish |
| Alignment | [515, 511] | "alge" | WRONG - 511 renders "ge" |
| Personality | [511, 516] | "ge?" | WRONG |

---

## Root Cause Investigation

The task assumed the shared glyph IDs were in a hardcoded EXE table at 0x3AB080-0x3AF080. **This was incorrect.** Exhaustive binary search confirmed:

- Glyph 346 (0x015A) does NOT appear anywhere in the 0x3AB080-0x3AF080 region, in either BE or LE encoding
- The same applies to glyphs 718, 696, 535, 717, 582, 719, 590, 720, 721
- Glyph 511 appeared in that region only as coincidental byte patterns in packed layout data

The actual stat label glyph IDs are stored in **resource files**:
- **R38** (0038_type01.bin): MSG format, BE uint16 glyph IDs at offsets 0x030A-0x0378
- **R39** (0039_type15.bin): Layout descriptor format, stat labels at 0x06D0-0x077E
- **R44** (0044_type01.bin): MSG format, stat labels at 0x0842-0x088A

All three resources are already patched to English ASCII in the build:
- R38 MSG 2 = "str" (glyphs 83,84,82), MSG 5 = "vit" (glyphs 86,73,84)
- R39 has "STR /", "Vital", "Agili" etc.
- R44 has "Change to str", "Change to vit" etc.

The font atlas stat entries in `menu_labels.csv` serve as a **fallback** for any rendering path that uses original Japanese kanji glyph IDs directly (e.g., from the EXE layout table data for the chargen screen).

---

## Fix Applied

Modified `data/menu_labels.csv` stat entries to resolve all three sharing conflicts:

### Glyph 346 (STR/VIT conflict)
- **Changed**: `english` from `"str"` to `""` (blank)
- **Result**: VIT = "vi"+"t"+"" = "vit" (correct). STR via font atlas = blank (acceptable; R38 provides English STR on primary screens).

### Glyph 511 (Gender/Alignment/Personality conflict)
- **Changed**: `english` from `"ge"` to `""` (blank)
- **Changed glyph 512**: `english` from `"nd"` to `"sex"` (gender = ""+"sex" = "sex")
- **Changed glyph 515**: `english` from `"al"` to `"algn"` (alignment = "algn"+"" = "algn")
- **Added glyph 516**: `english` = `"pers"` (personality = ""+"pers" = "pers")

### Glyph 590 (AGI/LCK -- no conflict)
- Already blank in both contexts. No change needed.

### After fix (corrected rendering via font atlas path)

| Label | Glyphs | Rendered | Status |
|---|---|---|---|
| STR | [346] | "" | Blank (R38 provides "str") |
| INT | [535, 717] | "int" | Correct |
| FTH | [308, 354, 320] | "fth" | Correct |
| VIT | [718, 696, 346] | "vit" | FIXED |
| AGI | [582, 719, 590] | "agi" | Correct |
| LCK | [720, 721, 590] | "lck" | Correct |
| Gender | [511, 512] | "sex" | FIXED |
| Alignment | [515, 511] | "algn" | FIXED |
| Personality | [511, 516] | "pers" | FIXED (new) |

---

## No EXE Patch Needed

The original task assumed EXE patching was required. After investigation:
- The EXE `build/patch_exe.py` does NOT need changes for this fix
- The stat label data is in resource files (R38/R39/R44), not in the EXE
- The font atlas approach (patching `menu_labels.csv` -> `render_menu_tiles.py` -> `generate_font_atlas.py`) is the correct fix path
- All changes flow through the existing build pipeline

## Files Modified

- `data/menu_labels.csv` -- Fixed stat_346, stat_511, stat_512, stat_515; added stat_516

## Verification

```
python tools/render_menu_tiles.py
# Output: Rendered 196 menu tiles
# Glyph 346: 0 foreground pixels (blank - correct)
# Glyph 511: 0 foreground pixels (blank - correct)
# Glyph 512: 41 foreground pixels ("sex")
# Glyph 515: 42 foreground pixels ("algn")
# Glyph 516: 50 foreground pixels ("pers")
```
