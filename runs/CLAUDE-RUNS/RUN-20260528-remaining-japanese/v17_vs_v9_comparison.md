# V17 vs V9 Build Comparison: R38 Regression Analysis

**Date**: 2026-05-28
**Method**: Binary extraction of R38 (resource 38, type-01) from ISOs, decoded via english_glyph_table

---

## Key Discovery

**The v9 ISO on disk (`BUSIN0_EN_v9.iso`) is NOT the original v9 build.** It was rebuilt on May 30 at 20:07 and is byte-identical to `BUSIN0_EN_v17.iso` (MD5: `fbeddbd1cf3fef38e1120d4ab7b1a9de`). The original v9 build that produced the `AttributeissuesV9.p2s` save state (May 25 09:10) no longer exists.

**Closest surviving build to v9**: `BUSIN0_EN_v8.iso` (May 25 01:20) -- built ~8 hours before the v9 save state was captured.

---

## Build Timeline

| Build | Date | R38 Size | R38 Msgs | Status |
|-------|------|----------|----------|--------|
| v3 (original JP base) | May 24 23:18 | 12,288 bytes | 189 | Japanese + partial EN (initial glyph injection) |
| v8 (closest to v9 save) | May 25 01:20 | 12,288 bytes | 189 | First full EN labels, Title Case, v8 glyph mapping |
| v9/v17 (current, identical) | May 30 20:07-08 | 10,240 bytes | 189 | Full EN but with regressions |

---

## Regression #1: Message Index Shift (MSG 25-34)

The `chunk_r38_fix.json` translations are shifted by 2 positions for messages 25-34, causing a cascade of wrong labels.

| MSG | v3 (original JP) | v8 (v9 save showed this) | v17 (current) | Expected | BUG? |
|-----|-------------------|--------------------------|---------------|----------|------|
| 25 | Lv7 (fullwidth) | Lv7 | lv7 | lv7 | OK |
| **26** | Male kanji (518) | Male kanji (518) | **lv.6** | male | **YES - shifted** |
| **27** | Female kanji (349) | Female kanji (349) | **lv.7** | female | **YES - shifted** |
| **28** | Io | Io | **male** | io | **YES - shifted** |
| **29** | Europa | Europa | **female** | europa | **YES - shifted** |
| 30 | Human | Human | human | human | OK |
| 31 | Elf | Elf | elf | elf | OK |
| 32 | Gnome | Gnome | gnome | gnome | OK |
| 33 | Dwarf | Dwarf | dwarf | dwarf | OK |
| 34 | Hobbit | Hobbit | hobbit | hobbit | OK |

**Root cause**: `chunk_r38_fix.json` has entries for MSG 25="lv.6", MSG 26="lv.7", MSG 27="male", MSG 28="female". But the actual R38 message layout is:
- MSG 25 = Lv7 (spell level 7)
- MSG 26 = Male (gender kanji 518)
- MSG 27 = Female (gender kanji 349)
- MSG 28 = Io (world name)
- MSG 29 = Europa (world name)

The translation file's message indices are off by 2, pushing "lv.6" into the Male slot and cascading everything down.

**What v9 save showed**: MSG 26 and 27 were still Japanese kanji (518/349 = male/female symbols). They showed correctly as Japanese characters because the build had NOT yet attempted to translate them. The attribute screen showed Japanese gender kanji but otherwise worked fine.

**What v17 shows**: MSG 26 displays "lv.6" where "male" should appear. MSG 27 displays "lv.7" where "female" should appear. MSG 28-29 (Io/Europa world names) are overwritten with "male"/"female".

---

## Regression #2: Alignment Label Triplication (MSG 149-159)

| MSG | v3 (original) | v8 (v9 save) | v17 (current) | Expected | BUG? |
|-----|--------------|--------------|---------------|----------|------|
| 149 | Good "G" | Good "G" | **good "g"** | good "g" | OK |
| **150** | Neutral "N" | Neutral "N" | **good "g"** | neutral "n" | **YES** |
| **151** | Evil "E" | Evil "E" | **good "g"** | evil "e" | **YES** |
| **152** | Good (JP kanji 520) | Good (JP kanji 520) | **neutral "n"** | good | **YES - shifted** |
| **153** | Neutral | Neutral | **evil "e"** | neutral | **YES - shifted** |
| **154** | Evil (JP kanji 289) | Evil (JP kanji 289) | **good** | evil | **YES - shifted** |
| **155** | G | G | **neutral** | g | **YES - shifted** |
| **156** | N | N | **evil** | n | **YES - shifted** |
| **157** | E | E | **g** | e | **YES - shifted** |
| **158** | Lv | Lv | **n** | lv | **YES - shifted** |
| **159** | Commoner | Commoner | **e** | commoner | **YES - shifted** |

**Root cause**: Same shift pattern. `chunk_r38_fix.json` contains translations for MSG 148-156 that are shifted. MSG 149 through 151 all contain "good \"g\"" instead of having distinct values. The shift cascades: "Lv" label (MSG 158) becomes "n", and "Commoner" (MSG 159) reputation label becomes "e".

**What v9 save showed**: MSG 150-151 showed as Japanese kanji (Neutral/Evil), 152/154 showed as single kanji. The alignment selection worked correctly because the original Japanese was preserved.

**What v17 shows**: Selecting any of the three alignment options shows "good" -- the neutral and evil labels are replaced with copies of "good". The shift also corrupts the "Lv" label and "Commoner" reputation name.

---

## Regression #3: Case Change (Cosmetic)

| Category | v8 (v9 save) | v17 (current) |
|----------|-------------|---------------|
| Stat labels | HP, STR, INT, FTH, VIT, AGI, LCK | hp, str, int, fth, vit, agi, lck |
| Field labels | Name, Level, Race, Gender... | name, level, race, gender... |
| Reputation names | Commoner, Hooligan, Evil... | COMMONER, HOOLIGAN, EVIL... |

**v8 used Title Case** for labels (Name, Level, Good) and mixed case for reputation names.
**v17 uses lowercase** for labels (name, level, good) but **UPPERCASE** for some reputation names (HOOLIGAN, EVIL, VICIOUS).

This is cosmetic but inconsistent. The uppercase reputation names appear to be the original v3 glyph mappings bleeding through (v3 used uppercase ASCII glyph IDs 33-58 which map to A-Z).

---

## Regression #4: R38 Size Reduction

R38 shrank from 12,288 bytes (v8) to 10,240 bytes (v17) -- a loss of 2,048 bytes (1 sector). This is because the v17 build encodes English text using fewer glyphs per message (shorter words like "str" vs kanji sequences), and the data fit in 5 sectors instead of 6. The padding is zeroed out. However, the **PACKDATA TOC was correctly updated** from 6 sectors to 5, so this is not a bug per se -- but it means translations that exceed the original byte budget will be silently truncated.

---

## What Was Working in V9 That Broke

1. **Gender labels**: Showed correct Japanese kanji for male/female (not translated yet, but not corrupted)
2. **World names**: Io and Europa showed correctly (either Japanese or English)
3. **Alignment labels**: Good/Neutral/Evil showed correctly (Japanese kanji in v9, correctly distinct)
4. **Reputation labels**: Commoner, Lv, etc. were correct and consistent
5. **Title Case consistency**: All labels were Title Case (Name, Level, Race)

---

## What's New in V17 That Wasn't in V9

1. **Stat labels fully lowercase**: str, int, fth, vit, agi, lck (were uppercase STR/INT in v8, or Japanese kanji in v3)
2. **MSG 3 translated**: "str" instead of raw kanji 346 (was untranslated even in v8)
3. **More messages attempted**: v17 tries to translate MSG 25-29, 149-156 which v8 left as Japanese
4. **R1188 tab labels patched**: Name entry screen tabs (not in R38 but related)

---

## Fix Required

The `chunk_r38_fix.json` has a **message index offset error**. The fix entries need to be re-indexed:

### Gender/World fix:
- Current MSG 25 ("lv.6") -> DELETE (MSG 25 is already lv7 from lv1-lv7 translations)
- Current MSG 26 ("lv.7") -> DELETE
- Current MSG 27 ("male") -> Change to MSG 26 (male)
- Current MSG 28 ("female") -> Change to MSG 27 (female)
- MSG 28 needs "io" (world name), MSG 29 needs "europa"

### Alignment fix:
- MSG 149: should be "neutral \"n\"" (currently "good \"g\"" -- wrong value, not just wrong index)
- MSG 150: should be "evil \"e\"" (currently "good \"g\"")
- MSG 151-159: each shifted by +1, all need re-indexing

### Root cause investigation needed:
The chunk_r38_fix.json was likely generated from a glyph dump that counted messages differently (possibly skipping the palette/header message at MSG 0, or counting FFFE line breaks as message separators instead of FFFF terminators).
