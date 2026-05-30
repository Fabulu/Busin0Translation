# Global Overflow Audit - Busin 0 Translation

Generated: 2026-05-28

## Summary

- **Total flagged entries**: 302
- **Type-1 (chunk) issues**: 289
  - Overflow (>3 lines): 86
  - Wide lines (>20 chars): 238
- **Type-2 (batch) issues**: 13 (words >18 chars that break word-wrap)
- **Entries with proposed rewrites**: 299
- **Still needs manual rewrite**: 0

## Architecture Notes

### Type-1 (chunk files) -- Fixed UI labels
- Item names, menu options, chargen descriptions, dungeon messages
- ` / ` = explicit FFFE line break token
- NO auto word-wrapping -- text must be pre-formatted by translator
- Hard limit: 3 lines max, ~20 chars per line (224px box at 12px/glyph)
- **Every overflow/wide entry here is a real display bug**

### Type-2 (batch files) -- Dialogue and narration
- `encode_text()` in build pipeline auto-wraps at 18 chars/line, 3 lines/page
- Auto page-breaks via FFD2 token after every 3 lines
- ` / ` = explicit line break within auto-wrapped text
- Only issue: individual words >18 chars that cannot be split by word-wrap

### Trailing ` /` normalization
- Build pipeline normalizes trailing ` /` to ` / ` before splitting
- This audit applies the same normalization to avoid false positives

## Breakdown by File

| File | Total | Overflow | Wide |
|------|-------|----------|------|
| batch_06.json | 10 | 0 | 10 |
| batch_r39_equip_a.json | 3 | 0 | 3 |
| chunk_00_translated.json | 3 | 0 | 3 |
| chunk_01_translated.json | 1 | 0 | 1 |
| chunk_02_translated.json | 19 | 12 | 10 |
| chunk_03_translated.json | 14 | 10 | 10 |
| chunk_04_translated.json | 10 | 0 | 10 |
| chunk_06_translated.json | 49 | 0 | 49 |
| chunk_07_translated.json | 9 | 7 | 2 |
| chunk_08_translated.json | 68 | 0 | 68 |
| chunk_09_translated.json | 39 | 32 | 24 |
| chunk_r37_extra.json | 4 | 3 | 1 |
| chunk_r37_r48_r49_translated.json | 8 | 0 | 8 |
| chunk_r38_fix.json | 29 | 22 | 16 |
| chunk_r40_r42_translated.json | 30 | 0 | 30 |
| chunk_r43_r45_translated.json | 6 | 0 | 6 |

---

## Overflow Entries (>3 lines) -- CRITICAL

**86 entries** have more lines than the 3-line display box can show.

### [chunk_02_translated.json] r38 msg117 -- 4 lines

**Current:**
```
  L1 (19ch): Gender affects base
  L2 (17ch): stats and growth.
  L3 (15ch): Men are strong,
  L4 (15ch): women are wise.
```
**Proposed rewrite:**
```
  L1 (16ch): Gender sets base
  L2 (18ch): stats. Men=strong,
  L3 (11ch): women=wise.
```

### [chunk_02_translated.json] r38 msg118 -- 4 lines

**Current:**
```
  L1 (20ch): Race determines base
  L2 (19ch): growth. Humans have
  L3 (21ch): high faith & balanced <-- WIDE
  L4 (14ch): stats overall.
```
**Proposed rewrite:**
```
  L1 (17ch): Human: High faith
  L2 (16ch): & balanced stats
  L3 ( 8ch): overall.
```

### [chunk_02_translated.json] r38 msg119 -- 4 lines

**Current:**
```
  L1 (20ch): Race determines base
  L2 (19ch): growth. Elves excel
  L3 (20ch): in INT & VIT but are
  L4 (20ch): weak. Best at magic.
```
**Proposed rewrite:**
```
  L1 (19ch): Elf: High INT & VIT
  L2 (15ch): but frail. Best
  L3 ( 9ch): at magic.
```

### [chunk_02_translated.json] r38 msg120 -- 4 lines

**Current:**
```
  L1 (20ch): Race determines base
  L2 (19ch): growth. Gnomes have
  L3 (21ch): high faith & agility. <-- WIDE
  L4 (19ch): Suited for Priests.
```
**Proposed rewrite:**
```
  L1 (17ch): Gnome: High faith
  L2 (17ch): & agility. Suited
  L3 (12ch): for Priests.
```

### [chunk_02_translated.json] r38 msg121 -- 4 lines

**Current:**
```
  L1 (20ch): Race determines base
  L2 (19ch): growth. Dwarves are
  L3 (20ch): slow but strong with
  L4 (21ch): deep faith. Fighters. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (15ch): Dwarf: Slow but
  L2 (16ch): strong with deep
  L3 (16ch): faith. Fighters.
```

### [chunk_02_translated.json] r38 msg122 -- 4 lines

**Current:**
```
  L1 (20ch): Race determines base
  L2 (19ch): growth. Hobbits are
  L3 (19ch): small but agile and
  L4 (20ch): lucky. Born thieves.
```
**Proposed rewrite:**
```
  L1 (17ch): Hobbit: Small but
  L2 (16ch): agile and lucky.
  L3 (13ch): Born thieves.
```

### [chunk_02_translated.json] r38 msg123 -- 6 lines

**Current:**
```
  L1 (20ch): Good upholds justice
  L2 (20ch): but may turn Evil if
  L3 (16ch): acting unjustly.
  L4 (20ch): Classes: FIG MAG PRI
  L5 (19ch): SAM GIZ BIS KNI ALC
  L6 ( 3ch): MON
```
**Proposed rewrite:**
```
  L1 (17ch): Good=justice. May
  L2 (18ch): turn Evil. FIG MAG
  L3 (16ch): PRI SAM GIZ BIS+
```

### [chunk_02_translated.json] r38 msg124 -- 4 lines

**Current:**
```
  L1 (18ch): Those without bias
  L2 (19ch): are called Neutral.
  L3 (20ch): Classes: FIG THI MAG
  L4 (15ch): SAM GIZ ALC MON
```
**Proposed rewrite:**
```
  L1 (16ch): Neutral=no bias.
  L2 (15ch): FIG THI MAG SAM
  L3 (11ch): GIZ ALC MON
```

### [chunk_02_translated.json] r38 msg125 -- 5 lines

**Current:**
```
  L1 (17ch): Evil favors rest.
  L2 (19ch): Some rarely turn to
  L3 (18ch): Good. Classes: FIG
  L4 (19ch): THI MAG PRI NIN BIS
  L5 ( 3ch): ALC
```
**Proposed rewrite:**
```
  L1 (18ch): Evil=self-serving.
  L2 (15ch): FIG THI MAG PRI
  L3 (11ch): NIN BIS ALC
```

### [chunk_02_translated.json] r38 msg127 -- 4 lines

**Current:**
```
  L1 (15ch): Can reduce trap
  L2 (17ch): difficulty & find
  L3 (16ch): treasure chests.
  L4 (19ch): Learns Sorcery Lv3.
```
**Proposed rewrite:**
```
  L1 (17ch): Lowers trap level
  L2 (15ch): & finds chests.
  L3 (12ch): Sorcery Lv3.
```

### [chunk_02_translated.json] r38 msg129 -- 4 lines

**Current:**
```
  L1 (14ch): Master of Holy
  L2 (16ch): Magic. Can learn
  L3 (18ch): Dispel vs. undead.
  L4 (15ch): All Holy Magic.
```
**Proposed rewrite:**
```
  L1 (18ch): Holy magic master.
  L2 (18ch): Can Dispel undead.
  L3 (16ch): All Holy spells.
```

### [chunk_02_translated.json] r38 msg130 -- 4 lines

**Current:**
```
  L1 (17ch): Excels at earning
  L2 (17ch): EXP. Can instant-
  L3 (17ch): kill foes. Learns
  L4 (18ch): Sorcery up to Lv2.
```
**Proposed rewrite:**
```
  L1 (19ch): Great EXP gain. Can
  L2 (18ch): instant-kill foes.
  L3 (18ch): Sorcery up to Lv2.
```

### [chunk_03_translated.json] r38 msg131 -- 4 lines

**Current:**
```
  L1 (17ch): Can equip weapons
  L2 (22ch): and armor for knights. <-- WIDE
  L3 (16ch): Learns Sorceries
  L4 (10ch): up to Lv5.
```
**Proposed rewrite:**
```
  L1 (19ch): Knight gear usable.
  L2 (14ch): Learns Sorcery
  L3 (10ch): up to Lv5.
```

### [chunk_03_translated.json] r38 msg132 -- 6 lines

**Current:**
```
  L1 (18ch): Has the ability to
  L2 (11ch): restore HP.
  L3 (16ch): Can learn Dispel
  L4 (17ch): to banish undead.
  L5 (20ch): Learns Sorceries and
  L6 (21ch): Holy Magic up to Lv6. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Restores HP. Dispel
  L2 (17ch): vs undead. Sorc &
  L3 (15ch): Holy Magic Lv6.
```

### [chunk_03_translated.json] r38 msg133 -- 6 lines

**Current:**
```
  L1 (17ch): Can equip poleaxe
  L2 (13ch): type weapons.
  L3 (16ch): Can learn Dispel
  L4 (17ch): to banish undead.
  L5 (17ch): Learns Holy Magic
  L6 (10ch): up to Lv5.
```
**Proposed rewrite:**
```
  L1 (16ch): Poleaxe weapons.
  L2 (17ch): Dispel vs undead.
  L3 (15ch): Holy Magic Lv5.
```

### [chunk_03_translated.json] r38 msg135 -- 5 lines

**Current:**
```
  L1 (19ch): Can equip longbows.
  L2 (22ch): Lowers trap difficulty <-- WIDE
  L3 (20ch): and can steal items.
  L4 (20ch): Learns Sorceries and
  L5 (21ch): Holy Magic up to Lv3. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Longbow user. Lowers
  L2 (19ch): traps, steals items
  L3 (14ch): Sorc+Holy Lv3.
```

### [chunk_03_translated.json] r38 msg136 -- 6 lines

**Current:**
```
  L1 (16ch): Can equip staffs
  L2 (20ch): and knuckle weapons.
  L3 (16ch): Can learn Dispel
  L4 (17ch): to banish undead.
  L5 (17ch): Learns Holy Magic
  L6 (10ch): up to Lv5.
```
**Proposed rewrite:**
```
  L1 (18ch): Staffs & knuckles.
  L2 (17ch): Dispel vs undead.
  L3 (15ch): Holy Magic Lv5.
```

### [chunk_03_translated.json] r38 msg137 -- 5 lines

**Current:**
```
  L1 (16ch): Holy aura slowly
  L2 (18ch): restores party HP.
  L3 (22ch): Can also learn Dispel. <-- WIDE
  L4 (20ch): Learns Sorceries and
  L5 (21ch): Holy Magic up to Lv6. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Holy aura heals HP.
  L2 (17ch): Can learn Dispel.
  L3 (14ch): Sorc+Holy Lv6.
```

### [chunk_03_translated.json] r38 msg138 -- 4 lines

**Current:**
```
  L1 (17ch): Can remove curses
  L2 (20ch): from equipped items.
  L3 (16ch): Learns Sorceries
  L4 (10ch): up to Lv6.
```
**Proposed rewrite:**
```
  L1 (19ch): Removes curses from
  L2 (15ch): equipped items.
  L3 (12ch): Sorcery Lv6.
```

### [chunk_03_translated.json] r38 msg139 -- 6 lines

**Current:**
```
  L1 (21ch): Excels at gaining EXP <-- WIDE
  L2 (22ch): and instant death atk. <-- WIDE
  L3 (20ch): Can also see through
  L4 (15ch): dark fog zones.
  L5 (16ch): Learns Sorceries
  L6 (10ch): up to Lv5.
```
**Proposed rewrite:**
```
  L1 (18ch): Great EXP & insta-
  L2 (18ch): kill. Sees in fog.
  L3 (12ch): Sorcery Lv5.
```

### [chunk_03_translated.json] r38 msg140 -- 5 lines

**Current:**
```
  L1 (14ch): Can dual wield
  L2 (19ch): weapons of the same
  L3 (20ch): type simultaneously.
  L4 (16ch): Learns Sorceries
  L5 (10ch): up to Lv6.
```
**Proposed rewrite:**
```
  L1 (16ch): Dual wields same
  L2 (19ch): weapon type. Learns
  L3 (12ch): Sorcery Lv6.
```

### [chunk_03_translated.json] r38 msg141 -- 6 lines

**Current:**
```
  L1 (19ch): Can equip longbows.
  L2 (19ch): Greatly lowers trap
  L3 (21ch): difficulty. Can steal <-- WIDE
  L4 (19ch): items from enemies.
  L5 (20ch): Learns Sorceries and
  L6 (21ch): Holy Magic up to Lv4. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Longbow. Best trap
  L2 (19ch): skill. Steals items
  L3 (14ch): Sorc+Holy Lv4.
```

### [chunk_07_translated.json] r46 msg1 -- 9 lines

**Current:**
```
  L1 (16ch): A bulletin board
  L2 (19ch): has been set up for
  L3 (15ch): the citizens of
  L4 (17ch): Duhan to exchange
  L5 ( 0ch): 
  L6 (18ch): opinions. To leave
  L7 (19ch): a message, fill out
  L8 (17ch): the form and drop
  L9 (14ch): it in the box.
```
**Proposed rewrite:**
```
  L1 (18ch): Bulletin board for
  L2 (17ch): Duhan citizens to
  L3 (15ch): share opinions.
```

### [chunk_07_translated.json] r46 msg2 -- 9 lines

**Current:**
```
  L1 (17ch): This is Miri, who
  L2 (18ch): posted the request
  L3 (13ch): for the Kreta
  L4 (18ch): stone. Never mind.
  L5 ( 0ch): 
  L6 (17ch): Someone else gave
  L7 (17ch): it to me already.
  L8 (17ch): Request canceled.
  L9 ( 7ch): Thanks!
```
**Proposed rewrite:**
```
  L1 (16ch): Miri here. Never
  L2 (14ch): mind the Kreta
  L3 (14ch): stone request.
```

### [chunk_07_translated.json] r46 msg3 -- 9 lines

**Current:**
```
  L1 (12ch): You know the
  L2 (16ch): Self-Seraph Shop
  L3 (17ch): in the labyrinth?
  L4 (19ch): They sell a strange
  L5 ( 0ch): 
  L6 (15ch): key there. What
  L7 (15ch): does it unlock?
  L8 (17ch): Has anyone bought
  L9 ( 8ch): one yet?
```
**Proposed rewrite:**
```
  L1 (16ch): Self-Seraph Shop
  L2 (19ch): sells a strange key
  L3 (17ch): What's it unlock?
```

### [chunk_07_translated.json] r46 msg4 -- 8 lines

**Current:**
```
  L1 (15ch): The Vigger Shop
  L2 (14ch): is looking for
  L3 (18ch): part-time workers!
  L4 ( 0ch): 
  L5 (17ch): This is posted on
  L6 (17ch): the board, not as
  L7 (13ch): a request, so
  L8 (17ch): everyone can see.
```
**Proposed rewrite:**
```
  L1 (17ch): Vigger Shop seeks
  L2 (18ch): part-time workers!
  L3 (16ch): All are welcome!
```

### [chunk_07_translated.json] r46 msg5 -- 5 lines

**Current:**
```
  L1 (15ch): The Vigger Shop
  L2 (16ch): has lots of orcs
  L3 (17ch): working there. Do
  L4 (16ch): they accept orcs
  L5 (19ch): as part-timers too?
```
**Proposed rewrite:**
```
  L1 (15ch): Vigger Shop has
  L2 (18ch): many orcs. Do they
  L3 (17ch): hire orc workers?
```

### [chunk_07_translated.json] r46 msg6 -- 8 lines

**Current:**
```
  L1 (18ch): A friendly orc who
  L2 (16ch): fits in with the
  L3 (16ch): town is welcome!
  L4 ( 0ch): 
  L5 (14ch): We have 3 orcs
  L6 (19ch): already. Same race,
  L7 (17ch): they'll get along
  L8 (10ch): just fine!
```
**Proposed rewrite:**
```
  L1 (17ch): Friendly orcs are
  L2 (18ch): welcome! We have 3
  L3 (17ch): already. Join us!
```

### [chunk_07_translated.json] r46 msg7 -- 14 lines

**Current:**
```
  L1 (16ch): I went exploring
  L2 (17ch): on the 4th floor,
  L3 (18ch): got haunted by the
  L4 (16ch): Grim Reaper, got
  L5 ( 0ch): 
  L6 (16ch): lost... it was a
  L7 (15ch): disaster. But I
  L8 (15ch): stumbled into a
  L9 (19ch): room where a Hobbit
  L10 ( 0ch): 
  L11 (17ch): and an Imp lived.
  L12 (19ch): Odd folks, but they
  L13 (15ch): gave me a cure.
  L14 (12ch): Nice people!
```
**Proposed rewrite:**
```
  L1 (19ch): Got lost on 4F, met
  L2 (18ch): a Hobbit & Imp who
  L3 (15ch): gave me a cure.
```

### [chunk_09_translated.json] r2654 msg1 -- 4 lines

**Current:**
```
  L1 (19ch): 2 front row members
  L2 (21ch): time their strikes on <-- WIDE
  L3 (17ch): 1 enemy together,
  L4 (21ch): dealing heavy damage. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): 2 front row strike
  L2 (16ch): 1 enemy together
  L3 (17ch): for heavy damage.
```

### [chunk_09_translated.json] r2654 msg2 -- 7 lines

**Current:**
```
  L1 (16ch): Channel back row
  L2 (20ch): magic into front row
  L3 (18ch): weapons to attack.
  L4 (18ch): Hits limited to 1,
  L5 (20ch): but greatly improves
  L6 (16ch): hit rate vs high
  L7 (16ch): evasion enemies.
```
**Proposed rewrite:**
```
  L1 (17ch): Back magic boosts
  L2 (20ch): front weapons. 1 hit
  L3 (18ch): but high accuracy.
```

### [chunk_09_translated.json] r2654 msg3 -- 6 lines

**Current:**
```
  L1 (20ch): Back row magic stuns
  L2 (22ch): the enemy, letting the <-- WIDE
  L3 (17ch): front row attack.
  L4 (18ch): Hits limited to 1,
  L5 (21ch): but effective against <-- WIDE
  L6 (18ch): high evasion foes.
```
**Proposed rewrite:**
```
  L1 (20ch): Back magic stuns foe
  L2 (17ch): for front attack.
  L3 (16ch): 1 hit, high acc.
```

### [chunk_09_translated.json] r2654 msg4 -- 6 lines

**Current:**
```
  L1 (20ch): Back row magic lifts
  L2 (18ch): front row into the
  L3 (21ch): air to jump attack at <-- WIDE
  L4 (20ch): turn's end. Hits are
  L5 (21ch): limited to 1, but can <-- WIDE
  L6 (17ch): bypass enemy DEF.
```
**Proposed rewrite:**
```
  L1 (16ch): Back magic lifts
  L2 (19ch): front for jump atk.
  L3 (14ch): 1 hit, no DEF.
```

### [chunk_09_translated.json] r2654 msg5 -- 6 lines

**Current:**
```
  L1 (20ch): 2 adjacent front row
  L2 (19ch): members strike both
  L3 (20ch): enemy front and back
  L4 (18ch): rows in sync. Hits
  L5 (17ch): limited to 1, but
  L6 (16ch): always connects.
```
**Proposed rewrite:**
```
  L1 (16ch): 2 front hit both
  L2 (19ch): enemy rows in sync.
  L3 (15ch): 1 hit, no miss.
```

### [chunk_09_translated.json] r2654 msg6 -- 6 lines

**Current:**
```
  L1 (22ch): 2 back row cross their <-- WIDE
  L2 (19ch): magic to seal enemy
  L3 (16ch): movement, then 2
  L4 (16ch): front row strike
  L5 (19ch): together. Effective
  L6 (20ch): vs high EVA/HP foes.
```
**Proposed rewrite:**
```
  L1 (16ch): 2 back seal foe,
  L2 (18ch): 2 front strike. vs
  L3 (17ch): high EVA/HP foes.
```

### [chunk_09_translated.json] r2654 msg7 -- 5 lines

**Current:**
```
  L1 (20ch): All front row take a
  L2 (17ch): defensive stance,
  L3 (21ch): boosting EVA and DEF. <-- WIDE
  L4 (21ch): Blocks status effects <-- WIDE
  L5 (15ch): and enemy RUSH.
```
**Proposed rewrite:**
```
  L1 (17ch): All front defend.
  L2 (17ch): Boosts EVA & DEF.
  L3 (18ch): Blocks status+RUSH
```

### [chunk_09_translated.json] r2654 msg8 -- 5 lines

**Current:**
```
  L1 (19ch): 2 back row activate
  L2 (17ch): magic to create a
  L3 (16ch): barrier. Reduces
  L4 (16ch): magic damage and
  L5 (16ch): boosts RES rate.
```
**Proposed rewrite:**
```
  L1 (20ch): 2 back cast barrier.
  L2 (18ch): Cuts magic damage,
  L3 (16ch): boosts RES rate.
```

### [chunk_09_translated.json] r2654 msg9 -- 6 lines

**Current:**
```
  L1 (21ch): All back row activate <-- WIDE
  L2 (18ch): magic to cover the
  L3 (19ch): field with a strong
  L4 (21ch): barrier. Neither side <-- WIDE
  L5 (15ch): can cast spells
  L6 (10ch): this turn.
```
**Proposed rewrite:**
```
  L1 (20ch): All back cast strong
  L2 (18ch): barrier. No spells
  L3 (17ch): from either side.
```

### [chunk_09_translated.json] r2654 msg10 -- 6 lines

**Current:**
```
  L1 (19ch): All back row create
  L2 (21ch): mirror images for the <-- WIDE
  L3 (20ch): party. Images vanish
  L4 (13ch): when hit, but
  L5 (16ch): protect the real
  L6 (17ch): body from damage.
```
**Proposed rewrite:**
```
  L1 (19ch): All back make decoy
  L2 (19ch): images. Images take
  L3 (15ch): hits for party.
```

### [chunk_09_translated.json] r2654 msg11 -- 6 lines

**Current:**
```
  L1 (17ch): All party members
  L2 (17ch): scatter to reduce
  L3 (16ch): breath and magic
  L4 (16ch): damage. However,
  L5 (20ch): normal attack damage
  L6 (16ch): taken increases.
```
**Proposed rewrite:**
```
  L1 (17ch): Party scatters to
  L2 (20ch): cut breath+magic dmg
  L3 (15ch): Phys dmg rises.
```

### [chunk_09_translated.json] r2654 msg12 -- 6 lines

**Current:**
```
  L1 (17ch): All party members
  L2 (20ch): take evasive stance,
  L3 (20ch): greatly boosting EVA
  L4 (19ch): and DEF vs physical
  L5 (19ch): attacks. Breath and
  L6 (16ch): magic damage up.
```
**Proposed rewrite:**
```
  L1 (17ch): Party evades. Big
  L2 (18ch): EVA/DEF boost, but
  L3 (18ch): magic dmg goes up.
```

### [chunk_09_translated.json] r2654 msg13 -- 6 lines

**Current:**
```
  L1 (20ch): When a guarded front
  L2 (18ch): row member is hit,
  L3 (19ch): back row intercepts
  L4 (20ch): with ranged attacks.
  L5 (18ch): Triggers each time
  L6 (18ch): the target is hit.
```
**Proposed rewrite:**
```
  L1 (18ch): When front is hit,
  L2 (18ch): back counters with
  L3 (15ch): ranged attacks.
```

### [chunk_09_translated.json] r2654 msg14 -- 4 lines

**Current:**
```
  L1 (21ch): Before allies attack, <-- WIDE
  L2 (17ch): all back row fire
  L3 (21ch): ranged shots to boost <-- WIDE
  L4 ( 9ch): hit rate.
```
**Proposed rewrite:**
```
  L1 (19ch): All back fire first
  L2 (18ch): to boost front row
  L3 ( 9ch): hit rate.
```

### [chunk_09_translated.json] r2654 msg15 -- 5 lines

**Current:**
```
  L1 (19ch): When an enemy tries
  L2 (21ch): to cast a spell, back <-- WIDE
  L3 (21ch): row attacks to cancel <-- WIDE
  L4 (16ch): it. Limited uses
  L5 ( 9ch): per turn.
```
**Proposed rewrite:**
```
  L1 (15ch): Back attacks to
  L2 (20ch): cancel enemy spells.
  L3 (17ch): Limited per turn.
```

### [chunk_09_translated.json] r2654 msg16 -- 5 lines

**Current:**
```
  L1 (19ch): When an enemy tries
  L2 (19ch): to use breath, back
  L3 (21ch): row attacks to cancel <-- WIDE
  L4 (16ch): it. Limited uses
  L5 ( 9ch): per turn.
```
**Proposed rewrite:**
```
  L1 (15ch): Back attacks to
  L2 (19ch): cancel enemy breath
  L3 (17ch): Limited per turn.
```

### [chunk_09_translated.json] r2654 msg17 -- 6 lines

**Current:**
```
  L1 (19ch): When a guarded back
  L2 (18ch): row member is hit,
  L3 (19ch): front row takes the
  L4 (18ch): blow instead. Also
  L5 (19ch): blocks enemy ranged
  L6 ( 8ch): attacks.
```
**Proposed rewrite:**
```
  L1 (20ch): Front takes hits for
  L2 (17ch): guarded back row.
  L3 (18ch): Blocks ranged too.
```

### [chunk_09_translated.json] r2654 msg18 -- 6 lines

**Current:**
```
  L1 (19ch): Decoy retreats when
  L2 (16ch): attacked, others
  L3 (19ch): flank and intercept
  L4 (17ch): enemy coordinated
  L5 (16ch): attacks. Limited
  L6 (14ch): uses per turn.
```
**Proposed rewrite:**
```
  L1 (15ch): Decoy retreats,
  L2 (15ch): others flank to
  L3 (18ch): stop enemy combos.
```

### [chunk_09_translated.json] r2654 msg19 -- 6 lines

**Current:**
```
  L1 (19ch): 3 back row activate
  L2 (21ch): magic to expand spell <-- WIDE
  L3 (18ch): range. Also lowers
  L4 (18ch): enemy spell resist
  L5 (16ch): and boosts spell
  L6 ( 6ch): power.
```
**Proposed rewrite:**
```
  L1 (19ch): 3 back expand spell
  L2 (17ch): range. Lowers foe
  L3 (18ch): resist+boosts pow.
```

### [chunk_09_translated.json] r2654 msg20 -- 6 lines

**Current:**
```
  L1 (20ch): All back row channel
  L2 (16ch): magic to dispel.
  L3 (18ch): Cures party's Mute
  L4 (18ch): status, and breaks
  L5 (17ch): enemy Magic Shell
  L6 (21ch): and Anti-Magic Shell. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): All back dispel.
  L2 (18ch): Cures Mute, breaks
  L3 (17ch): foe magic shells.
```

### [chunk_09_translated.json] r2654 msg21 -- 6 lines

**Current:**
```
  L1 (19ch): 2 adjacent back row
  L2 (21ch): members cast the same <-- WIDE
  L3 (20ch): spell in small doses
  L4 (20ch): to speed up casting.
  L5 (20ch): Faster than breaking
  L6 (17ch): Anti-Magic Shell.
```
**Proposed rewrite:**
```
  L1 (16ch): 2 back cast same
  L2 (18ch): spell in doses for
  L3 (15ch): faster casting.
```

### [chunk_09_translated.json] r2654 msg22 -- 6 lines

**Current:**
```
  L1 (20ch): Back row enchants an
  L2 (18ch): ally's weapon with
  L3 (20ch): magic. If the attack
  L4 (17ch): hits, it bypasses
  L5 (18ch): enemy spell resist
  L6 (16ch): and Magic Shell.
```
**Proposed rewrite:**
```
  L1 (18ch): Back enchants wpn.
  L2 (16ch): Hit bypasses foe
  L3 (18ch): resist & Mag Shell
```

### [chunk_09_translated.json] r2654 msg23 -- 4 lines

**Current:**
```
  L1 (19ch): 2 back row cast the
  L2 (19ch): same spell together
  L3 (20ch): to greatly boost its
  L4 ( 6ch): power.
```
**Proposed rewrite:**
```
  L1 (16ch): 2 back cast same
  L2 (18ch): spell together for
  L3 (16ch): big power boost.
```

### [chunk_09_translated.json] r2654 msg24 -- 6 lines

**Current:**
```
  L1 (20ch): 3 front row attack 1
  L2 (18ch): enemy in sequence,
  L3 (21ch): each hit dealing more <-- WIDE
  L4 (21ch): damage than the last. <-- WIDE
  L5 (20ch): The 3rd strike deals
  L6 (16ch): the most damage.
```
**Proposed rewrite:**
```
  L1 (17ch): 3 front hit 1 foe
  L2 (17ch): in sequence. Each
  L3 (18ch): hit does more dmg.
```

### [chunk_09_translated.json] r2654 msg25 -- 7 lines

**Current:**
```
  L1 (19ch): 1 front row acts as
  L2 (18ch): decoy. After being
  L3 (19ch): attacked, the other
  L4 (18ch): 2 sneak behind the
  L5 (16ch): enemy to strike.
  L6 (19ch): Hit rate and damage
  L7 (18ch): greatly increased.
```
**Proposed rewrite:**
```
  L1 (15ch): 1 front decoys,
  L2 (19ch): 2 sneak behind foe.
  L3 (15ch): High acc & dmg.
```

### [chunk_09_translated.json] r2654 msg26 -- 7 lines

**Current:**
```
  L1 (21ch): An evolved version of <-- WIDE
  L2 (20ch): Stun Smash. 1 member
  L3 (20ch): lifts the enemy into
  L4 (17ch): the air with full
  L5 (19ch): force, then strikes
  L6 (16ch): as they fall for
  L7 (13ch): heavy damage.
```
**Proposed rewrite:**
```
  L1 (17ch): Lift foe into air
  L2 (19ch): then strike as they
  L3 (17ch): fall. Big damage.
```

### [chunk_09_translated.json] r2654 msg27 -- 5 lines

**Current:**
```
  L1 (17ch): All party members
  L2 (19ch): attack all enemies.
  L3 (16ch): Cannot be evaded
  L4 (17ch): unless blocked by
  L5 (12ch): Front Guard.
```
**Proposed rewrite:**
```
  L1 (20ch): All attack all foes.
  L2 (18ch): Can't dodge unless
  L3 (18ch): Front Guard active
```

### [chunk_09_translated.json] r2654 msg28 -- 7 lines

**Current:**
```
  L1 (17ch): 2 front row feint
  L2 (20ch): while 1 aims for the
  L3 (19ch): enemy's weak point.
  L4 (19ch): All hits limited to
  L5 (19ch): 1, but 3rd member's
  L6 (20ch): crit rate is greatly
  L7 (10ch): increased.
```
**Proposed rewrite:**
```
  L1 (16ch): 2 front feint, 1
  L2 (16ch): aims weak point.
  L3 (17ch): Crit rate way up.
```

### [chunk_09_translated.json] r2654 msg29 -- 5 lines

**Current:**
```
  L1 (21ch): 2 members form a Holy <-- WIDE
  L2 (20ch): Symbol and perform a
  L3 (16ch): powerful Dispel.
  L4 (14ch): Very effective
  L5 (19ch): against the undead.
```
**Proposed rewrite:**
```
  L1 (18ch): 2 form Holy Symbol
  L2 (19ch): for powerful Dispel
  L3 (17ch): Strong vs undead.
```

### [chunk_09_translated.json] r2654 msg30 -- 7 lines

**Current:**
```
  L1 (18ch): 1 back row opens a
  L2 (18ch): Warp Gate. 3 front
  L3 (20ch): row jump through and
  L4 (20ch): attack from above at
  L5 (20ch): turn's end. Bypasses
  L6 (19ch): enemy DEF. Airborne
  L7 (20ch): allies can't be hit.
```
**Proposed rewrite:**
```
  L1 (20ch): 1 back warps 3 front
  L2 (18ch): to atk from above.
  L3 (17ch): Ignores DEF. Safe
```

### [chunk_09_translated.json] r2654 msg31 -- 7 lines

**Current:**
```
  L1 (21ch): An evolved Slay Crash <-- WIDE
  L2 (19ch): from a Monk's bond.
  L3 (16ch): 2 members charge
  L4 (18ch): through the enemy,
  L5 (17ch): dealing damage on
  L6 (20ch): the way through. Can
  L7 (16ch): also hit undead.
```
**Proposed rewrite:**
```
  L1 (16ch): 2 charge through
  L2 (15ch): foe for damage.
  L3 (16ch): Hits undead too.
```

### [chunk_09_translated.json] r2654 msg32 -- 7 lines

**Current:**
```
  L1 (18ch): An evolved W-Slash
  L2 (20ch): from a bond. 2 front
  L3 (20ch): row swing weapons to
  L4 (19ch): create a sonic wave
  L5 (20ch): that can also damage
  L6 (18ch): enemies behind the
  L7 ( 7ch): target.
```
**Proposed rewrite:**
```
  L1 (16ch): 2 front swing to
  L2 (17ch): make a sonic wave
  L3 (17ch): hits foes behind.
```

### [chunk_r37_extra.json] r37 msg19 -- 6 lines

**Current:**
```
  L1 (10ch): ABCDEFGHIJ
  L2 (10ch): KLMNOPQRST
  L3 (10ch): UVWXYZ.,!?
  L4 (10ch): abcdefghij
  L5 (10ch): klmnopqrst
  L6 ( 9ch): uvwxyz -'
```

### [chunk_r37_extra.json] r37 msg20 -- 6 lines

**Current:**
```
  L1 (10ch): abcdefghij
  L2 (10ch): klmnopqrst
  L3 (10ch): uvwxyz.,!?
  L4 (10ch): ABCDEFGHIJ
  L5 (10ch): KLMNOPQRST
  L6 ( 9ch): UVWXYZ -'
```

### [chunk_r37_extra.json] r37 msg21 -- 4 lines

**Current:**
```
  L1 (10ch): 1234567890
  L2 (10ch): +=#$&@*^~!
  L3 (10ch): <>(){}[]|_
  L4 (10ch): :;,.?!'"-%
```

### [chunk_r38_fix.json] r38 msg117 -- 4 lines

**Current:**
```
  L1 (19ch): gender affects base
  L2 (17ch): stats and growth.
  L3 (15ch): men are strong,
  L4 (15ch): women are wise.
```
**Proposed rewrite:**
```
  L1 (16ch): Gender sets base
  L2 (18ch): stats. Men=strong,
  L3 (11ch): women=wise.
```

### [chunk_r38_fix.json] r38 msg118 -- 4 lines

**Current:**
```
  L1 (20ch): race determines base
  L2 (19ch): growth. humans have
  L3 (21ch): high faith & balanced <-- WIDE
  L4 (14ch): stats overall.
```
**Proposed rewrite:**
```
  L1 (17ch): Human: High faith
  L2 (16ch): & balanced stats
  L3 ( 8ch): overall.
```

### [chunk_r38_fix.json] r38 msg119 -- 4 lines

**Current:**
```
  L1 (20ch): race determines base
  L2 (19ch): growth. elves excel
  L3 (20ch): in int & vit but are
  L4 (20ch): weak. best at magic.
```
**Proposed rewrite:**
```
  L1 (19ch): Elf: High INT & VIT
  L2 (15ch): but frail. Best
  L3 ( 9ch): at magic.
```

### [chunk_r38_fix.json] r38 msg120 -- 4 lines

**Current:**
```
  L1 (20ch): race determines base
  L2 (19ch): growth. gnomes have
  L3 (21ch): high faith & agility. <-- WIDE
  L4 (19ch): suited for priests.
```
**Proposed rewrite:**
```
  L1 (17ch): Gnome: High faith
  L2 (17ch): & agility. Suited
  L3 (12ch): for Priests.
```

### [chunk_r38_fix.json] r38 msg121 -- 4 lines

**Current:**
```
  L1 (20ch): race determines base
  L2 (19ch): growth. dwarves are
  L3 (20ch): slow but strong with
  L4 (21ch): deep faith. fighters. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (15ch): Dwarf: Slow but
  L2 (16ch): strong with deep
  L3 (16ch): faith. Fighters.
```

### [chunk_r38_fix.json] r38 msg122 -- 4 lines

**Current:**
```
  L1 (20ch): race determines base
  L2 (19ch): growth. hobbits are
  L3 (19ch): small but agile and
  L4 (20ch): lucky. born thieves.
```
**Proposed rewrite:**
```
  L1 (17ch): Hobbit: Small but
  L2 (16ch): agile and lucky.
  L3 (13ch): Born thieves.
```

### [chunk_r38_fix.json] r38 msg123 -- 6 lines

**Current:**
```
  L1 (20ch): good upholds justice
  L2 (20ch): but may turn evil if
  L3 (16ch): acting unjustly.
  L4 (20ch): classes: fig mag pri
  L5 (19ch): sam giz bis kni alc
  L6 ( 3ch): mon
```
**Proposed rewrite:**
```
  L1 (17ch): Good=justice. May
  L2 (18ch): turn Evil. FIG MAG
  L3 (16ch): PRI SAM GIZ BIS+
```

### [chunk_r38_fix.json] r38 msg124 -- 4 lines

**Current:**
```
  L1 (18ch): those without bias
  L2 (19ch): are called neutral.
  L3 (20ch): classes: fig thi mag
  L4 (15ch): sam giz alc mon
```
**Proposed rewrite:**
```
  L1 (16ch): Neutral=no bias.
  L2 (15ch): FIG THI MAG SAM
  L3 (11ch): GIZ ALC MON
```

### [chunk_r38_fix.json] r38 msg125 -- 5 lines

**Current:**
```
  L1 (17ch): evil favors rest.
  L2 (19ch): some rarely turn to
  L3 (18ch): good. classes: fig
  L4 (19ch): thi mag pri nin bis
  L5 ( 3ch): alc
```
**Proposed rewrite:**
```
  L1 (18ch): Evil=self-serving.
  L2 (15ch): FIG THI MAG PRI
  L3 (11ch): NIN BIS ALC
```

### [chunk_r38_fix.json] r38 msg127 -- 4 lines

**Current:**
```
  L1 (15ch): can reduce trap
  L2 (17ch): difficulty & find
  L3 (16ch): treasure chests.
  L4 (19ch): learns sorcery lv3.
```
**Proposed rewrite:**
```
  L1 (17ch): Lowers trap level
  L2 (15ch): & finds chests.
  L3 (12ch): Sorcery Lv3.
```

### [chunk_r38_fix.json] r38 msg129 -- 4 lines

**Current:**
```
  L1 (14ch): master of holy
  L2 (16ch): magic. can learn
  L3 (18ch): dispel vs. undead.
  L4 (15ch): all holy magic.
```
**Proposed rewrite:**
```
  L1 (18ch): Holy magic master.
  L2 (18ch): Can Dispel undead.
  L3 (16ch): All Holy spells.
```

### [chunk_r38_fix.json] r38 msg130 -- 4 lines

**Current:**
```
  L1 (17ch): excels at earning
  L2 (17ch): exp. can instant-
  L3 (17ch): kill foes. learns
  L4 (18ch): sorcery up to lv2.
```
**Proposed rewrite:**
```
  L1 (19ch): Great EXP gain. Can
  L2 (18ch): instant-kill foes.
  L3 (18ch): Sorcery up to Lv2.
```

### [chunk_r38_fix.json] r38 msg131 -- 4 lines

**Current:**
```
  L1 (17ch): can equip weapons
  L2 (22ch): and armor for knights. <-- WIDE
  L3 (14ch): learns sorcery
  L4 (10ch): up to lv5.
```
**Proposed rewrite:**
```
  L1 (19ch): Knight gear usable.
  L2 (14ch): Learns Sorcery
  L3 (10ch): up to Lv5.
```

### [chunk_r38_fix.json] r38 msg132 -- 6 lines

**Current:**
```
  L1 (18ch): has the ability to
  L2 (11ch): restore hp.
  L3 (16ch): can learn dispel
  L4 (17ch): to banish undead.
  L5 (18ch): learns sorcery and
  L6 (21ch): holy magic up to lv6. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Restores HP. Dispel
  L2 (17ch): vs undead. Sorc &
  L3 (15ch): Holy Magic Lv6.
```

### [chunk_r38_fix.json] r38 msg133 -- 6 lines

**Current:**
```
  L1 (17ch): can equip poleaxe
  L2 (13ch): type weapons.
  L3 (16ch): can learn dispel
  L4 (17ch): to banish undead.
  L5 (17ch): learns holy magic
  L6 (10ch): up to lv5.
```
**Proposed rewrite:**
```
  L1 (16ch): Poleaxe weapons.
  L2 (17ch): Dispel vs undead.
  L3 (15ch): Holy Magic Lv5.
```

### [chunk_r38_fix.json] r38 msg135 -- 5 lines

**Current:**
```
  L1 (19ch): can equip longbows.
  L2 (22ch): lowers trap difficulty <-- WIDE
  L3 (20ch): and can steal items.
  L4 (18ch): learns sorcery and
  L5 (21ch): holy magic up to lv3. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Longbow user. Lowers
  L2 (19ch): traps, steals items
  L3 (14ch): Sorc+Holy Lv3.
```

### [chunk_r38_fix.json] r38 msg136 -- 6 lines

**Current:**
```
  L1 (16ch): can equip staffs
  L2 (20ch): and knuckle weapons.
  L3 (16ch): can learn dispel
  L4 (17ch): to banish undead.
  L5 (17ch): learns holy magic
  L6 (10ch): up to lv5.
```
**Proposed rewrite:**
```
  L1 (18ch): Staffs & knuckles.
  L2 (17ch): Dispel vs undead.
  L3 (15ch): Holy Magic Lv5.
```

### [chunk_r38_fix.json] r38 msg137 -- 5 lines

**Current:**
```
  L1 (16ch): holy aura slowly
  L2 (18ch): restores party hp.
  L3 (22ch): can also learn dispel. <-- WIDE
  L4 (18ch): learns sorcery and
  L5 (21ch): holy magic up to lv6. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Holy aura heals HP.
  L2 (17ch): Can learn Dispel.
  L3 (14ch): Sorc+Holy Lv6.
```

### [chunk_r38_fix.json] r38 msg138 -- 4 lines

**Current:**
```
  L1 (17ch): can remove curses
  L2 (20ch): from equipped items.
  L3 (14ch): learns sorcery
  L4 (10ch): up to lv6.
```
**Proposed rewrite:**
```
  L1 (19ch): Removes curses from
  L2 (15ch): equipped items.
  L3 (12ch): Sorcery Lv6.
```

### [chunk_r38_fix.json] r38 msg139 -- 6 lines

**Current:**
```
  L1 (21ch): excels at gaining exp <-- WIDE
  L2 (22ch): and instant death atk. <-- WIDE
  L3 (20ch): can also see through
  L4 (15ch): dark fog zones.
  L5 (14ch): learns sorcery
  L6 (10ch): up to lv5.
```
**Proposed rewrite:**
```
  L1 (18ch): Great EXP & insta-
  L2 (18ch): kill. Sees in fog.
  L3 (12ch): Sorcery Lv5.
```

### [chunk_r38_fix.json] r38 msg140 -- 5 lines

**Current:**
```
  L1 (14ch): can dual wield
  L2 (19ch): weapons of the same
  L3 (20ch): type simultaneously.
  L4 (14ch): learns sorcery
  L5 (10ch): up to lv6.
```
**Proposed rewrite:**
```
  L1 (16ch): Dual wields same
  L2 (19ch): weapon type. Learns
  L3 (12ch): Sorcery Lv6.
```

### [chunk_r38_fix.json] r38 msg141 -- 6 lines

**Current:**
```
  L1 (19ch): can equip longbows.
  L2 (19ch): greatly lowers trap
  L3 (21ch): difficulty. can steal <-- WIDE
  L4 (19ch): items from enemies.
  L5 (18ch): learns sorcery and
  L6 (21ch): holy magic up to lv4. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Longbow. Best trap
  L2 (19ch): skill. Steals items
  L3 (14ch): Sorc+Holy Lv4.
```

---

## Wide Lines (>20 chars, <=3 lines)

**216 entries** fit in 3 lines but have individual lines exceeding ~20 char width.

### [batch_06.json] r1208 msg355

**Current:**
```
  L1 (22ch): 0123456789-0123456789- <-- WIDE
  L2 (18ch): "Hey there, member
  L3 ( 9ch): number !"
```
**Proposed rewrite:**
```
  L1 (10ch): Hey there,
  L2 (15ch): member number !
```
**Long words:** 0123456789-0123456789-

### [batch_06.json] r1208 msg445

**Current:**
```
  L1 (14ch): You poured the
  L2 (22ch): recovery/magic/stamina <-- WIDE
  L3 (25ch): potion into the fountain. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (14ch): You poured the
  L2 (15ch): potion into the
  L3 ( 9ch): fountain.
```
**Long words:** recovery/magic/stamina

### [batch_06.json] r1209 msg29

**Current:**
```
  L1 (86ch): Hey there, I finally found you... Big Sister............. Big Succubus Sister......... <-- WIDE
```
**Proposed rewrite:**
```
  L1 (14ch): Hey, I finally
  L2 (12ch): found you...
  L3 (18ch): Big Sister........
```
**Long words:** Sister.............

### [batch_06.json] r1209 msg38

**Current:**
```
  L1 (19ch): Nooooooooooooooooo!
```
**Proposed rewrite:**
```
  L1 (19ch): Nooooooooooooooooo!
```
**Long words:** Nooooooooooooooooo!

### [batch_06.json] r1209 msg366

**Current:**
```
  L1 (63ch): 0123456789-0000000123456789- Oh, member number! Welcome aboard! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Oh, member number!
  L2 (15ch): Welcome aboard!
```
**Long words:** 0123456789-0000000123456789-

### [batch_06.json] r1209 msg376

**Current:**
```
  L1 (80ch): I'll take 1 point! Well then, let the Member Number Lottery begiiiiiiiiiiiiiiin! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): 1 point! Let the
  L2 (13ch): Member Number
  L3 (14ch): Lottery begin!
```
**Long words:** begiiiiiiiiiiiiiiin!

### [batch_06.json] r1209 msg377

**Current:**
```
  L1 (81ch): I'll take 3 points! Well then, let the Member Number Lottery begiiiiiiiiiiiiiiin! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): 3 points! Let the
  L2 (13ch): Member Number
  L3 (14ch): Lottery begin!
```
**Long words:** begiiiiiiiiiiiiiiin!

### [batch_06.json] r1209 msg378

**Current:**
```
  L1 (81ch): I'll take 5 points! Well then, let the Member Number Lottery begiiiiiiiiiiiiiiin! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): 5 points! Let the
  L2 (13ch): Member Number
  L3 (14ch): Lottery begin!
```
**Long words:** begiiiiiiiiiiiiiiin!

### [batch_06.json] r1209 msg383

**Current:**
```
  L1 (25ch): Oh my goodnessssssssssss! <-- WIDE
```
**Proposed rewrite:**
```
  L1 ( 5ch): Oh my
  L2 (19ch): goodnessssssssssss!
```
**Long words:** goodnessssssssssss!

### [batch_06.json] r1209 msg401

**Current:**
```
  L1 (30ch): 000000001234567890- Drawing... <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): 000000001234567890-
  L2 (10ch): Drawing...
```
**Long words:** 000000001234567890-

### [batch_r39_equip_a.json] r39 msg346

**Current:**
```
  L1 (217ch): Beat me at 5 rounds of Rock-Paper-Scissors and I'll give you something good! But if you lose, you get Ripu'd! Fee: 1 medal per loss. Confident in your luck? Come to B2F, the small room on the floor with lots of cells. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Beat me at 5 rounds
  L2 (14ch): of Rock-Paper-
  L3 (18ch): Scissors for loot!
```
**Long words:** Rock-Paper-Scissors

### [batch_r39_equip_a.json] r39 msg380

**Current:**
```
  L1 (23ch): Rock-Paper-Scissors Man <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Rock-Paper-Scissors
  L2 ( 3ch): Man
```
**Long words:** Rock-Paper-Scissors

### [batch_r39_equip_a.json] r39 msg403

**Current:**
```
  L1 (46ch): A shadow is targeting Rock-Paper-Scissors Man! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (11ch): A shadow is
  L2 (15ch): targeting Rock-
  L3 (19ch): Paper-Scissors Man!
```
**Long words:** Rock-Paper-Scissors

### [chunk_00_translated.json] r34 msg18

**Current:**
```
  L1 (21ch): Saint's Hair Ornament <-- WIDE
```
**Proposed rewrite:**
```
  L1 (12ch): Saint's Hair
  L2 ( 8ch): Ornament
```

### [chunk_00_translated.json] r34 msg21

**Current:**
```
  L1 (21ch): Witch's Hair Ornament <-- WIDE
```
**Proposed rewrite:**
```
  L1 (12ch): Witch's Hair
  L2 ( 8ch): Ornament
```

### [chunk_00_translated.json] r34 msg27

**Current:**
```
  L1 (21ch): Useless Orc Wristband <-- WIDE
```
**Proposed rewrite:**
```
  L1 (11ch): Useless Orc
  L2 ( 9ch): Wristband
```

### [chunk_01_translated.json] r37 msg1

**Current:**
```
  L1 (16ch): Enter your name.
  L2 (26ch): [M name/F name: Auto-fill] <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Enter your name. [M
  L2 (18ch): name/F name: Auto-
  L3 ( 5ch): fill]
```

### [chunk_02_translated.json] r38 msg88

**Current:**
```
  L1 (21ch): Sensitive to spirits. <-- WIDE
  L2 (15ch): Trembles at the
  L3 (15ch): sight of Death.
```
**Proposed rewrite:**
```
  L1 (14ch): Fears spirits.
  L2 (15ch): Trembles at the
  L3 (15ch): sight of Death.
```

### [chunk_02_translated.json] r38 msg95

**Current:**
```
  L1 (18ch): Believes in mystic
  L2 (17ch): power. Happy when
  L3 (22ch): magic knowledge grows. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Believes in mystic
  L2 (20ch): power. Loves gaining
  L3 (16ch): magic knowledge.
```

### [chunk_02_translated.json] r38 msg96

**Current:**
```
  L1 (17ch): A skilled warrior
  L2 (21ch): who seeks battle with <-- WIDE
  L3 (17ch): strong opponents.
```
**Proposed rewrite:**
```
  L1 (19ch): Skilled warrior who
  L2 (17ch): seeks battle with
  L3 (17ch): strong opponents.
```

### [chunk_02_translated.json] r38 msg104

**Current:**
```
  L1 (20ch): Cannot forgive those
  L2 (18ch): who slay friendly,
  L3 (21ch): non-hostile monsters. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Can't forgive those
  L2 (17ch): who slay friendly
  L3 ( 9ch): monsters.
```

### [chunk_02_translated.json] r38 msg107

**Current:**
```
  L1 (18ch): Hates fighting and
  L2 (17ch): bloodshed. Deeply
  L3 (21ch): mourns fallen allies. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Hates fighting and
  L2 (17ch): bloodshed. Mourns
  L3 (14ch): fallen allies.
```

### [chunk_02_translated.json] r38 msg108

**Current:**
```
  L1 (20ch): Very short-tempered.
  L2 (15ch): Long, drawn-out
  L3 (22ch): battles are maddening. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Very short-tempered.
  L2 (16ch): Long battles are
  L3 (10ch): maddening.
```

### [chunk_02_translated.json] r38 msg112

**Current:**
```
  L1 (17ch): Happy one moment,
  L2 (18ch): angry the next. An
  L3 (21ch): unpredictable nature. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): Happy one moment,
  L2 (15ch): angry the next.
  L3 (14ch): Unpredictable.
```

### [chunk_03_translated.json] r38 msg134

**Current:**
```
  L1 (19ch): Can handle alchemy.
  L2 (20ch): Learns Sorceries and
  L3 (21ch): Holy Magic up to Lv4. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): Handles alchemy.
  L2 (17ch): Sorc & Holy Magic
  L3 (10ch): up to Lv4.
```

### [chunk_03_translated.json] r38 msg143

**Current:**
```
  L1 (21ch): Affects Sorcery power <-- WIDE
  L2 (15ch): and resistance.
```
**Proposed rewrite:**
```
  L1 (15ch): Affects Sorcery
  L2 ( 9ch): power and
  L3 (11ch): resistance.
```

### [chunk_03_translated.json] r38 msg144

**Current:**
```
  L1 (18ch): Affects Holy Magic
  L2 (21ch): power and resistance. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Affects Holy Magic
  L2 ( 9ch): power and
  L3 (11ch): resistance.
```

### [chunk_03_translated.json] r38 msg147

**Current:**
```
  L1 (21ch): Affects breath resist <-- WIDE
  L2 (16ch): and critical hit
  L3 ( 7ch): chance.
```
**Proposed rewrite:**
```
  L1 (14ch): Affects breath
  L2 (19ch): resist and critical
  L3 (11ch): hit chance.
```

### [chunk_04_translated.json] r39 msg75

**Current:**
```
  L1 (20ch): Weapons of different
  L2 (24ch): element can't dual wield <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Weapons of different
  L2 (18ch): element can't dual
  L3 ( 5ch): wield
```

### [chunk_04_translated.json] r40 msg14

**Current:**
```
  L1 (23ch): 30 days have not passed <-- WIDE
  L2 (24ch): since last class change. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): 30 days have not
  L2 (17ch): passed since last
  L3 (13ch): class change.
```

### [chunk_04_translated.json] r40 msg15

**Current:**
```
  L1 (21ch): Delete from registry. <-- WIDE
  L2 (22ch): This cannot be undone. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (11ch): Delete from
  L2 (14ch): registry. This
  L3 (17ch): cannot be undone.
```

### [chunk_04_translated.json] r40 msg43

**Current:**
```
  L1 (19ch): Cannot change class
  L2 (21ch): while gear is in use. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Cannot change class
  L2 (16ch): while gear is in
  L3 ( 4ch): use.
```

### [chunk_04_translated.json] r40 msg45

**Current:**
```
  L1 (19ch): Stats and alignment
  L2 (23ch): don't match. No change. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Stats and alignment
  L2 (15ch): don't match. No
  L3 ( 7ch): change.
```

### [chunk_04_translated.json] r40 msg53

**Current:**
```
  L1 (22ch): Summoned via registry. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (12ch): Summoned via
  L2 ( 9ch): registry.
```

### [chunk_04_translated.json] r41 msg1

**Current:**
```
  L1 (21ch): This is Salem Church. <-- WIDE
  L2 (20ch): What business brings
  L3 ( 9ch): you here?
```
**Proposed rewrite:**
```
  L1 (18ch): Salem Church. What
  L2 (19ch): business brings you
  L3 ( 5ch): here?
```

### [chunk_04_translated.json] r41 msg2

**Current:**
```
  L1 (24ch): Welcome to Salem Church. <-- WIDE
  L2 (17ch): It seems you need
  L3 (11ch): divine aid.
```
**Proposed rewrite:**
```
  L1 (16ch): Welcome to Salem
  L2 (20ch): Church. It seems you
  L3 (16ch): need divine aid.
```

### [chunk_04_translated.json] r41 msg5

**Current:**
```
  L1 (19ch): You dare seek God's
  L2 (23ch): power without offering! <-- WIDE
  L3 (16ch): Begone, heretic!
```
**Proposed rewrite:**
```
  L1 (15ch): No offering, no
  L2 (13ch): divine power!
  L3 (16ch): Begone, heretic!
```

### [chunk_04_translated.json] r42 msg6

**Current:**
```
  L1 (18ch): Did you rest well?
  L2 (19ch): Good rest fuels the
  L3 (24ch): days ahead. Visit again. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Rest well? Good rest
  L2 (15ch): fuels tomorrow.
  L3 (12ch): Visit again.
```

### [chunk_06_translated.json] r45 msg36

**Current:**
```
  L1 (21ch): This is yer /storage. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (11ch): This is yer
  L2 ( 9ch): /storage.
```

### [chunk_06_translated.json] r45 msg38

**Current:**
```
  L1 (30ch): Whose items /d'ya wanna store? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): Whose items /d'ya
  L2 (12ch): wanna store?
```

### [chunk_06_translated.json] r45 msg40

**Current:**
```
  L1 (24ch): Whose item to /identify? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (13ch): Whose item to
  L2 (10ch): /identify?
```

### [chunk_06_translated.json] r45 msg41

**Current:**
```
  L1 (23ch): Which one to /identify? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (12ch): Which one to
  L2 (10ch): /identify?
```

### [chunk_06_translated.json] r45 msg43

**Current:**
```
  L1 (48ch): There! Now ya know /what it is. /Feels good, eh? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): There! Now ya know
  L2 (19ch): /what it is. /Feels
  L3 ( 9ch): good, eh?
```

### [chunk_06_translated.json] r45 msg44

**Current:**
```
  L1 (39ch): Who's the poor /soul that got /cursed?? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Who's the poor /soul
  L2 (18ch): that got /cursed??
```

### [chunk_06_translated.json] r45 msg45

**Current:**
```
  L1 (29ch): Which curse /should I remove? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Which curse /should
  L2 ( 9ch): I remove?
```

### [chunk_06_translated.json] r45 msg46

**Current:**
```
  L1 (56ch): Want it uncursed? /Bein' cursed all /the time hurts, eh? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): Want it uncursed?
  L2 (16ch): Bein' cursed all
  L3 (15ch): the time hurts!
```

### [chunk_06_translated.json] r45 msg47

**Current:**
```
  L1 (43ch): There! Curse is /gone now. /Feels good, eh? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (15ch): There! Curse is
  L2 (17ch): /gone now. /Feels
  L3 ( 9ch): good, eh?
```

### [chunk_06_translated.json] r45 msg48

**Current:**
```
  L1 (48ch): Ohhh, I'm the /uncursin' superstar /around here! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (13ch): Ohhh, I'm the
  L2 (20ch): /uncursin' superstar
  L3 (13ch): /around here!
```

### [chunk_06_translated.json] r45 msg49

**Current:**
```
  L1 (49ch): Right then. /Here's the latest /Vigger Shop info. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Right then. /Here's
  L2 (18ch): the latest /Vigger
  L3 (10ch): Shop info.
```

### [chunk_06_translated.json] r45 msg50

**Current:**
```
  L1 (33ch): Wanna invest in /our Vigger Shop? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Wanna invest in /our
  L2 (12ch): Vigger Shop?
```

### [chunk_06_translated.json] r45 msg51

**Current:**
```
  L1 (31ch): I'll make yer /storage bigger~! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (13ch): I'll make yer
  L2 (17ch): /storage bigger~!
```

### [chunk_06_translated.json] r45 msg52

**Current:**
```
  L1 (51ch): Build a branch /of our Vigger Shop? /I see, I see~! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Build a branch /of
  L2 (19ch): our Vigger Shop? /I
  L3 (12ch): see, I see~!
```

### [chunk_06_translated.json] r45 msg53

**Current:**
```
  L1 (32ch): Renovate and /reopen the branch? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Renovate and /reopen
  L2 (11ch): the branch?
```

### [chunk_06_translated.json] r45 msg54

**Current:**
```
  L1 (27ch): Relocate the /branch store? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Relocate the /branch
  L2 ( 6ch): store?
```

### [chunk_06_translated.json] r45 msg55

**Current:**
```
  L1 (47ch): Expand now and /you can store up /to 20 items~! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Expand now and /you
  L2 (19ch): can store up /to 20
  L3 ( 7ch): items~!
```

### [chunk_06_translated.json] r45 msg56

**Current:**
```
  L1 (47ch): Expand now and /you can store up /to 30 items~! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Expand now and /you
  L2 (19ch): can store up /to 30
  L3 ( 7ch): items~!
```

### [chunk_06_translated.json] r45 msg57

**Current:**
```
  L1 (47ch): Expand now and /you can store up /to 40 items~! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Expand now and /you
  L2 (19ch): can store up /to 40
  L3 ( 7ch): items~!
```

### [chunk_06_translated.json] r45 msg58

**Current:**
```
  L1 (47ch): Expand now and /you can store up /to 50 items~! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Expand now and /you
  L2 (19ch): can store up /to 50
  L3 ( 7ch): items~!
```

### [chunk_06_translated.json] r45 msg59

**Current:**
```
  L1 (47ch): Expand now and /you can store up /to 60 items~! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Expand now and /you
  L2 (19ch): can store up /to 60
  L3 ( 7ch): items~!
```

### [chunk_06_translated.json] r45 msg60

**Current:**
```
  L1 (47ch): Expand now and /you can store up /to 70 items~! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Expand now and /you
  L2 (19ch): can store up /to 70
  L3 ( 7ch): items~!
```

### [chunk_06_translated.json] r45 msg61

**Current:**
```
  L1 (47ch): Expand now and /you can store up /to 80 items~! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Expand now and /you
  L2 (19ch): can store up /to 80
  L3 ( 7ch): items~!
```

### [chunk_06_translated.json] r45 msg62

**Current:**
```
  L1 (47ch): Expand now and /you can store up /to 90 items~! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Expand now and /you
  L2 (19ch): can store up /to 90
  L3 ( 7ch): items~!
```

### [chunk_06_translated.json] r45 msg63

**Current:**
```
  L1 (48ch): Expand now and /you can store up /to 100 items~! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Expand now and /you
  L2 (20ch): can store up /to 100
  L3 ( 7ch): items~!
```

### [chunk_06_translated.json] r45 msg64

**Current:**
```
  L1 (38ch): Hey, you! /Ya don't have /enough gold! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Hey, you! /Ya don't
  L2 (18ch): have /enough gold!
```

### [chunk_06_translated.json] r45 msg65

**Current:**
```
  L1 (25ch): Where should we /open it? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (15ch): Where should we
  L2 ( 9ch): /open it?
```

### [chunk_06_translated.json] r45 msg66

**Current:**
```
  L1 (35ch): Our dream branch /is finally here~! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Our dream branch /is
  L2 (14ch): finally here~!
```

### [chunk_06_translated.json] r45 msg67

**Current:**
```
  L1 (56ch): If we can always /buy stuff, managin' /inventory's easy! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): If we can always
  L2 (20ch): /buy stuff, managin'
  L3 (18ch): /inventory's easy!
```

### [chunk_06_translated.json] r45 msg68

**Current:**
```
  L1 (51ch): I'll send yer /stuff to storage /anytime! Thank me! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): I'll send yer /stuff
  L2 (20ch): to storage /anytime!
  L3 ( 9ch): Thank me!
```

### [chunk_06_translated.json] r45 msg69

**Current:**
```
  L1 (50ch): Hold various /events and clients /won't get bored! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Hold various /events
  L2 (18ch): and clients /won't
  L3 (10ch): get bored!
```

### [chunk_06_translated.json] r45 msg70

**Current:**
```
  L1 (49ch): Rest anytime, /even when beat up! /No levels tho. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Rest anytime, /even
  L2 (17ch): when beat up! /No
  L3 (11ch): levels tho.
```

### [chunk_06_translated.json] r45 msg71

**Current:**
```
  L1 (34ch): The branch keeps /gettin' fancier! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): The branch keeps
  L2 (17ch): /gettin' fancier!
```

### [chunk_06_translated.json] r45 msg73

**Current:**
```
  L1 (43ch): Hope relocatin' /brings in more /customers! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (15ch): Hope relocatin'
  L2 (15ch): /brings in more
  L3 (11ch): /customers!
```

### [chunk_06_translated.json] r45 msg75

**Current:**
```
  L1 (25ch): Send 'em out /to explore? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): Send 'em out /to
  L2 ( 8ch): explore?
```

### [chunk_06_translated.json] r45 msg81

**Current:**
```
  L1 (28ch): Deliver and /complete order? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (11ch): Deliver and
  L2 (16ch): /complete order?
```

### [chunk_06_translated.json] r45 msg83

**Current:**
```
  L1 (32ch): Introduce this /order to allies? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (14ch): Introduce this
  L2 (17ch): /order to allies?
```

### [chunk_06_translated.json] r45 msg91

**Current:**
```
  L1 (32ch): Curse broken but /item survived! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): Curse broken but
  L2 (15ch): /item survived!
```

### [chunk_06_translated.json] r45 msg109

**Current:**
```
  L1 (28ch): It's equipped. /Sell anyway? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): It's equipped. /Sell
  L2 ( 7ch): anyway?
```

### [chunk_06_translated.json] r45 msg111

**Current:**
```
  L1 (27ch): Can't remove /due to curse! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Can't remove /due to
  L2 ( 6ch): curse!
```

### [chunk_06_translated.json] r45 msg112

**Current:**
```
  L1 (50ch): Dunno what this /is, so I'll only /pay 10g for it. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Dunno what this /is,
  L2 (17ch): so I'll only /pay
  L3 (11ch): 10g for it.
```

### [chunk_06_translated.json] r45 msg113

**Current:**
```
  L1 (26ch): Unequip it. /Is that okay? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Unequip it. /Is that
  L2 ( 5ch): okay?
```

### [chunk_06_translated.json] r45 msg125

**Current:**
```
  L1 (21ch): No items in /storage. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (11ch): No items in
  L2 ( 9ch): /storage.
```

### [chunk_06_translated.json] r45 msg134

**Current:**
```
  L1 (27ch): Adv. Goods /Buyback Lifted! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Adv. Goods /Buyback
  L2 ( 7ch): Lifted!
```

### [chunk_06_translated.json] r45 msg135

**Current:**
```
  L1 (29ch): Cursed Equip /Buyback Lifted! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (12ch): Cursed Equip
  L2 (16ch): /Buyback Lifted!
```

### [chunk_06_translated.json] r45 msg136

**Current:**
```
  L1 (22ch): Equip Buyback /Lifted! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (13ch): Equip Buyback
  L2 ( 8ch): /Lifted!
```

### [chunk_06_translated.json] r45 msg137

**Current:**
```
  L1 (30ch): Recovery Item /Buyback Lifted! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (13ch): Recovery Item
  L2 (16ch): /Buyback Lifted!
```

### [chunk_06_translated.json] r45 msg138

**Current:**
```
  L1 (21ch): Item Buyback /Lifted! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (12ch): Item Buyback
  L2 ( 8ch): /Lifted!
```

### [chunk_06_translated.json] r45 msg139

**Current:**
```
  L1 (21ch): No orders to /accept. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (12ch): No orders to
  L2 ( 8ch): /accept.
```

### [chunk_07_translated.json] r47 msg5

**Current:**
```
  L1 (23ch): Surprised the monsters! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (13ch): Surprised the
  L2 ( 9ch): monsters!
```

### [chunk_07_translated.json] r47 msg7

**Current:**
```
  L1 (21ch): Ambushed by monsters! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (11ch): Ambushed by
  L2 ( 9ch): monsters!
```

### [chunk_08_translated.json] r48 msg37

**Current:**
```
  L1 (27ch): Neighborhood Recycling Shop <-- WIDE
```
**Proposed rewrite:**
```
  L1 (12ch): Neighborhood
  L2 (14ch): Recycling Shop
```

### [chunk_08_translated.json] r48 msg38

**Current:**
```
  L1 (27ch): Neighborhood Dumping Ground <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Neighborhood Dumping
  L2 ( 6ch): Ground
```

### [chunk_08_translated.json] r48 msg39

**Current:**
```
  L1 (26ch): Neighborhood Disposal Site <-- WIDE
```
**Proposed rewrite:**
```
  L1 (12ch): Neighborhood
  L2 (13ch): Disposal Site
```

### [chunk_08_translated.json] r48 msg40

**Current:**
```
  L1 (31ch): Neighborhood Waste Incineration <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Neighborhood Waste
  L2 (12ch): Incineration
```

### [chunk_08_translated.json] r48 msg41

**Current:**
```
  L1 (25ch): Neighborhood Garbage Dump <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Neighborhood Garbage
  L2 ( 4ch): Dump
```

### [chunk_08_translated.json] r48 msg47

**Current:**
```
  L1 (27ch): Neighborhood Recycling Shop <-- WIDE
```
**Proposed rewrite:**
```
  L1 (12ch): Neighborhood
  L2 (14ch): Recycling Shop
```

### [chunk_08_translated.json] r48 msg48

**Current:**
```
  L1 (25ch): Settlement Dumping Ground <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Settlement Dumping
  L2 ( 6ch): Ground
```

### [chunk_08_translated.json] r48 msg49

**Current:**
```
  L1 (24ch): Settlement Disposal Site <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Settlement Disposal
  L2 ( 4ch): Site
```

### [chunk_08_translated.json] r48 msg50

**Current:**
```
  L1 (29ch): Settlement Waste Incineration <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): Settlement Waste
  L2 (12ch): Incineration
```

### [chunk_08_translated.json] r48 msg51

**Current:**
```
  L1 (23ch): Settlement Garbage Dump <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Settlement Garbage
  L2 ( 4ch): Dump
```

### [chunk_08_translated.json] r48 msg58

**Current:**
```
  L1 (25ch): Settlement Recycling Shop <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Settlement Recycling
  L2 ( 4ch): Shop
```

### [chunk_08_translated.json] r48 msg59

**Current:**
```
  L1 (22ch): Illegal Dumping Ground <-- WIDE
```
**Proposed rewrite:**
```
  L1 (15ch): Illegal Dumping
  L2 ( 6ch): Ground
```

### [chunk_08_translated.json] r48 msg61

**Current:**
```
  L1 (24ch): Waste Incineration Plant <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Waste Incineration
  L2 ( 5ch): Plant
```

### [chunk_08_translated.json] r48 msg62

**Current:**
```
  L1 (22ch): Oversized Garbage Dump <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): Oversized Garbage
  L2 ( 4ch): Dump
```

### [chunk_08_translated.json] r48 msg66

**Current:**
```
  L1 (27ch): Neighborhood Recycling Shop <-- WIDE
```
**Proposed rewrite:**
```
  L1 (12ch): Neighborhood
  L2 (14ch): Recycling Shop
```

### [chunk_08_translated.json] r48 msg67

**Current:**
```
  L1 (25ch): Settlement Dumping Ground <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Settlement Dumping
  L2 ( 6ch): Ground
```

### [chunk_08_translated.json] r48 msg68

**Current:**
```
  L1 (24ch): Settlement Disposal Site <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Settlement Disposal
  L2 ( 4ch): Site
```

### [chunk_08_translated.json] r48 msg69

**Current:**
```
  L1 (29ch): Settlement Waste Incineration <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): Settlement Waste
  L2 (12ch): Incineration
```

### [chunk_08_translated.json] r48 msg70

**Current:**
```
  L1 (23ch): Settlement Garbage Dump <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Settlement Garbage
  L2 ( 4ch): Dump
```

### [chunk_08_translated.json] r48 msg76

**Current:**
```
  L1 (25ch): Settlement Recycling Shop <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Settlement Recycling
  L2 ( 4ch): Shop
```

### [chunk_08_translated.json] r48 msg77

**Current:**
```
  L1 (22ch): Illegal Dumping Ground <-- WIDE
```
**Proposed rewrite:**
```
  L1 (15ch): Illegal Dumping
  L2 ( 6ch): Ground
```

### [chunk_08_translated.json] r48 msg79

**Current:**
```
  L1 (24ch): Waste Incineration Plant <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Waste Incineration
  L2 ( 5ch): Plant
```

### [chunk_08_translated.json] r48 msg80

**Current:**
```
  L1 (22ch): Oversized Garbage Dump <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): Oversized Garbage
  L2 ( 4ch): Dump
```

### [chunk_08_translated.json] r48 msg84

**Current:**
```
  L1 (22ch): Trashed Up Vacant Lots <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): Trashed Up Vacant
  L2 ( 4ch): Lots
```

### [chunk_08_translated.json] r48 msg88

**Current:**
```
  L1 (27ch): Neighborhood Recycling Shop <-- WIDE
```
**Proposed rewrite:**
```
  L1 (12ch): Neighborhood
  L2 (14ch): Recycling Shop
```

### [chunk_08_translated.json] r48 msg89

**Current:**
```
  L1 (22ch): Illegal Dumping Ground <-- WIDE
```
**Proposed rewrite:**
```
  L1 (15ch): Illegal Dumping
  L2 ( 6ch): Ground
```

### [chunk_08_translated.json] r48 msg91

**Current:**
```
  L1 (24ch): Waste Incineration Plant <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Waste Incineration
  L2 ( 5ch): Plant
```

### [chunk_08_translated.json] r48 msg92

**Current:**
```
  L1 (22ch): Oversized Garbage Dump <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): Oversized Garbage
  L2 ( 4ch): Dump
```

### [chunk_08_translated.json] r48 msg93

**Current:**
```
  L1 (22ch): Trashed Up Vacant Lots <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): Trashed Up Vacant
  L2 ( 4ch): Lots
```

### [chunk_08_translated.json] r48 msg97

**Current:**
```
  L1 (27ch): Neighborhood Recycling Shop <-- WIDE
```
**Proposed rewrite:**
```
  L1 (12ch): Neighborhood
  L2 (14ch): Recycling Shop
```

### [chunk_08_translated.json] r48 msg98

**Current:**
```
  L1 (22ch): Illegal Dumping Ground <-- WIDE
```
**Proposed rewrite:**
```
  L1 (15ch): Illegal Dumping
  L2 ( 6ch): Ground
```

### [chunk_08_translated.json] r48 msg100

**Current:**
```
  L1 (24ch): Waste Incineration Plant <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Waste Incineration
  L2 ( 5ch): Plant
```

### [chunk_08_translated.json] r48 msg101

**Current:**
```
  L1 (22ch): Oversized Garbage Dump <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): Oversized Garbage
  L2 ( 4ch): Dump
```

### [chunk_08_translated.json] r48 msg102

**Current:**
```
  L1 (22ch): Trashed Up Vacant Lots <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): Trashed Up Vacant
  L2 ( 4ch): Lots
```

### [chunk_08_translated.json] r48 msg106

**Current:**
```
  L1 (27ch): Neighborhood Recycling Shop <-- WIDE
```
**Proposed rewrite:**
```
  L1 (12ch): Neighborhood
  L2 (14ch): Recycling Shop
```

### [chunk_08_translated.json] r49 msg1

**Current:**
```
  L1 (26ch): Can't open from this side. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Can't open from this
  L2 ( 5ch): side.
```

### [chunk_08_translated.json] r49 msg2

**Current:**
```
  L1 (26ch): A fragile, crumbling wall. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): A fragile, crumbling
  L2 ( 5ch): wall.
```

### [chunk_08_translated.json] r49 msg3

**Current:**
```
  L1 (18ch): The switch is off.
  L2 (21ch): Turned the switch on. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): The switch is off.
  L2 (17ch): Turned the switch
  L3 ( 3ch): on.
```

### [chunk_08_translated.json] r49 msg4

**Current:**
```
  L1 (17ch): The switch is on.
  L2 (22ch): Turned the switch off. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): The switch is on.
  L2 (17ch): Turned the switch
  L3 ( 4ch): off.
```

### [chunk_08_translated.json] r49 msg6

**Current:**
```
  L1 (27ch): A loaded mine cart is here. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): A loaded mine cart
  L2 ( 8ch): is here.
```

### [chunk_08_translated.json] r49 msg7

**Current:**
```
  L1 (36ch): The bridge is raised. No way across. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (13ch): The bridge is
  L2 (14ch): raised. No way
  L3 ( 7ch): across.
```

### [chunk_08_translated.json] r49 msg8

**Current:**
```
  L1 (32ch): A large boulder blocks the path. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (15ch): A large boulder
  L2 (16ch): blocks the path.
```

### [chunk_08_translated.json] r49 msg9

**Current:**
```
  L1 (21ch): Cargo blocks the way. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): Cargo blocks the
  L2 ( 4ch): way.
```

### [chunk_08_translated.json] r49 msg10

**Current:**
```
  L1 (31ch): Collapsed cargo lies scattered. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Collapsed cargo lies
  L2 (10ch): scattered.
```

### [chunk_08_translated.json] r49 msg11

**Current:**
```
  L1 (29ch): An old barrel left abandoned. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): An old barrel left
  L2 (10ch): abandoned.
```

### [chunk_08_translated.json] r49 msg12

**Current:**
```
  L1 (27ch): A skeleton lies before you. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (15ch): A skeleton lies
  L2 (11ch): before you.
```

### [chunk_08_translated.json] r49 msg13

**Current:**
```
  L1 (29ch): A skeleton lies at your feet. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): A skeleton lies at
  L2 (10ch): your feet.
```

### [chunk_08_translated.json] r49 msg14

**Current:**
```
  L1 (34ch): A skeleton leans against the wall. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): A skeleton leans
  L2 (17ch): against the wall.
```

### [chunk_08_translated.json] r49 msg15

**Current:**
```
  L1 (30ch): A goddess statue is displayed. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): A goddess statue is
  L2 (10ch): displayed.
```

### [chunk_08_translated.json] r49 msg16

**Current:**
```
  L1 (29ch): A half-broken statue is here. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): A half-broken statue
  L2 ( 8ch): is here.
```

### [chunk_08_translated.json] r49 msg18

**Current:**
```
  L1 (22ch): The wall has crumbled. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (12ch): The wall has
  L2 ( 9ch): crumbled.
```

### [chunk_08_translated.json] r49 msg19

**Current:**
```
  L1 (23ch): Rubble blocks the path. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): Rubble blocks the
  L2 ( 5ch): path.
```

### [chunk_08_translated.json] r49 msg20

**Current:**
```
  L1 (29ch): A broken doll lies discarded. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): A broken doll lies
  L2 (10ch): discarded.
```

### [chunk_08_translated.json] r49 msg21

**Current:**
```
  L1 (30ch): A huge statue hangs suspended. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): A huge statue hangs
  L2 (10ch): suspended.
```

### [chunk_08_translated.json] r49 msg22

**Current:**
```
  L1 (30ch): A huge statue hangs suspended. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): A huge statue hangs
  L2 (10ch): suspended.
```

### [chunk_08_translated.json] r49 msg23

**Current:**
```
  L1 (29ch): An equestrian statue is here. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): An equestrian statue
  L2 ( 8ch): is here.
```

### [chunk_08_translated.json] r49 msg24

**Current:**
```
  L1 (23ch): A wall blocks the path. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): A wall blocks the
  L2 ( 5ch): path.
```

### [chunk_08_translated.json] r49 msg25

**Current:**
```
  L1 (29ch): An oddly shaped wall is here. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): An oddly shaped wall
  L2 ( 8ch): is here.
```

### [chunk_08_translated.json] r49 msg26

**Current:**
```
  L1 (32ch): Some device is set on the fence. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Some device is set
  L2 (13ch): on the fence.
```

### [chunk_08_translated.json] r49 msg27

**Current:**
```
  L1 (29ch): Spring water has pooled here. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): Spring water has
  L2 (12ch): pooled here.
```

### [chunk_08_translated.json] r49 msg28

**Current:**
```
  L1 (28ch): Dead end above. Can't go up. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (15ch): Dead end above.
  L2 (12ch): Can't go up.
```

### [chunk_08_translated.json] r49 msg29

**Current:**
```
  L1 (22ch): There are stairs here. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): There are stairs
  L2 ( 5ch): here.
```

### [chunk_08_translated.json] r49 msg30

**Current:**
```
  L1 (28ch): A device to move the stairs. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): A device to move the
  L2 ( 7ch): stairs.
```

### [chunk_08_translated.json] r49 msg31

**Current:**
```
  L1 (26ch): A large grave stands here. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): A large grave stands
  L2 ( 5ch): here.
```

### [chunk_08_translated.json] r49 msg32

**Current:**
```
  L1 (27ch): A device next to the grave. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): A device next to the
  L2 ( 6ch): grave.
```

### [chunk_08_translated.json] r49 msg33

**Current:**
```
  L1 (31ch): A hole big enough to jump into. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): A hole big enough to
  L2 (10ch): jump into.
```

### [chunk_08_translated.json] r49 msg34

**Current:**
```
  L1 (24ch): Open the treasure chest? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): Open the treasure
  L2 ( 6ch): chest?
```

### [chunk_08_translated.json] r49 msg37

**Current:**
```
  L1 (21ch): Left the chest alone. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (14ch): Left the chest
  L2 ( 6ch): alone.
```

### [chunk_09_translated.json] r49 msg62

**Current:**
```
  L1 (22ch): Climb down the ladder? <-- WIDE
```
**Proposed rewrite:**
```
  L1 (14ch): Climb down the
  L2 ( 7ch): ladder?
```

### [chunk_09_translated.json] r49 msg67

**Current:**
```
  L1 (22ch): Debris blocks the way. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): Debris blocks the
  L2 ( 4ch): way.
```

### [chunk_09_translated.json] r49 msg77

**Current:**
```
  L1 (21ch): Flames block the way. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): Flames block the
  L2 ( 4ch): way.
```

### [chunk_09_translated.json] r49 msg78

**Current:**
```
  L1 (23ch): Stairs in the distance. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (13ch): Stairs in the
  L2 ( 9ch): distance.
```

### [chunk_09_translated.json] r49 msg86

**Current:**
```
  L1 (22ch): An adventurer's corpse <-- WIDE
  L2 (19ch): lies by the rubble.
```
**Proposed rewrite:**
```
  L1 (15ch): An adventurer's
  L2 (18ch): corpse lies by the
  L3 ( 7ch): rubble.
```

### [chunk_09_translated.json] r49 msg92

**Current:**
```
  L1 (13ch): The air feels
  L2 (22ch): especially heavy here. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (13ch): The air feels
  L2 (16ch): especially heavy
  L3 ( 5ch): here.
```

### [chunk_09_translated.json] r49 msg93

**Current:**
```
  L1 (21ch): There is a water jug. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): There is a water
  L2 ( 4ch): jug.
```

### [chunk_r37_extra.json] r37 msg124

**Current:**
```
  L1 (19ch): Press O or X button
  L2 (24ch): to confirm your choices. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Press O or X button
  L2 (15ch): to confirm your
  L3 ( 8ch): choices.
```

### [chunk_r37_r48_r49_translated.json] r37 msg2

**Current:**
```
  L1 (13ch): enter a name.
  L2 (25ch): m name, f name: auto-fill <-- WIDE
```
**Proposed rewrite:**
```
  L1 (15ch): enter a name. m
  L2 (19ch): name, f name: auto-
  L3 ( 4ch): fill
```

### [chunk_r37_r48_r49_translated.json] r37 msg7

**Current:**
```
  L1 (21ch): allocate stat points. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (13ch): allocate stat
  L2 ( 7ch): points.
```

### [chunk_r37_r48_r49_translated.json] r49 msg1

**Current:**
```
  L1 (21ch): nothing unusual here. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (15ch): nothing unusual
  L2 ( 5ch): here.
```

### [chunk_r37_r48_r49_translated.json] r49 msg4

**Current:**
```
  L1 (18ch): the switch is off.
  L2 (25ch): the switch was turned on. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): the switch is off.
  L2 (14ch): the switch was
  L3 (10ch): turned on.
```

### [chunk_r37_r48_r49_translated.json] r49 msg5

**Current:**
```
  L1 (17ch): the switch is on.
  L2 (26ch): the switch was turned off. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): the switch is on.
  L2 (14ch): the switch was
  L3 (11ch): turned off.
```

### [chunk_r37_r48_r49_translated.json] r49 msg62

**Current:**
```
  L1 (20ch): climb up the ladder?
  L2 (21ch): confirm: o  cancel: x <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): climb up the ladder?
  L2 (19ch): confirm: o  cancel:
  L3 ( 1ch): x
```

### [chunk_r37_r48_r49_translated.json] r49 msg63

**Current:**
```
  L1 (18ch): climb down ladder?
  L2 (21ch): confirm: o  cancel: x <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): climb down ladder?
  L2 (19ch): confirm: o  cancel:
  L3 ( 1ch): x
```

### [chunk_r37_r48_r49_translated.json] r49 msg69

**Current:**
```
  L1 (13ch): used the key.
  L2 (23ch): the rusty key crumbled. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): used the key. the
  L2 (19ch): rusty key crumbled.
```

### [chunk_r38_fix.json] r38 msg87

**Current:**
```
  L1 (13ch): bores easily.
  L2 (21ch): return to town often. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): bores easily. return
  L2 (14ch): to town often.
```

### [chunk_r38_fix.json] r38 msg89

**Current:**
```
  L1 (20ch): lives to hoard gold.
  L2 (21ch): angry if loot is low. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): lives to hoard gold.
  L2 (16ch): angry if loot is
  L3 ( 4ch): low.
```

### [chunk_r38_fix.json] r38 msg107

**Current:**
```
  L1 (16ch): hates bloodshed.
  L2 (21ch): mourns fallen allies. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): hates bloodshed.
  L2 (13ch): mourns fallen
  L3 ( 7ch): allies.
```

### [chunk_r38_fix.json] r38 msg134

**Current:**
```
  L1 (19ch): can handle alchemy.
  L2 (18ch): learns sorcery and
  L3 (21ch): holy magic up to lv4. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): Handles alchemy.
  L2 (17ch): Sorc & Holy Magic
  L3 (10ch): up to Lv4.
```

### [chunk_r38_fix.json] r38 msg143

**Current:**
```
  L1 (21ch): affects sorcery power <-- WIDE
  L2 (15ch): and resistance.
```
**Proposed rewrite:**
```
  L1 (15ch): affects sorcery
  L2 ( 9ch): power and
  L3 (11ch): resistance.
```

### [chunk_r38_fix.json] r38 msg144

**Current:**
```
  L1 (18ch): affects holy magic
  L2 (21ch): power and resistance. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): affects holy magic
  L2 ( 9ch): power and
  L3 (11ch): resistance.
```

### [chunk_r38_fix.json] r38 msg147

**Current:**
```
  L1 (21ch): affects breath resist <-- WIDE
  L2 (16ch): and critical hit
  L3 ( 7ch): chance.
```
**Proposed rewrite:**
```
  L1 (14ch): affects breath
  L2 (19ch): resist and critical
  L3 (11ch): hit chance.
```

### [chunk_r40_r42_translated.json] r40 msg15

**Current:**
```
  L1 (23ch): 30 days have not passed <-- WIDE
  L2 (28ch): since the last class change. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): 30 days have not
  L2 (16ch): passed since the
  L3 (18ch): last class change.
```

### [chunk_r40_r42_translated.json] r40 msg16

**Current:**
```
  L1 (21ch): delete from registry. <-- WIDE
  L2 (22ch): this cannot be undone. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (11ch): delete from
  L2 (14ch): registry. this
  L3 (17ch): cannot be undone.
```

### [chunk_r40_r42_translated.json] r40 msg22

**Current:**
```
  L1 (34ch): the leader cannot leave the party. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): the leader cannot
  L2 (16ch): leave the party.
```

### [chunk_r40_r42_translated.json] r40 msg25

**Current:**
```
  L1 (21ch): same class as current <-- WIDE
  L2 (12ch): is selected.
```
**Proposed rewrite:**
```
  L1 (13ch): same class as
  L2 (20ch): current is selected.
```

### [chunk_r40_r42_translated.json] r40 msg39

**Current:**
```
  L1 (22ch): sort by highest level. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (15ch): sort by highest
  L2 ( 6ch): level.
```

### [chunk_r40_r42_translated.json] r40 msg40

**Current:**
```
  L1 (21ch): sort by lowest level. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (14ch): sort by lowest
  L2 ( 6ch): level.
```

### [chunk_r40_r42_translated.json] r40 msg42

**Current:**
```
  L1 (28ch): select a class to change to. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): select a class to
  L2 (10ch): change to.
```

### [chunk_r40_r42_translated.json] r40 msg43

**Current:**
```
  L1 (30ch): all equipment will be removed. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): all equipment will
  L2 (11ch): be removed.
```

### [chunk_r40_r42_translated.json] r40 msg44

**Current:**
```
  L1 (25ch): cannot change class while <-- WIDE
  L2 (35ch): equipment is in use. unequip first. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): Can't change class
  L2 (13ch): with gear on.
  L3 (14ch): Unequip first.
```

### [chunk_r40_r42_translated.json] r40 msg45

**Current:**
```
  L1 (17ch): press l1 or r1 to
  L2 (21ch): skip to final result. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): press l1 or r1 to
  L2 (13ch): skip to final
  L3 ( 7ch): result.
```

### [chunk_r40_r42_translated.json] r40 msg46

**Current:**
```
  L1 (26ch): stats and alignment do not <-- WIDE
  L2 (27ch): match. cannot change class. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): stats and alignment
  L2 (20ch): do not match. cannot
  L3 (13ch): change class.
```

### [chunk_r40_r42_translated.json] r40 msg47

**Current:**
```
  L1 (19ch): leader cannot move.
  L2 (22ch): cannot remove members. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): leader cannot move.
  L2 (13ch): cannot remove
  L3 ( 8ch): members.
```

### [chunk_r40_r42_translated.json] r40 msg53

**Current:**
```
  L1 (25ch): this is the party leader. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): this is the party
  L2 ( 7ch): leader.
```

### [chunk_r40_r42_translated.json] r40 msg54

**Current:**
```
  L1 (28ch): recruited from the registry. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): recruited from the
  L2 ( 9ch): registry.
```

### [chunk_r40_r42_translated.json] r40 msg57

**Current:**
```
  L1 (29ch): automata without a heart have <-- WIDE
  L2 (23ch): no trust or party rank. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (18ch): automata without a
  L2 (19ch): heart have no trust
  L3 (14ch): or party rank.
```

### [chunk_r40_r42_translated.json] r41 msg2

**Current:**
```
  L1 (28ch): this is the church of salem. <-- WIDE
  L2 (20ch): what business do you
  L3 (10ch): have here?
```
**Proposed rewrite:**
```
  L1 (18ch): Salem Church. What
  L2 (15ch): business do you
  L3 (10ch): have here?
```

### [chunk_r40_r42_translated.json] r41 msg3

**Current:**
```
  L1 (21ch): welcome to the church <-- WIDE
  L2 (22ch): of salem. it seems you <-- WIDE
  L3 (14ch): need our help.
```
**Proposed rewrite:**
```
  L1 (16ch): Welcome to Salem
  L2 (18ch): Church. Looks like
  L3 (18ch): you need our help.
```

### [chunk_r40_r42_translated.json] r41 msg5

**Current:**
```
  L1 (20ch): then we shall accept
  L2 (23ch): the offering the church <-- WIDE
  L3 ( 9ch): requires.
```
**Proposed rewrite:**
```
  L1 (20ch): then we shall accept
  L2 (16ch): the offering the
  L3 (16ch): church requires.
```

### [chunk_r40_r42_translated.json] r41 msg6

**Current:**
```
  L1 (23ch): you dare beg for divine <-- WIDE
  L2 (27ch): aid without a proper tithe! <-- WIDE
  L3 (16ch): begone, heretic!
```
**Proposed rewrite:**
```
  L1 (19ch): No tithe, no divine
  L2 (12ch): aid! Begone,
  L3 ( 8ch): heretic!
```

### [chunk_r40_r42_translated.json] r41 msg7

**Current:**
```
  L1 (19ch): without an offering
  L2 (22ch): to the gods, you shall <-- WIDE
  L3 (19ch): surely be punished.
```
**Proposed rewrite:**
```
  L1 (16ch): Without offering
  L2 (16ch): to the gods, you
  L3 (17ch): will be punished.
```

### [chunk_r40_r42_translated.json] r41 msg8

**Current:**
```
  L1 (19ch): without an offering
  L2 (22ch): to the gods, you shall <-- WIDE
  L3 (19ch): surely be punished.
```
**Proposed rewrite:**
```
  L1 (16ch): Without offering
  L2 (16ch): to the gods, you
  L3 (17ch): will be punished.
```

### [chunk_r40_r42_translated.json] r41 msg9

**Current:**
```
  L1 (19ch): without an offering
  L2 (22ch): to the gods, you shall <-- WIDE
  L3 (19ch): surely be punished.
```
**Proposed rewrite:**
```
  L1 (16ch): Without offering
  L2 (16ch): to the gods, you
  L3 (17ch): will be punished.
```

### [chunk_r40_r42_translated.json] r41 msg10

**Current:**
```
  L1 (19ch): without an offering
  L2 (22ch): to the gods, you shall <-- WIDE
  L3 (19ch): surely be punished.
```
**Proposed rewrite:**
```
  L1 (16ch): Without offering
  L2 (16ch): to the gods, you
  L3 (17ch): will be punished.
```

### [chunk_r40_r42_translated.json] r41 msg11

**Current:**
```
  L1 (19ch): without an offering
  L2 (22ch): to the gods, you shall <-- WIDE
  L3 (19ch): surely be punished.
```
**Proposed rewrite:**
```
  L1 (16ch): Without offering
  L2 (16ch): to the gods, you
  L3 (17ch): will be punished.
```

### [chunk_r40_r42_translated.json] r41 msg12

**Current:**
```
  L1 (19ch): without an offering
  L2 (22ch): to the gods, you shall <-- WIDE
  L3 (19ch): surely be punished.
```
**Proposed rewrite:**
```
  L1 (16ch): Without offering
  L2 (16ch): to the gods, you
  L3 (17ch): will be punished.
```

### [chunk_r40_r42_translated.json] r41 msg13

**Current:**
```
  L1 (19ch): without an offering
  L2 (22ch): to the gods, you shall <-- WIDE
  L3 (19ch): surely be punished.
```
**Proposed rewrite:**
```
  L1 (16ch): Without offering
  L2 (16ch): to the gods, you
  L3 (17ch): will be punished.
```

### [chunk_r40_r42_translated.json] r41 msg14

**Current:**
```
  L1 (17ch): whenever you need
  L2 (18ch): our help, bring an
  L3 (25ch): offering and come see us. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Need our help? Bring
  L2 (15ch): an offering and
  L3 (12ch): come see us.
```

### [chunk_r40_r42_translated.json] r42 msg2

**Current:**
```
  L1 (19ch): welcome to the inn.
  L2 (20ch): a place to rest your
  L3 (23ch): body and gain strength. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): Welcome to the inn.
  L2 (18ch): Rest your body and
  L3 (14ch): gain strength.
```

### [chunk_r40_r42_translated.json] r42 msg7

**Current:**
```
  L1 (18ch): did you rest well?
  L2 (25ch): good rest brings strength <-- WIDE
  L3 (25ch): for tomorrow. come again. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Rest well? Good rest
  L2 (16ch): brings strength.
  L3 (11ch): Come again.
```

### [chunk_r40_r42_translated.json] r42 msg13

**Current:**
```
  L1 (28ch): a potential ability awakened <-- WIDE
```
**Proposed rewrite:**
```
  L1 (19ch): a potential ability
  L2 ( 8ch): awakened
```

### [chunk_r43_r45_translated.json] r44 msg4

**Current:**
```
  L1 (16ch): Let's form magic
  L2 (18ch): stones from medals
  L3 (21ch): collected by knights. <-- WIDE
```
**Proposed rewrite:**
```
  L1 (17ch): Form magic stones
  L2 (16ch): from medals your
  L3 (18ch): knights collected.
```

### [chunk_r43_r45_translated.json] r44 msg5

**Current:**
```
  L1 (16ch): Ruins of ancient
  L2 (21ch): magic. Need help with <-- WIDE
  L3 (13ch): the automata?
```
**Proposed rewrite:**
```
  L1 (16ch): Ruins of ancient
  L2 (16ch): magic. Need help
  L3 (18ch): with the automata?
```

### [chunk_r43_r45_translated.json] r44 msg8

**Current:**
```
  L1 (14ch): By using magic
  L2 (21ch): stones, you can power <-- WIDE
  L3 (16ch): up the automata.
```
**Proposed rewrite:**
```
  L1 (16ch): Use magic stones
  L2 (15ch): to power up the
  L3 ( 9ch): automata.
```

### [chunk_r43_r45_translated.json] r44 msg40

**Current:**
```
  L1 (22ch): Not enough curse power <-- WIDE
```
**Proposed rewrite:**
```
  L1 (16ch): Not enough curse
  L2 ( 5ch): power
```

### [chunk_r43_r45_translated.json] r45 msg10

**Current:**
```
  L1 (14ch): Hiring workers
  L2 (16ch): makes this place
  L3 (22ch): feel like a real shop! <-- WIDE
```
**Proposed rewrite:**
```
  L1 (20ch): Hiring workers makes
  L2 (20ch): this place feel like
  L3 (12ch): a real shop!
```

### [chunk_r43_r45_translated.json] r45 msg112

**Current:**
```
  L1 (26ch): Cannot unequip cursed item <-- WIDE
```
**Proposed rewrite:**
```
  L1 (14ch): Cannot unequip
  L2 (11ch): cursed item
```
