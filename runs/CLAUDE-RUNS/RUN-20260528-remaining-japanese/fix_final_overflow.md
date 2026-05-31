# Fix: Personality Description Overflow (R38 msgs 87-116)

**Date**: 2026-05-28

## Problem

The Sadist personality description (and 27 other personality descriptions) overflow on the status screen. The Japanese originals use 2 lines per description, so the textbox is sized for 2 lines. The English translations were written as 3 lines (3 segments of up to 20 chars each), causing the third line to overflow the textbox boundary.

## Root Cause

All 28 personality descriptions with 3-line English text were overflowing:
- Japanese originals: 2 lines (2 segments separated by ` / `)
- English translations: 3 lines (3 segments separated by ` / `)
- Status screen textbox: sized for 2 lines only

Only 2 descriptions (msg 98 "Sensitive" and msg 103 "Fervor") already fit in 2 lines.

## Fix Applied

Rewrote all 28 overflowing descriptions from 3 lines to 2 lines in:
- `data/translate_chunks/chunk_02_translated.json` (28 entries changed)

Each line segment is <= 20 characters (the `encode_text` wrap limit).

## Changes

| MSG | Personality | Before (3 lines) | After (2 lines) |
|-----|-------------|-------------------|------------------|
| 87 | Fickle | Gets bored easily. / Must return to town / often or mood drops. | Bores easily. Must / go back or sulks. |
| 88 | Coward | Fears spirits. / Trembles at the / sight of Death. | Fears spirits. / Trembles at Death. |
| 89 | Miser | Lives to hoard gold. / Gets angry if loot / is too scarce. | Lives to hoard gold. / Mad if loot is low. |
| 90 | Lonely | Dislikes crowds and / large groups. Calmer / in small parties. | Hates large groups. / Calm in small ones. |
| 91 | Social | Enjoys socializing / in large groups. / Hates small parties. | Loves big groups. / Hates small parties. |
| 92 | Collector | Can't resist loot. / Item collecting is / their life's goal. | Can't resist loot. / Collecting is life. |
| 93 | Wary | Believes reckless / adventurers can't / be trusted. | Distrusts reckless / adventurers deeply. |
| 94 | Nature | Deeply interested in / monster biology. / Loves to study them. | Loves studying / monster biology. |
| 95 | Smart | Believes in mystic / power. Loves gaining / magic knowledge. | Believes in mystic / power. Loves magic. |
| 96 | Aggro | Skilled warrior who / seeks battle with / strong opponents. | Skilled warrior who / seeks strong foes. |
| 97 | Advent | An adventurer must / adventure. Staying / idle is unbearable. | Must adventure. / Hates sitting idle. |
| 99 | Trapper | Obsessed with traps. / Happy on success, / crushed on failure. | Obsessed with traps. / Crushed on failure. |
| 100 | Timid | Anxious in dungeons / too long. Wishes the / undead would vanish. | Anxious in dungeons. / Wishes undead gone. |
| 101 | Ecologist | Values recycling. / Hates discarding / usable items. | Values recycling. / Hates wasting items. |
| 102 | Maiden | With maiden bonds, / no need for men / even in hard fights. | Maiden bonds endure / even the worst odds. |
| 104 | Just | Can't forgive those / who slay friendly / monsters. | Can't forgive those / who slay kind foes. |
| 105 | Slayer | Lives to slay every / monster. Despises / cowardly retreat. | Lives to slay all. / Hates cowardly flee. |
| 106 | Helper | Values party action. / Dislikes doing / things solo. | Values teamwork. / Dislikes going solo. |
| 107 | Pacifist | Hates fighting and / bloodshed. Mourns / fallen allies. | Hates bloodshed. / Mourns lost allies. |
| 108 | Cranky | Very short-tempered. / Long battles are / maddening. | Very short-tempered. / Long fights enrage. |
| 109 | Economist | Born with a merchant / spirit. Deeply into / business and trade. | Born merchant soul. / Loves trade deeply. |
| 110 | Lusty | Keen interest in the / opposite sex. Bored / by same-sex parties. | Keen on other sex. / Bored by same-sex. |
| 111 | Narcissist | Believes they are / the most beautiful. / Shocked when harmed. | Believes they are / the most beautiful. |
| 112 | Moody | Happy one moment, / angry the next. / Unpredictable. | Happy then angry. / Unpredictable mood. |
| 113 | Sadist | Thrives in hardship. / Being healed or / helped feels worse. | Thrives in hardship. / Healing feels worse. |
| 114 | Tribal | Deep bond with own / race. Wants nothing / to do with others. | Deep bond with own / race. Shuns others. |
| 115 | Simple | Thinks of nothing. / If others are happy, / they're happy too. | Thinks of nothing. / Happy if others are. |
| 116 | Frugal | Use everything you / own. Hoarding loot / is unforgivable. | Use everything you / own. Never hoard. |

## Trailing ` / ` Handling

The build pipeline (`build_full_english_v2.py` line 127) already correctly strips trailing empty segments after splitting on ` / `:
```python
while parts and not parts[-1].strip():
    parts.pop()
```
This prevents phantom blank lines from the trailing ` / ` delimiter. No fix needed.

## Validation

All 30 personality descriptions (msgs 87-116) now pass:
- 30/30 PASS: <= 2 lines, each segment <= 20 chars
- 0/30 FAIL
