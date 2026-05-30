# R38 Full Decode from v17 ISO

## Extraction Details

- **Source:** `build/BUSIN0_EN_v17.iso`
- **PACKDATA.DIG LBA:** 16029 (byte offset 32,827,392)
- **R38 TOC:** sector_offset=1969, sector_count=5, type_code=1
- **R38 absolute offset:** 36,859,904 (0x2327000)
- **Sub-header:** zero1=0, payload_size=8304, stride=0x10 (16), zero2=0
- **Payload:** 8304 bytes, 4152 uint16 values

## Message Count

| Metric | Value |
|--------|-------|
| FFFF delimiters | 189 |
| Message count | 189 |
| Expected (original) | 189 |
| **Match** | **YES** |

## Issues Summary

**MSG 0 is the offset table** (188 x 4-byte LE offsets = 752 bytes). The script decoded these as glyphs,
but they are structural data, not text. This is expected and NOT an issue.

**All 188 actual text messages (MSG 1-188) are fully English.** Zero Japanese glyphs remain.
No unmapped glyphs, no corruption, no unexpected control codes in text messages.

## Specific Checks

### Stat Labels (MSG 1-8) -- ALL ENGLISH

| MSG | Text |
|-----|------|
| 1 | HP |
| 2 | hp/mhp |
| 3 | str |
| 4 | int |
| 5 | fth |
| 6 | vit |
| 7 | agi |
| 8 | lck |

### Gender (MSG 28-29) -- ALL ENGLISH

Note: The user asked for MSG 27-28, but gender labels are at MSG 28-29 in the actual data.

| MSG | Text |
|-----|------|
| 28 | male |
| 29 | female |

### Alignment (MSG 149-159) -- ALL ENGLISH

Note: Alignment labels are at MSG 149-159 (user asked for 150-158).

| MSG | Text | Notes |
|-----|------|-------|
| 149 | good "g" | Full label + abbreviation |
| 150 | good "g" | Duplicate (3 good slots: 149-151) |
| 151 | good "g" | Duplicate |
| 152 | neutral "n" | Full label + abbreviation |
| 153 | evil "e" | Full label + abbreviation |
| 154 | good | Plain label |
| 155 | neutral | Plain label |
| 156 | evil | Plain label |
| 157 | g | Single-letter abbreviation |
| 158 | n | Single-letter abbreviation |
| 159 | e | Single-letter abbreviation |

### Personality Traits (MSG 53-86) -- ALL ENGLISH

| MSG | Text |
|-----|------|
| 53 | high thief |
| 54 | omnitsu |
| 55 | militant |
| 56 | wasteful |
| 57 | lonely |
| 58 | sociable |
| 59 | collector |
| 60 | cautious |
| 61 | hoarder |
| 62 | intellectual |
| 63 | belligerent |
| 64 | adventurous |
| 65 | superstitious |
| 66 | studious |
| 67 | pusillanimous |
| 68 | ecologist |
| 69 | maiden heart |
| 70 | hot-blooded |
| 71 | just |
| 72 | determined |
| 73 | cooperative |
| 74 | fraternal |
| 75 | short-tempered |
| 76 | economist |
| 77 | lustful |
| 78 | narcissist |
| 79 | moody |
| 80 | sadist |
| 81 | tribal love |
| 82 | bold |
| 83 | hobbyist |
| 84 | attack |
| 85 | accuracy |
| 86 | defense |

## Full Message Listing

All 188 text messages decoded (MSG 1-188). MSG 0 is the offset table.

```
MSG   1: HP
MSG   2: hp/mhp
MSG   3: str
MSG   4: int
MSG   5: fth
MSG   6: vit
MSG   7: agi
MSG   8: lck
MSG   9: name
MSG  10: level
MSG  11: race
MSG  12: gender
MSG  13: alignment
MSG  14: class
MSG  15: personality
MSG  16: sorcery
MSG  17: holy magic
MSG  18: attributes
MSG  19: lv1
MSG  20: lv2
MSG  21: lv3
MSG  22: lv4
MSG  23: lv5
MSG  24: lv6
MSG  25: lv7
MSG  26: lv.6
MSG  27: lv.7
MSG  28: male
MSG  29: female
MSG  30: human
MSG  31: elf
MSG  32: gnome
MSG  33: dwarf
MSG  34: hobbit
MSG  35: automata
MSG  36: (space)
MSG  37: (space)
MSG  38: fighter
MSG  39: thief
MSG  40: mage
MSG  41: priest
MSG  42: ninja
MSG  43: ninja
MSG  44: bishop
MSG  45: samurai
MSG  46: alchemist
MSG  47: gizoku
MSG  48: monk
MSG  49: paladin
MSG  50: dark knight
MSG  51: shogun
MSG  52: knight
MSG  53: high thief
MSG  54: omnitsu
MSG  55: militant
MSG  56: wasteful
MSG  57: lonely
MSG  58: sociable
MSG  59: collector
MSG  60: cautious
MSG  61: hoarder
MSG  62: intellectual
MSG  63: belligerent
MSG  64: adventurous
MSG  65: superstitious
MSG  66: studious
MSG  67: pusillanimous
MSG  68: ecologist
MSG  69: maiden heart
MSG  70: hot-blooded
MSG  71: just
MSG  72: determined
MSG  73: cooperative
MSG  74: fraternal
MSG  75: short-tempered
MSG  76: economist
MSG  77: lustful
MSG  78: narcissist
MSG  79: moody
MSG  80: sadist
MSG  81: tribal love
MSG  82: bold
MSG  83: hobbyist
MSG  84: attack
MSG  85: accuracy
MSG  86: defense
MSG  87: evasion
MSG  88: bores easily. / return / to town often.
MSG  89: senses spirits. / trembles at death.
MSG  90: lives to hoard / gold. / angry if loot is / low.
MSG  91: dislikes crowds. / calmer in few.
MSG  92: loves big groups. / hates small / parties.
MSG  93: can't resist loot. / lives to collect.
MSG  94: distrusts reckless / adventurers.
MSG  95: fascinated by / monster biology.
MSG  96: believes in mystic / power. loves / magic.
MSG  97: skilled warrior. / seeks strong foes.
MSG  98: must adventure. / idleness is agony.
MSG  99: reacts keenly to / sudden events.
MSG 100: obsessed with / traps. / crushed by / success.
MSG 101: anxious in / dungeons. / dreads the undead.
MSG 102: values recycling. / hates wasting / items.
MSG 103: strong maiden / bonds. / no need for men.
MSG 104: believes women / have / no place in / battle.
MSG 105: won't forgive / those / who slay tame / foes.
MSG 106: lives to slay all. / despises retreat.
MSG 107: values teamwork. / hates going solo.
MSG 108: hates bloodshed. / mourns fallen / allies.
MSG 109: short-tempered. / long fights / enrage.
MSG 110: born merchant. / loves trade.
MSG 111: likes opposite / sex. / bored by same sex.
MSG 112: vain narcissist. / shocked when / harmed.
MSG 113: happy then angry. / unpredictable / mood.
MSG 114: thrives in / hardship. / hates being / helped.
MSG 115: bonds with own / race. / shuns other races.
MSG 116: empty-headed. / happy if others / are.
MSG 117: use everything. / hoarding is a sin.
MSG 118: Gender sets base / stats. Men=strong, / women=wise.
MSG 119: Human: High faith / & balanced stats / overall.
MSG 120: Elf: High INT & / VIT / but frail. Best / at magic.
MSG 121: Gnome: High faith / & agility. Suited / for Priests.
MSG 122: Dwarf: Slow but / strong with deep / faith. Fighters.
MSG 123: Hobbit: Small but / agile and lucky. / Born thieves.
MSG 124: Good=justice. May / turn Evil. FIG MAG / PRI SAM GIZ BIS+
MSG 125: Neutral=no bias. / FIG THI MAG SAM / GIZ ALC MON
MSG 126: Evil=self-serving. / FIG THI MAG PRI / NIN BIS ALC
MSG 127: combat expert. / cannot learn any / magic spells.
MSG 128: Lowers trap level / & finds chests. / Sorcery Lv3.
MSG 129: master of sorcery. / can learn all / sorcery spells.
MSG 130: Holy magic master. / Can Dispel undead. / All Holy spells.
MSG 131: Great EXP gain. / Can / instant-kill foes. / Sorcery up to Lv2.
MSG 132: Knight gear / usable. / Learns Sorcery / up to Lv5.
MSG 133: Restores HP. / Dispel / vs undead. Sorc & / Holy Magic Lv6.
MSG 134: Poleaxe weapons. / Dispel vs undead. / Holy Magic Lv5.
MSG 135: Handles alchemy. / Sorc & Holy Magic / up to Lv4.
MSG 136: Longbow user. / Lowers / traps, steals / items / Sorc+Holy Lv3.
MSG 137: Staffs & knuckles. / Dispel vs undead. / Holy Magic Lv5.
MSG 138: Holy aura heals / HP. / Can learn Dispel. / Sorc+Holy Lv6.
MSG 139: Removes curses / from / equipped items. / Sorcery Lv6.
MSG 140: Great EXP & insta- / kill. Sees in fog. / Sorcery Lv5.
MSG 141: Dual wields same / weapon type. / Learns / Sorcery Lv6.
MSG 142: Longbow. Best trap / skill. Steals / items / Sorc+Holy Lv4.
MSG 143: affects damage / dealt / with weapons.
MSG 144: affects sorcery / power and / resistance.
MSG 145: affects holy magic / power and / resistance.
MSG 146: affects max hp, / status resistance, / and revival / success.
MSG 147: affects turn order / in battle.
MSG 148: affects breath / resist and / critical / hit chance.
MSG 149: good "g"
MSG 150: good "g"
MSG 151: good "g"
MSG 152: neutral "n"
MSG 153: evil "e"
MSG 154: good
MSG 155: neutral
MSG 156: evil
MSG 157: g
MSG 158: n
MSG 159: e
MSG 160: HOOLIGAN
MSG 161: EVIL
MSG 162: VENOM FANG
MSG 163: VILLAIN
MSG 164: GANGSTER
MSG 165: cruelty
MSG 166: VICIOUS
MSG 167: dangerous
MSG 168: CURIOSITY
MSG 169: COMMONER
MSG 170: ADVENTURER
MSG 171: GUARD
MSG 172: BOLDNESS
MSG 173: BRAVERY
MSG 174: FAMOUS
MSG 175: VETERAN
MSG 176: CONQUEROR
MSG 177: HERO
MSG 178: QUEEN GUARD
MSG 179: COMMONER
MSG 180: HONEST PERSON
MSG 181: KIND
MSG 182: RELIABLE
MSG 183: GREAT HEART
MSG 184: FAIRNESS
MSG 185: noble
MSG 186: ACHIEVEMENT
MSG 187: SAGE
MSG 188: GOD HAND
```

## Verdict

**R38 in v17 is 100% English.** All 189 FFFF groups match the original count. All text messages
(MSG 1-188) contain only ASCII glyphs (range 0-94). MSG 0 is the offset table (not text).
No Japanese glyphs, no unmapped glyphs, no corruption found in any text message.
