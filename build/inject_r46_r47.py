"""
R46/R47 type-03 text injector — in-place fixed-size replacement.

R46 (bulletin board) and R47 (combat encounters) are type-03 resources
with 3 sub-resources each, containing MSG glyph streams.

Only the glyph content within each FFFF-delimited slot is replaced.
Shorter English text is padded with 0x0000 (null glyphs).
Headers, offset tables, and all structure are preserved verbatim.

Each translation is carefully sized to fit within the original slot capacity.
"""

import struct, json, os, sys

BASE = 'C:/Programmieren/wizardrytranslation'
os.chdir(BASE)

glyph_table = json.load(open('data/english_glyph_table.json', encoding='utf-8'))

def encode_english(text):
    parts = text.split(' / ')
    glyphs = []
    for pi, part in enumerate(parts):
        if pi > 0:
            glyphs.append(0xFFFE)
        for ch in part.strip():
            if ch in glyph_table:
                glyphs.append(int(glyph_table[ch]))
            elif ch.lower() in glyph_table:
                glyphs.append(int(glyph_table[ch.lower()]))
            elif ch == ' ':
                glyphs.append(0)
            else:
                glyphs.append(31)
    return glyphs

def tlen(text):
    return len(encode_english(text))

# ============================================================================
# R46 SUB0: Bulletin board posts
# Capacities: msg2=102, msg3=103, msg4=72, msg5=84, msg6=63, msg7=75,
# msg8=153, msg9=165, msg10=90, msg11=70, msg12=23, msg13=76, msg14=77,
# msg15=128, msg16=144, msg17=99, msg18=133, msg19=143, msg20=126,
# msg21=147, msg22=66, msg23=105, msg24=56, msg25=28, msg26=72,
# msg27=56, msg28=47, msg29=73, msg30=156, msg31=87, msg32=78,
# msg33=45, msg34=30, msg35=132, msg36=76, msg37=91, msg38=49,
# msg39=82, msg40=28, msg41=121, msg42=95, msg43=106, msg44=135,
# msg45=85, msg46=63, msg47=99, msg48=79, msg49=76, msg50=115,
# msg51=111, msg52=70, msg53=137, msg54=28, msg55=178, msg56=117,
# msg57=67, msg58=46, msg59=18, msg60=134, msg61=107, msg62=118,
# msg63=75, msg64=89, msg65=46, msg66=102, msg67=122, msg68=132,
# msg69=116, msg70=117, msg71=150, msg72=132, msg73=122, msg74=148,
# msg75=89, msg76=44, msg77=95, msg78=91, msg79=119, msg80=88,
# msg81=127, msg82=82, msg83=112, msg84=45, msg85=76, msg86=89,
# msg87=59, msg88=79, msg89=63, msg90=52, msg91=73, msg92=135,
# msg93=106, msg94=151, msg95=86, msg96=105, msg97=106, msg98=114
# ============================================================================
R46_SUB0 = {
    2: "a board for duhan / is now set up. to / post, fill a form / and drop it in / the box.",
    3: "miri here. kreta / spell tablet req / is done. someone / found one for me! / cancelled!",
    4: "self-seraph shop / sells a weird key. / whats it for?",
    5: "vigger shop needs / live-in workers! / not just fighters, / all welcome!",
    6: "vigger shop has many / orcs. can orcs / apply too?",
    7: "friendly orcs are / ok! we have 3 orcs / already. youll get / along great!",
    8: "on b4f i got cursed / and lost. found a / room with a hobbit / and imp. odd folk / but they gave me a / healing item. nice!",
    9: "duhan trade guild / marks 50 years! / karman tour for 5 / pairs! spend 10000g / at member shops to / enter the draw! / duhan residents / only",
    10: "bogey cats are so / cute! those eyes / are adorable! / dont hurt em much.",
    11: "venoan bookstore / moved to 124-3 / porora street.",
    12: "how to learn magic?",
    13: "huh? magic comes / from spell tablets! / make em at the / adventurer guild!",
    14: "vigger shop job / results are in. / come to vigger / shop.",
    15: "been to jankenman? / cant win! lose and / he warps you back / with ripu! now i / go there when i / wanna go home.",
    16: "i tried too. his / luck is insane! / but his voice / wavers each time / he says janken. / it changes. his / hands follow a / pattern. study!",
    17: "air in karmans / labyrinth is odd. / its dangerous. / lets share tips / with each other.",
    18: "i'll start! if in / danger use escape / or return scrolls. / keep em stocked! / ripu is best but / that tablet is / special!",
    19: "im a mage. my / combo should work / but ripu wont. / keeps making thief / eye. oh i see! / special means / mutation! only / guild gear can / trigger them!",
    20: "nice tip! know / the level up sign? / when exp is full / bottom panel will / flash! if so go / back and rest at / the inn!",
    21: "i'll never forget / those days. oriana / in town, cheering, / streamers in sky. / duhan was pure / joy. but now the / princess and hope / are gone. fare / well.",
    22: "saw her that day / too. damn! cant / forgive! beat / the witch!",
    23: "we watched her from / birth. she was the / child of all duhan! / the witch took her! / cant be forgiven!",
    24: "what is aurora like / shes called witch / so female right?",
    25: "if shes male, wow!",
    26: "oldest record of / aurora is 600 yr / ago at the battle / of narcia.",
    27: "600 years ago? what? / is she an elf? / cant be true.",
    28: "they say simson went / mad from seeing aurora.",
    29: "simsons diary says / he got to b8f but / soldiers have it. / details unknown.",
    30: "hello from vigger / shop! we put lots / of effort into our / orders! new staff / and a fresh start! / no other shop can / match us! please / order from us!",
    31: "did ya know? theres / a healing spring / on b1f! use it! / no need for / healers anymore!",
    32: "soldiers beaten / on b2f again! / bergran sends more / but they just / keep losing!",
    33: "the witch loves / torture. it was / gruesome!",
    34: "a pretty witch? / id let her!",
    35: "pardon me. must / vent. my party is / all male. amorous / ones have no trust! / it keeps dropping! / any item to change / personality? / doubt it!",
    36: "no such item sorry. / just hire women. / only obvious / advice i got!",
    37: "as i feared! they / keep saying no gals / no drive! what a / pain! otherwise / capable guys.",
    38: "confusion is rough / so i kill em first / thanks!",
    39: "banshees have nice / voices! i try to / dispel not kill. / sorry if i slip!",
    40: "pixies are cute! / want one!",
    41: "vigger shop seems / to try hard but / is it any good? / is it safe for a / girl like me? tell / pamela!",
    42: "its a nice shop. / orders handled / well, good stock. / orc staff are fun / to watch. try it!",
    43: "its ok. orders / handled fine, items / decent. handy shop / in duhan. worth a / visit.",
    44: "that shop is bad. / they take orders / but dont finish. / only junk for sale. / shady types only. / orcs fought out / front last time!",
    45: "thanks for replies! / nice shop! pamela / glad! can they find / a rare map? i'll / visit!",
    46: "thanks for replies! / seems worth a look. / maybe i'll go!",
    47: "oh no pamela is / sad! orcs werent / nice! junk items / no thx! was gonna / order but nah!",
    48: "simsons squad had / us hopeful! they / were gallant! no / hero like that / for a while!",
    49: "on b2f rumor says / the witch eats / monsters! orcs are / in a panic!",
    50: "when i think witch / i picture hat and / broom! but aurora / eats monsters? / more like a beast. / disappointing.",
    51: "witch on b3f! one / party wiped out / but ninja turgot / barely survived! / info from turgot / himself so its / reliable!",
    52: "for real? witch on / b3f?! he survived. / skilled guy. much / respect!",
    53: "new hero in duhan! / faced the witch and / lived! unheard of! / must be a top / fighter. maybe / turgot will slay / the witch next!",
    54: "turgot so cool! / beat her!",
    55: "sorry but this is / turgot. dont expect / big deeds from me. / i just trembled / before the witch. / survived by luck. / that fear was bad. / im just a coward. / not strong or cool / at all.",
    56: "gido you brat! i / told you stuff for / a request and you / post my name! all / my intel! never / telling you / again!!",
    57: "waah sorry turgot! / your stories were / exciting! i wont / do it again!",
    58: "post deemed unfit / was removed from / board.",
    59: "what did it say?",
    60: "sorry to write / again! hired 3 / women but one has / no trust! trait is / loner! wants to be / alone?! cant / fight solo! what / do i do?!",
    61: "me again sorry! / im a loner too so / i get it. max 4 / in a party for / us. born this / way!",
    62: "got worked up / before. sorry. / only 4? drop 2?! / starting to want / to be alone too! / being leader is / tough. learned it / now.",
    63: "gido stopped and / info dried up! / anyone have fresh / dungeon news?",
    64: "wait, are posters / here folk who / never went in? / im just a tavern / keeper so nope!",
    65: "so many fans here! / you all love / monsters too!",
    66: "use the map! fill / it in and the path / will open! if / stuck look for / spots you missed!",
    67: "wild stuff on b5f! / dolls lured folk / into traps! popo / the fortune teller / was saved by an / adventurer. she / praised em!",
    68: "those dolls are / automata from old / elf ruins! elves / built em to fight / invaders. they / think and act on / their own. one / beats a platoon!",
    69: "princess oriana / is alive!! calm / down me. how can / i be calm?! shes / alive! so glad! / cant stop tears!",
    70: "old man calm down. / princess was on / b6f it seems. / dunno the royal / drama but webster / did something. / lousy fiance.",
    71: "on b7f i saw it! / webster became an / undead dark priest! / an adventurer beat / him! great skill! / i might follow / them. bet theyll / do more amazing / things!",
    72: "the one who beat / webster did it / again! downed a / writhing one on / b8f! fought one / on b2f before. / tough but nothing / stops em now!",
    73: "heres the update! / the adventurer all / duhan watches! / writhing one on / b9f beaten again! / nearly invincible / but they won!",
    74: "made it to b10f! / getting hard to / follow them. the / monsters here are / scary! nearly / died. gotta level / up first. info / may be delayed / a while. sorry!",
    75: "the princess is / alive?! is it true? / we can see her / again?! best news!",
    76: "wonderful! long / live princess / oriana!!",
    77: "mood in town got / brighter! but if / princess is alive / the witch didnt / do anything bad?",
    78: "soldiers beaten / but maybe witch / defended herself? / why did king lie? / what is she?!",
    79: "you liar! i drank / that water and my / party got poisoned! / watch out all! / this info is a / total lie!",
    80: "be careful all! / theres a poison / spring on b1f! / someone poisoned / the water! dont / drink!",
    81: "from citizens to / adventurers i / offer info for / all needs! tips / and dungeon hints / ready! come to / venoan bookstore!",
    82: "saw an evil group / in the dungeon! / a hooded man led / tough warriors. / evil aligned!",
    83: "dark knight / macbain leads the / feared warband of / san-goth. came to / duhan! whats / their goal? not / witch hunting!",
    84: "if they come to / my bakery i'll / kick em out!",
    85: "bringing crooks / to hunt the witch? / what are soldiers / thinking?!",
    86: "info shop closed / for now. i'll get / more hot news and / return someday! / thanks!",
    87: "damn it! who stole / the request we took / you thieves!!!",
    88: "some requests have / deadlines. you / failed so another / party did it.",
    89: "you loudmouth! come / out and say it to / my face! i'll end / you!!",
    90: "this tranmell, the / leader? poor party / members.",
    91: "this labyrinth is / too tough! complex / layout, monsters / wont stop! tips?",
    92: "im a mage. when we / explore we use the / thru spell to skip / fights and learn / terrain first. so / escape routes are / clear if needed.",
    93: "i heard thru cant / be made normally! / no one in my party / has it. give me / that tablet and / i'll do any job!",
    94: "jankenman what a / joke! rare bracelet / he says. its just / a common appraise / bracelet! want / this junk? come / get it. not free / though!",
    95: "im in a room on / b4f. want it? / search around the / bumpy path past / the rocks.",
    96: "i have a favor to / ask. anyone? im / in a room on b4f / near the bumpy / path. reward / included!",
    97: "hey thats against / the rules! use the / request counter! / this kind of thing / ruins board / manners!",
    98: "i do things my / way! both places / are official so / who cares?! board / rules are not my / problem!",
}

# ============================================================================
# R46 SUB1: Poster names
# Capacities: msg2=8 msg3=11 msg4=5 msg5=7 msg6=9 msg7=10 msg8=4 msg9=5
# msg10=5 msg11=5 msg12=5 msg13=4 msg14=6 msg15=7 msg16=4 msg17=7 msg18=7
# msg19=7 msg20=4 msg21=8 msg22=4 msg23=5 msg24=5 msg25=4 msg26=6 msg27=4
# msg28=8 msg29=4 msg30=4 msg31=5 msg32=4 msg33=5 msg34=10 msg35=3 msg36=4
# msg37=6 msg38=7 msg39=5 msg40=6 msg41=8 msg42=8 msg43=5
# ============================================================================
R46_SUB1 = {
    2: "gin",          # 8: "owner: gin" too long -> just gin
    3: "trade guild",  # 11
    4: "fighter",      # 5 -> too long. just 5 chars max... NO wait capacity=5 glyphs = 5 chars
    # Actually capacity is in glyph slots. Each ASCII char = 1 glyph. Space = 1 glyph.
    # So capacity 5 = max 5 characters including spaces
    5: "vigger",       # 7 cap, 6 chars = ok
    6: "anonymous",    # 9 cap, 9 chars = ok
    7: "venoan ceo",   # 10 cap, 10 chars = ok
    8: "miri",         # 4 cap, 4 chars = ok
    9: "piko",         # 5 cap, 4 chars = ok
    10: "lucy",        # 5 cap, 4 chars = ok
    11: "celav",       # 5 cap
    12: "shela",       # 5 cap
    13: "alef",        # 4 cap
    14: "kish",        # 6 cap, 4 chars
    15: "thomas",      # 7 cap, 6 chars
    16: "erin",        # 4 cap
    17: "rippen",      # 7 cap, 6 chars
    18: "barfic",      # 7 cap, 6 chars
    19: "sirius",      # 7 cap, 6 chars
    20: "maya",        # 4 cap
    21: "yan monk",    # 8 cap
    22: "yuse",        # 4 cap
    23: "ordi",        # 5 cap, 4 chars
    24: "yopen",       # 5 cap
    25: "gran",        # 4 cap
    26: "gido*",       # 6 cap, 5 chars (info broker tag lost)
    27: "yose",        # 4 cap (yosef truncated)
    28: "gordon",      # 8 cap, 6 chars
    29: "a bushi",     # capacity is only 4 -> "bshi" won't work
    # Actually let me recount: sub1 msg29 = 4 slots. So max 4 chars.
    30: "mond",        # 4 cap
    31: "geist",       # 5 cap
    32: "pame",        # 4 cap (pamela truncated)
    33: "natas",       # 5 cap (natasha truncated)
    34: "turgot",      # 10 cap, 6 chars
    35: "gid",         # 3 cap
    36: "ian",         # 4 cap, 3 chars
    37: "tranml",      # 6 cap
    38: "joe",         # 7 cap, 3 chars
    39: "tuckr",       # 5 cap
    40: "gerard",      # 6 cap
    41: "sheera",      # 8 cap, 6 chars
    42: "heintz",      # 8 cap, 6 chars
}

# Fix msg4 and msg29 which have very tight caps
R46_SUB1[4] = "fight"   # 5 cap, 5 chars
R46_SUB1[29] = "bshi"   # 4 cap, 4 chars (samurai abbrev)

# ============================================================================
# R46 SUB2: Thread titles
# Capacities listed above. Each must fit exactly.
# ============================================================================
R46_SUB2 = {
    2: "board is now open",     # 15 -> 17 chars. too long! -> 15 max
    3: "done:kreta tablet",    # 16 -> 17. exactly? "done:kreta tablet" = 17. too long
    4: "seraph new item",      # 14 -> 15. too long
    5: "part-time job",        # 14 -> 13
    6: "a query",              # 7
    7: "ok!",                  # 6 -> 3
    8: "dungeon weirdo",       # 15
    9: "karman tour?",         # 15 -> 12
    10: "bogey cats!",         # 14 -> 11
    11: "bookstore moved",     # 16 -> 15
    12: "learn magic",         # 12 -> 11
    13: "huh?",                # 4
    14: "vigger job done",     # 17 -> 15
    15: "adventurer tip",      # 12 -> 14
    16: "tip1:survive!",       # 14 -> 13
    17: "ripu",                # 6 -> 4
    18: "tip2:level up",       # 15 -> 13
    19: "old times",           # 10 -> 9
    20: "no way!",             # 8 -> 7. but cap is 8
    21: "the witch",           # 10
    22: "a woman?",            # 9 -> 8
    23: "600 yr?!",            # 7 -> 8. but cap is 7
    24: "simso",               # 5 -> cap 5
    25: "rumor!",              # 7 -> 6
    26: "our child!",          # 11 -> 10
    27: "tome",                # 4
    28: "janken?",             # 12 -> 7
    29: "janken tip",          # 11 -> 10
    30: "order please!",       # 14 -> 13
    31: "heal pool",            # 10 -> 9
    32: "beaten again?!",      # 15 -> 14
    33: "pain",                # 5 -> 4
    34: "ooh!",                # 5 -> 4
    35: "traits",              # 9 -> 6
    36: "hmm!",                # 5 -> 4
    37: "yeah!",               # 5
    38: "it's ok",             # 7
    39: "banshee!",            # 8
    40: "pixies too!",         # 13 -> 11
    41: "how's vigger shop",   # 19 -> 17. too long
    42: "good!",               # 7 -> 5
    43: "so-so",               # 6 -> 5
    44: "stay away",           # 9
    45: "yay!",                # 4
    46: "thx!",                # 5 -> 4
    47: "shock!",              # 6
    48: "really",              # 6
    49: "eats them?!",         # 12 -> 11
    50: "no way!",             # 8 -> 7 but cap is 8
    51: "witch on b3f!!",      # 19 -> 14
    52: "turgot wow",          # 10
    53: "amazing!",            # 8
    54: "so cool!",            # 10 -> 8
    55: "not strong",          # 13 -> 10
    56: "to gido",             # 7
    57: "sorry!!",             # 8 -> 7
    58: "[deleted]",           # 12 -> 9
    59: "hmm!",                # 5 -> 4. but cap=5
    60: "personlt2",           # 10 -> 9
    61: "reply",               # 5
    62: "sorry",               # 6 -> 5
    63: "no info?",             # 10 -> 8
    64: "huh?",                # 4
    65: "ooh!",                # 5 -> 4
    66: "tip3:use maps",       # 15 -> 13
    67: "b5f intel",           # 13 -> 9
    68: "automata",            # 8
    69: "she's back!!",        # 14 -> 12
    70: "relax",               # 5
    71: "webster!!",           # 11 -> 9
    72: "beat writhing!",      # 16 -> 14
    73: "beat it again!",      # 18 -> 14
    74: "floor b10!",          # 11 -> 10
    75: "is it true?",         # 11
    76: "hooray!",             # 7
    77: "good but...",         # 11 -> 10
    78: "hmm.",                # 4
    79: "you lied!",           # 8 -> 9. cap is 8
    80: "poison!!",            # 10 -> 8
    81: "info shop!",          # 12 -> 10
    82: "evil band",            # 10 (1 ctrl = 9 usable)
    83: "huh?!",               # 5
    84: "scary",               # 8 -> 5
    85: "what?!",              # 9 -> 6
    86: "on break",            # 9 -> 8
    87: "who did it!",         # 10 -> 11. too long
    88: "oh please",           # 10 -> 9
    89: "come fight!",         # 14 -> 11
    90: "poor guys",           # 9
    91: "tips please!",        # 14 -> 12
    92: "use thru!",           # 9
    93: "but thru!",           # 8 -> 9. cap 8
    94: "bracelet trade",      # 17 -> 14
    95: "also...",             # 8 -> 6
    96: "my request",          # 15 -> 10
    97: "use counter!",        # 13 -> 12
}

# Fix over-capacity entries
R46_SUB2[2] = "board is open"       # 15 cap, 13 chars ok
R46_SUB2[3] = "kreta tablet ok"     # 16 cap, 15 chars ok
R46_SUB2[4] = "seraph's item"       # 14 cap, 13 chars ok
R46_SUB2[14] = "vigger job info"    # 17 cap, 14 chars ok
R46_SUB2[15] = "adventurertip"      # 12 cap, 13 -> "adv. tip" = 8
R46_SUB2[15] = "explore tip"        # 12 cap, 11
R46_SUB2[20] = "no way!"            # 8 cap, 7 ok
R46_SUB2[22] = "a woman?"           # 9 cap, 8 ok
R46_SUB2[23] = "600yr?!"            # 7 cap, 7 ok
R46_SUB2[25] = "rumor!"             # 7 cap, 6 ok
R46_SUB2[26] = "our child!"         # 11 cap, 10 ok
R46_SUB2[35] = "traits"             # 9 cap, 6
R46_SUB2[40] = "pixies too!"        # 13 cap, 11 ok
R46_SUB2[41] = "vigger shop how?"   # 19 cap, 16 ok
R46_SUB2[50] = "no way!"            # 8 cap, 7 ok
R46_SUB2[51] = "witch on b3f!!"     # 19 cap, 14 ok
R46_SUB2[55] = "not strong"         # 13 cap, 10 ok
R46_SUB2[58] = "[deleted]"          # 12 cap, 9 ok
R46_SUB2[60] = "personlt2"          # 10 cap, 9 ok
R46_SUB2[63] = "no info now"        # 10 cap, 11-> too long. "no info"=7 ok
R46_SUB2[63] = "no new info"        # 10 cap, 11 -> still too long. spaces count!
R46_SUB2[63] = "no info?"           # 10 cap, 8
R46_SUB2[72] = "writhing one!"      # 16 cap, 13 ok
R46_SUB2[73] = "beat it again!"     # 18 cap, 14 ok
R46_SUB2[79] = "you lied!"          # 8 cap... "you lied!" = 9 chars -> too long
R46_SUB2[79] = "liar!!"             # 8 cap, 6 ok
R46_SUB2[87] = "who?!"              # 10 cap, 5 ok
R46_SUB2[93] = "but thru"           # 8 cap, 8 ok

# ============================================================================
# BUG-B fix: bulletin-board source text was authored ALL LOWERCASE. The board
# title renders capitalized (separate source) but every POST body/name/title
# above is lowercase. Recapitalize the FINAL effective R46 values (after all
# overrides) to proper sentence case + proper nouns.
#
# CRITICAL: this is purely a per-letter case change (a/A are distinct glyphs
# but BOTH single-width — verified against english_glyph_table.json), so glyph
# COUNT is preserved exactly. Line breaks (' / '), control codes, and slot
# capacities used by build_symmetric_payload are therefore untouched. Applied
# ONLY to R46 (bulletin board); R47 combat/UI labels are left as-is.
# ============================================================================
import re as _re_recap

_RECAP_PROPER = {
    "duhan": "Duhan", "oriana": "Oriana", "vigger": "Vigger", "venoan": "Venoan",
    "venoa": "Venoa", "karman": "Karman", "karmans": "Karmans", "seraph": "Seraph",
    "kreta": "Kreta", "ripu": "Ripu", "jankenman": "Jankenman", "janken": "Janken",
    "turgot": "Turgot", "gido": "Gido", "miri": "Miri", "pamela": "Pamela",
    "aurora": "Aurora", "simson": "Simson", "simsons": "Simsons", "bergran": "Bergran",
    "narcia": "Narcia", "webster": "Webster", "macbain": "Macbain", "popo": "Popo",
    "tranmell": "Tranmell", "porora": "Porora", "bogey": "Bogey", "banshee": "Banshee",
    "banshees": "Banshees", "orc": "Orc", "orcs": "Orcs", "hobbit": "Hobbit",
    "imp": "Imp", "pixie": "Pixie", "pixies": "Pixies", "elf": "Elf", "elves": "Elves",
    "automata": "Automata", "gerard": "Gerard", "thru": "Thru", "princess": "Princess",
    "witch": "Witch", "san": "San", "goth": "Goth",
}
_RECAP_I_FORMS = {"i", "im", "ill", "id", "ive", "i'm", "i'll", "i'd", "i've"}

def _recap_fix_i(tok):
    return ("I" + tok[1:]) if tok.lower() in _RECAP_I_FORMS else tok

def _recap_word(tok, prev_hyphen, next_hyphen):
    low = tok.lower()
    if low in ("san", "goth"):  # only proper inside the hyphenated San-Goth
        return _RECAP_PROPER[low] if (prev_hyphen or next_hyphen) else tok
    return _RECAP_PROPER.get(low, tok)

def recapitalize_post(text):
    """Sentence-case + proper-noun capitalization. Length-preserving (case-only)."""
    out = []
    toks = _re_recap.findall(r"[A-Za-z']+|[^A-Za-z']+", text)
    sentence_start = True
    for i, tok in enumerate(toks):
        if _re_recap.match(r"^[A-Za-z']+$", tok):
            ph = i > 0 and toks[i - 1].endswith('-')
            nh = i + 1 < len(toks) and toks[i + 1].startswith('-')
            w = _recap_word(_recap_fix_i(tok), ph, nh)
            if sentence_start and w[0].islower():
                w = w[0].upper() + w[1:]
            out.append(w)
            sentence_start = False
        else:
            out.append(tok)
            if _re_recap.search(r"[.!?]", tok):
                sentence_start = True   # new sentence after . ! ?
            elif _re_recap.search(r"[0-9]", tok):
                sentence_start = False  # digits begin sentence content (e.g. "600 years")
    return "".join(out)

for _recap_d in (R46_SUB0, R46_SUB1, R46_SUB2):
    for _recap_k in list(_recap_d):
        _recap_new = recapitalize_post(_recap_d[_recap_k])
        assert len(_recap_new) == len(_recap_d[_recap_k]), \
            f"recap changed length for {_recap_k!r}: {_recap_d[_recap_k]!r} -> {_recap_new!r}"
        _recap_d[_recap_k] = _recap_new

# ============================================================================
# R47 SUB0: Combat text  --  REALIGNED 2026-06-28 (release-blocker fix)
#
# The previous dict was SCRAMBLED: nearly every key wrote text belonging to a
# DIFFERENT group. Most fatally, the friendly-monster CHOICE cluster (groups
# 2-11: the "Decide Response" title, "Friendly monster!!" prompt, Fight/Leave
# options and flee-result lines) was overwritten with ability/scan labels
# (Dispel/Steal/Swap/...), destroying the spare/recruit mechanic for every
# friendly encounter. The ability labels actually live at groups 18-21 and the
# scan/stat labels at 31-52. This dict is now keyed 1:1 to the PRISTINE
# FFFF-delimited groups of extracted/packdata_raw/0047_type03.raw, every entry
# decoded from the pristine glyph stream (data/msg_glyph_map.json).
#
# Group budgets (cells incl. the trailing 0xFFFE separator; English glyph
# count must be <= budget -- enforced by validate() + the R47 guard below):
#   g2=6  g3=13 g4=5  g5=5  g6=15 g7=20 g8=16 g9=18 g10=13 g11=13
#   g12=11 g13=5 g14=6 g15=8 g16=16 g17=9 g18=6 g19=8 g20=6 g21=7
#   g22=12 g23=18 g24=6 g25=18 g26=13 g27=15 g28=3 g29=13 g30=13
#   g31=8 g32=8 g33=8 g34=8 g35=8 g36=8 g37=8 g38=8 g39=8 g40=8 g41=8
#   g42=6 g43=6 g44=6 g45=6 g46=6 g47=6 g48=6 g49=6 g50=6 g51=6 g52=6
#   g53=8 g54=3 g55=15 g56=14 g57=15 g58=12 g59=14 g60=13 g61=11 g62=9
#   g63=6 g64=5 g65=18 g66=14 g67=15 g68=19 g69=22 g70=18 g71=9 g72=27
#   g73=11 g74=6
#
# Groups intentionally SHIPPED PRISTINE (JP) -- could not be confidently
# decoded (glyph-map quirk) so a working JP label beats garbled English:
#   g52 (前罰系aa  -- 4th AA category, kanji unresolved)
#   g64 (一偉逃街  -- unresolved; near the void/banish AA cluster)
# ============================================================================
R47_SUB0 = {
    # --- Friendly-monster CHOICE cluster (release-blocker: groups 2-11) ---
    2:  "React?",            # g2  対応の決定  (choice menu title)
    3:  "Friendly!!",        # g3  友好的なモンスターだ!!  (encounter prompt)
    4:  "Fight",             # g4  戦う        (choice 1)
    5:  "Leave",             # g5  立ち去る    (choice 2)
    6:  "Caught napping!",   # g6  (モンスターの)油断をついた
    7:  "It suddenly attacks",  # g7  モンスターは突然おそいかかってきた
    8:  "We're off guard!",  # g8  モンスターに(油断)をとられた
    9:  "Flees in terror!",  # g9  ...は恐怖にかられて逃げ出そうとする
    10: "Fled away!!",       # g10 ...が逃げ出してしまった!!
    11: "Escaped!",          # g11 ...は逃げ出すのに成功した
    # --- Treasure box (already correct in old dict) ---
    12: "Open box?",         # g12 (宝)箱を開錠しますか?
    13: "Open",              # g13 (宝)箱開錠
    14: "Retry",             # g14 やりなおす
    15: "Box res.",          # g15 (宝)箱開錠の結果
    16: "New AA created!!",  # g16 新たなAAを生み出しました
    17: "Opening",           # g17 (宝)箱を開錠します
    # --- Friendly-action / ability labels (the real Dispel/Steal home) ---
    18: "Gain",              # g18 獲得
    19: "Dispel",            # g19 ディスペル
    20: "Steal",             # g20 盗む
    21: "Swap",              # g21 (隊列)交代
    22: "Nothing!",          # g22 何も持っていなかった
    23: "Can't steal:full!", # g23 アイテムがいっぱいで盗めなかった
    24: "Stole!",            # g24 ...を盗んだ
    25: "Flees in terror!",  # g25 ...は恐怖にかられて逃げだそうとする
    26: "But stumbled!",     # g26 しかしこけてしまった
    27: "Allies chased!!",   # g27 仲間たちも(敵)を追いかけた!!
    28: "G.",                # g28 g.  (gold marker)
    29: "Too big!",          # g29 大きすぎて回りこめない
    30: "Too big!",          # g30 大きすぎてとばせない
    # --- Monster-scan stat / resistance labels ---
    31: "HP/MaxHP",          # g31 hp／(最)大hp
    32: "Level",             # g32 レベル
    33: "Hit Lv",            # g33 命中レベル
    34: "Gain Pow",          # g34 獲得力
    35: "Evade",             # g35 回避力
    36: "Dispel",            # g36 解消力
    37: "Agility",           # g37 敏捷度
    38: "Fire Res",          # g38 炎(効性)
    39: "Thnd Res",          # g39 (雷)気効性
    40: "Ice Res",           # g40 (冷気)効性
    41: "Nullify",           # g41 (使呪消除)能力
    42: "Normal",            # g42 ふつう
    43: "Bit Hi",            # g43 すこし強い
    44: "High",              # g44 強い
    45: "V.High",            # g45 とても強い
    46: "Bit Lo",            # g46 すこし弱い
    47: "Low",               # g47 弱い
    48: "V.Low",             # g48 とても弱い
    49: "GainAA",            # g49 獲得系aa
    50: "DispAA",            # g50 解消系aa
    51: "SkilAA",            # g51 騎法系aa
    # 52 SHIPPED PRISTINE (前罰系aa -- 4th AA category, unresolved)
    53: "Found!",            # g53 ...を発見しました
    54: "H.",                # g54 h.
    # --- Spell incantations (flavor lines) ---
    55: "Return to rest!",   # g55 (無)形の者よあるべき場所へ戻れ
    56: "Be sealed!",        # g56 (無)形の使呪(形)にするを許さず
    57: "Gather to us!",     # g57 われらが(騎)力(の)もとに(集)まれ
    58: "Be my light!",      # g58 われの力を(しの)光となれ
    59: "Unseen shield!",    # g59 われらをつつめ見えざる(盾)よ
    60: "Unseen power!",     # g60 われらに宿れ見えざる(理)よ
    61: "Come back!",        # g61 (元)よわれらの(元)に戻れ
    62: "Bless us!",         # g62 (我)らの道に幸あれ
    63: "F/B Sw",            # g63 前(列)(後列)交代
    # 64 SHIPPED PRISTINE (一偉逃街 -- unresolved)
    # --- AA / party-buff result messages ---
    65: "Sent to void!!",    # g65 モンスターを(虚)空間に送りこんだ!!
    66: "Sealed magic!",     # g66 モンスターの(騎法)を封じた
    67: "Buffs removed!",    # g67 パーティの(騎)力が解除された
    68: "All HP/MP restored!",  # g68 パーティ全員のhp・mpが回復した
    69: "Evade & Dispel up!",   # g69 パーティ全員の回避力・解消力がアップした
    70: "Party Gain up!",    # g70 パーティ全員の獲得力がアップした
    71: "Revived!",          # g71 (死)者が復活した
    72: "MP max! EXP & Gold up!",  # g72 mpが(最)限となり、(配下)expとgoldがアップした
    73: "Too far!",          # g73 (獲得)がとどかない
    74: "?????",             # g74 ?????
}

# ============================================================================
# R47 SUB1: Battle UI
# Caps: msg2=30 msg3=12 msg4=27 msg5=18 msg6=23 msg7=23 msg8=17
# msg9=13 msg10=18 msg11=20 msg12=15 msg13=6 msg14=5 msg15=5 msg16=16
# msg17=18 msg18=16 msg19=15 msg20=11 msg21=6 msg22=32 msg23=31
# msg24=22 msg25=16
# ============================================================================
R47_SUB1 = {
    2: "Select Allied Action (AA)",     # 30 cap, 25 ok
    3: "Select Action",                 # 12 cap, 13 -> too long. "your action"=11
    4: "Reset AA. Skip This Turn",      # 27 cap, 24 ok
    5: "Swap Front And Back",           # 18 cap, 19 -> "swap front/back"=15
    6: "Flee. May Succeed",             # 23 cap, 17 ok (but needs ' / ' for line break? no, this is single display)
    7: "Toggle Effect Cut",             # 23 cap, 18 ok
    8: "Pick Swap Target",              # 17 cap, 15 ok
    9: "Pick Target",                   # 13 cap, 11 ok
    10: "Pick Spell Caster",            # 18 cap, 17 ok
    11: "Pick Gate Opener",             # 20 cap, 16 ok
    12: "Pick The Decoy",               # 15 cap, 14 ok
    13: "Target",                       # 6 cap, 6 ok
    14: "Front",                        # 5 cap, 5 ok
    15: "Back",                         # 5 cap, 4 ok
    16: "Pick 2 For Swap",              # 16 cap, 15 ok
    17: "Pick 2 To Capture",            # 18 cap, 17 ok
    18: "Pick 2 To Attack",             # 16 cap, 16 ok
    19: "Pick Attacker",                # 15 cap, 13 ok
    20: "Swap Target",                  # 11 cap, 11 ok
    21: "Race",                         # 6 cap, 4 ok
    22: "Low Trust Aut Needs Leader",   # 32 cap, 26 ok -> "low trust: must be w/leader"
    23: "Low Trust Aut Won't Join",     # 31 cap, 24 ok
    24: "Cancel Selected AA",           # 22 cap, 18 ok
}

# Fix msg3 and msg5
R47_SUB1[3] = "Your Action"         # 12 cap, 11 ok
R47_SUB1[5] = "Swap Front/Back"     # 18 cap, 15 ok

# ============================================================================
# R47 SUB2: Special abilities
# Caps: msg2=8 msg3=8 msg4=8 msg5=8 msg6=4 msg7=4 msg8=16 msg9=9
# msg10=6 msg11=9 msg12=9 msg13=10 msg14=4 msg15=5 msg16=9 msg17=4
# msg18=19 msg19=9 msg20=8 msg21=9 msg22=7 msg23=7 msg24=9 msg25=9
# msg26=6 msg27=4
# ============================================================================
R47_SUB2 = {
    2: "Fire Brt",             # 8 cap, 8 ok (breath abbreviated)
    3: "Cold Brt",             # 8 cap, 8 ok
    4: "Thndr Bt",             # 8 cap, 8 ok (thunder breath)
    5: "Poisn Bt",             # 8 cap, 8 ok (poison breath)
    6: "Gaze",                 # 4 cap, 4 ok
    7: "Roar",                 # 4 cap, 4 ok
    8: "Forgot a spell!!",     # 16 cap, 16 ok
    9: "Summon",               # 9 cap, 6 ok
    10: "Call",                # 6 cap, 4 ok
    11: "Called!",             # 9 cap, 7 ok
    12: "Ally came!",          # 9 cap, 10 -> "ally came"=9
    13: "None came",           # 10 cap, 9 ok
    14: "Bash",                # 4 cap, 4 ok (knock back)
    15: "Agony",               # 5 cap, 5 ok
    16: "Dbl Actn",            # 9 cap, 8 ok
    17: "Dark",                # 4 cap, 4 ok
    18: "All buffs removed!!",  # 19 cap, 20 -> too long. "buffs dispelled!!"=17
    19: "Dmn Jump",            # 9 cap, 8 ok
    20: "Dmn Dive",            # 8 cap, 8 ok
    21: "Dmn Whip",            # 9 cap, 8 ok
    22: "Cannibl",             # 7 cap, 7 ok
    23: "K.Back",              # 7 cap, 6 ok
    24: "Dmn Beam",            # 9 cap, 8 ok
    25: "Mirror",              # 9 cap, 6 ok
    26: "Countr",              # 6 cap, 6 ok
}

# Fix msg12 and msg18
R47_SUB2[12] = "Ally came"          # 9 cap, 9 ok
R47_SUB2[18] = "Buffs dispelled!!"  # 19 cap, 17 ok

# ============================================================================
# Processing functions
# ============================================================================
def build_symmetric_payload(glyphs, cap):
    """Symmetric per-line padding for R46 (bulletin board) — BUG-8 fix.

    The board renderer horizontally centers each post on the WIDEST line,
    counting every non-FFFE word (incl. 0x0000 blanks) as one full-width
    cell. The old behavior dumped ALL spare slot capacity as trailing
    0x0000 after the last glyph, inflating the last line's width and
    shifting the centered block left (clipping the first chars of every
    line off the board).

    Instead: split into lines at 0xFFFE, give every line p leading 0x0000
    (p = max(0, ceil((E - sum_slack) / (2*n))), clamped so the leading
    pads never overdraw the spare budget), then distribute the remaining
    spare one word at a time as trailing 0x0000 onto the currently
    shortest line. This equalizes line widths toward Mtext + p and caps
    the max width at Mtext + 2p, keeping the text block visually centered.
    Total word count always equals `cap` exactly; FFFE count is preserved.
    """
    lines = [[]]
    for g in glyphs:
        if g == 0xFFFE:
            lines.append([])
        else:
            lines[-1].append(g)
    n = len(lines)
    E = cap - len(glyphs)
    if E <= 0:
        return list(glyphs)
    M = max(len(l) for l in lines)
    sum_slack = sum(M - len(l) for l in lines)
    d = E - sum_slack
    p = 0
    if d > 0:
        # ceil(d / (2n)), clamped so n*p never exceeds the spare beyond slack
        p = min(-(-d // (2 * n)), d // n)
        p = max(0, p)
    widths = [p + len(l) for l in lines]
    extra = [0] * n
    budget = E - n * p
    for _ in range(budget):
        i = min(range(n), key=lambda k: widths[k])
        extra[i] += 1
        widths[i] += 1
    payload = []
    for i, l in enumerate(lines):
        if i > 0:
            payload.append(0xFFFE)
        payload.extend([0x0000] * p)
        payload.extend(l)
        payload.extend([0x0000] * extra[i])
    assert len(payload) == cap, f"payload {len(payload)} != cap {cap}"
    assert payload[-1] != 0xFFFE, "dangling FFFE at payload end"
    return payload

def process_resource(r_id, raw_path, out_path, sub_translations, symmetric_pad=False):
    raw = bytearray(open(raw_path, 'rb').read())
    out = bytearray(raw)
    print(f"\nR{r_id}: {len(raw)} bytes")

    subs = []
    for i in range(3):
        idx, size, offset, pad = struct.unpack_from('<IIII', raw, i * 16)
        subs.append((idx, size, offset))

    total_replaced = 0
    total_truncated = 0

    for si, (idx, size, offset) in enumerate(subs):
        if si not in sub_translations:
            continue
        trans = sub_translations[si]

        ffff_pos = []
        for j in range(0, size, 2):
            if struct.unpack_from('>H', raw, offset + j)[0] == 0xFFFF:
                ffff_pos.append(j)

        msgs = []
        prev = 0
        for fp in ffff_pos:
            msgs.append((prev, fp))
            prev = fp + 2

        replaced = 0
        truncated = 0
        for msg_idx, en_text in trans.items():
            if msg_idx < 0 or msg_idx >= len(msgs):
                continue

            slot_start, slot_end = msgs[msg_idx]
            abs_start = offset + slot_start
            abs_end = offset + slot_end

            # Preserve leading control codes
            ctrl_bytes = bytearray()
            scan = abs_start
            while scan < abs_end:
                v = struct.unpack_from('>H', raw, scan)[0]
                if v >= 0xFB00 and v not in (0xFFFF, 0xFFFE):
                    ctrl_bytes += struct.pack('>H', v)
                    scan += 2
                else:
                    break

            en_glyphs = encode_english(en_text)
            slot_capacity = (abs_end - abs_start) // 2
            ctrl_count = len(ctrl_bytes) // 2

            if len(en_glyphs) + ctrl_count > slot_capacity:
                print(f"  TRUNC sub{si}[{msg_idx}]: {len(en_glyphs)+ctrl_count}>{slot_capacity} "
                      f"'{en_text[:30]}'")
                en_glyphs = en_glyphs[:slot_capacity - ctrl_count]
                # Truncation may leave a dangling line separator at the end
                while en_glyphs and en_glyphs[-1] == 0xFFFE:
                    en_glyphs.pop()
                truncated += 1

            payload_cap = slot_capacity - ctrl_count
            if symmetric_pad:
                payload = build_symmetric_payload(en_glyphs, payload_cap)
            else:
                payload = list(en_glyphs) + [0x0000] * (payload_cap - len(en_glyphs))

            write_pos = abs_start
            for b in range(0, len(ctrl_bytes), 2):
                struct.pack_into('>H', out, write_pos, struct.unpack('>H', ctrl_bytes[b:b+2])[0])
                write_pos += 2
            for g in payload:
                struct.pack_into('>H', out, write_pos, g)
                write_pos += 2
            assert write_pos == abs_end, f"slot fill mismatch sub{si}[{msg_idx}]"
            replaced += 1

        print(f"  Sub{si}: {replaced} replaced ({truncated} truncated)")
        total_replaced += replaced
        total_truncated += truncated

    # Verify FFFF counts
    for si, (idx, size, offset) in enumerate(subs):
        orig_ffff = sum(1 for j in range(0, size, 2)
                       if struct.unpack_from('>H', raw, offset + j)[0] == 0xFFFF)
        new_ffff = sum(1 for j in range(0, size, 2)
                      if struct.unpack_from('>H', out, offset + j)[0] == 0xFFFF)
        status = "OK" if orig_ffff == new_ffff else "MISMATCH!"
        print(f"  Sub{si} FFFF: {orig_ffff}=={new_ffff} {status}")

    assert out[:48] == raw[:48], "Header changed!"

    pad = (2048 - len(out) % 2048) % 2048
    output = bytes(out) + b'\x00' * pad

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'wb') as f:
        f.write(output)
    print(f"  Written {len(output)} bytes -> {out_path}")
    return total_replaced, total_truncated

# ============================================================================
# Duplicate detection
# ============================================================================
def detect_dups(raw_path, sub_idx, base_trans):
    raw = open(raw_path, 'rb').read()
    sub_off = struct.unpack_from('<I', raw, sub_idx * 16 + 8)[0]
    sub_size = struct.unpack_from('<I', raw, sub_idx * 16 + 4)[0]

    ffff_pos = []
    for j in range(0, sub_size, 2):
        if struct.unpack_from('>H', raw, sub_off + j)[0] == 0xFFFF:
            ffff_pos.append(j)

    msgs = []
    prev = 0
    for fp in ffff_pos:
        msgs.append((prev, fp))
        prev = fp + 2

    msg_content = {}
    for mi in range(len(msgs)):
        s, e = msgs[mi]
        msg_content[mi] = raw[sub_off + s:sub_off + e]

    full_trans = dict(base_trans)
    for mi in range(len(msgs)):
        if mi in full_trans:
            continue
        for ti, en in base_trans.items():
            if ti < len(msgs) and msg_content.get(mi) == msg_content.get(ti):
                full_trans[mi] = en
                break
    return full_trans

# ============================================================================
# Main execution
# ============================================================================
print("=" * 50)
print("  R46/R47 Type-03 Text Injection")
print("=" * 50)

# Validate all translations fit before running
def validate(name, trans, raw_path, sub_idx):
    raw = open(raw_path, 'rb').read()
    sub_off = struct.unpack_from('<I', raw, sub_idx * 16 + 8)[0]
    sub_size = struct.unpack_from('<I', raw, sub_idx * 16 + 4)[0]
    ffff_pos = []
    for j in range(0, sub_size, 2):
        if struct.unpack_from('>H', raw, sub_off + j)[0] == 0xFFFF:
            ffff_pos.append(j)
    msgs = []
    prev = 0
    for fp in ffff_pos:
        msgs.append((prev, fp))
        prev = fp + 2
    errors = 0
    for mi, en in trans.items():
        if mi >= len(msgs):
            continue
        cap = (msgs[mi][1] - msgs[mi][0]) // 2
        need = tlen(en)
        if need > cap:
            print(f"  ERR {name}[{mi}]: need {need} > cap {cap}: '{en}'")
            errors += 1
    return errors

# ----------------------------------------------------------------------------
# BUILD GUARD (release-blocker safety net, 2026-06-28)
#
# Two checks so a future misalignment fails the build LOUDLY instead of
# silently clobbering the friendly-monster mechanic again:
#   (A) groups_for() decodes the pristine FFFF groups of a sub-resource.
#   (B) assert_r47_friendly_signature() proves the pristine R47 sub0 still
#       carries the 対応の決定 / 戦う / 立ち去る / ディスペル / 盗む signature at
#       the groups our dict expects -- i.e. our keys are aimed at the right
#       targets. Glyph values are taken VERBATIM from the pristine raw so the
#       check is byte-exact, not glyph-map dependent.
#   (C) the cell-budget validate() below is now a HARD assert (was a warning):
#       every injected group's English glyph count must be <= its pristine
#       cell budget for ALL of R46+R47.
# ----------------------------------------------------------------------------
def groups_for(raw, sub_idx):
    sub_off = struct.unpack_from('<I', raw, sub_idx * 16 + 8)[0]
    sub_size = struct.unpack_from('<I', raw, sub_idx * 16 + 4)[0]
    ffff_pos = [j for j in range(0, sub_size, 2)
                if struct.unpack_from('>H', raw, sub_off + j)[0] == 0xFFFF]
    msgs = []
    prev = 0
    for fp in ffff_pos:
        s, e = prev, fp
        vals = [struct.unpack_from('>H', raw, sub_off + s + k)[0]
                for k in range(0, e - s, 2)]
        msgs.append(vals)
        prev = fp + 2
    return msgs

# Expected pristine glyph signatures (verbatim from pristine 0047 sub0).
# Each entry: group index -> list of (cell_index, expected_u16).
_R47_FRIENDLY_SIG = {
    2:  [(0, 0x0176), (1, 0x027D), (2, 0x0088), (3, 0x02E1), (4, 0x01AC)],  # 対応の決定
    4:  [(0, 0x011E), (1, 0x0000), (2, 0x0000), (3, 0x0072)],               # 戦__う
    5:  [(0, 0x0154), (1, 0x0080), (2, 0x0358), (3, 0x0098)],               # 立ち去る
    19: [(1, 0x00FC), (2, 0x010C), (3, 0x00CD), (4, 0x0106), (5, 0x00E9)],  # ディスペル
    20: [(1, 0x013B), (3, 0x0090)],                                         # 盗む
}

def assert_r47_friendly_signature(raw_path):
    raw = open(raw_path, 'rb').read()
    groups = groups_for(raw, 0)
    for gi, sig in _R47_FRIENDLY_SIG.items():
        assert gi < len(groups), (
            f"R47 GUARD: pristine sub0 has only {len(groups)} groups, "
            f"expected group {gi} -- resource layout changed!")
        g = groups[gi]
        for ci, exp in sig:
            assert ci < len(g) and g[ci] == exp, (
                f"R47 GUARD: pristine sub0 group {gi} cell {ci} = "
                f"{g[ci] if ci < len(g) else 'OOB':#06x}, expected {exp:#06x}. "
                f"The friendly-monster choice cluster is NOT where R47_SUB0 "
                f"expects it -- dict is misaligned, ABORTING to avoid "
                f"clobbering the spare/recruit mechanic.")
    print("  R47 friendly-choice signature OK "
          "(title/Fight/Leave at g2,4,5; Dispel/Steal at g19,20)")

print("\nGuard: checking pristine R47 friendly-choice signature...")
assert_r47_friendly_signature('extracted/packdata_raw/0047_type03.raw')

print("\nValidating translations...")
errs = 0
errs += validate("r46s0", R46_SUB0, 'extracted/packdata_raw/0046_type03.raw', 0)
errs += validate("r46s1", R46_SUB1, 'extracted/packdata_raw/0046_type03.raw', 1)
errs += validate("r46s2", R46_SUB2, 'extracted/packdata_raw/0046_type03.raw', 2)
errs += validate("r47s0", R47_SUB0, 'extracted/packdata_raw/0047_type03.raw', 0)
errs += validate("r47s1", R47_SUB1, 'extracted/packdata_raw/0047_type03.raw', 1)
errs += validate("r47s2", R47_SUB2, 'extracted/packdata_raw/0047_type03.raw', 2)
# HARD cell-budget guard: never ship an over-budget (truncated) group again.
assert errs == 0, (f"\n{errs} cell-budget ERRORS found (English > pristine "
                   f"group budget)! Fix the offending dict entries above "
                   f"before building -- truncation is no longer silent.")
print("All translations fit!")

# Detect duplicates
r46_sub0_full = detect_dups('extracted/packdata_raw/0046_type03.raw', 0, R46_SUB0)
r46_sub2_full = detect_dups('extracted/packdata_raw/0046_type03.raw', 2, R46_SUB2)
r47_sub0_full = detect_dups('extracted/packdata_raw/0047_type03.raw', 0, R47_SUB0)

print(f"R46 sub0: {len(R46_SUB0)} + {len(r46_sub0_full)-len(R46_SUB0)} dups")
print(f"R46 sub2: {len(R46_SUB2)} + {len(r46_sub2_full)-len(R46_SUB2)} dups")
print(f"R47 sub0: {len(R47_SUB0)} + {len(r47_sub0_full)-len(R47_SUB0)} dups")

# Process R46
r46_rep, r46_trunc = process_resource(
    46,
    'extracted/packdata_raw/0046_type03.raw',
    'build/packdata_resources/0046_type03.raw',
    {0: r46_sub0_full, 1: R46_SUB1, 2: r46_sub2_full},
    symmetric_pad=True  # BUG-8: board renderer centers on widest line
)

# Process R47
r47_rep, r47_trunc = process_resource(
    47,
    'extracted/packdata_raw/0047_type03.raw',
    'build/packdata_resources/0047_type03.raw',
    {0: r47_sub0_full, 1: R47_SUB1, 2: R47_SUB2}
)

print(f"\nTotal: R46={r46_rep} ({r46_trunc} trunc), R47={r47_rep} ({r47_trunc} trunc)")
print("Done!")
