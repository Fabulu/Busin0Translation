# v23 R38 Chargen Textbox Overflow Check

**Source:** `C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v23.iso`
**Date:** 2026-05-28

## Constraints

- Chargen description textbox: **3 lines** (max 2 FFFE line breaks)
- Max glyphs per line: **~20** (fullwidth glyphs)

## Race Names (MSG 29-34)

| MSG | Expected | Decoded | Glyphs | Status |
|-----|----------|---------|--------|--------|
| 29 | Human | `human` | 5 | OK |
| 30 | Elf | `elf` | 3 | OK |
| 31 | Gnome | `gnome` | 5 | OK |
| 32 | Dwarf | `dwarf` | 5 | OK |
| 33 | Hobbit | `hobbit` | 6 | OK |
| 34 | Automata | `automata` | 8 | OK |

## Description Messages (MSG 87-148)

### Overflow Issues (57 found)

| MSG | Lines | Line Lengths | Problem | Text |
|-----|-------|-------------|---------|------|
| 87 | 4 | [18, 19, 20, 0] | 4 LINES (3 breaks) | `gets bored easily.|must return to town|often or mood drops.|` |
| 88 | 4 | [14, 15, 15, 0] | 4 LINES (3 breaks) | `fears spirits.|trembles at the|sight of death.|` |
| 89 | 4 | [20, 18, 14, 0] | 4 LINES (3 breaks) | `liｖes to hoard gold.|gets angry if loot|is too scarce.|` |
| 90 | 4 | [19, 20, 17, 0] | 4 LINES (3 breaks) | `dislikes crowds and|large groups. calmer|in small parties.|` |
| 91 | 4 | [18, 16, 20, 0] | 4 LINES (3 breaks) | `enjoys socializing|in large groups.|hates small parties.|` |
| 92 | 4 | [18, 18, 18, 0] | 4 LINES (3 breaks) | `can't resist loot.|item collecting is|their life's goal.|` |
| 93 | 4 | [17, 17, 11, 0] | 4 LINES (3 breaks) | `belieｖes reckless|adｖenturers can't|be trusted.|` |
| 94 | 4 | [20, 16, 20, 0] | 4 LINES (3 breaks) | `deeply interested in|monster biology.|loｖes to study them.|` |
| 95 | 4 | [18, 20, 16, 0] | 4 LINES (3 breaks) | `belieｖes in mystic|power. loｖes gaining|magic knowledge.|` |
| 96 | 4 | [19, 17, 17, 0] | 4 LINES (3 breaks) | `skilled warrior who|seeks battle with|strong opponents.|` |
| 97 | 4 | [18, 18, 19, 0] | 4 LINES (3 breaks) | `an adｖenturer must|adｖenture. staying|idle is unbearable.|` |
| 99 | 4 | [20, 17, 19, 0] | 4 LINES (3 breaks) | `obsessed with traps.|happy on success,|crushed on failure.|` |
| 100 | 4 | [19, 20, 20, 0] | 4 LINES (3 breaks) | `anxious in dungeons|too long. wishes the|undead would ｖanish.|` |
| 101 | 4 | [17, 16, 13, 0] | 4 LINES (3 breaks) | `values recycling.|hates discarding|usable items.|` |
| 102 | 4 | [18, 15, 20, 0] | 4 LINES (3 breaks) | `with maiden bonds,|no need for men|eｖen in hard fights.|` |
| 104 | 4 | [19, 17, 9, 0] | 4 LINES (3 breaks) | `can't forgiｖe those|who slay friendly|monsters.|` |
| 105 | 4 | [19, 17, 17, 0] | 4 LINES (3 breaks) | `liｖes to slay eｖery|monster. despises|cowardly retreat.|` |
| 106 | 4 | [20, 14, 12, 0] | 4 LINES (3 breaks) | `values party action.|dislikes doing|things solo.|` |
| 107 | 4 | [18, 17, 14, 0] | 4 LINES (3 breaks) | `hates fighting and|bloodshed. mourns|fallen allies.|` |
| 108 | 4 | [20, 16, 10, 0] | 4 LINES (3 breaks) | `very short−tempered.|long battles are|maddening.|` |
| 109 | 4 | [20, 19, 19, 0] | 4 LINES (3 breaks) | `born with a merchant|spirit. deeply into|business and trade.|` |
| 110 | 4 | [20, 19, 20, 0] | 4 LINES (3 breaks) | `keen interest in the|opposite sex. bored|by same−sex parties.|` |
| 111 | 4 | [17, 19, 20, 0] | 4 LINES (3 breaks) | `belieｖes they are|the most beautiful.|shocked when harmed.|` |
| 112 | 4 | [17, 15, 14, 0] | 4 LINES (3 breaks) | `happy one moment,|angry the next.|unpredictable.|` |
| 113 | 4 | [20, 15, 19, 0] | 4 LINES (3 breaks) | `thriｖes in hardship.|being healed or|helped feels worse.|` |
| 114 | 4 | [18, 19, 18, 0] | 4 LINES (3 breaks) | `deep bond with own|race. wants nothing|to do with others.|` |
| 115 | 4 | [18, 20, 18, 0] | 4 LINES (3 breaks) | `thinks of nothing.|if others are happy,|they're happy too.|` |
| 116 | 4 | [18, 18, 16, 0] | 4 LINES (3 breaks) | `use eｖerything you|own. hoarding loot|is unforgiｖable.|` |
| 117 | 4 | [16, 18, 11, 0] | 4 LINES (3 breaks) | `gender sets base|stats. men=strong,|women=wise.|` |
| 118 | 4 | [17, 16, 8, 0] | 4 LINES (3 breaks) | `human： high faith|& balanced stats|oｖerall.|` |
| 119 | 4 | [19, 15, 9, 0] | 4 LINES (3 breaks) | `elf： high int & vit|but frail. best|at magic.|` |
| 120 | 4 | [17, 17, 12, 0] | 4 LINES (3 breaks) | `gnome： high faith|& agility. suited|for priests.|` |
| 121 | 4 | [15, 16, 16, 0] | 4 LINES (3 breaks) | `dwarf： slow but|strong with deep|faith. fighters.|` |
| 122 | 4 | [17, 16, 13, 0] | 4 LINES (3 breaks) | `hobbit： small but|agile and lucky.|born thieｖes.|` |
| 123 | 4 | [17, 18, 16, 0] | 4 LINES (3 breaks) | `good=justice. may|turn eｖil. fig mag|pri sam giz bis教|` |
| 124 | 4 | [16, 15, 11, 0] | 4 LINES (3 breaks) | `neutral=no bias.|fig thi mag sam|giz alc mon|` |
| 125 | 4 | [18, 15, 11, 0] | 4 LINES (3 breaks) | `eｖil=self−serｖing.|fig thi mag pri|nin bis alc|` |
| 126 | 4 | [14, 16, 13, 0] | 4 LINES (3 breaks) | `combat expert.|cannot learn any|magic spells.|` |
| 127 | 4 | [17, 15, 12, 0] | 4 LINES (3 breaks) | `lowers trap leｖel|& finds chests.|sorcery lｖ３.|` |
| 128 | 4 | [18, 13, 15, 0] | 4 LINES (3 breaks) | `master of sorcery.|can learn all|sorcery spells.|` |
| 129 | 4 | [18, 18, 16, 0] | 4 LINES (3 breaks) | `holy magic master.|can dispel undead.|all holy spells.|` |
| 130 | 4 | [19, 18, 18, 0] | 4 LINES (3 breaks) | `great exp gain. can|instant−kill foes.|sorcery up to lｖ２.|` |
| 131 | 4 | [19, 14, 10, 0] | 4 LINES (3 breaks) | `knight gear usable.|learns sorcery|up to lｖ５.|` |
| 132 | 4 | [19, 17, 15, 0] | 4 LINES (3 breaks) | `restores hp. dispel|ｖs undead. sorc &|holy magic lｖ６.|` |
| 133 | 4 | [16, 17, 15, 0] | 4 LINES (3 breaks) | `poleaxe weapons.|dispel ｖs undead.|holy magic lｖ５.|` |
| 134 | 4 | [16, 17, 10, 0] | 4 LINES (3 breaks) | `handles alchemy.|sorc & holy magic|up to lｖ４.|` |
| 135 | 4 | [20, 19, 14, 0] | 4 LINES (3 breaks) | `longbow user. lowers|traps, steals items|sorc教holy lｖ３.|` |
| 136 | 4 | [18, 17, 15, 0] | 4 LINES (3 breaks) | `staffs & knuckles.|dispel ｖs undead.|holy magic lｖ５.|` |
| 137 | 4 | [19, 17, 14, 0] | 4 LINES (3 breaks) | `holy aura heals hp.|can learn dispel.|sorc教holy lｖ６.|` |
| 138 | 4 | [19, 15, 12, 0] | 4 LINES (3 breaks) | `remoｖes curses from|equipped items.|sorcery lｖ６.|` |
| 139 | 4 | [18, 18, 12, 0] | 4 LINES (3 breaks) | `great exp & insta−|kill. sees in fog.|sorcery lｖ５.|` |
| 140 | 4 | [16, 19, 12, 0] | 4 LINES (3 breaks) | `dual wields same|weapon type. learns|sorcery lｖ６.|` |
| 141 | 4 | [18, 19, 14, 0] | 4 LINES (3 breaks) | `longbow. best trap|skill. steals items|sorc教holy lｖ４.|` |
| 143 | 4 | [15, 9, 11, 0] | 4 LINES (3 breaks) | `affects sorcery|power and|resistance.|` |
| 144 | 4 | [18, 9, 11, 0] | 4 LINES (3 breaks) | `affects holy magic|power and|resistance.|` |
| 145 | 4 | [15, 18, 20, 0] | 4 LINES (3 breaks) | `affects max hp,|status resistance,|and reｖiｖal success.|` |
| 147 | 4 | [14, 19, 11, 0] | 4 LINES (3 breaks) | `affects breath|resist and critical|hit chance.|` |

### All Descriptions Detail

| MSG | Breaks | Lines | Max Line | Text |
|-----|--------|-------|----------|------|
| 87 | 3 | 4 | 20 | `gets bored easily.|must return to town|often or mood drops.|` **OVERFLOW** |
| 88 | 3 | 4 | 15 | `fears spirits.|trembles at the|sight of death.|` **OVERFLOW** |
| 89 | 3 | 4 | 20 | `liｖes to hoard gold.|gets angry if loot|is too scarce.|` **OVERFLOW** |
| 90 | 3 | 4 | 20 | `dislikes crowds and|large groups. calmer|in small parties.|` **OVERFLOW** |
| 91 | 3 | 4 | 20 | `enjoys socializing|in large groups.|hates small parties.|` **OVERFLOW** |
| 92 | 3 | 4 | 18 | `can't resist loot.|item collecting is|their life's goal.|` **OVERFLOW** |
| 93 | 3 | 4 | 17 | `belieｖes reckless|adｖenturers can't|be trusted.|` **OVERFLOW** |
| 94 | 3 | 4 | 20 | `deeply interested in|monster biology.|loｖes to study them.|` **OVERFLOW** |
| 95 | 3 | 4 | 20 | `belieｖes in mystic|power. loｖes gaining|magic knowledge.|` **OVERFLOW** |
| 96 | 3 | 4 | 19 | `skilled warrior who|seeks battle with|strong opponents.|` **OVERFLOW** |
| 97 | 3 | 4 | 19 | `an adｖenturer must|adｖenture. staying|idle is unbearable.|` **OVERFLOW** |
| 98 | 2 | 3 | 16 | `reacts keenly to|sudden eｖents.|` |
| 99 | 3 | 4 | 20 | `obsessed with traps.|happy on success,|crushed on failure.|` **OVERFLOW** |
| 100 | 3 | 4 | 20 | `anxious in dungeons|too long. wishes the|undead would ｖanish.|` **OVERFLOW** |
| 101 | 3 | 4 | 17 | `values recycling.|hates discarding|usable items.|` **OVERFLOW** |
| 102 | 3 | 4 | 20 | `with maiden bonds,|no need for men|eｖen in hard fights.|` **OVERFLOW** |
| 103 | 2 | 3 | 19 | `belieｖes women haｖe|no place in battle.|` |
| 104 | 3 | 4 | 19 | `can't forgiｖe those|who slay friendly|monsters.|` **OVERFLOW** |
| 105 | 3 | 4 | 19 | `liｖes to slay eｖery|monster. despises|cowardly retreat.|` **OVERFLOW** |
| 106 | 3 | 4 | 20 | `values party action.|dislikes doing|things solo.|` **OVERFLOW** |
| 107 | 3 | 4 | 18 | `hates fighting and|bloodshed. mourns|fallen allies.|` **OVERFLOW** |
| 108 | 3 | 4 | 20 | `very short−tempered.|long battles are|maddening.|` **OVERFLOW** |
| 109 | 3 | 4 | 20 | `born with a merchant|spirit. deeply into|business and trade.|` **OVERFLOW** |
| 110 | 3 | 4 | 20 | `keen interest in the|opposite sex. bored|by same−sex parties.|` **OVERFLOW** |
| 111 | 3 | 4 | 20 | `belieｖes they are|the most beautiful.|shocked when harmed.|` **OVERFLOW** |
| 112 | 3 | 4 | 17 | `happy one moment,|angry the next.|unpredictable.|` **OVERFLOW** |
| 113 | 3 | 4 | 20 | `thriｖes in hardship.|being healed or|helped feels worse.|` **OVERFLOW** |
| 114 | 3 | 4 | 19 | `deep bond with own|race. wants nothing|to do with others.|` **OVERFLOW** |
| 115 | 3 | 4 | 20 | `thinks of nothing.|if others are happy,|they're happy too.|` **OVERFLOW** |
| 116 | 3 | 4 | 18 | `use eｖerything you|own. hoarding loot|is unforgiｖable.|` **OVERFLOW** |
| 117 | 3 | 4 | 18 | `gender sets base|stats. men=strong,|women=wise.|` **OVERFLOW** |
| 118 | 3 | 4 | 17 | `human： high faith|& balanced stats|oｖerall.|` **OVERFLOW** |
| 119 | 3 | 4 | 19 | `elf： high int & vit|but frail. best|at magic.|` **OVERFLOW** |
| 120 | 3 | 4 | 17 | `gnome： high faith|& agility. suited|for priests.|` **OVERFLOW** |
| 121 | 3 | 4 | 16 | `dwarf： slow but|strong with deep|faith. fighters.|` **OVERFLOW** |
| 122 | 3 | 4 | 17 | `hobbit： small but|agile and lucky.|born thieｖes.|` **OVERFLOW** |
| 123 | 3 | 4 | 18 | `good=justice. may|turn eｖil. fig mag|pri sam giz bis教|` **OVERFLOW** |
| 124 | 3 | 4 | 16 | `neutral=no bias.|fig thi mag sam|giz alc mon|` **OVERFLOW** |
| 125 | 3 | 4 | 18 | `eｖil=self−serｖing.|fig thi mag pri|nin bis alc|` **OVERFLOW** |
| 126 | 3 | 4 | 16 | `combat expert.|cannot learn any|magic spells.|` **OVERFLOW** |
| 127 | 3 | 4 | 17 | `lowers trap leｖel|& finds chests.|sorcery lｖ３.|` **OVERFLOW** |
| 128 | 3 | 4 | 18 | `master of sorcery.|can learn all|sorcery spells.|` **OVERFLOW** |
| 129 | 3 | 4 | 18 | `holy magic master.|can dispel undead.|all holy spells.|` **OVERFLOW** |
| 130 | 3 | 4 | 19 | `great exp gain. can|instant−kill foes.|sorcery up to lｖ２.|` **OVERFLOW** |
| 131 | 3 | 4 | 19 | `knight gear usable.|learns sorcery|up to lｖ５.|` **OVERFLOW** |
| 132 | 3 | 4 | 19 | `restores hp. dispel|ｖs undead. sorc &|holy magic lｖ６.|` **OVERFLOW** |
| 133 | 3 | 4 | 17 | `poleaxe weapons.|dispel ｖs undead.|holy magic lｖ５.|` **OVERFLOW** |
| 134 | 3 | 4 | 17 | `handles alchemy.|sorc & holy magic|up to lｖ４.|` **OVERFLOW** |
| 135 | 3 | 4 | 20 | `longbow user. lowers|traps, steals items|sorc教holy lｖ３.|` **OVERFLOW** |
| 136 | 3 | 4 | 18 | `staffs & knuckles.|dispel ｖs undead.|holy magic lｖ５.|` **OVERFLOW** |
| 137 | 3 | 4 | 19 | `holy aura heals hp.|can learn dispel.|sorc教holy lｖ６.|` **OVERFLOW** |
| 138 | 3 | 4 | 19 | `remoｖes curses from|equipped items.|sorcery lｖ６.|` **OVERFLOW** |
| 139 | 3 | 4 | 18 | `great exp & insta−|kill. sees in fog.|sorcery lｖ５.|` **OVERFLOW** |
| 140 | 3 | 4 | 19 | `dual wields same|weapon type. learns|sorcery lｖ６.|` **OVERFLOW** |
| 141 | 3 | 4 | 19 | `longbow. best trap|skill. steals items|sorc教holy lｖ４.|` **OVERFLOW** |
| 142 | 2 | 3 | 20 | `affects damage dealt|with weapons.|` |
| 143 | 3 | 4 | 15 | `affects sorcery|power and|resistance.|` **OVERFLOW** |
| 144 | 3 | 4 | 18 | `affects holy magic|power and|resistance.|` **OVERFLOW** |
| 145 | 3 | 4 | 20 | `affects max hp,|status resistance,|and reｖiｖal success.|` **OVERFLOW** |
| 146 | 2 | 3 | 18 | `affects turn order|in battle.|` |
| 147 | 3 | 4 | 19 | `affects breath|resist and critical|hit chance.|` **OVERFLOW** |
| 148 | 1 | 2 | 8 | `good "g"|` |

## Summary

- Messages checked: 62
- Overflow issues: 57
- Race name issues: 0
