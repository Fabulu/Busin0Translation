# Label Overflow Audit: R38 Single-Line Labels

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6

---

## Rendering Facts

- **Glyph advance**: 12px per glyph (both JP kanji/kana and EN Latin letters)
- **Description box width**: 224px = ~18 glyphs max per line (VA 0x305980)
- **Selection list items**: rendered in the same glyph system; overflow occurs when English text is wider than the original Japanese text, since the UI element width was designed for the JP glyph count

**Rule**: If `len(english) > len(japanese)`, the English text occupies more pixels than the original and WILL overflow the allocated UI space by `(en_len - jp_len) * 12` pixels.

---

## Category 1: RACE NAMES (MSG 29-34) -- Selection List in Phase 3

| MSG | Japanese | JP Glyphs | English | EN Chars | Overflow | Proposed Fix |
|-----|----------|-----------|---------|----------|----------|-------------|
| 29 | 人壁 | 2 | Human | 5 | +3 (36px) | **Human** (keep -- standard RPG term) |
| 30 | エルフ | 3 | Elf | 3 | 0 | OK |
| 31 | ノーム | 3 | Gnome | 5 | +2 (24px) | **Gnome** (keep) or "Gnom" |
| 32 | ドワーフ | 4 | Dwarf | 5 | +1 (12px) | **Dwarf** (keep -- minor overflow) |
| 33 | ホビット | 4 | Hobbit | 6 | +2 (24px) | **Hobit** or **Hobbt** |
| 34 | オートマター | 6 | Automata | 8 | +2 (24px) | **Automa** or **Auto** |

**Context**: The race selection list shows 6 races vertically. The longest JP name is オートマター at 6 glyphs, so the selection box width is likely designed for ~6 glyphs = 72px. All EN names except Elf overflow.

**Recommendation**: The real question is how wide the selection highlight box actually is. If it's 6 glyphs wide (72px), then anything > 6 chars overflows. If it's wider (e.g., designed with padding), more might fit. "Human" (5) and "Gnome" (5) and "Dwarf" (5) may all render fine if the box has even 1-2 glyphs of padding. The critical overflows are:
- **Automata (8)** -- definitely overflows any reasonable box. Shorten to **"Automa"** (6) or **"Auto"** (4).
- **Hobbit (6)** -- right at the edge. May fit if box = 6 glyphs. Keep as-is and test.

---

## Category 2: CLASS NAMES (MSG 37-53) -- Selection List in Phase 5

| MSG | Japanese | JP Glyphs | English | EN Chars | Overflow | Proposed Fix |
|-----|----------|-----------|---------|----------|----------|-------------|
| 37 | 戦士 | 2 | Fighter | 7 | +5 (60px) | **Fightr** or **Fight.** or keep |
| 38 | 盗賊 | 2 | Thief | 5 | +3 (36px) | Keep |
| 39 | 騎事務 | 3 | Mage | 4 | +1 (12px) | Keep |
| 40 | 神聖 | 2 | Priest | 6 | +4 (48px) | Keep |
| 41 | 忍者 | 2 | Ninja | 5 | +3 (36px) | Keep |
| 43 | 集教 | 2 | Bishop | 6 | +4 (48px) | Keep |
| 44 | 兵士 | 2 | Samurai | 7 | +5 (60px) | **Samuri** or keep |
| 45 | 冒金事務 | 4 | Alchemist | 9 | +5 (60px) | **Alchem** or **Alchm.** |
| 46 | 義賊 | 2 | Gizoku | 6 | +4 (48px) | Keep (JP loan term) |
| 47 | モンク | 3 | Monk | 4 | +1 (12px) | Keep |
| 48 | 聖兵士 | 3 | Paladin | 7 | +4 (48px) | **Paladn** or keep |
| 49 | 暗兵士 | 3 | Dark Knight | 11 | +8 (96px) | **DrkKnt** or **D.Kngt** |
| 50 | 将後 | 2 | Shogun | 6 | +4 (48px) | Keep (JP loan term) |
| 51 | 教授 | 2 | Knight | 6 | +4 (48px) | Keep |
| 52 | 美盗 | 2 | High Thief | 10 | +8 (96px) | **HiThif** or **H.Thf** |
| 53 | 飽き果 | 3 | Omnitsu | 7 | +4 (48px) | **Omnits** or keep |

**Context**: 16 classes displayed in a list (likely 2 columns of 8, using the "slti 7" or "slti 10" handler). Most JP class names are 2-3 glyphs. The selection box width is probably designed for ~4 glyphs = 48px.

**Critical overflows**:
- **Dark Knight (11)** -- by far the worst. Shorten to **"DrkKnt"** (6) or **"DkKngt"** (6).
- **High Thief (10)** -- very bad. Shorten to **"HiThif"** (6) or **"Outlaw"** (6).
- **Alchemist (9)** -- bad. Shorten to **"Alchem"** (6).
- **Fighter (7)**, **Samurai (7)**, **Paladin (7)**, **Omnitsu (7)** -- moderate.

---

## Category 3: PERSONALITY NAMES (MSG 55-82) -- Selection List in Phase 6

| MSG | Japanese | JP Glyphs | English | EN Chars | Overflow | Proposed Fix |
|-----|----------|-----------|---------|----------|----------|-------------|
| 55 | れ全費 | 3 | Wasteful | 8 | +5 | **Waste** (5) |
| 56 | 孤独 | 2 | Lonely | 6 | +4 | **Lonely** or **Lone** |
| 57 | 社交的 | 3 | Sociable | 8 | +5 | **Social** (6) |
| 58 | 収集家 | 3 | Collector | 9 | +6 | **Collct** (6) |
| 59 | 慎重 | 2 | Cautious | 8 | +6 | **Wary** (4) |
| 60 | 与蓄家 | 3 | Hoarder | 7 | +4 | **Hoard** (5) |
| 61 | 知的 | 2 | Intellectual | 12 | +10 | **Smart** (5) or **Brainy** (6) |
| 62 | 好戦的 | 3 | Belligerent | 11 | +8 | **Warlik** (6) or **Aggro** (5) |
| 63 | 冒険家 | 3 | Adventurous | 11 | +8 | **Advent** (6) or **Bold** (4) |
| 64 | 迷信家 | 3 | Superstitious | 13 | +10 | **Suprst** (6) or **Mystic** (6) |
| 65 | 勤勉務 | 3 | Studious | 8 | +5 | **Studis** (6) |
| 66 | 効向け | 3 | Pusillanimous | 13 | +10 | **Timid** (5) or **Coward** (6) |
| 67 | エコロジスト | 6 | Ecologist | 9 | +3 | **Ecolog** (6) |
| 68 | 乙女心 | 3 | Maiden Heart | 12 | +9 | **Maiden** (6) |
| 69 | 重腕漢 | 3 | Hot-Blooded | 11 | +8 | **Fervor** (6) or **HotBld** (6) |
| 70 | 多義感 | 3 | Just | 4 | +1 | Keep |
| 71 | 勤ち気 | 3 | Determined | 10 | +7 | **Resolv** (6) |
| 72 | 協力的 | 3 | Cooperative | 11 | +8 | **CoopOp** (6) or **Helper** (6) |
| 73 | 友愛 | 2 | Fraternal | 9 | +7 | **Frater** (6) or **Kindly** (6) |
| 74 | 短気 | 2 | Short-Tempered | 14 | +12 | **Cranky** (6) or **Temper** (6) |
| 75 | エコノミスト | 6 | Economist | 9 | +3 | **Econom** (6) |
| 76 | 好色 | 2 | Lustful | 7 | +5 | **Lusty** (5) |
| 77 | ナルシスト | 5 | Narcissist | 10 | +5 | **Narcis** (6) |
| 78 | 気分屋 | 3 | Moody | 5 | +2 | Keep |
| 79 | 自己的 | 3 | Sadist | 6 | +3 | Keep |
| 80 | 種族愛 | 3 | Tribal Love | 11 | +8 | **Tribal** (6) |
| 81 | 大胆 | 2 | Bold | 4 | +2 | Keep |
| 82 | 除味家 | 3 | Stupid | 6 | +3 | Keep |

**Context**: 28 personality traits displayed in a scrolling list. Most JP names are 2-3 glyphs. The worst offenders are:
- **Short-Tempered (14)** -- catastrophic overflow (+12)
- **Superstitious (13)** and **Pusillanimous (13)** -- catastrophic (+10)
- **Intellectual (12)** and **Maiden Heart (12)** -- catastrophic (+10, +9)
- **Belligerent (11)**, **Adventurous (11)**, **Hot-Blooded (11)**, **Cooperative (11)**, **Tribal Love (11)** -- severe (+8)

---

## Category 4: HEADER / FIELD LABELS (MSG 12-17)

These labels appear in different UI contexts (stat panels, field labels on the confirmation screen).

| MSG | Japanese | JP Glyphs | English | EN Chars | Overflow | Proposed Fix |
|-----|----------|-----------|---------|----------|----------|-------------|
| 12 | 条果 | 2 | Alignment | 9 | +7 | **Align** (5) |
| 13 | 職業 | 2 | Class | 5 | +3 | Keep |
| 14 | 果性 | 2 | Gender | 6 | +4 | Keep or **Sex** (3) |
| 15 | 騎事務騎法 | 5 | Sorcery | 7 | +2 | Keep |
| 16 | 神聖騎法 | 4 | Holy Magic | 10 | +6 | **H.Magic** (7) or **Divine** (6) |
| 17 | 能力値 | 3 | Attributes | 10 | +7 | **Stats** (5) or **Attrs** (5) |

---

## Category 5: STAT LABELS (MSG 83-86)

| MSG | Japanese | JP Glyphs | English | EN Chars | Overflow | Proposed Fix |
|-----|----------|-----------|---------|----------|----------|-------------|
| 83 | 獲得力 | 3 | Attack | 6 | +3 | **ATK** (3) |
| 84 | 命中果 | 3 | Accuracy | 8 | +5 | **ACC** (3) or **Hit** (3) |
| 85 | 解消力 | 3 | Defense | 7 | +4 | **DEF** (3) |
| 86 | 回避果 | 3 | Evasion | 7 | +4 | **EVA** (3) or **EVD** (3) |

---

## Category 6: MOON NAMES (MSG 27-28)

| MSG | Japanese | JP Glyphs | English | EN Chars | Overflow | Proposed Fix |
|-----|----------|-----------|---------|----------|----------|-------------|
| 27 | イオ | 2 | Io | 2 | 0 | OK |
| 28 | エウロパ | 4 | Europa | 6 | +2 | Keep (proper noun) |

---

## Summary: Severity Tiers

### TIER 1 -- CATASTROPHIC (overflow > 8 chars, must fix)

| MSG | Category | Current | Overflow | Suggested |
|-----|----------|---------|----------|-----------|
| 74 | Personality | Short-Tempered | +12 | **Cranky** |
| 64 | Personality | Superstitious | +10 | **Suprst** |
| 66 | Personality | Pusillanimous | +10 | **Timid** |
| 61 | Personality | Intellectual | +10 | **Smart** |
| 68 | Personality | Maiden Heart | +9 | **Maiden** |
| 58 | Personality | Collector | +9 | **Collct** |
| 73 | Personality | Fraternal | +7 | **Kindly** |
| 49 | Class | Dark Knight | +8 | **DrkKnt** |
| 52 | Class | High Thief | +8 | **HiThif** |
| 62 | Personality | Belligerent | +8 | **Aggro** |
| 63 | Personality | Adventurous | +8 | **Advent** |
| 69 | Personality | Hot-Blooded | +8 | **Fervor** |
| 72 | Personality | Cooperative | +8 | **Helper** |
| 80 | Personality | Tribal Love | +8 | **Tribal** |

### TIER 2 -- SEVERE (overflow 5-7 chars, should fix)

| MSG | Category | Current | Overflow | Suggested |
|-----|----------|---------|----------|-----------|
| 12 | Header | Alignment | +7 | **Align** |
| 17 | Header | Attributes | +7 | **Stats** |
| 16 | Header | Holy Magic | +6 | **Divine** |
| 37 | Class | Fighter | +5 | Keep (standard term) |
| 44 | Class | Samurai | +5 | Keep (standard term) |
| 45 | Class | Alchemist | +5 | **Alchem** |
| 55 | Personality | Wasteful | +5 | **Waste** |
| 57 | Personality | Sociable | +5 | **Social** |
| 65 | Personality | Studious | +5 | **Studis** |
| 76 | Personality | Lustful | +5 | **Lusty** |
| 77 | Personality | Narcissist | +5 | **Narcis** |
| 71 | Personality | Determined | +7 | **Resolv** |
| 84 | Stat | Accuracy | +5 | **ACC** |

### TIER 3 -- MODERATE (overflow 3-4 chars, fix if possible)

All remaining overflows with +3 to +4 difference. These include most class names (Thief, Ninja, Mage, Priest, Bishop, etc.) and shorter personality names (Moody, Sadist, Bold, Just, etc.).

### TIER 4 -- MINOR (overflow 1-2 chars, likely OK)

| MSG | Category | Current | Overflow |
|-----|----------|---------|----------|
| 32 | Race | Dwarf | +1 |
| 39 | Class | Mage | +1 |
| 47 | Class | Monk | +1 |
| 70 | Personality | Just | +1 |
| 78 | Personality | Moody | +2 |
| 81 | Personality | Bold | +2 |

These will likely render fine with any padding in the UI elements.

---

## Recommended Short-Form Translations

Below are the recommended translations that balance readability with the 6-char target (matching the longest JP label, オートマター/エコロジスト at 6 glyphs).

### Race Names (target: 6 chars max)
```
Human   (5) -- keep
Elf     (3) -- keep
Gnome   (5) -- keep
Dwarf   (5) -- keep
Hobbit  (6) -- keep (right at limit)
Automa  (6) -- was "Automata" (8)
```

### Class Names (target: 6 chars max, but many standard RPG terms are 7)
```
Fighter (7) -- keep (widely recognized)
Thief   (5) -- keep
Mage    (4) -- keep
Priest  (6) -- keep
Ninja   (5) -- keep
Bishop  (6) -- keep
Samurai (7) -- keep (widely recognized)
Alchem  (6) -- was "Alchemist" (9)
Gizoku  (6) -- keep
Monk    (4) -- keep
Paladn  (6) -- was "Paladin" (7), or keep at 7
DrkKnt  (6) -- was "Dark Knight" (11)
Shogun  (6) -- keep
Knight  (6) -- keep
HiThif  (6) -- was "High Thief" (10), alt: "Outlaw" (6)
Omnits  (6) -- was "Omnitsu" (7), or keep at 7
```

### Personality Names (target: 6 chars max)
```
Waste   (5) -- was "Wasteful" (8)
Lonely  (6) -- keep
Social  (6) -- was "Sociable" (8)
Collct  (6) -- was "Collector" (9), alt: "Gather" (6)
Wary    (4) -- was "Cautious" (8)
Hoardr  (6) -- was "Hoarder" (7)
Smart   (5) -- was "Intellectual" (12)
Aggro   (5) -- was "Belligerent" (11), alt: "Warlik" (6)
Advent  (6) -- was "Adventurous" (11)
Suprst  (6) -- was "Superstitious" (13), alt: "Mystic" (6)
Studis  (6) -- was "Studious" (8)
Timid   (5) -- was "Pusillanimous" (13)
Ecolog  (6) -- was "Ecologist" (9)
Maiden  (6) -- was "Maiden Heart" (12)
Fervor  (6) -- was "Hot-Blooded" (11)
Just    (4) -- keep
Resolv  (6) -- was "Determined" (10)
Helper  (6) -- was "Cooperative" (11)
Kindly  (6) -- was "Fraternal" (9)
Cranky  (6) -- was "Short-Tempered" (14)
Econom  (6) -- was "Economist" (9)
Lusty   (5) -- was "Lustful" (7)
Narcis  (6) -- was "Narcissist" (10)
Moody   (5) -- keep
Sadist  (6) -- keep
Tribal  (6) -- was "Tribal Love" (11)
Bold    (4) -- keep
Stupid  (6) -- keep
```

### Header/Field Labels (target: match JP width)
```
Align   (5) -- was "Alignment" (9)
Class   (5) -- keep
Gender  (6) -- keep
Sorcry  (6) -- was "Sorcery" (7), or keep at 7
Divine  (6) -- was "Holy Magic" (10)
Stats   (5) -- was "Attributes" (10)
```

### Stat Labels (target: 3 chars = JP width)
```
ATK     (3) -- was "Attack" (6)
ACC     (3) -- was "Accuracy" (8)
DEF     (3) -- was "Defense" (7)
EVA     (3) -- was "Evasion" (7)
```

---

## Next Steps

1. **Test in-game first**: Before applying any shortening, test the current translations in PCSX2 to see the actual visual overflow. The selection boxes may have more padding than the strict JP glyph count suggests.
2. **Apply Tier 1 fixes immediately**: The 14 catastrophic overflows (Short-Tempered, Superstitious, Pusillanimous, Dark Knight, etc.) will definitely overflow and need shortening regardless of box width.
3. **Update chunk_02_translated.json**: Apply the shortened translations via the build pipeline.
4. **Consider halfwidth font**: If a halfwidth (6px advance) Latin font is implemented, ALL overflow issues disappear since English at 6px would be half the width of JP at 12px. This is the ideal long-term solution but requires significant renderer work.
