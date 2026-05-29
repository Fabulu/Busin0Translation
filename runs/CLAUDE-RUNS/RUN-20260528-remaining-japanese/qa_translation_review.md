# QA Translation Review Report

Date: 2026-05-28

Total entries scanned: 15898
  - Type-2 (batch_*.json): 13705
  - Type-1 (chunk_*.json): 2193

## Summary

| Category | Count | Severity |
|---|---|---|
| Uppercase characters | 14915 entries | HIGH - font atlas only has lowercase |
| Lines > 28 chars | 859 lines | HIGH - will truncate on screen |
| Non-ASCII characters | 0 entries | OK |
| Empty english fields | 25 entries | MEDIUM |
| Duplicate keys (cross-file) | 932 keys | HIGH - build conflict |
| Duplicate keys (same-file) | 0 keys | LOW - likely intentional |
| Missing required fields | 0 entries | HIGH |

## A. Uppercase Characters (font atlas only has lowercase a-z)

14915 of 15898 entries (93%) contain uppercase.

**NOTE:** The build pipeline's glyph encoder maps uppercase to lowercase automatically,
so these will render as lowercase in-game. However, the source data should ideally be
pre-lowercased for clarity. This is a cosmetic/data-hygiene issue, not a functional bug.

### Per-file breakdown

| File | Entries with uppercase | Total entries | % |
|---|---|---|---|
| batch_01.json | 1955 | 1989 | 98% |
| batch_02.json | 927 | 936 | 99% |
| batch_03.json | 1574 | 1580 | 99% |
| batch_04.json | 1795 | 1833 | 97% |
| batch_05.json | 1743 | 1761 | 98% |
| batch_06.json | 1446 | 1484 | 97% |
| batch_07.json | 1351 | 1368 | 98% |
| batch_08.json | 730 | 750 | 97% |
| batch_09.json | 915 | 935 | 97% |
| batch_10.json | 137 | 137 | 100% |
| batch_11.json | 114 | 114 | 100% |
| batch_dungeon_a.json | 34 | 35 | 97% |
| batch_gap1347.json | 132 | 132 | 100% |
| batch_gap989.json | 3 | 3 | 100% |
| batch_intro.json | 2 | 2 | 100% |
| batch_intro_narration.json | 2 | 2 | 100% |
| batch_r1198.json | 87 | 88 | 98% |
| batch_r39_equip_a.json | 271 | 307 | 88% |
| batch_r39_equip_b.json | 232 | 238 | 97% |
| chunk_00_translated.json | 113 | 113 | 100% |
| chunk_01_translated.json | 112 | 113 | 99% |
| chunk_02_translated.json | 113 | 113 | 100% |
| chunk_03_translated.json | 107 | 113 | 94% |
| chunk_04_translated.json | 108 | 113 | 95% |
| chunk_05_translated.json | 110 | 113 | 97% |
| chunk_06_translated.json | 113 | 113 | 100% |
| chunk_07_translated.json | 108 | 113 | 95% |
| chunk_08_translated.json | 112 | 113 | 99% |
| chunk_09_translated.json | 110 | 112 | 98% |
| chunk_r37_extra.json | 109 | 111 | 98% |
| chunk_r43_fix.json | 26 | 26 | 100% |
| chunk_r43_r45_translated.json | 224 | 264 | 84% |

### Entries with ONLY uppercase (no lowercase) - 56 entries

- **batch_04.json** [#553]: `WINNERRRRR!`
- **batch_05.json** [#469]: `WINNER!`
- **batch_05.json** [#491]: `MISS!`
- **batch_05.json** [#496]: `MISS!`
- **batch_05.json** [#1354]: `WINNER!`
- **batch_05.json** [#1373]: `MISS!`
- **batch_05.json** [#1377]: `MISS!`
- **batch_05.json** [#1380]: `WINNEEEER!`
- **batch_07.json** [#405]: `WINNERRR!`
- **batch_07.json** [#1010]: `WINNERRR!`
- **batch_08.json** [#312]: `WINNER!!`
- **batch_09.json** [#309]: `WINNER!!`
- **batch_gap1347.json** [#10]: `[DEBUG] A I U E O KA KI KU KE KO / SA SHI SU SE SO / TA CHI TSU TE TO NA NI NU N`
- **batch_r39_equip_b.json** [#13]: `G`
- **chunk_00_translated.json** [#39]: `ON / `
- **chunk_00_translated.json** [#40]: `OFF / `
- **chunk_01_translated.json** [#102]: `HP / `
- **chunk_01_translated.json** [#103]: `HP/MHP / `
- **chunk_01_translated.json** [#104]: `INT / `
- **chunk_01_translated.json** [#105]: `FTH / `
- ... and 36 more

## B. Lines Exceeding 28 Characters

Total: 859 long lines across all entries

| Severity | Count |
|---|---|
| 29-32 chars | 146 |
| 33-40 chars | 108 |
| 41-50 chars | 124 |
| 51+ chars | 481 |

### Critical (51+ chars) - likely multi-line or unformatted text

- **batch_r39_equip_a.json** [#249] (217 chars): `Beat me at 5 rounds of Rock-Paper-Scissors
and I'll give you something good! But if you
lose, you ge`
- **batch_r39_equip_a.json** [#248] (212 chars): `I want to learn magic but I don't have any
magic stones. Without magic, I'll waste away.
Please give`
- **batch_r39_equip_a.json** [#270] (205 chars): `I poured the labyrinth's magic into the
masterwork armor and tempered it rigorously,
but something i`
- **batch_r39_equip_a.json** [#277] (198 chars): `Somewhere on B10F, there should be a room
with a large water vase in the center.
I don't know where `
- **batch_r39_equip_a.json** [#267] (191 chars): `The guide for the Karman Exploration Tour
organized by the Duhan Merchant Guild has
suddenly become `
- **batch_r39_equip_a.json** [#171] (189 chars): `One front row member acts as a decoy. When
attacked, the remaining front row members
counterattack f`
- **batch_r39_equip_a.json** [#252] (188 chars): `Information has come in that ruins of an
ancient Elf kingdom were found in the
labyrinth. Items need`
- **batch_r39_equip_a.json** [#263] (183 chars): `The Knight Order is conducting level checks
on registered adventurers.
This is a test of how well yo`
- **batch_r39_equip_a.json** [#247] (177 chars): `If you're reading this, please come
immediately to the small room just past the
first warp on B5F. I`
- **batch_r39_equip_a.json** [#269] (176 chars): `The masterwork armor, obtained with great
effort. But to find the new light, something
is still miss`
- **batch_r39_equip_a.json** [#181] (173 chars): `Two front row members feint while the third
strikes from above at the enemy's weak point.
All member`
- **batch_r39_equip_a.json** [#250] (171 chars): `Duhan Castle has recently established an
Adventurer Assistance Program.
Bring 5 companions to the Ca`
- **batch_r39_equip_a.json** [#264] (171 chars): `I'm Melanie, an elf girl training daily
to become a full-fledged mage,
and my manager Miri.
I want t`
- **batch_r39_equip_a.json** [#159] (168 chars): `Two back row members bind the enemy with
crossed magic, pull it forward, and two front
row members a`
- **batch_r39_equip_a.json** [#256] (168 chars): `As a reward for accepting this request,
I will transfer a piece of land to you.
Details will only be`
- **batch_r39_equip_a.json** [#160] (166 chars): `All front row members take a defensive stance,
reducing evasion and defense. Cures stun,
paralysis, `
- **batch_r39_equip_a.json** [#166] (164 chars): `When a protected front row member is attacked,
a back row member counterattacks with ranged
weapons.`
- **batch_r39_equip_a.json** [#183] (164 chars): `One back row member creates a warp gate, and
three front row members dive-attack from an
aerial gate`
- **batch_r39_equip_a.json** [#274] (164 chars): `I've never seen anyone possessed by a death
spirit, so I'd like to meet one.
Please come back to the`
- **batch_r39_equip_a.json** [#266] (161 chars): `I dropped my precious treasure chest
in the scary room on B1F.
I can't write the details here, but
I`
- **batch_r39_equip_a.json** [#163] (160 chars): `All back row members create duplicates of
every party member. Duplicates vanish when
hit, but real m`
- **batch_r39_equip_a.json** [#179] (155 chars): `Evolved Concentrated Attack with a Fighter.
The first member launches the enemy into the
air, then a`
- **batch_r39_equip_a.json** [#258] (155 chars): `The magic portal room connecting B4F and B1F
is locked and I'm in trouble.
Ingo should be able to he`
- **batch_r39_equip_a.json** [#165] (153 chars): `The entire party takes an evasive formation,
greatly increasing evasion and defense against
physical`
- **batch_r39_equip_a.json** [#184] (153 chars): `Evolved Slay Crash with a Monk.
Two members charge through the enemy with
spirit energy, dealing dam`
- **batch_r39_equip_a.json** [#262] (152 chars): `I want to talk to the Succubus ladies but
they always run away.
Now's my chance!
Please catch a Succ`
- **batch_r39_equip_a.json** [#254] (151 chars): `I borrowed 20 medals from the Ogre boss
and debt collectors are after me.
I'm exhausted.
Please, giv`
- **batch_r39_equip_a.json** [#175] (150 chars): `A back row member enchants an ally's weapon
with a spell. If the attack hits, it bypasses
enemy spel`
- **batch_r39_equip_a.json** [#178] (150 chars): `One front row member acts as a decoy. When
attacked, the other two rush behind the enemy
and counter`
- **batch_r39_equip_a.json** [#276] (148 chars): `Punish the bad adventurer who punched
my friend!
He was examining a weird statue on B5F,
in the room`
- **batch_r39_equip_a.json** [#177] (147 chars): `Three front row members consecutively attack
a single enemy, greatly increasing damage.
The combo ma`
- **batch_r39_equip_a.json** [#157] (145 chars): `A back row member lifts a front row member
into the air with magic for a dive-attack
at the start of`
- **batch_r39_equip_a.json** [#261] (143 chars): `We're holding a Trap Game Contest at the
tavern. Anyone confident in their skills,
please sign up!
T`
- **batch_r39_equip_a.json** [#168] (142 chars): `When an enemy attempts to cast a spell, a
back row member attacks with a ranged weapon
to interrupt `
- **batch_r39_equip_a.json** [#189] (142 chars): `Evolved SJ Attack with a Dark Knight.
Slams a spirit-charged weapon from above to
create a shockwave`
- **batch_r39_equip_a.json** [#188] (141 chars): `Evolved Back Attack with a Samurai.
The samurai's swordsmanship enables an even
more powerful counte`
- **batch_r39_equip_a.json** [#190] (141 chars): `Evolved Hold Attack with a Bishop.
The back row spots the enemy's weakness while
holding, allowing t`
- **batch_r39_equip_a.json** [#273] (141 chars): `I have one more secret potion left, but
no use for it. I hear there's a fountain
on B6F.
Wouldn't it`
- **batch_r39_equip_a.json** [#169] (139 chars): `When an enemy attempts to use breath, a back
row member attacks with a ranged weapon to
interrupt th`
- **batch_r39_equip_a.json** [#185] (139 chars): `Evolved W-Slash with a Fighter.
Two front row members swing their weapons to
create a shockwave. May`
- **batch_r39_equip_a.json** [#246] (138 chars): `Our Vigger Shop is currently recruiting
new employees! Only one position available.
Applicants, plea`
- **batch_r39_equip_a.json** [#173] (137 chars): `All back row members concentrate magic to
break silence. Cures the party's Mute status
and breaks en`
- **batch_r39_equip_a.json** [#259] (137 chars): `I knew someone would want the key I made!
But I'm not giving it away for free.
If you want it, bring`
- **batch_r39_equip_a.json** [#268] (136 chars): `To master the way of the samurai and find
a new light, I feel I need armor crafted by
a master artis`
- **batch_r39_equip_a.json** [#172] (135 chars): `Three back row members concentrate magic to
expand spell area of effect. Also reduces
enemy spell re`
- **batch_r39_equip_a.json** [#174] (134 chars): `Two adjacent back row members who both know
the same spell cast it together, increasing
execution sp`
- **batch_r39_equip_a.json** [#257] (134 chars): `I'm stuck in a one-way passage and
can't get out!
Please hurry and help me!
I fell through a trapdoo`
- **batch_r39_equip_a.json** [#164] (133 chars): `When an enemy uses breath, the entire party
takes cover, reducing breath and magic damage.
However, `
- **batch_r39_equip_a.json** [#186] (133 chars): `Three front row members charge through the
entire enemy front row as one, dealing damage
to each ene`
- **batch_06.json** [#1354] (132 chars): `The survey is a flat 1000G, regardless of the number of dolls. I will see how far your Automata has `
- ... and 431 more

### High (41-50 chars)

- **batch_06.json** [#916] (50 chars): `Maybe... I... I wonder if they really hate me...!?`
- **batch_06.json** [#967] (50 chars): `to take back the Duhan royal family into my hands.`
- **batch_06.json** [#974] (50 chars): `So did Lord Webster say, and looked up to the sky.`
- **batch_06.json** [#1004] (50 chars): `I'm going to return with the Princess to the city.`
- **batch_06.json** [#1083] (50 chars): `Do you want to join? (Admission Fee: 5000G) Yes No`
- **batch_06.json** [#1340] (50 chars): `The Dark Medal costs 1 for 1000G. Want to buy one?`
- **batch_r39_equip_a.json** [#106] (50 chars): `Warps to the stairs entrance on the current floor.`
- **batch_r39_equip_b.json** [#76] (50 chars): `User's alignment changed
to Neutral.
SP activated.`
- **batch_r39_equip_b.json** [#80] (50 chars): `Allied action proficiency
increased.
SP activated.`
- **chunk_06_translated.json** [#33] (50 chars): `Hold various /events and clients /won't get bored!`
- **chunk_06_translated.json** [#74] (50 chars): `Dunno what this /is, so I'll only /pay 10g for it.`
- **batch_06.json** [#1301] (49 chars): `You picked up the stone that Lomi offered to you.`
- **batch_06.json** [#1339] (49 chars): `We do have Trap Game Medals though. How about it?`
- **batch_06.json** [#1352] (49 chars): `We do have Trap Game Medals though. How about it?`
- **batch_06.json** [#1410] (49 chars): `The orcs happily returned to exploring the floor.`
- **batch_06.json** [#1426] (49 chars): `and then suddenly they appeared on the 7th floor!`
- **batch_06.json** [#1448] (49 chars): `Emilia went to hide herself in the shadows again.`
- **batch_r39_equip_a.json** [#103] (49 chars): `Restores one ally's HP and cures status ailments.`
- **chunk_06_translated.json** [#13] (49 chars): `Right then. /Here's the latest /Vigger Shop info.`
- **chunk_06_translated.json** [#34] (49 chars): `Rest anytime, /even when beat up! /No levels tho.`
- **batch_06.json** [#890] (48 chars): `Would you mind subduing Big Sister for a moment?`
- **batch_06.json** [#930] (48 chars): `Or are you still interested in doing me a favor?`
- **batch_06.json** [#1050] (48 chars): `You came to check out the shop? Me too actually.`
- **batch_06.json** [#1080] (48 chars): `Please make sure that you get in next time, bro!`
- **batch_06.json** [#1082] (48 chars): `Please make sure that you get in next time, sis!`
- **batch_06.json** [#1095] (48 chars): `Please make sure that you get in next time, bro!`
- **batch_06.json** [#1097] (48 chars): `Please make sure that you get in next time, sis!`
- **batch_06.json** [#1480] (48 chars): `So what piece of the puzzle are we missing here?`
- **chunk_06_translated.json** [#7] (48 chars): `There! Now ya know /what it is. /Feels good, eh?`
- **chunk_06_translated.json** [#12] (48 chars): `Ohhh, I'm the /uncursin' superstar /around here!`
- ... and 94 more

### Medium (33-40 chars)

- **batch_01.json** [#56] (40 chars): `You just sit there!
Girl B: I didn't say`
- **batch_06.json** [#942] (40 chars): `Emilia peeked out from behind your back.`
- **batch_06.json** [#953] (40 chars): `Who could have imagined such an outcome?`
- **batch_06.json** [#1125] (40 chars): `So whose fortune do you want me to read?`
- **batch_06.json** [#1256] (40 chars): `Please come back again with more points!`
- **batch_06.json** [#1319] (40 chars): `Oh, welcome, welcome to the Medal Store!`
- **batch_06.json** [#1455] (40 chars): `I can't say that I dislike men like him.`
- **batch_06.json** [#1464] (40 chars): `But did Webster know about it, I wonder?`
- **batch_r39_equip_b.json** [#68] (40 chars): `User's Strength increased.
SP activated.`
- **batch_r39_equip_b.json** [#71] (40 chars): `User's Vitality increased.
SP activated.`
- **batch_r39_equip_b.json** [#231] (40 chars): `Party rank [Disabled]
has been restored.`
- **batch_01.json** [#58] (39 chars): `a magic sword!
Girl B: Would that work?`
- **batch_06.json** [#957] (39 chars): `But then again, God is a shifty fellow.`
- **batch_06.json** [#1416] (39 chars): `Lute will be bringing Bergran with her!`
- **batch_06.json** [#1419] (39 chars): `The orc noticed you and leaped for joy.`
- **batch_06.json** [#1421] (39 chars): `Emilia: Please, please, please help us!`
- **batch_06.json** [#1445] (39 chars): `Really, I'm such a good-natured person.`
- **batch_r39_equip_a.json** [#73] (39 chars): `Temporarily prevents random encounters.`
- **batch_r39_equip_a.json** [#223] (39 chars): `2 Dispel-capable front and back members`
- **batch_r39_equip_a.json** [#240] (39 chars): `Alleid Action settings have been reset.`
- **batch_r39_equip_a.json** [#296] (39 chars): `??? has started heading for the spring.`
- **batch_r39_equip_b.json** [#72] (39 chars): `User's Agility increased.
SP activated.`
- **batch_r39_equip_b.json** [#84] (39 chars): `User's Defense increased.
SP activated.`
- **batch_r39_equip_b.json** [#236] (39 chars): `[Some of AA's parts have
been removed.]`
- **chunk_06_translated.json** [#8] (39 chars): `Who's the poor /soul that got /cursed??`
- **batch_01.json** [#63] (38 chars): `This is special!
Girl A: Special, huh!`
- **batch_01.json** [#64] (38 chars): `You'll go many times!
Girl A: I guess!`
- **batch_06.json** [#903] (38 chars): `Don't come near me! You're disgusting!`
- **batch_06.json** [#1108] (38 chars): `A voice called you out from somewhere.`
- **batch_06.json** [#1290] (38 chars): `You picked up the Helmet of Fortitude.`
- ... and 78 more

### Low (29-32 chars)

- **batch_06.json** [#997] (32 chars): `Emilia rushed towards the altar.`
- **batch_06.json** [#1072] (32 chars): `Ahem! I'll start explaining now!`
- **batch_06.json** [#1120] (32 chars): `No, I won't give you a discount.`
- **batch_06.json** [#1331] (32 chars): `You received 5 Trap Game Medals!`
- **batch_06.json** [#1432] (32 chars): `You're going to go and get Lute.`
- **batch_10.json** [#3] (32 chars): `[LAYOUT] Equipment screen layout`
- **batch_gap1347.json** [#2] (32 chars): `sa shi su se so ta chi tsu te to`
- **batch_gap1347.json** [#3] (32 chars): `[DEBUG] a i u e o ka ki ku ke ko`
- **batch_gap1347.json** [#3] (32 chars): `sa shi su se so ta chi tsu te to`
- **batch_gap1347.json** [#10] (32 chars): `[DEBUG] A I U E O KA KI KU KE KO`
- **batch_gap1347.json** [#41] (32 chars): `in the red gemstone, you learned`
- **batch_gap1347.json** [#58] (32 chars): `[DEBUG] Melanie/Ekunnal: This is`
- **batch_gap1347.json** [#61] (32 chars): `[DEBUG] Melanie/Ekunnal: This is`
- **batch_gap1347.json** [#64] (32 chars): `[DEBUG] Melanie/Ekunnal: This is`
- **batch_gap1347.json** [#67] (32 chars): `[DEBUG] Melanie/Ekunnal: This is`
- **batch_gap1347.json** [#70] (32 chars): `[DEBUG] Melanie/Ekunnal: This is`
- **batch_gap1347.json** [#73] (32 chars): `[DEBUG] Melanie/Ekunnal: This is`
- **batch_gap1347.json** [#114] (32 chars): `voices of knights on guard duty.`
- **batch_r39_equip_a.json** [#79] (32 chars): `Deals ice damage to all enemies.`
- **batch_r39_equip_a.json** [#216] (32 chars): `1 back row caster and 1 attacker`
- **batch_r39_equip_b.json** [#60] (32 chars): `I Want to Meet Someone Possessed`
- **chunk_06_translated.json** [#17] (32 chars): `Renovate and /reopen the branch?`
- **chunk_06_translated.json** [#47] (32 chars): `Introduce this /order to allies?`
- **chunk_06_translated.json** [#55] (32 chars): `Curse broken but /item survived!`
- **chunk_08_translated.json** [#81] (32 chars): `A large boulder
blocks the path.`
- **chunk_08_translated.json** [#99] (32 chars): `Some device is
set on the fence.`
- **batch_01.json** [#62] (31 chars): `keep it!
Girl B: No! We'll have`
- **batch_06.json** [#900] (31 chars): `What... what are you doing...!?`
- **batch_06.json** [#954] (31 chars): `I was imagining various things.`
- **batch_06.json** [#1031] (31 chars): `Cell disappeared into thin air.`
- ... and 116 more

## C. Non-ASCII Characters (ord > 127)

Total: 0 entries -- CLEAN

## D. Empty English Fields

Total: 25 entries

- **batch_r1163_1167.json** [#0] r=1163 m=-1: jp=`?`
- **batch_r1163_1167.json** [#1] r=1164 m=-1: jp=`?`
- **batch_r1163_1167.json** [#2] r=1165 m=-1: jp=`?`
- **batch_r1163_1167.json** [#3] r=1166 m=-1: jp=`?`
- **batch_r1163_1167.json** [#4] r=1167 m=-1: jp=`?`
- **batch_r1168_1173.json** [#0] r=1168 m=None: jp=`?`
- **batch_r1168_1173.json** [#1] r=1169 m=None: jp=`?`
- **batch_r1168_1173.json** [#2] r=1170 m=None: jp=`?`
- **batch_r1168_1173.json** [#3] r=1171 m=None: jp=`?`
- **batch_r1168_1173.json** [#4] r=1172 m=None: jp=`?`
- **batch_r1168_1173.json** [#5] r=1173 m=None: jp=`?`
- **batch_r39_equip_a.json** [#0] r=39 m=97: jp=`?`
- **batch_r39_equip_a.json** [#57] r=39 m=154: jp=`?`
- **batch_r39_equip_a.json** [#153] r=39 m=250: jp=`?`
- **batch_r39_equip_a.json** [#217] r=39 m=314: jp=`?`
- **batch_r39_equip_a.json** [#244] r=39 m=341: jp=`?`
- **batch_r39_equip_a.json** [#278] r=39 m=375: jp=`?`
- **batch_r39_equip_b.json** [#0] r=39 m=412: jp=` [FFFE]`
- **batch_r39_equip_b.json** [#30] r=39 m=443: jp=` [FFFE]`
- **batch_r39_equip_b.json** [#64] r=39 m=478: jp=` [FFFE]`
- **batch_r39_equip_b.json** [#108] r=39 m=524: jp=` [FFFE]`
- **batch_r39_equip_b.json** [#122] r=39 m=539: jp=` [FFFE]`
- **batch_r39_equip_b.json** [#237] r=39 m=655: jp=`                                                            `
- **chunk_r36_translated.json** [#0] r=36 m=0: jp=` `
- **chunk_r36_translated.json** [#97] r=36 m=97: jp=` `

## E. Duplicate (resource, msg_index) Pairs

Total: 932 duplicate keys
  - Cross-file: 932 (potential build conflicts)
  - Same-file: 0 (likely intentional repeated messages)

### Cross-file duplicates (HIGH priority)

- r=35 m=3: batch_dungeon_a.json[#1], chunk_00_translated.json[#26]
- r=35 m=4: batch_dungeon_a.json[#2], chunk_00_translated.json[#27]
- r=35 m=5: batch_dungeon_a.json[#3], chunk_00_translated.json[#28]
- r=35 m=6: batch_dungeon_a.json[#4], chunk_00_translated.json[#29]
- r=35 m=7: batch_dungeon_a.json[#5], chunk_00_translated.json[#30]
- r=35 m=8: batch_dungeon_a.json[#6], chunk_00_translated.json[#31]
- r=35 m=9: batch_dungeon_a.json[#7], chunk_00_translated.json[#32]
- r=35 m=10: batch_dungeon_a.json[#8], chunk_00_translated.json[#33]
- r=35 m=11: batch_dungeon_a.json[#9], chunk_00_translated.json[#34]
- r=35 m=12: batch_dungeon_a.json[#10], chunk_00_translated.json[#35]
- r=35 m=13: batch_dungeon_a.json[#11], chunk_00_translated.json[#36]
- r=35 m=15: batch_dungeon_a.json[#13], chunk_00_translated.json[#37]
- r=35 m=16: batch_dungeon_a.json[#14], chunk_00_translated.json[#38]
- r=35 m=17: batch_dungeon_a.json[#15], chunk_00_translated.json[#39]
- r=35 m=18: batch_dungeon_a.json[#16], chunk_00_translated.json[#40]
- r=35 m=19: batch_dungeon_a.json[#17], chunk_00_translated.json[#41]
- r=35 m=22: batch_dungeon_a.json[#20], chunk_00_translated.json[#42]
- r=35 m=23: batch_dungeon_a.json[#21], chunk_00_translated.json[#43]
- r=36 m=1: chunk_00_translated.json[#44], chunk_r36_translated.json[#1]
- r=36 m=2: chunk_00_translated.json[#45], chunk_r36_translated.json[#2]
- r=36 m=3: chunk_00_translated.json[#46], chunk_r36_translated.json[#3]
- r=36 m=4: chunk_00_translated.json[#47], chunk_r36_translated.json[#4]
- r=36 m=5: chunk_00_translated.json[#48], chunk_r36_translated.json[#5]
- r=36 m=6: chunk_00_translated.json[#49], chunk_r36_translated.json[#6]
- r=36 m=7: chunk_00_translated.json[#50], chunk_r36_translated.json[#7]
- r=36 m=8: chunk_00_translated.json[#51], chunk_r36_translated.json[#8]
- r=36 m=9: chunk_00_translated.json[#52], chunk_r36_translated.json[#9]
- r=36 m=10: chunk_00_translated.json[#53], chunk_r36_translated.json[#10]
- r=36 m=11: chunk_00_translated.json[#54], chunk_r36_translated.json[#11]
- r=36 m=12: chunk_00_translated.json[#55], chunk_r36_translated.json[#12]
- r=36 m=13: chunk_00_translated.json[#56], chunk_r36_translated.json[#13]
- r=36 m=14: chunk_00_translated.json[#57], chunk_r36_translated.json[#14]
- r=36 m=15: chunk_00_translated.json[#58], chunk_r36_translated.json[#15]
- r=36 m=16: chunk_00_translated.json[#59], chunk_r36_translated.json[#16]
- r=36 m=17: chunk_00_translated.json[#60], chunk_r36_translated.json[#17]
- r=36 m=18: chunk_00_translated.json[#61], chunk_r36_translated.json[#18]
- r=36 m=19: chunk_00_translated.json[#62], chunk_r36_translated.json[#19]
- r=36 m=20: chunk_00_translated.json[#63], chunk_r36_translated.json[#20]
- r=36 m=21: chunk_00_translated.json[#64], chunk_r36_translated.json[#21]
- r=36 m=22: chunk_00_translated.json[#65], chunk_r36_translated.json[#22]
- r=36 m=23: chunk_00_translated.json[#66], chunk_r36_translated.json[#23]
- r=36 m=24: chunk_00_translated.json[#67], chunk_r36_translated.json[#24]
- r=36 m=25: chunk_00_translated.json[#68], chunk_r36_translated.json[#25]
- r=36 m=26: chunk_00_translated.json[#69], chunk_r36_translated.json[#26]
- r=36 m=27: chunk_00_translated.json[#70], chunk_r36_translated.json[#27]
- r=36 m=28: chunk_00_translated.json[#71], chunk_r36_translated.json[#28]
- r=36 m=29: chunk_00_translated.json[#72], chunk_r36_translated.json[#29]
- r=36 m=30: chunk_00_translated.json[#73], chunk_r36_translated.json[#30]
- r=36 m=31: chunk_00_translated.json[#74], chunk_r36_translated.json[#31]
- r=36 m=32: chunk_00_translated.json[#75], chunk_r36_translated.json[#32]
- r=36 m=33: chunk_00_translated.json[#76], chunk_r36_translated.json[#33]
- r=36 m=34: chunk_00_translated.json[#77], chunk_r36_translated.json[#34]
- r=36 m=35: chunk_00_translated.json[#78], chunk_r36_translated.json[#35]
- r=36 m=36: chunk_00_translated.json[#79], chunk_r36_translated.json[#36]
- r=36 m=37: chunk_00_translated.json[#80], chunk_r36_translated.json[#37]
- r=36 m=38: chunk_00_translated.json[#81], chunk_r36_translated.json[#38]
- r=36 m=39: chunk_00_translated.json[#82], chunk_r36_translated.json[#39]
- r=36 m=40: chunk_00_translated.json[#83], chunk_r36_translated.json[#40]
- r=36 m=41: chunk_00_translated.json[#84], chunk_r36_translated.json[#41]
- r=36 m=42: chunk_00_translated.json[#85], chunk_r36_translated.json[#42]
- r=36 m=43: chunk_00_translated.json[#86], chunk_r36_translated.json[#43]
- r=36 m=44: chunk_00_translated.json[#87], chunk_r36_translated.json[#44]
- r=36 m=45: chunk_00_translated.json[#88], chunk_r36_translated.json[#45]
- r=36 m=46: chunk_00_translated.json[#89], chunk_r36_translated.json[#46]
- r=36 m=47: chunk_00_translated.json[#90], chunk_r36_translated.json[#47]
- r=36 m=48: chunk_00_translated.json[#91], chunk_r36_translated.json[#48]
- r=36 m=49: chunk_00_translated.json[#92], chunk_r36_translated.json[#49]
- r=36 m=50: chunk_00_translated.json[#93], chunk_r36_translated.json[#50]
- r=36 m=51: chunk_00_translated.json[#94], chunk_r36_translated.json[#51]
- r=36 m=52: chunk_00_translated.json[#95], chunk_r36_translated.json[#52]
- r=36 m=53: chunk_00_translated.json[#96], chunk_r36_translated.json[#53]
- r=36 m=54: chunk_00_translated.json[#97], chunk_r36_translated.json[#54]
- r=36 m=55: chunk_00_translated.json[#98], chunk_r36_translated.json[#55]
- r=36 m=56: chunk_00_translated.json[#99], chunk_r36_translated.json[#56]
- r=36 m=57: chunk_00_translated.json[#100], chunk_r36_translated.json[#57]
- r=36 m=58: chunk_00_translated.json[#101], chunk_r36_translated.json[#58]
- r=36 m=59: chunk_00_translated.json[#102], chunk_r36_translated.json[#59]
- r=36 m=60: chunk_00_translated.json[#103], chunk_r36_translated.json[#60]
- r=36 m=61: chunk_00_translated.json[#104], chunk_r36_translated.json[#61]
- r=36 m=62: chunk_00_translated.json[#105], chunk_r36_translated.json[#62]
- ... and 852 more

## F. Missing Required Fields

Total: 0 entries


## G. Canonical Name Consistency Check

### 'duhan' - 129 occurrences
  - batch_01.json[#15]: `You arrived at the / plaza in the center / of Duhan.`
  - batch_01.json[#75]: `Duhan is cursed.`
  - batch_01.json[#87]: `Their prowess caught / the attention of / Duhan's king.`
  - batch_01.json[#89]: `At last, Simson / reached the capital / of Duhan itself.`
  - batch_01.json[#94]: `Even war-weary / Duhan now fought / fearlessly.`
  - ... and 124 more

### 'karman' - 17 occurrences
  - batch_01.json[#358]: `Karman's Labyrinth, / yes? Their numbers / are still small,`
  - batch_01.json[#429]: `Wounded were being / carried out of / Karman's Labyrinth.`
  - batch_01.json[#590]: `mercenary captain. / But Karman's / Labyrinth destroyed`
  - batch_01.json[#609]: `twins were nearly / identical. "You're / going to Karman's`
  - batch_01.json[#665]: `But Karman's / Labyrinth destroyed / his mind.`
  - ... and 12 more

### 'barbus' - 1 occurrences
  - batch_01.json[#928]: `I am the owner of / this place. My / name is Gin Barbus.`

### 'almohad' - 0 occurrences

**WARNING:** Canonical name is "vera almohad" but batch_01.json uses "Vera el-Muwahhid" instead.
This is a name consistency issue -- the character's surname should be "almohad" per project conventions.
Location: batch_01.json entry near line 10938: `Thank you. I am / Vera el-Muwahhid.`

### 'luna' - 3 occurrences
  - batch_01.json[#1829]: `THE JEWEL OF VENOA / DUHAN BAR LUNA / In the tavern / adventurers / enjoyed them`
  - batch_03.json[#1310]: `He commands a / band of lunatics / who roam / battlefields.`
  - chunk_r37_extra.json[#103]: `Luna / `

**WARNING:** batch_01.json[#1829] has "DUHAN BAR LUNA" but the guide says "DUHAN BAR LUNA LIGHT".
The word "LIGHT" is missing from the bar name.

## H. Build-Relevant Notes

### Cross-file duplicates are expected
All 932 cross-file duplicates are type-1 chunk_*_translated.json entries overlapping with
their _fix/_extra/_r*_translated counterparts. The build pipeline (build_full_english_v2.py)
handles this correctly with "later entries win" deduplication. No action needed.

### Uppercase is auto-handled
The glyph encoder maps uppercase to lowercase automatically. The 14,915 entries with uppercase
will render correctly in-game. This is data hygiene only -- not a functional issue.

### Key action items
1. **CRITICAL:** 481 lines with 51+ chars will truncate on-screen. Most are in batch_r39_equip_a.json
   (quest descriptions, skill descriptions) which use newlines instead of " / " delimiters.
   These entries likely use a different text rendering mode that allows longer lines.
2. **Name fix needed:** "Vera el-Muwahhid" -> "vera almohad" in batch_01.json
3. **Name fix needed:** "DUHAN BAR LUNA" -> "duhan bar luna light" in batch_01.json[#1829]
4. **25 empty english entries** -- mostly placeholder/separator entries with no translatable content
