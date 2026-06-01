#!/usr/bin/env python3
"""
R39 Extra Data Patcher — Replaces ALL Japanese text in bytes 2702+ with English.

This patches the "extra data" section of 0039_type15.raw which contains:
  - Spell names (E2-E57)
  - Spell descriptions (E60-E115)
  - Combat skill names (E117-E155)
  - Allied action descriptions (E158-E194)
  - Allied action requirements (E195-E240)
  - Allied action UI messages (E242-E248)
  - Quest descriptions (E250-E283)
  - Quest NPC/location names (E286-E313)
  - Quest UI labels (E316-E344)
  - Quest title names (E347-E379)
  - SP effect messages (E382-E403)
  - Ability/sense names (E405-E425)
  - NPC/guild names (E428-E440)
  - Equipment/item category names (E443-E547)
  - Party rank messages (E549-E557)

Structural/lookup-table entries are preserved verbatim (E0, E58, E116, E156,
E241, E249, E284, E314, E345, E380, E404, E426, E441, E548).

Replacement is IN-PLACE: each entry's English text is encoded and padded/truncated
to exactly match the original glyph-slot capacity. FFFF delimiters are untouched.
"""

import struct, json, os, sys

BASE = 'C:/Programmieren/wizardrytranslation'
os.chdir(BASE)
sys.stdout.reconfigure(encoding='utf-8')

EXTRA_START = 2702

# Structural entries — DO NOT PATCH (lookup/index tables)
STRUCTURAL = {0, 58, 116, 156, 241, 249, 284, 314, 345, 380, 404, 426, 441, 548}

# ---------------------------------------------------------------------------
# Translation table: entry_index -> English text
# Use | for FFFE (line break within entry)
# Capacity constraints are enforced at write time (truncate + warn)
# ---------------------------------------------------------------------------
TRANSLATIONS = {
    # ===== SPELL NAMES (E2-E57) =====
    # These are Wizardry: Tale of the Forsaken Land / Busin 0 spell names
    2:  "Creta",
    3:  "Curdo",
    4:  "Teal",
    5:  "Analyze",
    6:  "Weak",
    7:  "Delay",
    8:  "Depth",
    9:  "Feeble",
    10: "Shulard",
    11: "Supreme",
    12: "Salome",
    13: "Escape",
    14: "Za Creta",
    15: "Za Curdo",
    16: "Za Teal",
    17: "Thru",
    18: "Za Lard",
    19: "Drain",
    20: "Repeal",
    21: "Cannibal",
    22: "Ja Creta",
    23: "Ja Curdo",
    24: "Ja Teal",
    25: "Late",
    26: "Ja Lard",
    27: "Valhalla",
    28: "Reflect",
    29: "Megadeth",
    30: "Feel",
    31: "Leap",
    32: "Bullets",
    33: "Thief Eye",
    34: "Yaiba",
    35: "Coat",
    36: "Bless",
    37: "Protect",
    38: "Amok",
    39: "Fields",
    40: "Poison",
    41: "Strain",
    42: "PoisCure",
    43: "ParaCure",
    44: "FearCure",
    45: "Vital",
    46: "Carcass",
    47: "Will",
    48: "Lumiel",
    49: "Undead",
    50: "Trans",
    51: "Recover",
    52: "Anchors",
    53: "Float",
    54: "Stigma",
    55: "Raphiel",
    56: "Offset",
    57: "Revive",

    # ===== SPELL DESCRIPTIONS (E60-E115) =====
    60: "Deal fire damage|to 1 enemy",
    61: "Deal curse damage|to 1 enemy",
    62: "Deal holy damage|to 1 enemy",
    63: "Check the status|of an enemy",
    64: "Raise or lower|1 enemy's ATK",
    65: "Raise or lower|1 enemy's AGI",
    66: "Raise or lower|1 enemy's EVA",
    67: "Raise or lower|1 enemy's RES",
    68: "Silence|1 enemy",
    69: "Put 1 enemy|to sleep",
    70: "Seal 1 enemy's|magic",
    71: "Flee from|battle",
    72: "Deal fire damage|to 1 group",
    73: "Deal curse damage|to 1 group",
    74: "Deal holy damage|to 1 group",
    75: "Monsters won't|appear briefly",
    76: "Silence|1 group",
    77: "Restore HP|to 1 ally",
    78: "Disarm a trap|on a chest",
    79: "Reflect physical|damage once",
    80: "Deal fire damage|to all enemies",
    81: "Deal curse damage|to all enemies",
    82: "Deal holy damage|to all enemies",
    83: "Attack 1 enemy|with RES power",
    84: "Silence|all enemies",
    85: "Cause an earthquake|at cost of 1 level",
    86: "Reflect magic|damage once",
    87: "Deal neutral dmg|to all enemies",
    88: "Restore HP|to 1 ally",
    89: "Teleport|to town",
    90: "Deal neutral dmg|to 1 enemy",
    91: "Check remaining|chests on floor",
    92: "Boost hit rate|and ATK, enable|striking undead",
    93: "Boost AGI|of 1 ally",
    94: "Boost EVA|of 1 ally",
    95: "Boost RES|of 1 ally",
    96: "Deal neutral dmg|to 1 group",
    97: "Restore HP|to 1 group",
    98: "Poison|1 group",
    99: "Paralyze 1 group|with magic",
    100: "Cure poison|for 1 ally",
    101: "Cure paralysis|for 1 ally",
    102: "Cure fear|for 1 ally",
    103: "Full stamina heal|and move freely",
    104: "Revive 1 ally|with full HP",
    105: "Restore HP and|status for 1 ally",
    106: "Dispel|Dark Fog",
    107: "Nullify dispel|against non-undead",
    108: "Teleport to|upstairs on floor",
    109: "Auto-heal HP|each turn",
    110: "Identify a used|item, but may|cause insanity",
    111: "Nullify damage|reduction briefly",
    112: "Deal neutral dmg|to all enemies",
    113: "Restore HP|to all allies",
    114: "Sacrifice self|to silence 1 foe",
    115: "Sacrifice self|to revive 1 ally",

    # ===== COMBAT SKILL NAMES (E117-E155) =====
    117: "None",
    118: "W-Slash",
    119: "StancSmash",
    120: "Hold Attack",
    121: "S.J.Attack",
    122: "SlayKrash",
    123: "CrossCageKl",
    124: "FrontGuard",
    125: "MagicShell",
    126: "AntiMagShel",
    127: "MirrorImage",
    128: "Brace-Front",
    129: "Brace-Back",
    130: "RevenFront",
    131: "RevenBack",
    132: "MagicCancel",
    133: "BrthCancel",
    134: "BackCover",
    135: "Intercept",
    136: "CastFocus",
    137: "BrkSilence",
    138: "MagicBoost",
    139: "MagicWeapon",
    140: "MagicCoOp",
    141: "FocusAtk",
    142: "BackAttack",
    143: "GaleSlash",
    144: "Rush",
    145: "GroupCast",
    146: "HolyCross",
    147: "WarpAttack",
    148: "SoulKrash",
    149: "SonicSword",
    150: "ElmntAtk",
    151: "FakeAttack",
    152: "Counterstk",
    153: "NtmrQuake",
    154: "WeakSmash",
    155: "DoublBreath",

    # ===== ALLIED ACTION DESCRIPTIONS (E158-E194) =====
    # These are 3-line descriptions with fixed 28-char lines padded with spaces
    # Use | for line breaks. Each line must fit in ~28 chars.
    158: "2 front members attack 1 foe|in sync for heavy damage.   |                            ",
    159: "Rear caster imbues weapon   |with magic for 1 hit. Can   |harm magic-resistant foes.   ",
    160: "Rear caster holds foe still |while front attacks once.    |Guaranteed hit if hold works.",
    161: "Rear caster launches front  |member airborne for a drop   |attack. Lowers foe's RES.   ",
    162: "2 adjacent front attack foe |from both sides. Guaranteed  |hit, but 1 attack each.     ",
    163: "2 rear hold foe and pull it |to front; 2 front strike.   |Strong vs low EVA/HP foes.  ",
    164: "All front brace to boost EVA|and RES. Also blocks status: |stun, para, poison, etc.    ",
    165: "2 rear focus magic to create|a barrier. Reduces magic dmg |and lowers resist failure.   ",
    166: "All rear focus to nullify   |all magic casting for both   |sides during the turn.       ",
    167: "All rear create duplicates  |of the whole party. Clones   |absorb hits, protecting you. ",
    168: "Party braces when breath is |used, reducing breath and    |magic dmg but boosting phys. ",
    169: "Party takes rear formation, |boosting EVA and RES vs phys.|But breath/magic dmg rises.  ",
    170: "When guarded front is hit,  |rear leaps in to block the  |attack. Triggers each hit.   ",
    171: "Before allies attack, all   |rear strike first, boosting  |the party's hit rate.        ",
    172: "When foe casts magic, rear  |interrupts with a strike to  |cancel it. Limited per turn. ",
    173: "When foe uses breath, rear  |interrupts with a strike to  |cancel it. Limited per turn. ",
    174: "When guarded rear is hit,   |front takes the blow instead.|Works vs ranged attacks too. ",
    175: "Lead front baits the foe,   |others flank and interrupt   |combos. Limited per turn.    ",
    176: "3 rear focus to expand magic|range. Also lowers foe's     |magic nullify and boosts you.",
    177: "All rear break enemy magic  |barriers. Cures party's      |Silence and dispels shields. ",
    178: "2 adjacent rear who share a |spell can cast it faster.    |Beats Anti-Magic Shell speed.",
    179: "Rear imbues ally weapon with|magic; if hit lands, breaks  |foe's shell and casts spell. ",
    180: "2 rear sync their magic to  |greatly boost spell power.   |                            ",
    181: "3 front chain-attack 1 foe. |Each successive hit deals    |less damage than the last.   ",
    182: "1 front baits the foe while |2 others flank from behind.  |Greatly boosts hit rate.     ",
    183: "Enhanced Focus Attack: 1st  |launches foe, then strikes   |on fall for heavy damage.    ",
    184: "Whole party charges for an  |area attack on all foes.     |Unblockable except by Guard. ",
    185: "2 front feint, 3rd drops    |from above on weak point.    |3rd gets big crit boost.     ",
    186: "2 front/rear draw a holy    |symbol for strong dispel.    |Very effective vs undead.    ",
    187: "1 rear opens a warp gate; 3 |front drop-attack from above.|Lowers foe RES; you're safe. ",
    188: "Enhanced Slay Krash: 2 rush |through foe and back. Deals  |double hits, slays undead.   ",
    189: "Enhanced W-Slash: 2 front   |swing to create shockwaves.  |Can hit adjacent enemies.    ",
    190: "3 front rush through all    |enemies in a line for heavy  |dmg but low accuracy.        ",
    191: "Enhanced Stance Smash: lead |feints to boost accuracy,    |then partner stuns the foe.  ",
    192: "Enhanced Back Attack with   |samurai skill for a stronger |counter that may paralyze.   ",
    193: "Enhanced S.J.A. with dark   |knight: slam weapon to shake |ground, damaging and stunning",
    194: "Enhanced Hold Attack with   |bishop: finds weakness while |holding for greater damage.  ",

    # ===== ALLIED ACTION REQUIREMENTS (E195-E240) =====
    195: "2 members",
    196: "1 member",
    197: "1 MP caster",
    198: "1 member",
    199: "1 MP caster",
    200: "1 member",
    201: "1 MP caster",
    202: "2 adjacent",
    203: "2 members",
    204: "2 MP casters",
    205: "2 or more",
    206: "2 MP casters",
    207: "3 MP casters",
    208: "3 MP casters",
    209: "2 or more",
    210: "2 or more",
    211: "1-2 members",
    212: "All members",
    213: "1-2 members",
    214: "2 members",
    215: "2 members",
    216: "3 members",
    217: "3 MP casters",
    218: "3 MP casters",
    219: "2 adj. w/ same spell",
    220: "1 caster + 1 melee",
    222: "2 MP casters",
    223: "3 members",
    224: "3 members",
    225: "4 or more",
    226: "3 members",
    227: "2 front/rear dispel",
    228: "3 members",
    229: "1 MP caster",
    230: "3 members",
    231: "3 members",
    232: "2 adjacent",
    233: "2 members",
    234: "1 member",
    235: "1 MP caster",
    236: "3 members",
    237: "1 member",
    238: "1 MP caster",
    239: "1 member",
    240: "1 MP caster",

    # ===== ALLIED ACTION UI (E242-E248) =====
    242: "None",
    243: "Removed all allied actions",
    244: "No allied actions are set",
    245: "Allied action settings reset",
    246: "Change squad and exit?",
    247: "Not enough AP",
    248: "Exit without changes? Are you sure?",

    # ===== QUEST DESCRIPTIONS (E250-E283) =====
    250: " ",
    251: "The temple would like to entrust you|with spreading Salem Church's|teachings far and wide.",
    252: "Vigor's shop is now hiring!|Only 1 position available.|Applicants should bring an|entry sheet to the store.",
    253: "To whoever reads this:|Come to the small room just|past the warp on B5 right now.|I'll put up a sign there.|Please hurry!",
    254: "I want to learn magic but|have no spell tome.|Without one I'll die.|Please give me a Creta tome.|I need it right now!",
    255: "Beat me at 5 rounds of|Jan-Ken and I'll give you|something good. Losers leap!|Entry fee: 1 temple per loss.|Confident? Meet me at B2.",
    256: "Duhan Guild has established|an adventurer aid fund.|Bring 5 allies to HQ and|everyone gets a special|bonus of 500g.",
    257: "Please take my dear,|precious Pippi to|basement floor 8.",
    258: "Reports say ancient elf|royal relics were found|in the dungeon. Check the|scrapyard on floor 3.|Could be useful for records.",
    259: "I'm so curious about the|tiny, cute pixies.|If you know all about them,|let's chat together!",
    260: "I owe the Ogre boss 20|medals and he's after me.|I'm in hiding.|Please give me some medals.|I want to stop running!",
    261: "The oh-so-sexy succubus...|Oh, I want to be teased.|Let's chat about her!",
    262: "As reward for this quest,|I'll give you some land.|Details only for those who|accept. Soldiers, please|refrain from applying.",
    263: "I'm stuck behind a|one-way passage!|Please help me!|I fell through a pit|on this floor.",
    264: "The magic room connecting|B4 and B1 is locked.|Ingo should have a key.|Go to his hideout on B4|and get it for me.",
    265: "You want the key I made?|I knew someone would ask!|But it ain't free.|Bring me 1 spare Small|Pedestal from my workshop.",
    266: "There's a shady adventurer|named Kunnal who's gone|missing. Could you find him|and tell him to come back?",
    267: "We're holding a Trap Game|Contest at the shop.|Enter if you're confident!|The champion gets|a rare item.",
    268: "I want to talk to the|succubus but she runs away.|Now's my chance!|Please catch the succubus|in front of me!",
    269: "The soldiers are conducting|level checks for registered|adventurers. It tests your|dungeon knowledge.|Accept the quest first.",
    270: "I'm Melanie, training to be|a knight, and my manager|Milli. We want to join a|party with spellcasters|to learn lots of magic!",
    271: "Please find my body.|Long ago I snuck into a|suspicious church alone|and was killed by a|scary-faced priest.",
    272: "I dropped my precious|treasure chest in a scary|room on B1. I'll give you|something nice if you|bring it back!",
    273: "Duhan Merchant Guild's|Kalman tour guide suddenly|quit. We need a replacement.|Experienced dungeon|explorers, please apply!",
    274: "To walk the way of the|samurai, I need armor made|by a master craftsman.|Could someone get one?",
    275: "I finally got the armor.|But I still need more to|find new enlightenment.|Could you temper it in the|dungeon's lava?",
    276: "I poured dungeon magic into|the armor and tempered it|rigorously, but something's|still missing. I want to|observe foreign combat.",
    277: "Could you mix my secret|potion into the spring|water on B1?",
    278: "Could you mix my secret|potion into the spring|water on B2?",
    279: "I have one more potion|but no use for it.|There's a fountain on B6.|Wouldn't it be great if|it could heal you?",
    280: "I've never seen someone|possessed by a death god.|Go into the dungeon, get|possessed, and come back|to HQ alive.",
    281: "My underling disappeared.|An orc named Casta.|Please find him.|He's probably hiding in a|locked room on B5!",
    282: "Punish the mean adventurer|who punched me!|He was examining a strange|statue on the 5th floor,|in the NW room.",
    283: "There's a room with a big|water jug on B10 but I|don't know where it is.|Take me there so I can|go back to my own time.",

    # ===== QUEST NPC/LOCATION NAMES (E286-E313) =====
    286: "Fuke",
    287: "Lucy",
    288: "Orogad",
    289: "Milli",
    290: "Jan-Ken Man",
    291: "Duhan Chief",
    292: "Angus",
    293: "Guillaume",
    294: "Yoppen",
    295: "Poor Little Imp",
    296: "Ingo",
    297: "Contest Over",
    298: "Romi",
    299: "Popo",
    300: "Merchant Gld",
    301: "Fudo",
    302: "Lang",
    303: "??? heads to the spring ",
    304: "HQ",
    305: "Scone",
    306: "Survey Limit",
    307: "Rogue heads to B5 ",
    308: "Soldiers",
    309: "Quest time expired ",
    310: "Liddy",
    311: "Vago",
    312: "Casta",
    313: "Shadows target Jan-Ken Man! ",

    # ===== QUEST UI LABELS (E316-E344) =====
    316: "Accept this quest?",
    317: "Abandon this quest?",
    318: "Abandoning lowers trust.|Are you sure?",
    319: "Yes",
    320: "No",
    321: "Client",
    322: "Reward",
    323: "Deadline",
    324: "From acceptance",
    325: "days",
    326: "Can't accept more",
    327: "None",
    329: "Quest Done",
    330: "Quest Failed",
    331: "Quest Clear",
    332: "Citizen Quest",
    333: "Adventurer Quest",
    334: "Underworld Quest",
    335: "Order",
    336: "Quest",
    337: "No quests accepted",
    338: "No orders accepted",
    339: "Left:",
    340: "Overdue",
    341: "In Progress",
    342: "In Progress",
    343: "Acceptable",
    344: "Completed",

    # ===== QUEST TITLE NAMES (E347-E379) =====
    347: "Salem Missionary Work",
    348: "Now Hiring! ",
    349: "Come to B5! ",
    350: "Creta Tome Wanted",
    351: "Jan-Ken Masters! ",
    352: "Adventurer Aid",
    353: "Take Care of Pippi",
    354: "Ancient Royal Relics",
    355: "About Pixies",
    356: "Give Me Medals!",
    357: "Succubus Fan Club",
    358: "Land For You",
    359: "Somebody Help Me! ",
    360: "I Want Ingo's Key",
    361: "If You Want the Key!",
    362: "Find Kunnal",
    363: "Trap Game Contest",
    364: "Catch the Succubus",
    365: "Dungeon Survey",
    366: "Join Our Party! ",
    367: "Find My Body!",
    368: "Find My Lost Item",
    369: "Kalman Guide Wanted ",
    370: "Need Master Armor",
    371: "Temper My Armor",
    372: "Show Me Real Combat",
    373: "Healing Fountain",
    374: "Healing Fountain 2",
    375: "Healing Fountain 3",
    376: "Meet a Possessed One",
    377: "Find My Underling",
    378: "Punish the Bully!",
    379: "Take Me to the Jug",

    # ===== SP EFFECT MESSAGES (E382-E403) =====
    382: "Party MP fully restored|SP activated ",
    383: "Party HP fully restored|SP activated ",
    384: "Max HP increased|SP activated ",
    385: "STR increased|SP activated ",
    386: "INT increased|SP activated ",
    387: "PIE increased|SP activated ",
    388: "VIT increased|SP activated ",
    389: "AGI increased|SP activated ",
    390: "LUK increased|SP activated ",
    391: "Dead ally revived|SP activated ",
    392: "Alignment to Good|SP activated ",
    393: "Alignment to Neutral|SP activated ",
    394: "Alignment to Evil|SP activated ",
    395: "Trust increased|SP activated ",
    396: "EXP increased|SP activated ",
    397: "Allied skill up|SP activated ",
    398: "Automata EXP up|SP activated ",
    399: "Uses restored|SP activated ",
    400: "Weapon ATK up|SP activated ",
    401: "RES increased|SP activated ",
    402: "Party status healed|SP activated ",
    403: "Death god vanished|SP activated ",

    # ===== ABILITY/SENSE NAMES (E405-E425) =====
    405: "None",
    406: "Magic: Sorc.",
    407: "Magic: Priest",
    408: "Natural Pwr",
    409: "Dark Pwr",
    410: "Good Arms",
    411: "Charm",
    412: "Foresight",
    413: "Danger Sense",
    414: "Accuracy Sns",
    415: "Weak Pt Sns",
    416: "Thief's Eye",
    417: "Body Sense",
    418: "Auto Heal",
    419: "Charisma",
    420: "Perception",
    421: "Weapon Sense",
    422: "Combat Sense",
    423: "Magic Sense",
    424: "Status Cure",
    425: "RES Sense",

    # ===== NPC/GUILD NAMES (E428-E440) =====
    428: "Vigor's Shop",
    429: "Milli",
    430: "Motchi",
    431: "Notchi",
    432: "Kunnal",
    433: "Melanie",
    434: "Liddy",
    435: "Lucy",
    436: "Yoppen",
    437: "Adv. Guild",
    438: "Adv. Guild",
    439: "Duhan Guild",
    440: "Soldiers",

    # ===== EQUIPMENT/ITEM CATEGORY NAMES (E443-E547) =====
    443: "Weapon",
    444: "Heal Weapon",
    445: "Regen Weapon",
    446: "Status Weapon",
    447: "Cursed Weapon",
    448: "Armor",
    449: "Heal Armor",
    450: "Regen Armor",
    451: "Status Armor",
    452: "Cursed Armor",
    453: "Accessory",
    454: "Heal Accessory",
    455: "Regen Accessory",
    456: "Status Accessory",
    457: "Cursed Accessory",
    458: "Item",
    459: "Spell Tome",
    460: "Sorc. Tome",
    461: "Priest Tome",
    462: "Automata Chip",
    463: "Heal Chip",
    464: "Regen Chip",
    465: "Equipment",
    466: "Heal Equip",
    467: "Regen Equip",
    468: "Status Equip",
    469: "Cursed Equip",
    470: "Dagger",
    471: "ShortSword",
    472: "LongSword",
    473: "GreatSword",
    474: "Katana",
    475: "Axe",
    476: "2H Sword",
    477: "2H Axe",
    478: "Spear",
    479: "Mace",
    480: "Flail",
    481: "Throw Dagger",
    482: "Crossbow",
    483: "Longbow",
    484: "Whip",
    485: "Poleaxe",
    486: "Glove",
    487: "?S.Armor",
    488: "?Shield",
    489: "?Katana",
    490: "?Axe",
    491: "?2H Weapon",
    492: "?Weapon",
    493: "?Mace",
    494: "?Flail",
    495: "?Wand",
    496: "?Staff",
    497: "Robe",
    498: "Helm",
    499: "Shield",
    500: "Gauntlet",
    501: "?Robe",
    502: "?Helm",
    503: "?Shield",
    504: "?Gauntlet",
    505: "Gem",
    506: "Talisman",
    507: "Ornament",
    508: "Crystal",
    509: "Boots",
    510: "Mantle",
    511: "?Gem",
    512: "?Talisman",
    513: "?Ornament",
    514: "?Crystal",
    515: "?Boots",
    516: "?Mantle",
    517: "Hand Chip",
    518: "?Hand Chip",
    519: "Body Chip",
    520: "?Body Chip",
    521: "Arm Chip",
    522: "?Arm Chip",
    523: "Leg Chip",
    524: "?Leg Chip",
    525: "Brain Chip",
    526: "?Brain Chip",
    527: "Lv1 Tome",
    528: "Lv2 Tome",
    529: "Lv3 Tome",
    530: "Lv4 Tome",
    531: "Lv5 Tome",
    532: "Lv6 Tome",
    533: "Lv7 Tome",
    534: "Lv1 Sorc Tome",
    535: "Lv2 Sorc Tome",
    536: "Lv3 Sorc Tome",
    537: "Lv4 Sorc Tome",
    538: "Lv5 Sorc Tome",
    539: "Lv6 Sorc Tome",
    540: "Lv7 Sorc Tome",
    541: "Lv1 Prst Tome",
    542: "Lv2 Prst Tome",
    543: "Lv3 Prst Tome",
    544: "Lv4 Prst Tome",
    545: "Lv5 Prst Tome",
    546: "Lv6 Prst Tome",
    547: "Lv7 Prst Tome",

    # ===== PARTY RANK MESSAGES (E549-E557) =====
    549: "None",
    550: "Party rank is now |<Rank>|. |<AA> can no longer be used. |",
    551: "<AA> can no longer be used ",
    552: "Party rank |<Rank>| recovered",
    553: "Party rank triggered ",
    554: "Party rank expired |<AA> can no longer be used |",
    555: "|Allied Points| increased ",
    556: "|Allied Points| decreased ",
    557: "|Some of <AA> was removed |",
}

# ---------------------------------------------------------------------------
# 1. Load binary and glyph table
# ---------------------------------------------------------------------------
raw = bytearray(open('extracted/packdata_raw/0039_type15.raw', 'rb').read())
assert len(raw) == 26624, f"Unexpected R39 size: {len(raw)}"

glyph_table = json.load(open('data/english_glyph_table.json', encoding='utf-8'))

def encode_english(text):
    """Encode English text to list of BE uint16 glyph IDs. | = FFFE line break."""
    parts = text.split('|')
    glyphs = []
    for pi, part in enumerate(parts):
        if pi > 0:
            glyphs.append(0xFFFE)
        for ch in part:
            if ch in glyph_table:
                glyphs.append(int(glyph_table[ch]))
            elif ch.lower() in glyph_table:
                glyphs.append(int(glyph_table[ch.lower()]))
            elif ch == ' ':
                glyphs.append(0)  # space
            else:
                glyphs.append(31)  # '?' fallback
    return glyphs

# ---------------------------------------------------------------------------
# 2. Parse extra-data entries (FFFF-delimited)
# ---------------------------------------------------------------------------
pos = EXTRA_START
entry_regions = []  # (start_byte, end_byte) for each entry
current_start = pos

while pos < len(raw) - 1:
    val = struct.unpack_from('>H', raw, pos)[0]
    if val == 0xFFFF:
        entry_regions.append((current_start, pos))
        pos += 2
        current_start = pos
    else:
        pos += 2

if current_start < len(raw):
    entry_regions.append((current_start, pos))

print(f"R39 extra data: {len(entry_regions)} FFFF-delimited entries")
print(f"Translations defined: {len(TRANSLATIONS)}")
print(f"Structural (skipped): {len(STRUCTURAL)}")

# ---------------------------------------------------------------------------
# 3. In-place replacement
# ---------------------------------------------------------------------------
out = bytearray(raw)
replaced = 0
truncated = 0
skipped_structural = 0

for idx, (start, end) in enumerate(entry_regions):
    if idx in STRUCTURAL:
        skipped_structural += 1
        continue
    if idx not in TRANSLATIONS:
        continue

    en_text = TRANSLATIONS[idx]
    en_glyphs = encode_english(en_text)
    capacity = (end - start) // 2  # available glyph slots

    if len(en_glyphs) > capacity:
        print(f"  WARN: E{idx} truncated: {len(en_glyphs)} -> {capacity} "
              f"('{en_text[:40]}...')")
        en_glyphs = en_glyphs[:capacity]
        truncated += 1

    # Write English glyphs
    write_pos = start
    for g in en_glyphs:
        struct.pack_into('>H', out, write_pos, g)
        write_pos += 2

    # Pad remaining with 0x0000 (space)
    while write_pos < end:
        struct.pack_into('>H', out, write_pos, 0x0000)
        write_pos += 2

    replaced += 1

print(f"Replaced: {replaced} entries ({truncated} truncated)")
print(f"Structural skipped: {skipped_structural}")

# ---------------------------------------------------------------------------
# 4. Sanity checks
# ---------------------------------------------------------------------------
# Verify bytes before EXTRA_START are untouched
assert out[:EXTRA_START] == raw[:EXTRA_START], "Pre-extra bytes changed!"

# Count FFFF delimiters in extra region
orig_ffff = 0
new_ffff = 0
for i in range(EXTRA_START, len(raw) - 1, 2):
    if struct.unpack_from('>H', raw, i)[0] == 0xFFFF:
        orig_ffff += 1
    if struct.unpack_from('>H', out, i)[0] == 0xFFFF:
        new_ffff += 1
assert orig_ffff == new_ffff, f"FFFF count changed: {orig_ffff} -> {new_ffff}"
print(f"Sanity: FFFF count preserved ({orig_ffff}), pre-extra bytes unchanged")

# ---------------------------------------------------------------------------
# 5. Write output
# ---------------------------------------------------------------------------
os.makedirs('build/packdata_resources', exist_ok=True)
output = bytes(out)
# Pad to sector boundary
pad = (2048 - len(output) % 2048) % 2048
output += b'\x00' * pad

with open('build/packdata_resources/0039_type15.raw', 'wb') as f:
    f.write(output)
print(f"Written {len(output)} bytes to build/packdata_resources/0039_type15.raw")

# ---------------------------------------------------------------------------
# 6. Verification: scan output for remaining JP
# ---------------------------------------------------------------------------
remaining_jp = 0
for idx, (start, end) in enumerate(entry_regions):
    if idx in STRUCTURAL:
        continue
    for p in range(start, end, 2):
        gid = struct.unpack_from('>H', out, p)[0]
        if gid > 94 and gid not in (0xFFFE, 0xFFFD, 0xFFFF):
            remaining_jp += 1
            break

if remaining_jp > 0:
    print(f"\nWARNING: {remaining_jp} non-structural entries still have JP glyphs!")
    for idx, (start, end) in enumerate(entry_regions):
        if idx in STRUCTURAL:
            continue
        has = False
        for p in range(start, end, 2):
            gid = struct.unpack_from('>H', out, p)[0]
            if gid > 94 and gid not in (0xFFFE, 0xFFFD, 0xFFFF):
                has = True
                break
        if has:
            print(f"  E{idx} still has JP")
else:
    print("\nAll non-structural entries are now English!")
