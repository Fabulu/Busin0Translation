# Chargen Description Box Overflow Analysis

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6

---

## Problem Summary

The chargen (character creation) screen has black textboxes that display description text for personality traits, races, classes, alignments, gender, and stats. When English translations are injected, some descriptions overflow the textbox, covering adjacent UI elements.

**Root cause**: The English translations use MORE LINES than the Japanese originals, and the textbox has a fixed height (3 lines max for the description box area).

---

## Key Findings

### 1. Line Width Is NOT the Problem

Japanese lines in the description messages (R38 msgs 53-218) max out at 26 glyphs per line. English lines max out at 22 characters per line. Since both JP and EN glyphs are rendered at 12px (or 24px at 2x scale), the English lines are actually NARROWER than the Japanese. No single EN line exceeds the box width.

**Distribution of EN line lengths** (261 total lines across all descriptions):
- Lines > 16 chars: 125 (48%)
- Lines > 18 chars: 79 (30%)
- Lines > 20 chars: 20 (8%)
- Lines > 22 chars: 0 (0%) -- all lines fit within width

### 2. Line COUNT Is the Problem

The game's description box appears designed for a maximum of 3 lines (matching the JP originals). The render state machine at VA 0x30CEF4 enforces `slti $v0, $s1, 3` for the dialogue-type text handler.

**Line count comparison by category**:

| Category | Msgs | JP Lines (max) | EN Lines (max) | EN Extra Lines |
|----------|------|----------------|----------------|----------------|
| Personality names | 53-88 | 2 | 2 | 0 |
| Personality descs | 89-116 | 2 | 2 | 0 |
| Gender desc | 117 | 2 | 4 | +2 |
| Race descs | 118-122 | 3 | 4 | +1 |
| Alignment descs | 123-125 | 3 | 6 | +3 |
| Class descs | 126-141 | 3 | 6 | +3 |
| Stat descs | 142-147 | 2 | 3 | +1 |
| Other (labels) | 148-218 | 1 | 1 | 0 |

**22 messages have >3 EN lines** (the presumed box limit):
- 6 messages with 6 lines: msgs 123, 132, 133, 136, 139, 141
- 4 messages with 5 lines: msgs 125, 135, 137, 140
- 12 messages with 4 lines: msgs 117-122, 124, 127, 129-131, 138

### 3. Why EN Needs More Lines

Each Japanese glyph (kanji/kana) conveys more semantic content than a single English letter. A 25-glyph Japanese line conveys a full clause, but translating it to English requires 2+ lines of ~20-char text. Example:

```
JP (msg 139, 3 lines):
  Line 1 (26): 経所獲得に長けており、一得で依とめる能力を持ちます。
  Line 2 (25): さらにダークゾーンを見るなどの能力も備えています。
  Line 3 (17): lｖ５までの騎事務騎法を習下可能。

EN (msg 139, 6 lines):
  Line 1 (21): excels at gaining exp
  Line 2 (22): and instant death atk.
  Line 3 (20): can also see through
  Line 4 (15): dark fog zones.
  Line 5 (14): learns sorcery
  Line 6 (10): up to lv5.
```

### 4. Render System Architecture

From the text renderer analysis (analysis_text_renderer.md):
- **MSG Parser** (VA 0x302DB0): Parses glyph streams, handles FFFE newlines, max 32 lines
- **Glyph Layout Engine** (VA 0x303C60): 12-byte slot per glyph, fixed 12px advance
- **Render State Machine** (VA 0x30CE90): Multiple handlers with different line limits:
  - Handler with `slti 3`: 3-line dialogue/description boxes (at VA 0x30CEF4, 0x30CF94, 0x30D0E4, 0x30D16C)
  - Handler with `slti 7`: 7-item menu/status lists (at VA 0x30CF24, 0x30CFEC, 0x30D888, 0x30D9DC, 0x30DA60)
  - Handler with `slti 10`: 10-item extended lists (at VA 0x30DB4C, 0x30DBCC)

- **Display box width**: 224px (at VA 0x305980), allowing ~18 JP glyphs at 12px each
- **Line spacing**: 24px per line
- **Box height for 3 lines**: ~72px (3 x 24px)

---

## Diagnosis

The overflow is caused by **(c) Too many lines in translation, not enough line breaks fitting within the box height**. Specifically:

1. The description textbox supports 3 visible lines (72px tall)
2. English translations frequently require 4-6 lines
3. Lines 4+ overflow the textbox boundary and overlap adjacent UI elements
4. The text IS being rendered (the parser and layout engine handle up to 32 lines), but the textbox background/clipping rectangle does not expand to accommodate them

---

## Proposed Solutions (Ranked by Feasibility)

### Solution A: REWRITE TRANSLATIONS TO FIT 3 LINES (Recommended)

Shorten English descriptions to fit within 3 lines of ~20 chars each (60 chars total per description). This requires tighter, more abbreviated writing.

**Example rewrites for the worst offenders**:

```
MSG 139 (ninja, currently 6 lines -> 3 lines):
  BEFORE: excels at gaining exp / and instant death atk. / can also see through / dark fog zones. / learns sorcery / up to lv5. /
  AFTER:  gains exp fast. can / instant-kill & see / dark zones. sorc lv5. /

MSG 141 (gizoku, currently 6 lines -> 3 lines):
  BEFORE: can equip longbows. / greatly lowers trap / difficulty. can steal / items from enemies. / learns sorcery and / holy magic up to lv4. /
  AFTER:  equip bows. lowers / trap diff & steals. / sorc+holy magic lv4. /

MSG 123 (good alignment, currently 6 lines -> 3 lines):
  BEFORE: good upholds justice / but may turn evil if / acting unjustly. / classes: fig mag pri / sam giz bis kni alc / mon /
  AFTER:  upholds justice. may / turn evil. fig mag / pri sam giz bis+more /
```

**Pros**: No EXE patching needed, works with existing renderer
**Cons**: Some descriptions become very terse/abbreviated

### Solution B: EXE PATCH TO EXPAND TEXTBOX HEIGHT

Patch the render state machine to allow more lines in the description box. The 3-line limit at VA 0x30CEF4 (`28620003` = `slti $v0, $s1, 3`) could be changed to 6 (`28620006`).

**Patch locations** (must determine which specific handler serves chargen descs):
- VA 0x30CEF4 (file 0x20CF74): `28620003` -> `28620006`
- VA 0x30CF94 (file 0x20D014): `28400003` -> `28400006`
- VA 0x30D0E4 (file 0x20D164): `28400003` -> `28400006`
- VA 0x30D16C (file 0x20D1EC): `28400003` -> `28400006`

**WARNING**: Also need to expand the background rectangle height from ~72px to ~144px, or text renders outside the black box. The background draw coordinates are likely set elsewhere in the chargen code (0x2E0000-0x2F0000 area).

**Pros**: Keeps full descriptive text
**Cons**: Risk of breaking other text displays that share the same handler; background box also needs resizing; may overlap other chargen UI elements regardless

### Solution C: HYBRID - EXPAND TO 4 LINES + SHORTEN SLIGHTLY

Patch box to 4 lines (a modest change), then rewrite translations to fit in 4 lines max instead of 3. This gives ~25% more space.

**Feasibility**: 12 of 22 overflow messages are exactly 4 lines, so this would fix 55% of cases with a minimal EXE patch. The remaining 10 messages (5-6 lines) would still need rewriting.

### Solution D: ADD PAGINATION (COMPLEX)

Implement a page system where the description text shows 3 lines at a time and the player presses a button to see the next page. This would require significant EXE modifications to the chargen input handler.

**Feasibility**: Very low - requires major RE and code injection.

---

## Recommended Action Plan

1. **Immediate**: Rewrite all 22 overflow descriptions to fit within 3 lines (Solution A)
   - Focus on msgs 117-141 (gender, race, alignment, class descriptions)
   - Use abbreviations: "sorc" for sorcery, "lv" for level, "&" for "and"
   - Drop redundant phrases like "can learn" -> "learns"
   - Combine related info: "learns sorc+holy lv4"

2. **Optional follow-up**: If 3-line constraint is too restrictive, try expanding to 4 lines (Solution C) by patching the specific handler used for chargen descriptions

3. **Prerequisite for Solution B/C**: Identify exactly which render handler serves the chargen description box (need to trace from the chargen code at VA 0x2F57BC through the resource loading and rendering pipeline)

---

## Messages Requiring Rewrite (22 total)

### Priority 1: 6-line messages (need halving)
| MSG | Category | Current Lines | Current Text |
|-----|----------|---------------|--------------|
| 123 | alignment (good) | 6 | good upholds justice / but may turn evil if / acting unjustly. / classes: fig mag pri / sam giz bis kni alc / mon |
| 132 | class (bishop) | 6 | has the ability to / restore hp. / can learn dispel / to banish undead. / learns sorcery and / holy magic up to lv6. |
| 133 | class (paladin) | 6 | can equip poleaxe / type weapons. / can learn dispel / to banish undead. / learns holy magic / up to lv5. |
| 136 | class (monk) | 6 | can equip staffs / and knuckle weapons. / can learn dispel / to banish undead. / learns holy magic / up to lv5. |
| 139 | class (ninja) | 6 | excels at gaining exp / and instant death atk. / can also see through / dark fog zones. / learns sorcery / up to lv5. |
| 141 | class (gizoku) | 6 | can equip longbows. / greatly lowers trap / difficulty. can steal / items from enemies. / learns sorcery and / holy magic up to lv4. |

### Priority 2: 5-line messages
| MSG | Category | Current Lines | Current Text |
|-----|----------|---------------|--------------|
| 125 | alignment (evil) | 5 | evil favors rest. / some rarely turn to / good. classes: fig / thi mag pri nin bis / alc |
| 135 | class (dark knight) | 5 | can equip longbows. / lowers trap difficulty / and can steal items. / learns sorcery and / holy magic up to lv3. |
| 137 | class (shogun) | 5 | holy aura slowly / restores party hp. / can also learn dispel. / learns sorcery and / holy magic up to lv6. |
| 140 | class (high thief) | 5 | can dual wield / weapons of the same / type simultaneously. / learns sorcery / up to lv6. |

### Priority 3: 4-line messages (minor overflow)
| MSG | Category | Current Lines |
|-----|----------|---------------|
| 117 | gender | 4 |
| 118-122 | race descs | 4 each (5 msgs) |
| 124 | alignment (neutral) | 4 |
| 127 | class (thief) | 4 |
| 129 | class (priest) | 4 |
| 130 | class (samurai) | 4 |
| 131 | class (knight) | 4 |
| 138 | class (alchemist) | 4 |
