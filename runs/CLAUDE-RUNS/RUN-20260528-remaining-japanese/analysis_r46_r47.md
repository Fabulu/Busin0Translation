# Analysis: R46 and R47 (type-03 resources with game text)

**Date**: 2026-05-28
**Files analyzed**:
- `extracted/packdata_raw/0046_type03.raw` (22,528 bytes, 11 sectors)
- `extracted/packdata_raw/0047_type03.raw` (4,096 bytes, 2 sectors)

---

## 1. Binary Structure

Both resources share the same format: a 48-byte header containing 3 sub-resource entries (LE, 16 bytes each), followed by 3 sub-resources containing MSG-format glyph streams.

### Header Format (48 bytes)
```
Offset  Size  Description
0x00    16    Sub-resource 0: { index(LE32)=0, size(LE32), offset(LE32), pad(LE32)=0 }
0x10    16    Sub-resource 1: { index(LE32)=1, size(LE32), offset(LE32), pad(LE32)=0 }
0x20    16    Sub-resource 2: { index(LE32)=2, size(LE32), offset(LE32), pad(LE32)=0 }
```

**Critical difference from standard MSG (type-05)**: Sub-resource indices start at 0 (not 1). This is the same format as R1053 (which caused VIF FIFO crashes when injected).

### R46 Layout
| Sub | Offset | Size | Content |
|-----|--------|------|---------|
| 0 | 0x30 | 18,740 | Main bulletin board posts (98 entries, 171 strings) |
| 1 | 0x4970 | 762 | Poster names/handles (43 entries) |
| 2 | 0x4C70 | 2,528 | Thread titles/labels (98 entries, matching Sub0) |
| - | 0x5650 | 432 | Zero padding to 22,528 (sector boundary) |

### R47 Layout
| Sub | Offset | Size | Content |
|-----|--------|------|---------|
| 0 | 0x30 | 1,962 | Combat text (74 entries, 129 strings) |
| 1 | 0x7E0 | 988 | Combat UI instructions (25 entries) |
| 2 | 0xBC0 | 586 | Special ability names/descriptions (27 entries) |
| - | 0xE0A | 502 | Zero padding to 4,096 (sector boundary) |

### Sub-resource Internal Format
Each sub-resource uses MSG glyph stream format:
1. **Offset table**: 4-byte entries (BE uint16 offset + 0x0000 padding)
2. **Some entries have L2 offsets**: BE uint32 pointers deeper into the sub-resource (nested structure, seen in Sub0 of R46 for the first ~25 entries which contain per-"thread" string groups)
3. **Glyph streams**: BE uint16 glyph indices terminated by 0xFFFF
4. **Control codes**: 0xFFFE (line break in bulletin board), 0x0001 (emphasis?), 0x0000 (separator), FF01..FFF0 (color/formatting)

Small alignment gaps (4-12 bytes of zeros) exist between sub-resources.

---

## 2. Content Summary

### R46: Bulletin Board System
This is the town bulletin board -- a forum-style system where NPCs post messages. It is one of the most flavorful and important text resources in the game.

**Sub0** (98 entries, ~171 individual messages): Full bulletin board posts including:
- Discussions about the witch Aurora, dungeon floors 1-10, Princess Oriana
- Vigour Shop ads, job postings, quest hints
- Character interactions (Thurgo, Gido, Pamela, etc.)
- Gameplay tips (use Thru spell, map usage, level-up indicators)
- NPC personality and world-building text

**Sub1** (43 entries): Poster names/handles:
- "Owner: Jin", "Vigour Shop", "Milly", "Pamela", "Anonymous", etc.

**Sub2** (98 entries): Thread titles matching Sub0:
- "[Order Please!]", "[Recovery Spring!]", "[About Personality]", etc.

### R47: Combat Encounter System
**Sub0** (74 entries, 129 strings): Battle text including:
- "Dispel", "Steal", "Formation Change"
- "Had nothing to steal!", "Items full, couldn't steal!"
- "fled in terror!", "stumbled and fell!"
- Stat labels: "HP/Max HP", "Level", "Hit Level", "Attack Power", etc.
- Elemental resistances: "Fire Resistance", "Lightning Resistance", etc.
- Spell incantations: "Shapeless ones, return to your place!"
- "A formidable monster!!", "Fight", "Leave"

**Sub1** (25 entries): Battle UI instructions:
- "Select Allied Action (AA)", "Select your own action"
- "Reset AA -- cannot act this turn", "Swap front/back rows"
- "Select target", "Front row", "Back row"

**Sub2** (27 entries): Special ability names:
- "Fire Breath", "Cold Breath", "Thunder Breath", "Poison Breath"
- "Gaze", "Demon Jump", "Demon Dive", "Canibalism"
- "Knock Back", "Demon Beam", "Mirror Image", "Counter"

---

## 3. Injection Safety Assessment

### WHY R1053 CRASHED but R46/R47 might be safe

R1053 (35,200 byte Sub0) is a genuine hybrid resource: its Sub0 starts with `10 00 00 00 0B 00 00 00` which is NOT an MSG offset table -- it contains actual 3D scene parameters mixed with embedded text strings. Injecting MSG-format data into it corrupted the 3D data, causing VIF FIFO errors.

R46 and R47 are **purely text resources** that happen to be tagged as type-03 in the resource table. Evidence:
1. All three sub-resources begin with valid MSG offset tables (4-byte entries: BE uint16 + 0x0000)
2. 100% of non-header content parses as valid glyph streams terminated by FFFF
3. No 3D data signatures (no VIF codes, no float values, no vertex data)
4. The sub-resource sizes account for all data (header + subs + sector padding = file size)
5. Non-zero byte density (~65%) matches pure text resources, not 3D model data

### INJECTION APPROACH: Safe with Custom Patcher

**The existing `patch_msg_resource.py` CANNOT be used.** It expects a 16-byte sub-header format and would destroy the 48-byte 3-sub-resource structure.

A custom patcher is needed that:
1. Preserves the 48-byte header
2. Rebuilds each sub-resource independently (new offset table + new glyph data)
3. Updates the size and offset fields in the header
4. Maintains alignment gaps between sub-resources
5. Pads to sector boundary

### RISK LEVEL: LOW (with custom patcher)

The resources are purely text. No 3D data will be corrupted. The key safety constraint is:
- **Do NOT increase the sector count** (R46: 11 sectors, R47: 2 sectors). English text is typically shorter in glyph count than Japanese, so this should not be an issue.
- If sector count does increase, the PACKDATA.DIG TOC entry must also be updated.

### RECOMMENDED APPROACH

1. **Write a dedicated `patch_type03_text.py`** that handles the 3-sub-resource format
2. Translate all strings and encode as glyph streams
3. Rebuild each sub-resource with new offset tables
4. Verify sector count does not exceed original
5. Test in-game before full pipeline integration

**Alternative (safer but limited)**: In-place glyph replacement only. Replace Japanese glyph sequences with English ones of equal or shorter length, padding with 0x0000. This avoids offset table rebuilding but limits translation length.

---

## 4. Glyph Coverage

The text uses standard MSG glyph codes. The existing glyph map (1,100 entries) covers the vast majority of codes used. A small number of codes in the text (approximately 15-20 genuine glyphs like 0x01A4, 0x0340, 0x034F, etc.) are unmapped and appear as `[XXXX]` in the decoded output. These represent rare kanji not yet in the map.

---

## 5. Translation Priority

| Resource | Priority | Reason |
|----------|----------|--------|
| R46 | **CRITICAL** | ~7,800 chars of world-building bulletin board text. Most atmospheric untranslated content in the game. |
| R47 | **HIGH** | ~550 chars of combat UI text. Player-facing battle mechanics. |

R46 is the single largest untranslated text resource in the game and contains crucial flavor text that makes the town feel alive.

---

## 6. String Duplication Pattern

R46 Sub0 has a nested structure: entries 0-24 are "thread groups" containing L2 (BE uint32) pointers to strings. Entries 25-97 are "direct" entries pointing to the same strings individually. This means 97 unique strings appear twice (170 total, 97 unique).

The same pattern holds for Sub2 (170 strings, 97 unique) and R47 Sub0 (126 strings, 72 unique). Sub1/Sub2 in R47 have no duplicates.

**For translation**: Only 97 unique R46 posts + 43 names + 97 titles + 72 R47 combat + 24 R47 UI + 26 R47 abilities = ~359 unique strings need translation.

**For injection**: The nested L2 pointer structure MUST be preserved. Thread groups in entries 0-24 reference strings via absolute offsets into Sub0. If string data moves (due to different English lengths), ALL L2 pointers must be recalculated.

---

## 7. Decoded Text Dump

Full decoded text saved to: `r46_r47_decoded_text.json`
- R46: 382 decoded strings (170 unique in Sub0, 43 in Sub1, 170 in Sub2)
- R47: 176 decoded strings (126 in Sub0, 24 in Sub1, 26 in Sub2)
