#!/usr/bin/env python3
"""Create translation chunk for R37, R48, R49 type-01 resources."""
import json
import sys
sys.stdout.reconfigure(encoding="utf-8")

entries = []

# ============================================================
# R37 - Character Creation (uncovered messages only)
# Already covered by chunk_r37_extra.json: 8,13,14,19-126
# Skipping: 0 (header), 1 (spacer), 127 (padding)
# ============================================================

entries.append({"resource": 37, "message": 2,
    "japanese": "名前を入力してください。「男名・女名＝名前を自動で入力」",
    "english": "enter a name. / m name, f name: auto-fill / "})

entries.append({"resource": 37, "message": 3,
    "japanese": "性別を選んでください。",
    "english": "select gender. / "})

entries.append({"resource": 37, "message": 4,
    "japanese": "種族を選んでください。",
    "english": "select a race. / "})

entries.append({"resource": 37, "message": 5,
    "japanese": "属性を選んでください。",
    "english": "select alignment. / "})

entries.append({"resource": 37, "message": 6,
    "japanese": "職業を選んでください。",
    "english": "select a class. / "})

entries.append({"resource": 37, "message": 7,
    "japanese": "能力値を振り分けてください。",
    "english": "allocate stat points. / "})

entries.append({"resource": 37, "message": 9,
    "japanese": "bonus point",
    "english": "bonus point / "})

entries.append({"resource": 37, "message": 10,
    "japanese": "はい",
    "english": "yes / "})

entries.append({"resource": 37, "message": 11,
    "japanese": "いいえ",
    "english": "no / "})

entries.append({"resource": 37, "message": 12,
    "japanese": "カナ",
    "english": "kana / "})

entries.append({"resource": 37, "message": 15,
    "japanese": "記述",
    "english": "abc / "})

entries.append({"resource": 37, "message": 16,
    "japanese": "自動",
    "english": "auto / "})

entries.append({"resource": 37, "message": 17,
    "japanese": "決定",
    "english": "ok / "})

entries.append({"resource": 37, "message": 18,
    "japanese": "hiragana keyboard",
    "english": "abcdefghij / klmnopqrst / uvwxyz.,!? / abcdefghij / klmnopqrst / uvwxyz -'  /           /           /           /           / ",
    "note": "Hiragana keyboard - replaced with Latin alphabet"})


# ============================================================
# R48 - Shop/Location Names (messages 1-107)
# Based on Vigger Shop store front reputation/level table from guide
# ============================================================

r48_translations = {
    1: "none",
    # --- Reputation -100: base tier ---
    2: "illegal dump site",
    3: "disposal plant",
    4: "waste incinerator",
    5: "garbage dump",
    6: "oversized garbage",
    7: "knockoff store",
    8: "run-down shop",
    9: "ramshackle shack",
    10: "shed",
    11: "private home",
    12: "mansion",
    13: "shop",
    14: "recycling shop",
    # --- Neighborhood tier ---
    15: "local dump site",
    16: "local disposal",
    17: "local incinerator",
    18: "local garbage dump",
    19: "huge garbage dump",
    20: "clip joint",
    21: "shanty",
    22: "residence",
    23: "pawn shop",
    24: "store",
    25: "cheap store",
    26: "local recycler",
    # --- Town tier ---
    27: "town dump site",
    28: "town disposal",
    29: "town incinerator",
    30: "town garbage dump",
    31: "illegal building",
    32: "crooked shop",
    33: "common store",
    34: "ruins",
    35: "nameless store",
    36: "discount store",
    37: "general store",
    38: "town recycler",
    # --- City tier ---
    39: "city dump site",
    40: "city disposal",
    41: "city incinerator",
    42: "city garbage dump",
    43: "crooked market",
    44: "clip joint shop",
    45: "shack",
    46: "regular store",
    47: "famous store",
    48: "city recycler",
    # --- Country tier ---
    49: "country dump site",
    50: "country disposal",
    51: "country incinerator",
    52: "country dump",
    53: "ripoff dept store",
    54: "specialty store",
    55: "trusted store",
    56: "specialty shop",
    57: "supermarket",
    58: "budget market",
    59: "country recycler",
    # --- Capital tier ---
    60: "capital dump site",
    61: "capital disposal",
    62: "capital incinerator",
    63: "capital dump",
    64: "thief market",
    65: "well-known store",
    66: "famous specialty",
    67: "capital recycler",
    # --- Continental tier ---
    68: "cont. dump site",
    69: "cont. disposal",
    70: "cont. incinerator",
    71: "cont. garbage dump",
    72: "pride of the store",
    73: "town office",
    74: "major specialty",
    75: "city office",
    76: "department store",
    77: "cont. recycler",
    # --- World tier ---
    78: "world dump site",
    79: "world disposal",
    80: "world incinerator",
    81: "world garbage dump",
    82: "crooked dept store",
    83: "hidden gem store",
    84: "well-stocked store",
    85: "city souvenir shop",
    86: "city attraction",
    87: "cont. office",
    88: "budget dept store",
    89: "budget recycler",
    # --- Global tier ---
    90: "global dump site",
    91: "global disposal",
    92: "global incinerator",
    93: "global garbage dump",
    94: "country souvenirs",
    95: "country attraction",
    96: "global office",
    97: "famous dept store",
    98: "global recycler",
    # --- Underground tier ---
    99: "u.g. dump site",
    100: "u.g. disposal",
    101: "u.g. incinerator",
    102: "u.g. garbage dump",
    103: "cont. souvenirs",
    104: "cont. attraction",
    105: "u.g. office",
    106: "world heritage",
    107: "u.g. recycler",
}

for msg_id in sorted(r48_translations):
    eng = r48_translations[msg_id]
    entries.append({
        "resource": 48,
        "message": msg_id,
        "japanese": f"(r48 msg {msg_id})",
        "english": eng + " / ",
    })


# ============================================================
# R49 - Dungeon Interactions (messages 1-111)
# ============================================================

r49_translations = {
    1: "nothing unusual here. / ",
    2: "it won't open from / this side. / ",
    3: "a crumbling wall. / ",
    4: "the switch is off. / the switch was turned on. / ",
    5: "the switch is on. / the switch was turned off. / ",
    6: "it is locked. / ",
    7: "a cart loaded / with cargo. / ",
    8: "the bridge is raised / and impassable. / ",
    9: "a large rock blocks / the path. / ",
    10: "luggage blocks / the way. / ",
    11: "collapsed luggage / is scattered about. / ",
    12: "old barrels left / abandoned here. / ",
    13: "a skeleton lies / on the ground ahead. / ",
    14: "a skeleton lies / at your feet. / ",
    15: "a skeleton is / leaning on the wall. / ",
    16: "a goddess statue / is displayed here. / ",
    17: "a half-broken statue / is displayed here. / ",
    18: "barrels are placed / here. / ",
    19: "the wall has / crumbled. / ",
    20: "rubble blocks / the path. / ",
    21: "a broken figure / is scattered about. / ",
    22: "a huge statue / hangs overhead. / ",
    23: "a huge statue / hangs overhead. / ",
    24: "an equestrian statue / is placed here. / ",
    25: "the wall blocks / the path. / ",
    26: "an oddly shaped / wall is here. / ",
    27: "some device is / set on the fence. / ",
    28: "spring water has / pooled here. / ",
    29: "the stairs ahead / are a dead end. / ",
    30: "there are stairs. / ",
    31: "a device to move / the stairs is here. / ",
    32: "a large tombstone / stands here. / ",
    33: "a device is next / to the tombstone. / ",
    34: "a hole large enough / to jump into. / ",
    35: "open the chest? / ",
    36: "the chest was empty. / ",
    37: "inventory is full. / drop something? / ",
    38: "gave up the chest. / ",
    39: " trap is set. / ",
    40: "take the item? / ",
    41: "spear / ",
    42: "dark fog / ",
    43: "crossbow / ",
    44: "roof fall / ",
    45: "mp drain / ",
    46: "poison gas / ",
    47: "alarm / ",
    48: "stone gas / ",
    49: "teleporter / ",
    50: "b / ",
    51: "f / ",
    52: "gave up the item. / ",
    53: "the chest is already / open. / ",
    54: "move via ladder? / cancel: x button / ",
    55: "floor above / ",
    56: "floor below / ",
    57: "go up the stairs? / ",
    58: "go down the stairs? / ",
    59: "warp to the floor / above? / ",
    60: "warp to the floor / below? / ",
    61: "used the key. / ",
    62: "climb up the ladder? / confirm: o  cancel: x / ",
    63: "climb down ladder? / confirm: o  cancel: x / ",
    64: "yes / ",
    65: "no / ",
    66: "cancel / ",
    67: "return to town? / ",
    68: "luggage blocks / the path completely. / ",
    69: "used the key. / the rusty key crumbled. / ",
    70: "warp to b1? / ",
    71: "warp to b4? / ",
    72: "warp to b5? / ",
    73: "warp to b10? / ",
    74: "enter the warp zone? / ",
    75: "move to b3? / ",
    76: "move to b5? / ",
    77: "there is a hole you / could jump down. / ",
    78: "flames block / the path. / ",
    79: "stairs visible / in the distance. / ",
    80: "there is a fountain. / ",
    81: "flames are blazing. / jumping down seems / dangerous. / ",
    82: "stairs are visible / in the water. / ",
    83: "a strange statue! / ",
    84: "a strange statue / blocks the path. / ",
    85: "something visible / beneath the statue. / ",
    86: "a mysterious statue / blocks the path. / ",
    87: "among the rubble, / a dead adventurer. / ",
    88: "a strange slave-like / statue is here. / ",
    89: "fine equipment is / on display. / ",
    90: "too heavy to open. / ",
    91: "a corpse lies here. / ",
    92: "a skeleton lies / scattered about. / ",
    93: "this spot feels / especially heavy. / ",
    94: "a water jug / is here. / ",
    95: "a beautiful shrine / is enshrined here. / ",
    96: "a huge goddess / statue is here. / ",
    97: "the broken floor / below is shining. / ",
    98: "warp to b8? / ",
    99: "warp to b6? / ",
    100: "warp to b3? / ",
    101: "a small bag has / fallen here. / ",
    102: "a gold lock is / on the door. / ",
    103: "a silver lock is / on the door. / ",
    104: "a rusty lock is / on the door. / ",
    105: "a large water jug / is displayed. / ",
    106: "the gate is raised / and impassable. / ",
    107: "an automaton / is lurking here. / ",
    108: "the statue is / chipped and worn. / ",
    109: "a knight face / statue is here. / ",
    110: "a gold plate / is floating. / ",
    111: "a beautiful altar / is here. / ",
}

for msg_id in sorted(r49_translations):
    eng = r49_translations[msg_id]
    entries.append({
        "resource": 49,
        "message": msg_id,
        "japanese": f"(r49 msg {msg_id})",
        "english": eng,
    })


# Summary and write
r37_count = sum(1 for e in entries if e["resource"] == 37)
r48_count = sum(1 for e in entries if e["resource"] == 48)
r49_count = sum(1 for e in entries if e["resource"] == 49)
print(f"Total entries: {len(entries)}")
print(f"  R37: {r37_count} new (14 messages, no overlap with chunk_r37_extra)")
print(f"  R48: {r48_count} (shop/location names)")
print(f"  R49: {r49_count} (dungeon interactions)")

out_path = "data/translate_chunks/chunk_r37_r48_r49_translated.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)
print(f"Written to {out_path}")
