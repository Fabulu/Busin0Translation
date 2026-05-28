# Encoding Pipeline Verification -- FINDINGS

**Date:** 2026-05-22
**Target:** Resource 49, message 0 ("Nothing unusual")
**Scope:** Encoder correctness, font atlas positions, resource injection integrity

---

## 1. Translation Source Discrepancy

The task references the translation from `data/translations_dungeon_story.json`:
- **translations_dungeon_story.json:** `"Nothing unusual here."` (resource_49, message 0)

But the actual build pipeline (`build/build_full_english.py`) reads from chunk files:
- **data/translate_chunks/chunk_08_translated.json line 444:** `"Nothing unusual. / "`

These are TWO DIFFERENT translation sources with different text. The build uses the chunk files, not the hand-curated translations_dungeon_story.json.

## 2. Trailing ` / ` Separator Bug (CRITICAL)

**Every translation in the chunk files has a trailing ` / ` separator.**

Examples from chunk_08_translated.json:
```
message 0: "Nothing unusual. / "
message 1: "Can't open from\nthis side. / "
message 5: "It's locked. / "
```

The ` / ` is a chunk format artifact (message separator), NOT intended game text. The `encode_text()` function treats it as literal characters, encoding:
- space -> glyph 1
- `/` -> glyph 26

This means **every single translated message has a trailing space-slash appended** in-game.

### Impact on message 0 glyph stream

Expected (clean): `N o t h i n g [sp] u n u s u a l .`
= `[125, 47, 52, 40, 41, 46, 39, 1, 53, 46, 53, 51, 53, 33, 44, 30]` (16 glyphs)

Actual (with artifact): `N o t h i n g [sp] u n u s u a l . [sp] /`
= `[125, 47, 52, 40, 41, 46, 39, 1, 53, 46, 53, 51, 53, 33, 44, 30, 1, 26]` (18 glyphs)

## 3. Multi-Message Entries Not Split (CRITICAL)

Some chunk entries contain multiple game messages joined by ` / `:

```json
{
    "resource": 49, "message": 3,
    "japanese": "Switch is off / Turned switch on / ",
    "english": "The switch is off. / Turned the\nswitch on. / "
}
```

The game stores these as **separate FFFF-delimited messages** (message 3 = first part, message 4 = second part), but the chunk file packs them into a single entry with message index 3. The build script replaces message 3's glyph stream with the concatenated text of both sub-messages, and message 4 gets no translation (falls back to original Japanese).

This is **structurally wrong** -- it conflates sub-messages that the game engine expects to be separate FFFF-delimited entries.

## 4. Glyph Table Verification (CORRECT)

The glyph table (`data/english_glyph_table.json`) maps characters correctly:

| Char | Glyph ID | Verified |
|------|----------|----------|
| N    | 125      | Correct  |
| o    | 47       | Correct  |
| t    | 52       | Correct  |
| h    | 40       | Correct  |
| i    | 41       | Correct  |
| n    | 46       | Correct  |
| g    | 39       | Correct  |
| (sp) | 1        | Correct  |
| u    | 53       | Correct  |
| s    | 51       | Correct  |
| a    | 33       | Correct  |
| l    | 44       | Correct  |
| .    | 30       | Correct  |

The encoder (`tools/encode_english_text.py`) itself is correct -- it faithfully maps characters to glyph IDs using the table.

## 5. Font Atlas Verification (CORRECT)

The font atlas (`tools/generate_font_atlas.py`) uses a 21-column, 12x12px cell grid on a 256x512 atlas. Glyph slot positions:

| Char | Slot | Grid (col,row) | Pixel (x,y)   |
|------|------|-----------------|----------------|
| N    | 125  | (20, 5)         | (240, 60)      |
| o    | 47   | (5, 2)          | (60, 24)       |
| t    | 52   | (10, 2)         | (120, 24)      |
| h    | 40   | (19, 1)         | (228, 12)      |
| i    | 41   | (20, 1)         | (240, 12)      |
| n    | 46   | (4, 2)          | (48, 24)       |
| g    | 39   | (18, 1)         | (216, 12)      |
| u    | 53   | (11, 2)         | (132, 24)      |
| A    | 112  | (7, 5)          | (84, 60)       |

Visual inspection of `build/english_font_atlas_preview.png` confirms characters are rendered at the correct grid positions. Lowercase a-z occupy row 1-2, uppercase A-Z occupy rows 5-6.

## 6. Resource Injection Logic (PARTIALLY CORRECT)

The build script (`build/build_full_english.py`) injection logic at lines 66-104:

**Correct aspects:**
- Finds message boundaries via FFFF delimiters
- Preserves pre-message header region (offset table)
- Updates sub-header payload_size
- Pads to sector boundary

**Potential issue:** The first-marker scan (line 67-70) looks for either 0xFFFF or 0xFFFE. If the first control word in the payload is an 0xFFFE (line break within message 0), the message boundary parser would start mid-message, misaligning all subsequent message indices. This depends on the specific resource format. For resource 49 (type01, Format A with offset table), the first marker should be 0xFFFF, so this may not be an issue for this specific resource.

## 7. `encode_all_translations.py` Does Not Process Resource 49 (CRITICAL)

The `encoded_translations.json` file only contains resources 34 and 36. The encoder at `tools/encode_all_translations.py` cannot handle the nested dict structure of `translations_dungeon_story.json`:

```
resource_49_dungeon_exploration.messages.0.english
```

The code at lines 19-23 iterates top-level dict keys but never recurses into `messages.{id}.english`. This means the hand-curated translations in `translations_dungeon_story.json` (resource 49) and `translations_menus.json` (resource 35 with `"en"` not `"english"`) are **silently dropped**.

However, this is moot for the actual build since `build_full_english.py` reads from chunk files instead.

---

## Summary of Issues

| # | Component | Severity | Description |
|---|-----------|----------|-------------|
| 1 | Chunk data | CRITICAL | Every translation has trailing ` / ` that gets encoded as literal glyphs (space + slash visible in-game) |
| 2 | Chunk data | CRITICAL | Multi-part messages (e.g., "switch off / switch on") are concatenated into one entry instead of split across message indices |
| 3 | encode_all_translations.py | HIGH | Cannot parse nested dict translation files (dungeon_story, menus); silently drops them |
| 4 | Translation sources | MEDIUM | Two competing translation sources (chunk files vs. curated JSON files) with different text |
| 5 | Glyph table | OK | Character-to-glyph mapping is correct |
| 6 | encode_english_text.py | OK | Encoder logic is correct (word wrap, line/page breaks work properly) |
| 7 | Font atlas | OK | Character rendering at correct grid positions verified |
| 8 | Resource injection | OK* | Logic is sound but depends on correct input data |

## Root Cause

The encoding pipeline itself (encoder + font atlas + injector) is mechanically correct. The corruption is in the **input data**: the chunk translation files contain ` / ` separators that are treated as literal text. Fixing this requires either:

1. Stripping trailing ` / ` from all chunk translations before encoding, OR
2. Switching the build script to use the hand-curated translation files (which have clean text but a different JSON structure requiring a new parser)

## Files Examined

- `C:/Programmieren/wizardrytranslation/data/english_glyph_table.json` -- glyph mapping table
- `C:/Programmieren/wizardrytranslation/tools/encode_english_text.py` -- text-to-glyph encoder
- `C:/Programmieren/wizardrytranslation/tools/encode_all_translations.py` -- batch encoder (broken for nested formats)
- `C:/Programmieren/wizardrytranslation/build/build_full_english.py` -- master build script
- `C:/Programmieren/wizardrytranslation/data/translate_chunks/chunk_08_translated.json` -- source of resource 49 translations
- `C:/Programmieren/wizardrytranslation/data/translations_dungeon_story.json` -- curated translations (unused by build)
- `C:/Programmieren/wizardrytranslation/build/packdata_resources/0049_type01.raw` -- patched resource (6144 bytes, up from 4096 original)
- `C:/Programmieren/wizardrytranslation/extracted/packdata_raw/0049_type01.raw` -- original Japanese resource
- `C:/Programmieren/wizardrytranslation/tools/generate_font_atlas.py` -- font atlas generator
- `C:/Programmieren/wizardrytranslation/build/english_font_atlas_preview.png` -- font atlas visual verification
