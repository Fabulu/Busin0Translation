# Dialogue Overflow Audit Report
**Date:** 2026-05-28
**Constraints:** 18 chars/line, 3 lines/page

## Summary

- **Total entries scanned:** 13705
- **Translated entries:** 13469
- **Entries with ANY line > 18 chars:** 2474
- **Entries with > 3 lines (page overflow):** 3034
- **Entries with BOTH issues:** 237
- **Total problem entries:** 5271
- **Clean entries:** 8198
- **Overflow rate:** 39.1%

## Line Length Distribution (overflowing lines only)

| Chars | Count |
|-------|-------|
| 19 | 992 |
| 20 | 485 |
| 21 | 318 |
| 22 | 210 |
| 23 | 106 |
| 24 | 94 |
| 25 | 73 |
| 26 | 23 |
| 27 | 24 |
| 28 | 17 |
| 29 | 22 |
| 30 | 26 |
| 31 | 17 |
| 32 | 20 |
| 33 | 12 |
| 34 | 15 |
| 35 | 12 |
| 36 | 13 |
| 37 | 12 |
| 38 | 11 |
| 39 | 13 |
| 40 | 11 |
| 41 | 26 |
| 42 | 6 |
| 43 | 8 |
| 44 | 16 |
| 45 | 10 |
| 46 | 8 |
| 47 | 9 |
| 48 | 8 |
| 49 | 7 |
| 50 | 9 |
| 51 | 7 |
| 52 | 7 |
| 53 | 8 |
| 54 | 6 |
| 55 | 7 |
| 56 | 9 |
| 57 | 8 |
| 58 | 9 |
| 59 | 10 |
| 60 | 11 |
| 61 | 11 |
| 62 | 4 |
| 63 | 6 |
| 64 | 10 |
| 65 | 17 |
| 66 | 5 |
| 67 | 6 |
| 68 | 6 |
| 69 | 13 |
| 70 | 7 |
| 71 | 7 |
| 72 | 9 |
| 73 | 10 |
| 74 | 5 |
| 75 | 7 |
| 76 | 5 |
| 77 | 6 |
| 78 | 3 |
| 79 | 15 |
| 80 | 11 |
| 81 | 6 |
| 82 | 11 |
| 83 | 5 |
| 84 | 4 |
| 85 | 6 |
| 86 | 6 |
| 87 | 6 |
| 88 | 2 |
| 89 | 7 |
| 90 | 5 |
| 91 | 3 |
| 92 | 4 |
| 93 | 5 |
| 94 | 6 |
| 95 | 6 |
| 96 | 2 |
| 97 | 3 |
| 98 | 3 |
| 99 | 3 |
| 100 | 5 |
| 101 | 6 |
| 102 | 2 |
| 103 | 5 |
| 104 | 4 |
| 105 | 4 |
| 106 | 5 |
| 107 | 6 |
| 108 | 3 |
| 109 | 3 |
| 110 | 4 |
| 111 | 1 |
| 112 | 2 |
| 113 | 4 |
| 114 | 2 |
| 115 | 1 |
| 116 | 1 |
| 117 | 2 |
| 119 | 3 |
| 120 | 1 |
| 121 | 2 |
| 122 | 3 |
| 123 | 4 |
| 124 | 2 |
| 125 | 1 |
| 126 | 2 |
| 127 | 3 |
| 128 | 2 |
| 129 | 2 |
| 130 | 4 |
| 132 | 1 |
| 133 | 2 |
| 134 | 2 |
| 135 | 1 |
| 136 | 1 |
| 137 | 2 |
| 138 | 1 |
| 139 | 2 |
| 141 | 3 |
| 142 | 2 |
| 143 | 1 |
| 145 | 1 |
| 147 | 1 |
| 148 | 1 |
| 150 | 2 |
| 151 | 1 |
| 152 | 1 |
| 153 | 2 |
| 155 | 2 |
| 160 | 1 |
| 161 | 1 |
| 164 | 3 |
| 166 | 1 |
| 168 | 2 |
| 171 | 2 |
| 173 | 1 |
| 176 | 1 |
| 177 | 1 |
| 183 | 1 |
| 188 | 1 |
| 189 | 1 |
| 191 | 1 |
| 198 | 1 |
| 205 | 1 |
| 212 | 1 |
| 217 | 1 |

**Buckets:**
- 19-20 chars (minor, 1-2 chars over): 1477 lines
- 21-25 chars (moderate, 3-7 chars over): 801 lines
- 26-30 chars (severe, 8-12 chars over): 112 lines
- 31+ chars (critical, 13+ chars over): 720 lines

## Page Overflow Distribution

| Lines | Count |
|-------|-------|
| 4 | 1906 |
| 5 | 728 |
| 6 | 240 |
| 7 | 97 |
| 8 | 44 |
| 9 | 10 |
| 10 | 2 |
| 11 | 1 |
| 12 | 3 |
| 14 | 1 |
| 45 | 1 |
| 64 | 1 |

## Breakdown by Batch File

| File | Translated | Line Overflow | Page Overflow | Total Issues |
|------|-----------|---------------|---------------|-------------|
| batch_01.json | 1989 | 377 | 259 | 613 |
| batch_02.json | 936 | 284 | 352 | 532 |
| batch_03.json | 1580 | 66 | 698 | 727 |
| batch_04.json | 1833 | 13 | 947 | 956 |
| batch_05.json | 1761 | 17 | 4 | 20 |
| batch_06.json | 1484 | 1164 | 29 | 1175 |
| batch_07.json | 1368 | 10 | 528 | 537 |
| batch_08.json | 750 | 52 | 16 | 64 |
| batch_09.json | 935 | 55 | 154 | 200 |
| batch_10.json | 7 | 2 | 5 | 6 |
| batch_11.json | 31 | 31 | 0 | 31 |
| batch_dungeon_680_911.json | 0 | 0 | 0 | 0 |
| batch_dungeon_a.json | 35 | 16 | 2 | 16 |
| batch_gap1347.json | 132 | 118 | 34 | 120 |
| batch_gap989.json | 3 | 3 | 0 | 3 |
| batch_intro.json | 2 | 0 | 2 | 2 |
| batch_intro_narration.json | 2 | 1 | 2 | 2 |
| batch_r1163_1167.json | 0 | 0 | 0 | 0 |
| batch_r1168_1173.json | 0 | 0 | 0 | 0 |
| batch_r1198.json | 88 | 42 | 2 | 44 |
| batch_r39_equip_a.json | 301 | 142 | 0 | 142 |
| batch_r39_equip_b.json | 232 | 81 | 0 | 81 |

## Top 50 Worst Offenders (by longest line)

### #1: R39 msg 346 (batch_r39_equip_a.json)
- **Longest line:** 217 chars
- **Total lines:** 1
- **Original:**
```
  L1 [217]: Beat me at 5 rounds of Rock-Paper-Scissors
and I'll give you something good! But if you
lose, you get Ripu'd! Fee: 1 medal per loss.
Confident in your luck? Come to B2F, the
small room on the floor with lots of cells. <<<OVER
```
- **Proposed fix** (still has overflow - needs manual edit):
```
  L1 [12]: Beat me at 5
  L2 [ 9]: rounds of
  L3 [19]: Rock-Paper-Scissors <<<STILL OVER
  --- PAGE BREAK ---
  L5 [17]: and I'll give you
  L6 [15]: something good!
  L7 [16]: But if you lose,
  --- PAGE BREAK ---
  L9 [15]: you get Ripu'd!
  L10 [16]: Fee: 1 medal per
  L11 [18]: loss. Confident in
  --- PAGE BREAK ---
  L13 [18]: your luck? Come to
  L14 [14]: B2F, the small
  L15 [17]: room on the floor
  --- PAGE BREAK ---
  L17 [12]: with lots of
  L18 [ 6]: cells.
```

### #2: R39 msg 345 (batch_r39_equip_a.json)
- **Longest line:** 212 chars
- **Total lines:** 1
- **Original:**
```
  L1 [212]: I want to learn magic but I don't have any
magic stones. Without magic, I'll waste away.
Please give me a Kreta magic stone.
I'm in a terrible hurry. Too late means over.
Anyone who can help right now, please do. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [15]: I want to learn
  L2 [17]: magic but I don't
  L3 [14]: have any magic
  --- PAGE BREAK ---
  L5 [15]: stones. Without
  L6 [17]: magic, I'll waste
  L7 [17]: away. Please give
  --- PAGE BREAK ---
  L9 [16]: me a Kreta magic
  L10 [15]: stone. I'm in a
  L11 [15]: terrible hurry.
  --- PAGE BREAK ---
  L13 [14]: Too late means
  L14 [16]: over. Anyone who
  L15 [14]: can help right
  --- PAGE BREAK ---
  L17 [15]: now, please do.
```

### #3: R39 msg 367 (batch_r39_equip_a.json)
- **Longest line:** 205 chars
- **Total lines:** 1
- **Original:**
```
  L1 [205]: I poured the labyrinth's magic into the
masterwork armor and tempered it rigorously,
but something is still missing. I'd like to
observe foreign fighting styles.
Awaiting a challenge from a master warrior. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [12]: I poured the
  L2 [17]: labyrinth's magic
  L3 [ 8]: into the
  --- PAGE BREAK ---
  L5 [16]: masterwork armor
  L6 [15]: and tempered it
  L7 [15]: rigorously, but
  --- PAGE BREAK ---
  L9 [18]: something is still
  L10 [17]: missing. I'd like
  L11 [18]: to observe foreign
  --- PAGE BREAK ---
  L13 [16]: fighting styles.
  L14 [10]: Awaiting a
  L15 [16]: challenge from a
  --- PAGE BREAK ---
  L17 [15]: master warrior.
```

### #4: R39 msg 374 (batch_r39_equip_a.json)
- **Longest line:** 198 chars
- **Total lines:** 1
- **Original:**
```
  L1 [198]: Somewhere on B10F, there should be a room
with a large water vase in the center.
I don't know where it is though.
If I can get there, I think I can return
to my former time, so please take me there. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [18]: Somewhere on B10F,
  L2 [17]: there should be a
  L3 [17]: room with a large
  --- PAGE BREAK ---
  L5 [17]: water vase in the
  L6 [15]: center. I don't
  L7 [16]: know where it is
  --- PAGE BREAK ---
  L9 [16]: though. If I can
  L10 [18]: get there, I think
  L11 [18]: I can return to my
  --- PAGE BREAK ---
  L13 [15]: former time, so
  L14 [14]: please take me
  L15 [ 6]: there.
```

### #5: R39 msg 364 (batch_r39_equip_a.json)
- **Longest line:** 191 chars
- **Total lines:** 1
- **Original:**
```
  L1 [191]: The guide for the Karman Exploration Tour
organized by the Duhan Merchant Guild has
suddenly become an adventurer, and we need
a replacement guide.
Confident explorers, we're waiting for you. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [17]: The guide for the
  L2 [18]: Karman Exploration
  L3 [17]: Tour organized by
  --- PAGE BREAK ---
  L5 [18]: the Duhan Merchant
  L6 [18]: Guild has suddenly
  L7 [ 9]: become an
  --- PAGE BREAK ---
  L9 [18]: adventurer, and we
  L10 [18]: need a replacement
  L11 [16]: guide. Confident
  --- PAGE BREAK ---
  L13 [16]: explorers, we're
  L14 [16]: waiting for you.
```

### #6: R39 msg 268 (batch_r39_equip_a.json)
- **Longest line:** 189 chars
- **Total lines:** 1
- **Original:**
```
  L1 [189]: One front row member acts as a decoy. When
attacked, the remaining front row members
counterattack from the sides, interrupting
the enemy's coordinated attack. Limited
activations per turn. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [13]: One front row
  L2 [16]: member acts as a
  L3 [11]: decoy. When
  --- PAGE BREAK ---
  L5 [13]: attacked, the
  L6 [15]: remaining front
  L7 [11]: row members
  --- PAGE BREAK ---
  L9 [18]: counterattack from
  L10 [10]: the sides,
  L11 [16]: interrupting the
  --- PAGE BREAK ---
  L13 [ 7]: enemy's
  L14 [11]: coordinated
  L15 [15]: attack. Limited
  --- PAGE BREAK ---
  L17 [15]: activations per
  L18 [ 5]: turn.
```

### #7: R39 msg 349 (batch_r39_equip_a.json)
- **Longest line:** 188 chars
- **Total lines:** 1
- **Original:**
```
  L1 [188]: Information has come in that ruins of an
ancient Elf kingdom were found in the
labyrinth. Items needed for the book of
adventures may be there. Go to the scrap
yard on B3F and investigate. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [15]: Information has
  L2 [18]: come in that ruins
  L3 [17]: of an ancient Elf
  --- PAGE BREAK ---
  L5 [18]: kingdom were found
  L6 [17]: in the labyrinth.
  L7 [16]: Items needed for
  --- PAGE BREAK ---
  L9 [11]: the book of
  L10 [17]: adventures may be
  L11 [16]: there. Go to the
  --- PAGE BREAK ---
  L13 [17]: scrap yard on B3F
  L14 [16]: and investigate.
```

### #8: R39 msg 360 (batch_r39_equip_a.json)
- **Longest line:** 183 chars
- **Total lines:** 1
- **Original:**
```
  L1 [183]: The Knight Order is conducting level checks
on registered adventurers.
This is a test of how well you know
the labyrinth and adventuring.
Interested parties, accept the request first. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [16]: The Knight Order
  L2 [13]: is conducting
  L3 [15]: level checks on
  --- PAGE BREAK ---
  L5 [10]: registered
  L6 [17]: adventurers. This
  L7 [16]: is a test of how
  --- PAGE BREAK ---
  L9 [17]: well you know the
  L10 [13]: labyrinth and
  L11 [12]: adventuring.
  --- PAGE BREAK ---
  L13 [10]: Interested
  L14 [15]: parties, accept
  L15 [18]: the request first.
```

### #9: R39 msg 344 (batch_r39_equip_a.json)
- **Longest line:** 177 chars
- **Total lines:** 1
- **Original:**
```
  L1 [177]: If you're reading this, please come
immediately to the small room just past the
first warp on B5F. I'll put up a sign there.
I'm in a real hurry.
I'll explain when you get here. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [17]: If you're reading
  L2 [17]: this, please come
  L3 [18]: immediately to the
  --- PAGE BREAK ---
  L5 [15]: small room just
  L6 [14]: past the first
  L7 [17]: warp on B5F. I'll
  --- PAGE BREAK ---
  L9 [13]: put up a sign
  L10 [15]: there. I'm in a
  L11 [16]: real hurry. I'll
  --- PAGE BREAK ---
  L13 [16]: explain when you
  L14 [ 9]: get here.
```

### #10: R39 msg 366 (batch_r39_equip_a.json)
- **Longest line:** 176 chars
- **Total lines:** 1
- **Original:**
```
  L1 [176]: The masterwork armor, obtained with great
effort. But to find the new light, something
is still missing.
So I'd like someone to temper this armor
in the labyrinth's lava rocks. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [14]: The masterwork
  L2 [15]: armor, obtained
  L3 [18]: with great effort.
  --- PAGE BREAK ---
  L5 [15]: But to find the
  L6 [10]: new light,
  L7 [18]: something is still
  --- PAGE BREAK ---
  L9 [15]: missing. So I'd
  L10 [15]: like someone to
  L11 [17]: temper this armor
  --- PAGE BREAK ---
  L13 [18]: in the labyrinth's
  L14 [11]: lava rocks.
```

### #11: R39 msg 278 (batch_r39_equip_a.json)
- **Longest line:** 173 chars
- **Total lines:** 1
- **Original:**
```
  L1 [173]: Two front row members feint while the third
strikes from above at the enemy's weak point.
All members attack once, but the third member's
critical rate is greatly increased. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [13]: Two front row
  L2 [13]: members feint
  L3 [15]: while the third
  --- PAGE BREAK ---
  L5 [18]: strikes from above
  L6 [14]: at the enemy's
  L7 [15]: weak point. All
  --- PAGE BREAK ---
  L9 [14]: members attack
  L10 [13]: once, but the
  L11 [14]: third member's
  --- PAGE BREAK ---
  L13 [16]: critical rate is
  L14 [18]: greatly increased.
```

### #12: R39 msg 347 (batch_r39_equip_a.json)
- **Longest line:** 171 chars
- **Total lines:** 1
- **Original:**
```
  L1 [171]: Duhan Castle has recently established an
Adventurer Assistance Program.
Bring 5 companions to the Castle and
each person will receive a special
adventurer stipend of 500G. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [16]: Duhan Castle has
  L2 [ 8]: recently
  L3 [14]: established an
  --- PAGE BREAK ---
  L5 [10]: Adventurer
  L6 [10]: Assistance
  L7 [16]: Program. Bring 5
  --- PAGE BREAK ---
  L9 [17]: companions to the
  L10 [15]: Castle and each
  L11 [11]: person will
  --- PAGE BREAK ---
  L13 [17]: receive a special
  L14 [18]: adventurer stipend
  L15 [ 8]: of 500G.
```

### #13: R39 msg 361 (batch_r39_equip_a.json)
- **Longest line:** 171 chars
- **Total lines:** 1
- **Original:**
```
  L1 [171]: I'm Melanie, an elf girl training daily
to become a full-fledged mage,
and my manager Miri.
I want to learn lots of spells, so please
let me join a party with adventurers. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [15]: I'm Melanie, an
  L2 [17]: elf girl training
  L3 [17]: daily to become a
  --- PAGE BREAK ---
  L5 [18]: full-fledged mage,
  L6 [14]: and my manager
  L7 [15]: Miri. I want to
  --- PAGE BREAK ---
  L9 [13]: learn lots of
  L10 [17]: spells, so please
  L11 [13]: let me join a
  --- PAGE BREAK ---
  L13 [10]: party with
  L14 [12]: adventurers.
```

### #14: R39 msg 256 (batch_r39_equip_a.json)
- **Longest line:** 168 chars
- **Total lines:** 1
- **Original:**
```
  L1 [168]: Two back row members bind the enemy with
crossed magic, pull it forward, and two front
row members attack simultaneously. Effective
against low-evasion, low-HP enemies. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [12]: Two back row
  L2 [16]: members bind the
  L3 [18]: enemy with crossed
  --- PAGE BREAK ---
  L5 [14]: magic, pull it
  L6 [16]: forward, and two
  L7 [17]: front row members
  --- PAGE BREAK ---
  L9 [ 6]: attack
  L10 [15]: simultaneously.
  L11 [17]: Effective against
  --- PAGE BREAK ---
  L13 [12]: low-evasion,
  L14 [15]: low-HP enemies.
```

### #15: R39 msg 353 (batch_r39_equip_a.json)
- **Longest line:** 168 chars
- **Total lines:** 1
- **Original:**
```
  L1 [168]: As a reward for accepting this request,
I will transfer a piece of land to you.
Details will only be shared with those
who accept.
Knight Order members, please refrain. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [15]: As a reward for
  L2 [14]: accepting this
  L3 [15]: request, I will
  --- PAGE BREAK ---
  L5 [16]: transfer a piece
  L6 [15]: of land to you.
  L7 [17]: Details will only
  --- PAGE BREAK ---
  L9 [14]: be shared with
  L10 [17]: those who accept.
  L11 [12]: Knight Order
  --- PAGE BREAK ---
  L13 [15]: members, please
  L14 [ 8]: refrain.
```

### #16: R39 msg 257 (batch_r39_equip_a.json)
- **Longest line:** 166 chars
- **Total lines:** 1
- **Original:**
```
  L1 [166]: All front row members take a defensive stance,
reducing evasion and defense. Cures stun,
paralysis, poison, ID, and drain from enemies,
and blocks enemy Rush attacks. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [13]: All front row
  L2 [14]: members take a
  L3 [17]: defensive stance,
  --- PAGE BREAK ---
  L5 [16]: reducing evasion
  L6 [18]: and defense. Cures
  L7 [16]: stun, paralysis,
  --- PAGE BREAK ---
  L9 [15]: poison, ID, and
  L10 [10]: drain from
  L11 [12]: enemies, and
  --- PAGE BREAK ---
  L13 [17]: blocks enemy Rush
  L14 [ 8]: attacks.
```

### #17: R39 msg 263 (batch_r39_equip_a.json)
- **Longest line:** 164 chars
- **Total lines:** 1
- **Original:**
```
  L1 [164]: When a protected front row member is attacked,
a back row member counterattacks with ranged
weapons. Activates each time the protected
front row member is attacked. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [16]: When a protected
  L2 [16]: front row member
  L3 [14]: is attacked, a
  --- PAGE BREAK ---
  L5 [15]: back row member
  L6 [14]: counterattacks
  L7 [11]: with ranged
  --- PAGE BREAK ---
  L9 [18]: weapons. Activates
  L10 [13]: each time the
  L11 [15]: protected front
  --- PAGE BREAK ---
  L13 [13]: row member is
  L14 [ 9]: attacked.
```

### #18: R39 msg 280 (batch_r39_equip_a.json)
- **Longest line:** 164 chars
- **Total lines:** 1
- **Original:**
```
  L1 [164]: One back row member creates a warp gate, and
three front row members dive-attack from an
aerial gate. Can reduce enemy defense.
Airborne enemies cannot be targeted. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [12]: One back row
  L2 [16]: member creates a
  L3 [14]: warp gate, and
  --- PAGE BREAK ---
  L5 [15]: three front row
  L6 [ 7]: members
  L7 [16]: dive-attack from
  --- PAGE BREAK ---
  L9 [15]: an aerial gate.
  L10 [16]: Can reduce enemy
  L11 [17]: defense. Airborne
  --- PAGE BREAK ---
  L13 [17]: enemies cannot be
  L14 [ 9]: targeted.
```

### #19: R39 msg 371 (batch_r39_equip_a.json)
- **Longest line:** 164 chars
- **Total lines:** 1
- **Original:**
```
  L1 [164]: I've never seen anyone possessed by a death
spirit, so I'd like to meet one.
Please come back to the Castle while
possessed by a death spirit.
Thank you in advance. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [15]: I've never seen
  L2 [16]: anyone possessed
  L3 [18]: by a death spirit,
  --- PAGE BREAK ---
  L5 [14]: so I'd like to
  L6 [16]: meet one. Please
  L7 [16]: come back to the
  --- PAGE BREAK ---
  L9 [12]: Castle while
  L10 [14]: possessed by a
  L11 [13]: death spirit.
  --- PAGE BREAK ---
  L13 [12]: Thank you in
  L14 [ 8]: advance.
```

### #20: R39 msg 363 (batch_r39_equip_a.json)
- **Longest line:** 161 chars
- **Total lines:** 1
- **Original:**
```
  L1 [161]: I dropped my precious treasure chest
in the scary room on B1F.
I can't write the details here, but
I'll give you something nice, so please,
go pick it up for me. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [12]: I dropped my
  L2 [17]: precious treasure
  L3 [18]: chest in the scary
  --- PAGE BREAK ---
  L5 [14]: room on B1F. I
  L6 [15]: can't write the
  L7 [17]: details here, but
  --- PAGE BREAK ---
  L9 [13]: I'll give you
  L10 [18]: something nice, so
  L11 [18]: please, go pick it
  --- PAGE BREAK ---
  L13 [10]: up for me.
```

### #21: R39 msg 260 (batch_r39_equip_a.json)
- **Longest line:** 160 chars
- **Total lines:** 1
- **Original:**
```
  L1 [160]: All back row members create duplicates of
every party member. Duplicates vanish when
hit, but real members take no damage from
attacks targeting the duplicates. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [12]: All back row
  L2 [14]: members create
  L3 [13]: duplicates of
  --- PAGE BREAK ---
  L5 [11]: every party
  L6 [18]: member. Duplicates
  L7 [16]: vanish when hit,
  --- PAGE BREAK ---
  L9 [16]: but real members
  L10 [14]: take no damage
  L11 [12]: from attacks
  --- PAGE BREAK ---
  L13 [13]: targeting the
  L14 [11]: duplicates.
```

### #22: R39 msg 276 (batch_r39_equip_a.json)
- **Longest line:** 155 chars
- **Total lines:** 1
- **Original:**
```
  L1 [155]: Evolved Concentrated Attack with a Fighter.
The first member launches the enemy into the
air, then attacks during the fall and recovery
for massive damage. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [ 7]: Evolved
  L2 [12]: Concentrated
  L3 [13]: Attack with a
  --- PAGE BREAK ---
  L5 [18]: Fighter. The first
  L6 [15]: member launches
  L7 [18]: the enemy into the
  --- PAGE BREAK ---
  L9 [17]: air, then attacks
  L10 [15]: during the fall
  L11 [16]: and recovery for
  --- PAGE BREAK ---
  L13 [15]: massive damage.
```

### #23: R39 msg 355 (batch_r39_equip_a.json)
- **Longest line:** 155 chars
- **Total lines:** 1
- **Original:**
```
  L1 [155]: The magic portal room connecting B4F and B1F
is locked and I'm in trouble.
Ingo should be able to help.
Please go to Ingo's hideout on B4F
and get the key. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [16]: The magic portal
  L2 [15]: room connecting
  L3 [14]: B4F and B1F is
  --- PAGE BREAK ---
  L5 [17]: locked and I'm in
  L6 [13]: trouble. Ingo
  L7 [17]: should be able to
  --- PAGE BREAK ---
  L9 [18]: help. Please go to
  L10 [17]: Ingo's hideout on
  L11 [15]: B4F and get the
  --- PAGE BREAK ---
  L13 [ 4]: key.
```

### #24: R39 msg 262 (batch_r39_equip_a.json)
- **Longest line:** 153 chars
- **Total lines:** 1
- **Original:**
```
  L1 [153]: The entire party takes an evasive formation,
greatly increasing evasion and defense against
physical attacks. However, breath and magic
damage increases. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [16]: The entire party
  L2 [16]: takes an evasive
  L3 [18]: formation, greatly
  --- PAGE BREAK ---
  L5 [18]: increasing evasion
  L6 [11]: and defense
  L7 [16]: against physical
  --- PAGE BREAK ---
  L9 [17]: attacks. However,
  L10 [16]: breath and magic
  L11 [17]: damage increases.
```

### #25: R39 msg 281 (batch_r39_equip_a.json)
- **Longest line:** 153 chars
- **Total lines:** 1
- **Original:**
```
  L1 [153]: Evolved Slay Crash with a Monk.
Two members charge through the enemy with
spirit energy, dealing damage on the charge
and return, and can destroy undead. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [18]: Evolved Slay Crash
  L2 [16]: with a Monk. Two
  L3 [14]: members charge
  --- PAGE BREAK ---
  L5 [17]: through the enemy
  L6 [11]: with spirit
  L7 [15]: energy, dealing
  --- PAGE BREAK ---
  L9 [13]: damage on the
  L10 [18]: charge and return,
  L11 [15]: and can destroy
  --- PAGE BREAK ---
  L13 [ 7]: undead.
```

### #26: R39 msg 359 (batch_r39_equip_a.json)
- **Longest line:** 152 chars
- **Total lines:** 1
- **Original:**
```
  L1 [152]: I want to talk to the Succubus ladies but
they always run away.
Now's my chance!
Please catch a Succubus that appears
right in front of me and hold her! <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [17]: I want to talk to
  L2 [12]: the Succubus
  L3 [15]: ladies but they
  --- PAGE BREAK ---
  L5 [16]: always run away.
  L6 [16]: Now's my chance!
  L7 [14]: Please catch a
  --- PAGE BREAK ---
  L9 [13]: Succubus that
  L10 [16]: appears right in
  L11 [15]: front of me and
  --- PAGE BREAK ---
  L13 [ 9]: hold her!
```

### #27: R39 msg 351 (batch_r39_equip_a.json)
- **Longest line:** 151 chars
- **Total lines:** 1
- **Original:**
```
  L1 [151]: I borrowed 20 medals from the Ogre boss
and debt collectors are after me.
I'm exhausted.
Please, give me medals.
I just want to stop living on the run. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [13]: I borrowed 20
  L2 [15]: medals from the
  L3 [18]: Ogre boss and debt
  --- PAGE BREAK ---
  L5 [14]: collectors are
  L6 [13]: after me. I'm
  L7 [18]: exhausted. Please,
  --- PAGE BREAK ---
  L9 [17]: give me medals. I
  L10 [17]: just want to stop
  L11 [18]: living on the run.
```

### #28: R39 msg 272 (batch_r39_equip_a.json)
- **Longest line:** 150 chars
- **Total lines:** 1
- **Original:**
```
  L1 [150]: A back row member enchants an ally's weapon
with a spell. If the attack hits, it bypasses
enemy spell resistance and Magic Shell to
deliver the spell. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [17]: A back row member
  L2 [18]: enchants an ally's
  L3 [13]: weapon with a
  --- PAGE BREAK ---
  L5 [13]: spell. If the
  L6 [15]: attack hits, it
  L7 [14]: bypasses enemy
  --- PAGE BREAK ---
  L9 [16]: spell resistance
  L10 [18]: and Magic Shell to
  L11 [18]: deliver the spell.
```

### #29: R39 msg 275 (batch_r39_equip_a.json)
- **Longest line:** 150 chars
- **Total lines:** 1
- **Original:**
```
  L1 [150]: One front row member acts as a decoy. When
attacked, the other two rush behind the enemy
and counterattack. Hit rate and damage are
greatly increased. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [13]: One front row
  L2 [16]: member acts as a
  L3 [11]: decoy. When
  --- PAGE BREAK ---
  L5 [13]: attacked, the
  L6 [14]: other two rush
  L7 [16]: behind the enemy
  --- PAGE BREAK ---
  L9 [18]: and counterattack.
  L10 [12]: Hit rate and
  L11 [18]: damage are greatly
  --- PAGE BREAK ---
  L13 [10]: increased.
```

### #30: R39 msg 373 (batch_r39_equip_a.json)
- **Longest line:** 148 chars
- **Total lines:** 1
- **Original:**
```
  L1 [148]: Punish the bad adventurer who punched
my friend!
He was examining a weird statue on B5F,
in the room to the northwest,
so he should be around there. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [14]: Punish the bad
  L2 [14]: adventurer who
  L3 [18]: punched my friend!
  --- PAGE BREAK ---
  L5 [18]: He was examining a
  L6 [15]: weird statue on
  L7 [16]: B5F, in the room
  --- PAGE BREAK ---
  L9 [17]: to the northwest,
  L10 [15]: so he should be
  L11 [13]: around there.
```

### #31: R39 msg 274 (batch_r39_equip_a.json)
- **Longest line:** 147 chars
- **Total lines:** 1
- **Original:**
```
  L1 [147]: Three front row members consecutively attack
a single enemy, greatly increasing damage.
The combo makes each successive hit stronger
than the last. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [15]: Three front row
  L2 [ 7]: members
  L3 [13]: consecutively
  --- PAGE BREAK ---
  L5 [15]: attack a single
  L6 [14]: enemy, greatly
  L7 [18]: increasing damage.
  --- PAGE BREAK ---
  L9 [15]: The combo makes
  L10 [15]: each successive
  L11 [17]: hit stronger than
  --- PAGE BREAK ---
  L13 [ 9]: the last.
```

### #32: R39 msg 254 (batch_r39_equip_a.json)
- **Longest line:** 145 chars
- **Total lines:** 1
- **Original:**
```
  L1 [145]: A back row member lifts a front row member
into the air with magic for a dive-attack
at the start of the turn. Temporarily
reduces enemy defense. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [17]: A back row member
  L2 [17]: lifts a front row
  L3 [15]: member into the
  --- PAGE BREAK ---
  L5 [18]: air with magic for
  L6 [16]: a dive-attack at
  L7 [16]: the start of the
  --- PAGE BREAK ---
  L9 [17]: turn. Temporarily
  L10 [13]: reduces enemy
  L11 [ 8]: defense.
```

### #33: R39 msg 358 (batch_r39_equip_a.json)
- **Longest line:** 143 chars
- **Total lines:** 1
- **Original:**
```
  L1 [143]: We're holding a Trap Game Contest at the
tavern. Anyone confident in their skills,
please sign up!
The grand champion will receive
a rare item. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [15]: We're holding a
  L2 [17]: Trap Game Contest
  L3 [14]: at the tavern.
  --- PAGE BREAK ---
  L5 [16]: Anyone confident
  L6 [16]: in their skills,
  L7 [15]: please sign up!
  --- PAGE BREAK ---
  L9 [18]: The grand champion
  L10 [14]: will receive a
  L11 [10]: rare item.
```

### #34: R39 msg 265 (batch_r39_equip_a.json)
- **Longest line:** 142 chars
- **Total lines:** 1
- **Original:**
```
  L1 [142]: When an enemy attempts to cast a spell, a
back row member attacks with a ranged weapon
to interrupt the casting. Limited activations
per turn. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [13]: When an enemy
  L2 [18]: attempts to cast a
  L3 [17]: spell, a back row
  --- PAGE BREAK ---
  L5 [14]: member attacks
  L6 [13]: with a ranged
  L7 [ 9]: weapon to
  --- PAGE BREAK ---
  L9 [13]: interrupt the
  L10 [16]: casting. Limited
  L11 [15]: activations per
  --- PAGE BREAK ---
  L13 [ 5]: turn.
```

### #35: R39 msg 286 (batch_r39_equip_a.json)
- **Longest line:** 142 chars
- **Total lines:** 1
- **Original:**
```
  L1 [142]: Evolved SJ Attack with a Dark Knight.
Slams a spirit-charged weapon from above to
create a shockwave, dealing damage and
stunning all enemies. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [17]: Evolved SJ Attack
  L2 [11]: with a Dark
  L3 [15]: Knight. Slams a
  --- PAGE BREAK ---
  L5 [14]: spirit-charged
  L6 [17]: weapon from above
  L7 [11]: to create a
  --- PAGE BREAK ---
  L9 [18]: shockwave, dealing
  L10 [10]: damage and
  L11 [12]: stunning all
  --- PAGE BREAK ---
  L13 [ 8]: enemies.
```

### #36: R39 msg 285 (batch_r39_equip_a.json)
- **Longest line:** 141 chars
- **Total lines:** 1
- **Original:**
```
  L1 [141]: Evolved Back Attack with a Samurai.
The samurai's swordsmanship enables an even
more powerful counterattack that can also
paralyze the enemy. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [12]: Evolved Back
  L2 [13]: Attack with a
  L3 [12]: Samurai. The
  --- PAGE BREAK ---
  L5 [ 9]: samurai's
  L6 [13]: swordsmanship
  L7 [15]: enables an even
  --- PAGE BREAK ---
  L9 [13]: more powerful
  L10 [18]: counterattack that
  L11 [17]: can also paralyze
  --- PAGE BREAK ---
  L13 [10]: the enemy.
```

### #37: R39 msg 287 (batch_r39_equip_a.json)
- **Longest line:** 141 chars
- **Total lines:** 1
- **Original:**
```
  L1 [141]: Evolved Hold Attack with a Bishop.
The back row spots the enemy's weakness while
holding, allowing the front row to deal even
greater damage. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [12]: Evolved Hold
  L2 [13]: Attack with a
  L3 [16]: Bishop. The back
  --- PAGE BREAK ---
  L5 [13]: row spots the
  L6 [16]: enemy's weakness
  L7 [14]: while holding,
  --- PAGE BREAK ---
  L9 [18]: allowing the front
  L10 [16]: row to deal even
  L11 [15]: greater damage.
```

### #38: R39 msg 370 (batch_r39_equip_a.json)
- **Longest line:** 141 chars
- **Total lines:** 1
- **Original:**
```
  L1 [141]: I have one more secret potion left, but
no use for it. I hear there's a fountain
on B6F.
Wouldn't it be wonderful if it could
heal you there? <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [15]: I have one more
  L2 [13]: secret potion
  L3 [16]: left, but no use
  --- PAGE BREAK ---
  L5 [14]: for it. I hear
  L6 [18]: there's a fountain
  L7 [16]: on B6F. Wouldn't
  --- PAGE BREAK ---
  L9 [18]: it be wonderful if
  L10 [17]: it could heal you
  L11 [ 6]: there?
```

### #39: R39 msg 266 (batch_r39_equip_a.json)
- **Longest line:** 139 chars
- **Total lines:** 1
- **Original:**
```
  L1 [139]: When an enemy attempts to use breath, a back
row member attacks with a ranged weapon to
interrupt the breath. Limited activations
per turn. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [13]: When an enemy
  L2 [15]: attempts to use
  L3 [18]: breath, a back row
  --- PAGE BREAK ---
  L5 [14]: member attacks
  L6 [13]: with a ranged
  L7 [ 9]: weapon to
  --- PAGE BREAK ---
  L9 [13]: interrupt the
  L10 [15]: breath. Limited
  L11 [15]: activations per
  --- PAGE BREAK ---
  L13 [ 5]: turn.
```

### #40: R39 msg 282 (batch_r39_equip_a.json)
- **Longest line:** 139 chars
- **Total lines:** 1
- **Original:**
```
  L1 [139]: Evolved W-Slash with a Fighter.
Two front row members swing their weapons to
create a shockwave. May also damage enemies
behind the target. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [15]: Evolved W-Slash
  L2 [15]: with a Fighter.
  L3 [13]: Two front row
  --- PAGE BREAK ---
  L5 [13]: members swing
  L6 [16]: their weapons to
  L7 [ 8]: create a
  --- PAGE BREAK ---
  L9 [14]: shockwave. May
  L10 [11]: also damage
  L11 [18]: enemies behind the
  --- PAGE BREAK ---
  L13 [ 7]: target.
```

### #41: R39 msg 343 (batch_r39_equip_a.json)
- **Longest line:** 138 chars
- **Total lines:** 1
- **Original:**
```
  L1 [138]: Our Vigger Shop is currently recruiting
new employees! Only one position available.
Applicants, please bring your entry sheet
to the shop. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [18]: Our Vigger Shop is
  L2 [ 9]: currently
  L3 [14]: recruiting new
  --- PAGE BREAK ---
  L5 [15]: employees! Only
  L6 [12]: one position
  L7 [10]: available.
  --- PAGE BREAK ---
  L9 [18]: Applicants, please
  L10 [16]: bring your entry
  L11 [18]: sheet to the shop.
```

### #42: R39 msg 270 (batch_r39_equip_a.json)
- **Longest line:** 137 chars
- **Total lines:** 1
- **Original:**
```
  L1 [137]: All back row members concentrate magic to
break silence. Cures the party's Mute status
and breaks enemy Magic Shell and Anti-Magic
Shell. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [12]: All back row
  L2 [ 7]: members
  L3 [17]: concentrate magic
  --- PAGE BREAK ---
  L5 [17]: to break silence.
  L6 [17]: Cures the party's
  L7 [15]: Mute status and
  --- PAGE BREAK ---
  L9 [18]: breaks enemy Magic
  L10 [ 9]: Shell and
  L11 [17]: Anti-Magic Shell.
```

### #43: R39 msg 356 (batch_r39_equip_a.json)
- **Longest line:** 137 chars
- **Total lines:** 1
- **Original:**
```
  L1 [137]: I knew someone would want the key I made!
But I'm not giving it away for free.
If you want it, bring me a spare
Gnome's Ring as my price. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [14]: I knew someone
  L2 [18]: would want the key
  L3 [15]: I made! But I'm
  --- PAGE BREAK ---
  L5 [18]: not giving it away
  L6 [16]: for free. If you
  L7 [17]: want it, bring me
  --- PAGE BREAK ---
  L9 [15]: a spare Gnome's
  L10 [17]: Ring as my price.
```

### #44: R39 msg 365 (batch_r39_equip_a.json)
- **Longest line:** 136 chars
- **Total lines:** 1
- **Original:**
```
  L1 [136]: To master the way of the samurai and find
a new light, I feel I need armor crafted by
a master artisan.
Would someone obtain one for me? <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [17]: To master the way
  L2 [18]: of the samurai and
  L3 [17]: find a new light,
  --- PAGE BREAK ---
  L5 [13]: I feel I need
  L6 [18]: armor crafted by a
  L7 [15]: master artisan.
  --- PAGE BREAK ---
  L9 [13]: Would someone
  L10 [18]: obtain one for me?
```

### #45: R39 msg 269 (batch_r39_equip_a.json)
- **Longest line:** 135 chars
- **Total lines:** 1
- **Original:**
```
  L1 [135]: Three back row members concentrate magic to
expand spell area of effect. Also reduces
enemy spell resistance and increases spell
power. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [14]: Three back row
  L2 [ 7]: members
  L3 [17]: concentrate magic
  --- PAGE BREAK ---
  L5 [15]: to expand spell
  L6 [15]: area of effect.
  L7 [18]: Also reduces enemy
  --- PAGE BREAK ---
  L9 [16]: spell resistance
  L10 [13]: and increases
  L11 [12]: spell power.
```

### #46: R39 msg 271 (batch_r39_equip_a.json)
- **Longest line:** 134 chars
- **Total lines:** 1
- **Original:**
```
  L1 [134]: Two adjacent back row members who both know
the same spell cast it together, increasing
execution speed. Faster than Anti-Magic Shell. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [17]: Two adjacent back
  L2 [15]: row members who
  L3 [18]: both know the same
  --- PAGE BREAK ---
  L5 [13]: spell cast it
  L6 [ 9]: together,
  L7 [10]: increasing
  --- PAGE BREAK ---
  L9 [16]: execution speed.
  L10 [11]: Faster than
  L11 [17]: Anti-Magic Shell.
```

### #47: R39 msg 354 (batch_r39_equip_a.json)
- **Longest line:** 134 chars
- **Total lines:** 1
- **Original:**
```
  L1 [134]: I'm stuck in a one-way passage and
can't get out!
Please hurry and help me!
I fell through a trapdoor on this floor
and ended up here. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [14]: I'm stuck in a
  L2 [15]: one-way passage
  L3 [18]: and can't get out!
  --- PAGE BREAK ---
  L5 [16]: Please hurry and
  L6 [15]: help me! I fell
  L7 [18]: through a trapdoor
  --- PAGE BREAK ---
  L9 [17]: on this floor and
  L10 [14]: ended up here.
```

### #48: R39 msg 261 (batch_r39_equip_a.json)
- **Longest line:** 133 chars
- **Total lines:** 1
- **Original:**
```
  L1 [133]: When an enemy uses breath, the entire party
takes cover, reducing breath and magic damage.
However, physical attack damage increases. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [18]: When an enemy uses
  L2 [18]: breath, the entire
  L3 [18]: party takes cover,
  --- PAGE BREAK ---
  L5 [15]: reducing breath
  L6 [17]: and magic damage.
  L7 [17]: However, physical
  --- PAGE BREAK ---
  L9 [13]: attack damage
  L10 [10]: increases.
```

### #49: R39 msg 283 (batch_r39_equip_a.json)
- **Longest line:** 133 chars
- **Total lines:** 1
- **Original:**
```
  L1 [133]: Three front row members charge through the
entire enemy front row as one, dealing damage
to each enemy. High damage but low hit rate. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [15]: Three front row
  L2 [14]: members charge
  L3 [18]: through the entire
  --- PAGE BREAK ---
  L5 [18]: enemy front row as
  L6 [12]: one, dealing
  L7 [14]: damage to each
  --- PAGE BREAK ---
  L9 [18]: enemy. High damage
  L10 [17]: but low hit rate.
```

### #50: R1209 msg 502 (batch_06.json)
- **Longest line:** 132 chars
- **Total lines:** 1
- **Original:**
```
  L1 [132]: The survey is a flat 1000G, regardless of the number of dolls. I will see how far your Automata has progressed to get her own heart. <<<OVER
```
- **Proposed fix** (fits):
```
  L1 [15]: The survey is a
  L2 [11]: flat 1000G,
  L3 [17]: regardless of the
  --- PAGE BREAK ---
  L5 [18]: number of dolls. I
  L6 [16]: will see how far
  L7 [17]: your Automata has
  --- PAGE BREAK ---
  L9 [17]: progressed to get
  L10 [14]: her own heart.
```

## Top 20 Page Overflow Offenders (by line count)

### R1194 msg 0 (batch_intro_narration.json)
- **Lines:** 64
- **Longest line:** 18 chars
- **Text:**
```
  L1 [13]: The Dark Lord
  L2 [14]: Ashira, driven
  L3 [13]: to the brink,
  L4 [13]: vanished into
  L5 [10]: the abyss.
  L6 [16]: The warriors who
  L7 [16]: fell were sealed
  L8 [14]: as Duhan's war
  L9 [16]: drew to a close.
  L10 [14]: Ortrud too, by
  L11 [17]: his own will, was
  L12 [16]: sealed alongside
  L13 [13]: the fallen of
  L14 [11]: Banquo. The
  L15 [12]: people shall
  L16 [13]: remember that
  L17 [14]: place forever.
  L18 [15]: Fresh snow fell
  L19 [14]: in winter, and
  L20 [13]: in spring the
  L21 [15]: sounds of peace
  L22 [16]: filled the land.
  L23 [17]: After long years,
  L24 [15]: Princess Oriana
  L25 [16]: declared herself
  L26 [14]: the new queen.
  L27 [12]: "The days of
  L28 [13]: bloodshed are
  L29 [14]: over at last."
  L30 [14]: "We must stand
  L31 [14]: united against
  L32 [16]: our common foe."
  L33 [12]: "For all who
  L34 [16]: dwell in Venoa."
  L35 [14]: "For the souls
  L36 [16]: of the brave who
  L37 [13]: have fallen."
  L38 [15]: "I hereby swear
  L39 [15]: my oath against
  L40 [11]: the lord of
  L41 [10]: darkness."
  L42 [11]: "Let me now
  L43 [14]: introduce them
  L44 [ 8]: to you."
  L45 [11]: The knights
  L46 [15]: marched forward
  L47 [18]: amid great cheers.
  L48 [14]: "The swords of
  L49 [11]: our beloved
  L50 [16]: Venoa! The noble
  L51 [14]: Queen's Guard,
  L52 [13]: who fight the
  L53 [10]: darkness!"
  L54 [11]: As confetti
  L55 [17]: rained down, this
  L56 [15]: scene became an
  L57 [15]: eternal legend.
  L58 [16]: It was the start
  L59 [14]: of the tale of
  L60 [16]: a fair queen and
  L61 [18]: her Queen's Guard.
  L62 [15]: But for now, we
  L63 [13]: set this tale
  L64 [ 6]: aside.
```

### R1194 msg 0 (batch_intro.json)
- **Lines:** 45
- **Longest line:** 18 chars
- **Text:**
```
  L1 [13]: The Dark Lord
  L2 [15]: Ashira vanished
  L3 [15]: into the abyss.
  L4 [17]: The warriors were
  L5 [14]: sealed away as
  L6 [16]: the war of Duhan
  L7 [16]: drew to a close.
  L8 [14]: Ortrud too was
  L9 [15]: sealed with the
  L10 [15]: warriors of the
  L11 [17]: Battle of Banquo.
  L12 [10]: Fresh snow
  L13 [18]: blanketed the land
  L14 [17]: and peace came at
  L15 [14]: last. Princess
  L16 [15]: Oriana declared
  L17 [14]: herself queen.
  L18 [18]: "Gone are the days
  L19 [18]: nations shed blood
  L20 [15]: We must advance
  L21 [18]: against our common
  L22 [14]: enemy, for all
  L23 [18]: who live in Venoa,
  L24 [17]: and the brave who
  L25 [14]: have fallen. I
  L26 [15]: declare my oath
  L27 [11]: as guardian
  L28 [17]: against darkness.
  L29 [16]: Let me introduce
  L30 [17]: them to you." The
  L31 [16]: knights advanced
  L32 [17]: amid loud cheers.
  L33 [18]: "The swords of our
  L34 [14]: beloved Venoa!
  L35 [17]: The noble Queen's
  L36 [16]: Guard, who fight
  L37 [14]: the darkness!"
  L38 [18]: As confetti rained
  L39 [16]: down, this scene
  L40 [14]: became legend.
  L41 [18]: The tale of a fair
  L42 [13]: queen and her
  L43 [14]: Queen's Guard.
  L44 [15]: For now, we set
  L45 [16]: this tale aside.
```

### R1355 msg 41 (batch_gap1347.json)
- **Lines:** 14
- **Longest line:** 26 chars
- **Text:**
```
  L1 [25]: Female: This time we went <<<OVER
  L2 [23]: to the sixth floor, but <<<OVER
  L3 [21]: there was no trace of <<<OVER
  L4 [16]: Aurora anywhere.
  L5 [21]: Soldier C: Any leads? <<<OVER
  L6 [26]: Female: Yes, but there was <<<OVER
  L7 [21]: one thing that caught <<<OVER
  L8 [13]: my attention.
  L9 [23]: Soldier C: What was it? <<<OVER
  L10 [15]: Please tell us.
  L11 [24]: Female: When I went deep <<<OVER
  L12 [22]: into the second floor, <<<OVER
  L13 [18]: I sensed something
  L14 [21]: strange and powerful! <<<OVER
```

### R1355 msg 42 (batch_gap1347.json)
- **Lines:** 12
- **Longest line:** 26 chars
- **Text:**
```
  L1 [25]: Soldier D: Was it Aurora? <<<OVER
  L2 [25]: Female: I don't think so. <<<OVER
  L3 [25]: It was something far more <<<OVER
  L4 [20]: evil than any demon. <<<OVER
  L5 [22]: Sorry I can't describe <<<OVER
  L6 [10]: it better.
  L7 [23]: Soldier D: That's fine. <<<OVER
  L8 [26]: If the famous Aoi says so, <<<OVER
  L9 [16]: it must be true.
  L10 [26]: Soldier C: Let's hurry and <<<OVER
  L11 [24]: authorize a search party <<<OVER
  L12 [18]: for the 2nd floor.
```

### R1193 msg 0 (batch_intro.json)
- **Lines:** 12
- **Longest line:** 17 chars
- **Text:**
```
  L1 [17]: For thirty years,
  L2 [17]: Duhan was plunged
  L3 [14]: into blood and
  L4 [16]: terror. This war
  L5 [17]: would be known as
  L6 [13]: the Battle of
  L7 [16]: Banquo. The king
  L8 [12]: of San-Goth,
  L9 [16]: possessed by the
  L10 [16]: spirit of death,
  L11 [15]: led his army to
  L12 [13]: attack Duhan!
```

### R1193 msg 0 (batch_intro_narration.json)
- **Lines:** 12
- **Longest line:** 19 chars
- **Text:**
```
  L1 [17]: For thirty years,
  L2 [19]: a war plunged Venoa <<<OVER
  L3 [14]: into blood and
  L4 [16]: terror. It would
  L5 [16]: come to be known
  L6 [16]: as the Battle of
  L7 [16]: Banquo. It began
  L8 [16]: when the king of
  L9 [15]: San-Goth raised
  L10 [14]: his banner and
  L11 [12]: attacked the
  L12 [17]: Kingdom of Duhan!
```

### R1205 msg 694 (batch_04.json)
- **Lines:** 11
- **Longest line:** 13 chars
- **Text:**
```
  L1 [10]: Alchemist:
  L2 [ 6]: I read
  L3 [ 9]: companion
  L4 [11]: dolls using
  L5 [ 8]: alchemy.
  L6 [ 8]: I make a
  L7 [ 6]: living
  L8 [13]: observing the
  L9 [ 8]: cycle of
  L10 [ 8]: soulless
  L11 [ 6]: dolls.
```

### R1205 msg 698 (batch_04.json)
- **Lines:** 10
- **Longest line:** 13 chars
- **Text:**
```
  L1 [ 6]: I read
  L2 [ 9]: companion
  L3 [11]: dolls using
  L4 [ 8]: alchemy.
  L5 [ 8]: I make a
  L6 [ 6]: living
  L7 [13]: observing the
  L8 [ 8]: cycle of
  L9 [ 8]: soulless
  L10 [ 6]: dolls.
```

### R1355 msg 54 (batch_gap1347.json)
- **Lines:** 10
- **Longest line:** 27 chars
- **Text:**
```
  L1 [19]: Aoi: My dream is to <<<OVER
  L2 [22]: sleep in a place where <<<OVER
  L3 [23]: no one will disturb me. <<<OVER
  L4 [27]: Soldier C: We're just going <<<OVER
  L5 [21]: to stand by the door. <<<OVER
  L6 [27]: Soldier D: We have no plans <<<OVER
  L7 [23]: to interrupt your rest. <<<OVER
  L8 [20]: Aoi: I know, I know. <<<OVER
  L9 [19]: It was just a joke. <<<OVER
  L10 [23]: I've gotten used to it. <<<OVER
```

### R1203 msg 1096 (batch_03.json)
- **Lines:** 9
- **Longest line:** 19 chars
- **Text:**
```
  L1 [14]: Ingo: Why do I
  L2 [15]: have to babysit
  L3 [ 9]: newbies?!
  L4 [19]: Soldier: That's not <<<OVER
  L5 [13]: my problem...
  L6 [15]: Ingo: I've even
  L7 [15]: read the Pope's
  L8 [14]: judgment! Tell
  L9 [10]: Belgradno!
```

### R1205 msg 334 (batch_04.json)
- **Lines:** 9
- **Longest line:** 15 chars
- **Text:**
```
  L1 [14]: Orc F: "Why do
  L2 [15]: we have to pull
  L3 [12]: up our pants
  L4 [ 9]: in unison
  L5 [14]: every battle?"
  L6 [13]: Orc G: "Isn't
  L7 [11]: that weird?
  L8 [14]: That's why you
  L9 [13]: drop things!"
```

### R1205 msg 336 (batch_04.json)
- **Lines:** 9
- **Longest line:** 14 chars
- **Text:**
```
  L1 [12]: Orc F: "Hmm,
  L2 [11]: is that so.
  L3 [13]: But don't you
  L4 [14]: think it lacks
  L5 [ 7]: style?"
  L6 [11]: Orc G: "Why
  L7 [ 7]: not try
  L8 [ 9]: something
  L9 [11]: different?"
```

### R1205 msg 695 (batch_04.json)
- **Lines:** 9
- **Longest line:** 14 chars
- **Text:**
```
  L1 [13]: The appraisal
  L2 [12]: fee is 1000g
  L3 [ 9]: per body,
  L4 [13]: regardless of
  L5 [14]: your standing.
  L6 [14]: Let me see how
  L7 [11]: much spirit
  L8 [10]: resides in
  L9 [10]: your doll.
```

### R1205 msg 763 (batch_04.json)
- **Lines:** 9
- **Longest line:** 14 chars
- **Text:**
```
  L1 [12]: Melanie: "S-
  L2 [ 8]: Stop it,
  L3 [ 6]: you're
  L4 [12]: embarrassing
  L5 [10]: me! People
  L6 [11]: will come!"
  L7 [14]: Voice: "That's
  L8 [ 9]: the whole
  L9 [ 7]: point!"
```

### R1205 msg 884 (batch_04.json)
- **Lines:** 9
- **Longest line:** 12 chars
- **Text:**
```
  L1 [12]: At the time,
  L2 [ 8]: even the
  L3 [ 9]: strongest
  L4 [12]: sorcerers of
  L5 [10]: Venoa were
  L6 [12]: overwhelmed.
  L7 [12]: That kingdom
  L8 [12]: fell to this
  L9 [10]: one witch.
```

### R1210 msg 101 (batch_07.json)
- **Lines:** 9
- **Longest line:** 16 chars
- **Text:**
```
  L1 [10]: Accept him
  L2 [15]: his blood shall
  L3 [11]: be thy body
  L4 [13]: his flesh thy
  L5 [10]: sustenance
  L6 [13]: the followers
  L7 [12]: shall be one
  L8 [14]: with the great
  L9 [16]: one forevermore.
```

### R1212 msg 722 (batch_08.json)
- **Lines:** 9
- **Longest line:** 17 chars
- **Text:**
```
  L1 [16]: Everything fades
  L2 [ 5]: Death
  L3 [11]: Demon cries
  L4 [ 8]: Crawlers
  L5 [ 7]: Screams
  L6 [ 8]: All gone
  L7 [14]: Why do I live?
  L8 [17]: To slay crawlers.
  L9 [16]: Got Murmur Core.
```

### R1355 msg 39 (batch_gap1347.json)
- **Lines:** 9
- **Longest line:** 24 chars
- **Text:**
```
  L1 [15]: Soldier A: Hey!
  L2 [17]: She has returned!
  L3 [24]: Soldier B: How are they? <<<OVER
  L4 [23]: She's unwounded, right? <<<OVER
  L5 [23]: Soldier A: She had just <<<OVER
  L6 [20]: handed Rudi the head <<<OVER
  L7 [17]: of a demon. Not a
  L8 [15]: scratch on her.
  L9 [22]: Soldier B: Incredible! <<<OVER
```

### R1355 msg 53 (batch_gap1347.json)
- **Lines:** 9
- **Longest line:** 24 chars
- **Text:**
```
  L1 [21]: Soldier C: Well then, <<<OVER
  L2 [18]: we will escort you
  L3 [11]: to the inn.
  L4 [24]: Aoi: On watch duty today <<<OVER
  L5 [24]: too, I see. I wonder how <<<OVER
  L6 [23]: much more carefree life <<<OVER
  L7 [17]: outside would be.
  L8 [23]: Soldier D: We are sorry <<<OVER
  L9 [11]: about that!
```

### R1200 msg 64 (batch_02.json)
- **Lines:** 8
- **Longest line:** 18 chars
- **Text:**
```
  L1 [12]: Investigate.
  L2 [10]: Curiosity?
  L3 [11]: Topics 1-10
  L4 [12]: Shadow Check
  L5 [ 9]: Lab anger
  L6 [12]: God's grace?
  L7 [18]: Cursed Allayed 1-8
  L8 [18]: Request completed.
```

---
*End of audit report*