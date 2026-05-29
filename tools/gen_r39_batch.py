#!/usr/bin/env python3
"""Generate batch_r39_equip_a.json translations for R39 sections 1-7."""
import struct, sys, json

sys.stdout.reconfigure(encoding='utf-8')

with open('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/0039_type15.raw', 'rb') as f:
    data = f.read()
with open('C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json', 'r', encoding='utf-8') as f:
    gmap = json.load(f)

def decode_glyphs(sec, start, end):
    result = ''
    pos = start
    while pos + 1 < end:
        val = struct.unpack_from('>H', sec, pos)[0]
        pos += 2
        if val == 0xFFFF:
            break
        if val == 0xFFFE:
            result += '\n'
            continue
        if 0xFF00 <= val < 0xFFFF:
            continue
        c = gmap.get(str(val))
        if c:
            result += c
        else:
            result += f'[{val:#06x}]'
    return result.strip()

# Parse sequential table
sections = []
for i in range(14):
    off = 16 + i * 16
    idx, size, start, z = struct.unpack_from('<IIII', data, off)
    sections.append((idx, size, start))

# ===== TRANSLATIONS =====

# Section 1: Spell names (57 entries)
spell_names = {
    0: "",
    1: "Kreta",
    2: "Kurudo",
    3: "Teal",
    4: "Analyze",
    5: "Weak",
    6: "Delay",
    7: "Depth",
    8: "Feeble",
    9: "Shroud",
    10: "Spleem",
    11: "Salome",
    12: "Escape",
    13: "Zakreta",
    14: "Zakurudo",
    15: "Zateal",
    16: "Through",
    17: "Zarado",
    18: "Drain",
    19: "Ripu",
    20: "Cannibal",
    21: "Jakreta",
    22: "Jakurudo",
    23: "Jateel",
    24: "Late",
    25: "Jarado",
    26: "Valhalla",
    27: "Reflect",
    28: "Megadeath",
    29: "Heal",
    30: "Leap",
    31: "Bullets",
    32: "Thief Eye",
    33: "Yaiba",
    34: "Coat",
    35: "Bless",
    36: "Protect",
    37: "Amok",
    38: "Heals",
    39: "Poison",
    40: "Strain",
    41: "Poisonkea",
    42: "Parazukea",
    43: "Fiakea",
    44: "Vital",
    45: "Carcass",
    46: "Will",
    47: "Lumiel",
    48: "Undead",
    49: "Trance",
    50: "Recover",
    51: "Anchors",
    52: "Float",
    53: "Stigma",
    54: "Raheal",
    55: "Offset",
    56: "Revive",
}

# Section 2: Spell descriptions (57 entries)
spell_descs = {
    0: "",
    1: "Deals fire damage to a single enemy.",
    2: "Deals ice damage to a single enemy.",
    3: "Deals lightning damage to a single enemy.",
    4: "Examines the status information of an enemy.",
    5: "Reduces the attack power of a single enemy.",
    6: "Reduces the agility of a single enemy.",
    7: "Reduces the evasion of a single enemy.",
    8: "Reduces the defense of a single enemy.",
    9: "Instantly kills a single enemy.",
    10: "Puts a single enemy to sleep.",
    11: "Seals a single enemy's magic.",
    12: "Flee from battle.",
    13: "Deals fire damage to an enemy group.",
    14: "Deals ice damage to an enemy group.",
    15: "Deals lightning damage to an enemy group.",
    16: "Temporarily prevents random encounters.",
    17: "Instantly kills an enemy group.",
    18: "Absorbs HP from a single enemy.",
    19: "Disarms traps on treasure chests.",
    20: "Reflects physical damage taken back once.",
    21: "Deals fire damage to all enemies.",
    22: "Deals ice damage to all enemies.",
    23: "Deals lightning damage to all enemies.",
    24: "Attacks a single enemy using defense power.",
    25: "Instantly kills all enemies.",
    26: "Sacrifices one level to cause a catastrophe.",
    27: "Reflects magic back once.",
    28: "Deals holy damage to all enemies.",
    29: "Restores HP to a single ally.",
    30: "Instantly warps back to town.",
    31: "Deals holy damage to a single enemy.",
    32: "Checks the number of treasure chests remaining on the floor.",
    33: "Increases one ally's hit rate and attack power, enabling hitting undead.",
    34: "Increases one ally's agility.",
    35: "Increases one ally's evasion.",
    36: "Increases one ally's defense.",
    37: "Deals holy damage to an enemy group.",
    38: "Restores HP to an ally group.",
    39: "Inflicts poison on an enemy group.",
    40: "Magically paralyzes an enemy group, preventing them from moving.",
    41: "Cures one ally's poison.",
    42: "Cures one ally's paralysis.",
    43: "Cures one ally's fear.",
    44: "Fully restores stamina and enables movement without encounters for a turn.",
    45: "Revives one ally with partial HP.",
    46: "Restores one ally's HP and cures status ailments.",
    47: "Removes Dark Fog.",
    48: "Makes Dispel highly effective against non-undead enemy groups.",
    49: "Warps to the stairs entrance on the current floor.",
    50: "Automatically restores a small amount of HP each turn.",
    51: "Restores a used equipped item.\nHowever, the caster may become frightened.",
    52: "Temporarily nullifies damage traps.",
    53: "Deals holy damage to all enemies.",
    54: "Restores HP to all allies.",
    55: "Sacrifices own life to instantly kill a single enemy.",
    56: "Sacrifices own life to revive a single ally.",
}

# Section 3: Allied Action names (39 entries)
aa_names = {
    0: "None",
    1: "W-Slash",
    2: "Stun Smash",
    3: "Hold Attack",
    4: "SJ Attack",
    5: "Slay Crash",
    6: "Cross-Gauge Kill",
    7: "Front Guard",
    8: "Magic Shield",
    9: "Anti-Magic Shell",
    10: "Mirror Image",
    11: "Dense Formation",
    12: "Evasive Maneuver",
    13: "Restrict Shot",
    14: "Support Shot",
    15: "Magic Cancel",
    16: "Breath Cancel",
    17: "Back Cover",
    18: "Intercept",
    19: "Concentrated Spell",
    20: "Silence Breaker",
    21: "Magic Rapid Fire",
    22: "Enchant",
    23: "Magic Cooperation",
    24: "Concentrated Attack",
    25: "Back Attack",
    26: "Gale Slash",
    27: "Rush",
    28: "Multi-Jump Attack",
    29: "Sacred Cross",
    30: "Warp Attack",
    31: "Soul Crash",
    32: "Sonic Sword",
    33: "Elemental Attack",
    34: "Fake Attack",
    35: "Zantsuki Iaijin",
    36: "Nightmare Quake",
    37: "Weak Smash",
    38: "Double Breath",
}

# Section 4: Allied Action descriptions (84 entries)
# 0 = empty, 1-37 = descriptions, 38-83 = party requirements
aa_descs = {
    0: "",
    1: "Two front row members attack a single enemy\nin sync, dealing massive damage.",
    2: "A back row member channels magic power into\na front row member's weapon. Only one attack,\nbut can stun magic-resistant monsters.",
    3: "A back row member uses magic to freeze an\nenemy in place, then a front row member\nattacks. A successful hold guarantees a hit.",
    4: "A back row member lifts a front row member\ninto the air with magic for a dive-attack\nat the start of the turn. Temporarily\nreduces enemy defense.",
    5: "Two adjacent front row members flank-attack\nenemies at the edges of both rows. Only one\nattack each, but hits are guaranteed.",
    6: "Two back row members bind the enemy with\ncrossed magic, pull it forward, and two front\nrow members attack simultaneously. Effective\nagainst low-evasion, low-HP enemies.",
    7: "All front row members take a defensive stance,\nreducing evasion and defense. Cures stun,\nparalysis, poison, ID, and drain from enemies,\nand blocks enemy Rush attacks.",
    8: "Two back row members create a magic barrier,\nreducing magic damage and lowering resist\nfailure rate.",
    9: "All back row members create a powerful magic\nbarrier over the entire battlefield. For that\nturn, neither side can cast any spells.",
    10: "All back row members create duplicates of\nevery party member. Duplicates vanish when\nhit, but real members take no damage from\nattacks targeting the duplicates.",
    11: "When an enemy uses breath, the entire party\ntakes cover, reducing breath and magic damage.\nHowever, physical attack damage increases.",
    12: "The entire party takes an evasive formation,\ngreatly increasing evasion and defense against\nphysical attacks. However, breath and magic\ndamage increases.",
    13: "When a protected front row member is attacked,\na back row member counterattacks with ranged\nweapons. Activates each time the protected\nfront row member is attacked.",
    14: "Before allies attack, all back row members\nperform ranged attacks, increasing the\noverall hit rate.",
    15: "When an enemy attempts to cast a spell, a\nback row member attacks with a ranged weapon\nto interrupt the casting. Limited activations\nper turn.",
    16: "When an enemy attempts to use breath, a back\nrow member attacks with a ranged weapon to\ninterrupt the breath. Limited activations\nper turn.",
    17: "When a protected back row member is attacked,\na front row member takes the hit instead. Also\nresponds to enemy ranged attacks.",
    18: "One front row member acts as a decoy. When\nattacked, the remaining front row members\ncounterattack from the sides, interrupting\nthe enemy's coordinated attack. Limited\nactivations per turn.",
    19: "Three back row members concentrate magic to\nexpand spell area of effect. Also reduces\nenemy spell resistance and increases spell\npower.",
    20: "All back row members concentrate magic to\nbreak silence. Cures the party's Mute status\nand breaks enemy Magic Shell and Anti-Magic\nShell.",
    21: "Two adjacent back row members who both know\nthe same spell cast it together, increasing\nexecution speed. Faster than Anti-Magic Shell.",
    22: "A back row member enchants an ally's weapon\nwith a spell. If the attack hits, it bypasses\nenemy spell resistance and Magic Shell to\ndeliver the spell.",
    23: "Two back row members cast the same spell\ntogether, greatly amplifying its power.",
    24: "Three front row members consecutively attack\na single enemy, greatly increasing damage.\nThe combo makes each successive hit stronger\nthan the last.",
    25: "One front row member acts as a decoy. When\nattacked, the other two rush behind the enemy\nand counterattack. Hit rate and damage are\ngreatly increased.",
    26: "Evolved Concentrated Attack with a Fighter.\nThe first member launches the enemy into the\nair, then attacks during the fall and recovery\nfor massive damage.",
    27: "The entire party charges the enemy party,\ndealing damage to all enemies. Cannot be\nblocked by Front Guard, and attacks always hit.",
    28: "Two front row members feint while the third\nstrikes from above at the enemy's weak point.\nAll members attack once, but the third member's\ncritical rate is greatly increased.",
    29: "A front and back row member trace a holy\nsymbol and perform a powerful Dispel.\nExtremely effective against undead.",
    30: "One back row member creates a warp gate, and\nthree front row members dive-attack from an\naerial gate. Can reduce enemy defense.\nAirborne enemies cannot be targeted.",
    31: "Evolved Slay Crash with a Monk.\nTwo members charge through the enemy with\nspirit energy, dealing damage on the charge\nand return, and can destroy undead.",
    32: "Evolved W-Slash with a Fighter.\nTwo front row members swing their weapons to\ncreate a shockwave. May also damage enemies\nbehind the target.",
    33: "Three front row members charge through the\nentire enemy front row as one, dealing damage\nto each enemy. High damage but low hit rate.",
    34: "Evolved Stun Smash with a Gizoku/Bitou.\nThe decoy performs a feint to boost hit rate,\nthen the other strikes to stun the enemy.",
    35: "Evolved Back Attack with a Samurai.\nThe samurai's swordsmanship enables an even\nmore powerful counterattack that can also\nparalyze the enemy.",
    36: "Evolved SJ Attack with a Dark Knight.\nSlams a spirit-charged weapon from above to\ncreate a shockwave, dealing damage and\nstunning all enemies.",
    37: "Evolved Hold Attack with a Bishop.\nThe back row spots the enemy's weakness while\nholding, allowing the front row to deal even\ngreater damage.",
    # Party requirements (38-83)
    38: "2 members",
    39: "1 member",
    40: "1 MP user",
    41: "1 member",
    42: "1 MP user",
    43: "1 member",
    44: "1 MP user",
    45: "2 adjacent members",
    46: "2 members",
    47: "2 MP users",
    48: "2 or more, all members",
    49: "2 MP users",
    50: "3 MP users",
    51: "3 MP users",
    52: "2 or more, all members",
    53: "2 or more, all members",
    54: "1-2 members",
    55: "All members",
    56: "1-2 members",
    57: "2 members",
    58: "2 members",
    59: "3 members",
    60: "3 MP users",
    61: "3 MP users",
    62: "2 adjacent members with same spell",
    63: "1 back row caster and 1 attacker",
    64: "",
    65: "2 MP users",
    66: "3 members",
    67: "3 members",
    68: "4 or more, all members",
    69: "3 members",
    70: "2 Dispel-capable front and back members",
    71: "3 members",
    72: "1 MP user",
    73: "3 members",
    74: "3 members",
    75: "2 adjacent members",
    76: "2 members",
    77: "1 member",
    78: "1 MP user",
    79: "3 members",
    80: "1 member",
    81: "1 MP user",
    82: "1 member",
    83: "1 MP user",
}

# Section 5: Allied Action UI messages (7 entries)
aa_ui = {
    0: "None",
    1: "All Alleid Actions have been removed.",
    2: "No Alleid Actions are currently set.",
    3: "Alleid Action settings have been reset.",
    4: "Change formation and exit?",
    5: "Not enough AP.",
    6: "Exit without changing formation?\nAre you sure?",
}

# Section 6: Quest descriptions (34 entries)
quest_descs = {
    0: "",
    1: "I don't mind entrusting you with the noble\ntask of spreading the healing power of the\nChurch of Salem throughout the world.",
    2: "Our Vigger Shop is currently recruiting\nnew employees! Only one position available.\nApplicants, please bring your entry sheet\nto the shop.",
    3: "If you're reading this, please come\nimmediately to the small room just past the\nfirst warp on B5F. I'll put up a sign there.\nI'm in a real hurry.\nI'll explain when you get here.",
    4: "I want to learn magic but I don't have any\nmagic stones. Without magic, I'll waste away.\nPlease give me a Kreta magic stone.\nI'm in a terrible hurry. Too late means over.\nAnyone who can help right now, please do.",
    5: "Beat me at 5 rounds of Rock-Paper-Scissors\nand I'll give you something good! But if you\nlose, you get Ripu'd! Fee: 1 medal per loss.\nConfident in your luck? Come to B2F, the\nsmall room on the floor with lots of cells.",
    6: "Duhan Castle has recently established an\nAdventurer Assistance Program.\nBring 5 companions to the Castle and\neach person will receive a special\nadventurer stipend of 500G.",
    7: "Please take my precious, adorable Pippi\ndown to B8F of the labyrinth.",
    8: "Information has come in that ruins of an\nancient Elf kingdom were found in the\nlabyrinth. Items needed for the book of\nadventures may be there. Go to the scrap\nyard on B3F and investigate.",
    9: "I'm really curious about those tiny, adorable\nPixies.\nAnyone who knows everything about Pixies,\nlet's talk about them together!",
    10: "I borrowed 20 medals from the Ogre boss\nand debt collectors are after me.\nI'm exhausted.\nPlease, give me medals.\nI just want to stop living on the run.",
    11: "Oh, the incredibly sexy Succubus ladies...\nAh, I want to be tormented.\nLet's have a nice long chat about that.",
    12: "As a reward for accepting this request,\nI will transfer a piece of land to you.\nDetails will only be shared with those\nwho accept.\nKnight Order members, please refrain.",
    13: "I'm stuck in a one-way passage and\ncan't get out!\nPlease hurry and help me!\nI fell through a trapdoor on this floor\nand ended up here.",
    14: "The magic portal room connecting B4F and B1F\nis locked and I'm in trouble.\nIngo should be able to help.\nPlease go to Ingo's hideout on B4F\nand get the key.",
    15: "I knew someone would want the key I made!\nBut I'm not giving it away for free.\nIf you want it, bring me a spare\nGnome's Ring as my price.",
    16: "A shady adventurer named Kunnal has gone\nmissing somewhere. I'm in trouble.\nPlease find him and tell him\nto come back immediately.",
    17: "We're holding a Trap Game Contest at the\ntavern. Anyone confident in their skills,\nplease sign up!\nThe grand champion will receive\na rare item.",
    18: "I want to talk to the Succubus ladies but\nthey always run away.\nNow's my chance!\nPlease catch a Succubus that appears\nright in front of me and hold her!",
    19: "The Knight Order is conducting level checks\non registered adventurers.\nThis is a test of how well you know\nthe labyrinth and adventuring.\nInterested parties, accept the request first.",
    20: "I'm Melanie, an elf girl training daily\nto become a full-fledged mage,\nand my manager Miri.\nI want to learn lots of spells, so please\nlet me join a party with adventurers.",
    21: "Please find my body.\nA long time ago, I snuck into\na suspicious church all by myself.\nA scary-faced priest\nkilled me.",
    22: "I dropped my precious treasure chest\nin the scary room on B1F.\nI can't write the details here, but\nI'll give you something nice, so please,\ngo pick it up for me.",
    23: "The guide for the Karman Exploration Tour\norganized by the Duhan Merchant Guild has\nsuddenly become an adventurer, and we need\na replacement guide.\nConfident explorers, we're waiting for you.",
    24: "To master the way of the samurai and find\na new light, I feel I need armor crafted by\na master artisan.\nWould someone obtain one for me?",
    25: "The masterwork armor, obtained with great\neffort. But to find the new light, something\nis still missing.\nSo I'd like someone to temper this armor\nin the labyrinth's lava rocks.",
    26: "I poured the labyrinth's magic into the\nmasterwork armor and tempered it rigorously,\nbut something is still missing. I'd like to\nobserve foreign fighting styles.\nAwaiting a challenge from a master warrior.",
    27: "Could you go mix my secret potion\ninto the spring water on B1F?",
    28: "Could you go mix my secret potion\ninto the spring water on B2F this time?",
    29: "I have one more secret potion left, but\nno use for it. I hear there's a fountain\non B6F.\nWouldn't it be wonderful if it could\nheal you there?",
    30: "I've never seen anyone possessed by a death\nspirit, so I'd like to meet one.\nPlease come back to the Castle while\npossessed by a death spirit.\nThank you in advance.",
    31: "My underling has gone missing.\nAn orc named Casta.\nPlease go find him.\nHe's probably hiding in the room with\nthe rusty key on B5F!",
    32: "Punish the bad adventurer who punched\nmy friend!\nHe was examining a weird statue on B5F,\nin the room to the northwest,\nso he should be around there.",
    33: "Somewhere on B10F, there should be a room\nwith a large water vase in the center.\nI don't know where it is though.\nIf I can get there, I think I can return\nto my former time, so please take me there.",
}

# Section 7: Quest/NPC names (29 entries)
quest_names = {
    0: "",
    1: "Fuke",
    2: "Lucy",
    3: "Orogad",
    4: "Miri",
    5: "Rock-Paper-Scissors Man",
    6: "Castle Steward",
    7: "Angus",
    8: "Guillaume",
    9: "Yoppen",
    10: "Pitiful Imp",
    11: "Ingo",
    12: "Contest Over",
    13: "Lomi",
    14: "Popo",
    15: "Merchant Guild",
    16: "Fudo",
    17: "Rang",
    18: "??? has started heading for the spring.",
    19: "Castle",
    20: "Scone",
    21: "Survey Deadline",
    22: "Rogue has started heading for B5F.",
    23: "Knight Order",
    24: "The return deadline has passed.",
    25: "Lidi",
    26: "Vago",
    27: "Casta",
    28: "A shadow is targeting Rock-Paper-Scissors Man!",
}

# Map section index to translation dict
trans_maps = [spell_names, spell_descs, aa_names, aa_descs, aa_ui, quest_descs, quest_names]

# Build output
output = []
msg_idx = 97

for si in range(7):
    idx, size, start = sections[si]
    sec = data[start:start + size]
    count = struct.unpack_from('>H', sec, 0)[0]

    offsets = []
    for i in range(count):
        val = struct.unpack_from('>I', sec, 2 + i * 4)[0]
        offsets.append(val)

    trans = trans_maps[si]

    for i in range(count):
        msg_start_off = offsets[i]
        if i + 1 < count:
            msg_end_off = offsets[i + 1]
        else:
            msg_end_off = size
        decoded = decode_glyphs(sec, msg_start_off, msg_end_off)

        english = trans.get(i, "")

        entry = {
            "resource": 39,
            "msg_index": msg_idx,
            "japanese": decoded,
            "english": english
        }
        output.append(entry)
        msg_idx += 1

# Write output
outpath = 'C:/Programmieren/wizardrytranslation/data/type2_translated/batch_r39_equip_a.json'
with open(outpath, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'Wrote {len(output)} entries to {outpath}')
print(f'msg_index range: {output[0]["msg_index"]} - {output[-1]["msg_index"]}')

# Summary
for si in range(7):
    sec_msgs = [e for e in output if e["msg_index"] >= 97 + sum(
        struct.unpack_from('>H', data[sections[j][2]:sections[j][2]+2], 0)[0]
        for j in range(si)
    ) and e["msg_index"] < 97 + sum(
        struct.unpack_from('>H', data[sections[j][2]:sections[j][2]+2], 0)[0]
        for j in range(si+1)
    )]
    print(f'Section {si+1}: {len(sec_msgs)} entries')
