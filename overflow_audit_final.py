"""
Final comprehensive overflow audit for Busin 0 translation.
Correctly handles trailing ' /' normalization to match build pipeline behavior.
"""
import json, os, textwrap
from collections import defaultdict

BASE = "C:/Programmieren/wizardrytranslation"
MAX_CHARS = 20
MAX_LINES = 3


def normalize_and_split(eng):
    """Split english text into display lines, matching build pipeline behavior."""
    eng = eng.replace("\n", " ").rstrip()
    # Build pipeline normalizes trailing ' /' to ' / ' for clean splitting
    if eng.endswith(" /"):
        eng = eng + " "
    lines = eng.split(" / ")
    while lines and lines[-1].strip() == "":
        lines.pop()
    return [l.strip() for l in lines]


def propose_rewrite(text, lines):
    """Propose a rewrite that fits 3 lines x 20 chars."""
    flat = " ".join(lines)
    for width in (20, 19, 18):
        wrapped = textwrap.wrap(flat, width=width)
        if len(wrapped) <= 3 and all(len(l) <= 20 for l in wrapped):
            return " / ".join(wrapped) + " /"
    return None


# ---- MANUAL REWRITES for entries too long for auto-wrap ----
# Key: (file, resource, msg_index) -> rewrite string
MANUAL = {
    # chunk_02: r38 personality traits
    ("chunk_02_translated.json", 38, 87): "Bores easily. Must / return to town or / mood drops. /",
    ("chunk_02_translated.json", 38, 88): "Fears spirits. / Trembles at the / sight of Death. /",
    ("chunk_02_translated.json", 38, 91): "Loves big groups. / Hates being in / small parties. /",
    ("chunk_02_translated.json", 38, 94): "Fascinated by / monster biology. / Loves studying them /",
    ("chunk_02_translated.json", 38, 95): "Believes in mystic / power. Loves gaining / magic knowledge. /",
    ("chunk_02_translated.json", 38, 96): "Skilled warrior who / seeks battle with / strong opponents. /",
    ("chunk_02_translated.json", 38, 97): "Must adventure. / Staying idle is / unbearable. /",
    ("chunk_02_translated.json", 38, 99): "Obsessed with traps / Happy on success, / crushed on failure /",
    ("chunk_02_translated.json", 38, 100): "Hates long dungeon / trips. Wishes undead / would vanish. /",
    ("chunk_02_translated.json", 38, 104): "Can't forgive those / who slay friendly / monsters. /",
    ("chunk_02_translated.json", 38, 107): "Hates fighting and / bloodshed. Mourns / fallen allies. /",
    ("chunk_02_translated.json", 38, 108): "Very short-tempered. / Long battles are / maddening. /",
    ("chunk_02_translated.json", 38, 109): "Born merchant. / Deeply into trade / and business. /",
    ("chunk_02_translated.json", 38, 110): "Keen interest in the / other sex. Bored by / same-sex parties. /",
    ("chunk_02_translated.json", 38, 111): "Believes they are / the most beautiful. / Shocked when hurt. /",
    ("chunk_02_translated.json", 38, 112): "Happy one moment, / angry the next. / Unpredictable. /",
    ("chunk_02_translated.json", 38, 113): "Thrives in hardship. / Being healed feels / even worse. /",
    # chunk_02: r38 race/gender/alignment
    ("chunk_02_translated.json", 38, 117): "Gender sets base / stats. Men=strong, / women=wise. /",
    ("chunk_02_translated.json", 38, 118): "Human: High faith / & balanced stats / overall. /",
    ("chunk_02_translated.json", 38, 119): "Elf: High INT & VIT / but frail. Best / at magic. /",
    ("chunk_02_translated.json", 38, 120): "Gnome: High faith / & agility. Suited / for Priests. /",
    ("chunk_02_translated.json", 38, 121): "Dwarf: Slow but / strong with deep / faith. Fighters. /",
    ("chunk_02_translated.json", 38, 122): "Hobbit: Small but / agile and lucky. / Born thieves. /",
    ("chunk_02_translated.json", 38, 123): "Good=justice. May / turn Evil. FIG MAG / PRI SAM GIZ BIS+ /",
    ("chunk_02_translated.json", 38, 124): "Neutral=no bias. / FIG THI MAG SAM / GIZ ALC MON /",
    ("chunk_02_translated.json", 38, 125): "Evil=self-serving. / FIG THI MAG PRI / NIN BIS ALC /",
    # chunk_02: r38 class descriptions
    ("chunk_02_translated.json", 38, 127): "Lowers trap level / & finds chests. / Sorcery Lv3. /",
    ("chunk_02_translated.json", 38, 129): "Holy magic master. / Can Dispel undead. / All Holy spells. /",
    ("chunk_02_translated.json", 38, 130): "Great EXP gain. Can / instant-kill foes. / Sorcery up to Lv2. /",
    # chunk_03: r38 class descriptions
    ("chunk_03_translated.json", 38, 131): "Knight gear usable. / Learns Sorcery / up to Lv5. /",
    ("chunk_03_translated.json", 38, 132): "Restores HP. Dispel / vs undead. Sorc & / Holy Magic Lv6. /",
    ("chunk_03_translated.json", 38, 133): "Poleaxe weapons. / Dispel vs undead. / Holy Magic Lv5. /",
    ("chunk_03_translated.json", 38, 134): "Handles alchemy. / Sorc & Holy Magic / up to Lv4. /",
    ("chunk_03_translated.json", 38, 135): "Longbow user. Lowers / traps, steals items / Sorc+Holy Lv3. /",
    ("chunk_03_translated.json", 38, 136): "Staffs & knuckles. / Dispel vs undead. / Holy Magic Lv5. /",
    ("chunk_03_translated.json", 38, 137): "Holy aura heals HP. / Can learn Dispel. / Sorc+Holy Lv6. /",
    ("chunk_03_translated.json", 38, 138): "Removes curses from / equipped items. / Sorcery Lv6. /",
    ("chunk_03_translated.json", 38, 139): "Great EXP & insta- / kill. Sees in fog. / Sorcery Lv5. /",
    ("chunk_03_translated.json", 38, 140): "Dual wields same / weapon type. Learns / Sorcery Lv6. /",
    ("chunk_03_translated.json", 38, 141): "Longbow. Best trap / skill. Steals items / Sorc+Holy Lv4. /",
    ("chunk_03_translated.json", 38, 145): "Affects max HP, / status resist, and / revival success. /",
    # chunk_04: r41 church, r42 inn
    ("chunk_04_translated.json", 41, 1): "Salem Church. What / business brings you / here? /",
    ("chunk_04_translated.json", 41, 5): "No offering, no / divine power! / Begone, heretic! /",
    ("chunk_04_translated.json", 41, 13): "Need aid? Bring an / offering and return / anytime. /",
    ("chunk_04_translated.json", 42, 6): "Rest well? Good rest / fuels tomorrow. / Visit again. /",
    # chunk_06: r45 shop
    ("chunk_06_translated.json", 45, 46): "Want it uncursed? / Bein' cursed all / the time hurts! /",
    # chunk_07: r45, r46
    ("chunk_07_translated.json", 45, 186): "They're fighting / right now, can't / hire 'em yet. /",
    ("chunk_07_translated.json", 46, 1): "Bulletin board for / Duhan citizens to / share opinions. /",
    ("chunk_07_translated.json", 46, 2): "Miri here. Never / mind the Kreta / stone request. /",
    ("chunk_07_translated.json", 46, 3): "Self-Seraph Shop / sells a strange key / What's it unlock? /",
    ("chunk_07_translated.json", 46, 4): "Vigger Shop seeks / part-time workers! / All are welcome! /",
    ("chunk_07_translated.json", 46, 5): "Vigger Shop has / many orcs. Do they / hire orc workers? /",
    ("chunk_07_translated.json", 46, 6): "Friendly orcs are / welcome! We have 3 / already. Join us! /",
    ("chunk_07_translated.json", 46, 7): "Got lost on 4F, met / a Hobbit & Imp who / gave me a cure. /",
    # chunk_09: r2654 formation descriptions
    ("chunk_09_translated.json", 2654, 1): "2 front row strike / 1 enemy together / for heavy damage. /",
    ("chunk_09_translated.json", 2654, 2): "Back magic boosts / front weapons. 1 hit / but high accuracy. /",
    ("chunk_09_translated.json", 2654, 3): "Back magic stuns foe / for front attack. / 1 hit, high acc. /",
    ("chunk_09_translated.json", 2654, 4): "Back magic lifts / front for jump atk. / 1 hit, no DEF. /",
    ("chunk_09_translated.json", 2654, 5): "2 front hit both / enemy rows in sync. / 1 hit, no miss. /",
    ("chunk_09_translated.json", 2654, 6): "2 back seal foe, / 2 front strike. vs / high EVA/HP foes. /",
    ("chunk_09_translated.json", 2654, 7): "All front defend. / Boosts EVA & DEF. / Blocks status+RUSH /",
    ("chunk_09_translated.json", 2654, 8): "2 back cast barrier. / Cuts magic damage, / boosts RES rate. /",
    ("chunk_09_translated.json", 2654, 9): "All back cast strong / barrier. No spells / from either side. /",
    ("chunk_09_translated.json", 2654, 10): "All back make decoy / images. Images take / hits for party. /",
    ("chunk_09_translated.json", 2654, 11): "Party scatters to / cut breath+magic dmg / Phys dmg rises. /",
    ("chunk_09_translated.json", 2654, 12): "Party evades. Big / EVA/DEF boost, but / magic dmg goes up. /",
    ("chunk_09_translated.json", 2654, 13): "When front is hit, / back counters with / ranged attacks. /",
    ("chunk_09_translated.json", 2654, 14): "All back fire first / to boost front row / hit rate. /",
    ("chunk_09_translated.json", 2654, 15): "Back attacks to / cancel enemy spells. / Limited per turn. /",
    ("chunk_09_translated.json", 2654, 16): "Back attacks to / cancel enemy breath / Limited per turn. /",
    ("chunk_09_translated.json", 2654, 17): "Front takes hits for / guarded back row. / Blocks ranged too. /",
    ("chunk_09_translated.json", 2654, 18): "Decoy retreats, / others flank to / stop enemy combos. /",
    ("chunk_09_translated.json", 2654, 19): "3 back expand spell / range. Lowers foe / resist+boosts pow. /",
    ("chunk_09_translated.json", 2654, 20): "All back dispel. / Cures Mute, breaks / foe magic shells. /",
    ("chunk_09_translated.json", 2654, 21): "2 back cast same / spell in doses for / faster casting. /",
    ("chunk_09_translated.json", 2654, 22): "Back enchants wpn. / Hit bypasses foe / resist & Mag Shell /",
    ("chunk_09_translated.json", 2654, 23): "2 back cast same / spell together for / big power boost. /",
    ("chunk_09_translated.json", 2654, 24): "3 front hit 1 foe / in sequence. Each / hit does more dmg. /",
    ("chunk_09_translated.json", 2654, 25): "1 front decoys, / 2 sneak behind foe. / High acc & dmg. /",
    ("chunk_09_translated.json", 2654, 26): "Lift foe into air / then strike as they / fall. Big damage. /",
    ("chunk_09_translated.json", 2654, 27): "All attack all foes. / Can't dodge unless / Front Guard active /",
    ("chunk_09_translated.json", 2654, 28): "2 front feint, 1 / aims weak point. / Crit rate way up. /",
    ("chunk_09_translated.json", 2654, 29): "2 form Holy Symbol / for powerful Dispel / Strong vs undead. /",
    ("chunk_09_translated.json", 2654, 30): "1 back warps 3 front / to atk from above. / Ignores DEF. Safe /",
    ("chunk_09_translated.json", 2654, 31): "2 charge through / foe for damage. / Hits undead too. /",
    ("chunk_09_translated.json", 2654, 32): "2 front swing to / make a sonic wave / hits foes behind. /",
    # chunk_r37_extra: keyboard grids - keep as-is, mark as special
    ("chunk_r37_extra.json", 37, 19): None,
    ("chunk_r37_extra.json", 37, 20): None,
    ("chunk_r37_extra.json", 37, 21): None,
    # chunk_r38_fix: duplicates of chunk_02/03 entries
    ("chunk_r38_fix.json", 38, 117): "Gender sets base / stats. Men=strong, / women=wise. /",
    ("chunk_r38_fix.json", 38, 118): "Human: High faith / & balanced stats / overall. /",
    ("chunk_r38_fix.json", 38, 119): "Elf: High INT & VIT / but frail. Best / at magic. /",
    ("chunk_r38_fix.json", 38, 120): "Gnome: High faith / & agility. Suited / for Priests. /",
    ("chunk_r38_fix.json", 38, 121): "Dwarf: Slow but / strong with deep / faith. Fighters. /",
    ("chunk_r38_fix.json", 38, 122): "Hobbit: Small but / agile and lucky. / Born thieves. /",
    ("chunk_r38_fix.json", 38, 123): "Good=justice. May / turn Evil. FIG MAG / PRI SAM GIZ BIS+ /",
    ("chunk_r38_fix.json", 38, 124): "Neutral=no bias. / FIG THI MAG SAM / GIZ ALC MON /",
    ("chunk_r38_fix.json", 38, 125): "Evil=self-serving. / FIG THI MAG PRI / NIN BIS ALC /",
    ("chunk_r38_fix.json", 38, 127): "Lowers trap level / & finds chests. / Sorcery Lv3. /",
    ("chunk_r38_fix.json", 38, 129): "Holy magic master. / Can Dispel undead. / All Holy spells. /",
    ("chunk_r38_fix.json", 38, 130): "Great EXP gain. Can / instant-kill foes. / Sorcery up to Lv2. /",
    ("chunk_r38_fix.json", 38, 131): "Knight gear usable. / Learns Sorcery / up to Lv5. /",
    ("chunk_r38_fix.json", 38, 132): "Restores HP. Dispel / vs undead. Sorc & / Holy Magic Lv6. /",
    ("chunk_r38_fix.json", 38, 133): "Poleaxe weapons. / Dispel vs undead. / Holy Magic Lv5. /",
    ("chunk_r38_fix.json", 38, 134): "Handles alchemy. / Sorc & Holy Magic / up to Lv4. /",
    ("chunk_r38_fix.json", 38, 135): "Longbow user. Lowers / traps, steals items / Sorc+Holy Lv3. /",
    ("chunk_r38_fix.json", 38, 136): "Staffs & knuckles. / Dispel vs undead. / Holy Magic Lv5. /",
    ("chunk_r38_fix.json", 38, 137): "Holy aura heals HP. / Can learn Dispel. / Sorc+Holy Lv6. /",
    ("chunk_r38_fix.json", 38, 138): "Removes curses from / equipped items. / Sorcery Lv6. /",
    ("chunk_r38_fix.json", 38, 139): "Great EXP & insta- / kill. Sees in fog. / Sorcery Lv5. /",
    ("chunk_r38_fix.json", 38, 140): "Dual wields same / weapon type. Learns / Sorcery Lv6. /",
    ("chunk_r38_fix.json", 38, 141): "Longbow. Best trap / skill. Steals items / Sorc+Holy Lv4. /",
    ("chunk_r38_fix.json", 38, 145): "Affects max HP, / status resist, and / revival success. /",
    # chunk_r40_r42
    ("chunk_r40_r42_translated.json", 40, 44): "Can't change class / with gear on. / Unequip first. /",
    ("chunk_r40_r42_translated.json", 41, 2): "Salem Church. What / business do you / have here? /",
    ("chunk_r40_r42_translated.json", 41, 3): "Welcome to Salem / Church. Looks like / you need our help. /",
    ("chunk_r40_r42_translated.json", 41, 6): "No tithe, no divine / aid! Begone, / heretic! /",
    ("chunk_r40_r42_translated.json", 41, 7): "Without offering / to the gods, you / will be punished. /",
    ("chunk_r40_r42_translated.json", 41, 8): "Without offering / to the gods, you / will be punished. /",
    ("chunk_r40_r42_translated.json", 41, 9): "Without offering / to the gods, you / will be punished. /",
    ("chunk_r40_r42_translated.json", 41, 10): "Without offering / to the gods, you / will be punished. /",
    ("chunk_r40_r42_translated.json", 41, 11): "Without offering / to the gods, you / will be punished. /",
    ("chunk_r40_r42_translated.json", 41, 12): "Without offering / to the gods, you / will be punished. /",
    ("chunk_r40_r42_translated.json", 41, 13): "Without offering / to the gods, you / will be punished. /",
    ("chunk_r40_r42_translated.json", 41, 14): "Need our help? Bring / an offering and / come see us. /",
    ("chunk_r40_r42_translated.json", 42, 2): "Welcome to the inn. / Rest your body and / gain strength. /",
    ("chunk_r40_r42_translated.json", 42, 7): "Rest well? Good rest / brings strength. / Come again. /",
    # chunk_r43_r45
    ("chunk_r43_r45_translated.json", 44, 4): "Form magic stones / from medals your / knights collected. /",
    ("chunk_r43_r45_translated.json", 44, 8): "Use magic stones / to power up the / automata. /",
    ("chunk_r43_r45_translated.json", 45, 71): "Rest stop = safety / even when hurt! / No EXP though. /",
    # batch_06: type-2 with long words
    ("batch_06.json", 1208, 355): "Hey there, / member number ! /",
    ("batch_06.json", 1208, 445): "You poured the / potion into the / fountain. /",
    ("batch_06.json", 1209, 29): "Hey, I finally / found you... / Big Sister........ /",
    ("batch_06.json", 1209, 366): "Oh, member number! / Welcome aboard! /",
    ("batch_06.json", 1209, 376): "1 point! Let the / Member Number / Lottery begin! /",
    ("batch_06.json", 1209, 377): "3 points! Let the / Member Number / Lottery begin! /",
    ("batch_06.json", 1209, 378): "5 points! Let the / Member Number / Lottery begin! /",
    ("batch_r39_equip_a.json", 39, 346): "Beat me at 5 rounds / of Rock-Paper- / Scissors for loot! /",
}


# ---- SCAN ALL FILES ----
all_issues = []

chunk_dir = os.path.join(BASE, "data/translate_chunks")
for fname in sorted(os.listdir(chunk_dir)):
    if not fname.endswith(".json") or fname.endswith(".master"):
        continue
    if "_translated" not in fname and "_fix" not in fname and "_extra" not in fname:
        continue
    data = json.load(open(os.path.join(chunk_dir, fname), encoding="utf-8"))
    if not isinstance(data, list):
        continue
    for entry in data:
        eng = entry.get("english")
        if not eng or not isinstance(eng, str):
            continue
        resource = entry.get("resource", "?")
        msg_idx = entry.get("message", "?")
        if resource == 37 and msg_idx in (17, 18):
            continue

        lines = normalize_and_split(eng)
        if not lines:
            continue

        overflow = len(lines) > MAX_LINES
        too_wide = any(len(l) > MAX_CHARS for l in lines)

        if overflow or too_wide:
            all_issues.append({
                "file": fname,
                "dir": "translate_chunks",
                "category": "chunk",
                "resource": resource,
                "msg_index": msg_idx,
                "english": eng,
                "lines": lines,
                "num_lines": len(lines),
                "longest": max(len(l) for l in lines),
                "overflow": overflow,
                "too_wide": too_wide,
            })

type2_dir = os.path.join(BASE, "data/type2_translated")
for fname in sorted(os.listdir(type2_dir)):
    if not fname.endswith(".json") or fname.endswith(".master"):
        continue
    data = json.load(open(os.path.join(type2_dir, fname), encoding="utf-8"))
    if not isinstance(data, list):
        continue
    for entry in data:
        eng = entry.get("english")
        if not eng or not isinstance(eng, str):
            continue
        resource = entry.get("resource", "?")
        msg_idx = entry.get("msg_index", "?")

        lines = normalize_and_split(eng)
        if not lines:
            continue

        long_words = []
        for seg in lines:
            for w in seg.split():
                if len(w) > 18:
                    long_words.append(w)

        if long_words:
            all_issues.append({
                "file": fname,
                "dir": "type2_translated",
                "category": "type2",
                "resource": resource,
                "msg_index": msg_idx,
                "english": eng,
                "lines": lines,
                "num_lines": len(lines),
                "longest": max(len(w) for w in long_words),
                "overflow": False,
                "too_wide": True,
                "long_words": long_words,
            })


# ---- GENERATE REWRITES ----
patches = []
for issue in all_issues:
    key = (issue["file"], issue["resource"], issue["msg_index"])

    if key in MANUAL:
        rw = MANUAL[key]
        if rw is None:
            # Keyboard grid - keep as-is
            patches.append({
                "file": issue["file"],
                "dir": issue["dir"],
                "resource": issue["resource"],
                "msg_index": issue["msg_index"],
                "original": issue["english"],
                "rewrite": issue["english"],
                "auto": True,
                "note": "keyboard grid - no rewrite needed",
            })
            issue["rewrite"] = issue["english"]
            continue
        else:
            issue["rewrite"] = rw
            patches.append({
                "file": issue["file"],
                "dir": issue["dir"],
                "resource": issue["resource"],
                "msg_index": issue["msg_index"],
                "original": issue["english"],
                "rewrite": rw,
                "auto": True,
            })
            continue

    # Try auto-rewrite
    rw = propose_rewrite(issue["english"], issue["lines"])
    issue["rewrite"] = rw
    p = {
        "file": issue["file"],
        "dir": issue["dir"],
        "resource": issue["resource"],
        "msg_index": issue["msg_index"],
        "original": issue["english"],
        "rewrite": rw,
        "auto": rw is not None,
    }
    if not rw:
        p["reason"] = "Too long for auto-wrap; needs manual condensing"
    patches.append(p)


# ---- VALIDATE ----
errors = 0
for p in patches:
    rw = p.get("rewrite")
    if not rw or rw == p["original"]:
        continue
    rw_lines = normalize_and_split(rw)
    if len(rw_lines) > MAX_LINES:
        print(f"VALIDATE ERROR: {len(rw_lines)} lines in [{p['file']}] r{p['resource']} msg{p['msg_index']}")
        print(f"  Rewrite: {rw}")
        errors += 1
    for i, l in enumerate(rw_lines):
        if len(l) > MAX_CHARS:
            print(f"VALIDATE ERROR: L{i+1} is {len(l)}ch in [{p['file']}] r{p['resource']} msg{p['msg_index']}")
            print(f"  Line: \"{l}\"")
            errors += 1


# ---- STATS ----
chunk_issues = [i for i in all_issues if i["category"] == "chunk"]
type2_issues = [i for i in all_issues if i["category"] == "type2"]
overflow_issues = [i for i in all_issues if i["overflow"]]
auto_ok = [p for p in patches if p["auto"]]
needs_manual = [p for p in patches if not p["auto"]]
has_rewrite = [p for p in patches if p.get("rewrite") and p["rewrite"] != p["original"]]

print(f"\n=== FINAL AUDIT RESULTS ===")
print(f"Total flagged entries: {len(all_issues)}")
print(f"  Chunk (type-1): {len(chunk_issues)} (overflow: {len([i for i in chunk_issues if i['overflow']])}, wide: {len([i for i in chunk_issues if i['too_wide']])})")
print(f"  Type-2: {len(type2_issues)} (unwrappable long words)")
print(f"With rewrites: {len(has_rewrite)}")
print(f"Needs manual rewrite: {len(needs_manual)}")
print(f"Validation errors: {errors}")

if needs_manual:
    print(f"\nEntries still needing manual rewrite:")
    for p in needs_manual:
        flat = " ".join(normalize_and_split(p["original"]))
        print(f"  [{p['file']}] r{p['resource']} msg{p['msg_index']}: ({len(flat)}ch) {flat[:100]}")


# ---- WRITE OUTPUTS ----
outdir = os.path.join(BASE, "runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese")
os.makedirs(outdir, exist_ok=True)

# JSON patches
patch_path = os.path.join(outdir, "overflow_patches.json")
with open(patch_path, "w", encoding="utf-8") as f:
    json.dump(patches, f, indent=2, ensure_ascii=False)
print(f"\nPatches saved to {patch_path}")

# Markdown report
R = []
R.append("# Global Overflow Audit - Busin 0 Translation")
R.append("")
R.append("Generated: 2026-05-28")
R.append("")
R.append("## Summary")
R.append("")
R.append(f"- **Total flagged entries**: {len(all_issues)}")
R.append(f"- **Type-1 (chunk) issues**: {len(chunk_issues)}")
R.append(f"  - Overflow (>3 lines): {len([i for i in chunk_issues if i['overflow']])}")
R.append(f"  - Wide lines (>20 chars): {len([i for i in chunk_issues if i['too_wide']])}")
R.append(f"- **Type-2 (batch) issues**: {len(type2_issues)} (words >18 chars that break word-wrap)")
R.append(f"- **Entries with proposed rewrites**: {len(has_rewrite)}")
R.append(f"- **Still needs manual rewrite**: {len(needs_manual)}")
R.append("")
R.append("## Architecture Notes")
R.append("")
R.append("### Type-1 (chunk files) -- Fixed UI labels")
R.append("- Item names, menu options, chargen descriptions, dungeon messages")
R.append("- ` / ` = explicit FFFE line break token")
R.append("- NO auto word-wrapping -- text must be pre-formatted by translator")
R.append("- Hard limit: 3 lines max, ~20 chars per line (224px box at 12px/glyph)")
R.append("- **Every overflow/wide entry here is a real display bug**")
R.append("")
R.append("### Type-2 (batch files) -- Dialogue and narration")
R.append("- `encode_text()` in build pipeline auto-wraps at 18 chars/line, 3 lines/page")
R.append("- Auto page-breaks via FFD2 token after every 3 lines")
R.append("- ` / ` = explicit line break within auto-wrapped text")
R.append("- Only issue: individual words >18 chars that cannot be split by word-wrap")
R.append("")
R.append("### Trailing ` /` normalization")
R.append("- Build pipeline normalizes trailing ` /` to ` / ` before splitting")
R.append("- This audit applies the same normalization to avoid false positives")
R.append("")
R.append("## Breakdown by File")
R.append("")

by_file = defaultdict(lambda: {"overflow": 0, "wide": 0, "total": 0})
for i in all_issues:
    by_file[i["file"]]["total"] += 1
    if i["overflow"]:
        by_file[i["file"]]["overflow"] += 1
    if i["too_wide"]:
        by_file[i["file"]]["wide"] += 1

R.append("| File | Total | Overflow | Wide |")
R.append("|------|-------|----------|------|")
for f in sorted(by_file.keys()):
    v = by_file[f]
    R.append(f"| {f} | {v['total']} | {v['overflow']} | {v['wide']} |")

R.append("")
R.append("---")
R.append("")
R.append("## Overflow Entries (>3 lines) -- CRITICAL")
R.append("")
R.append(f"**{len(overflow_issues)} entries** have more lines than the 3-line display box can show.")
R.append("")

for i in sorted(overflow_issues, key=lambda x: (x["file"], x["resource"], x["msg_index"])):
    R.append(f"### [{i['file']}] r{i['resource']} msg{i['msg_index']} -- {i['num_lines']} lines")
    R.append("")
    R.append("**Current:**")
    R.append("```")
    for idx, l in enumerate(i["lines"]):
        marker = " <-- WIDE" if len(l) > MAX_CHARS else ""
        R.append(f"  L{idx+1} ({len(l):2d}ch): {l}{marker}")
    R.append("```")
    rw = i.get("rewrite")
    if rw and rw != i["english"]:
        rw_lines = normalize_and_split(rw)
        R.append("**Proposed rewrite:**")
        R.append("```")
        for idx, l in enumerate(rw_lines):
            R.append(f"  L{idx+1} ({len(l):2d}ch): {l}")
        R.append("```")
    elif not rw:
        R.append("**Status:** NEEDS MANUAL REWRITE")
    R.append("")

wide_only = [i for i in all_issues if i["too_wide"] and not i["overflow"]]

R.append("---")
R.append("")
R.append("## Wide Lines (>20 chars, <=3 lines)")
R.append("")
R.append(f"**{len(wide_only)} entries** fit in 3 lines but have individual lines exceeding ~20 char width.")
R.append("")

for i in sorted(wide_only, key=lambda x: (x["file"], x["resource"], x["msg_index"])):
    R.append(f"### [{i['file']}] r{i['resource']} msg{i['msg_index']}")
    R.append("")
    R.append("**Current:**")
    R.append("```")
    for idx, l in enumerate(i["lines"]):
        marker = " <-- WIDE" if len(l) > MAX_CHARS else ""
        R.append(f"  L{idx+1} ({len(l):2d}ch): {l}{marker}")
    R.append("```")
    rw = i.get("rewrite")
    if rw and rw != i["english"]:
        rw_lines = normalize_and_split(rw)
        R.append("**Proposed rewrite:**")
        R.append("```")
        for idx, l in enumerate(rw_lines):
            R.append(f"  L{idx+1} ({len(l):2d}ch): {l}")
        R.append("```")
    elif not rw:
        R.append("**Status:** NEEDS MANUAL REWRITE")
    if i.get("long_words"):
        R.append(f"**Long words:** {', '.join(i['long_words'])}")
    R.append("")

report_path = os.path.join(outdir, "global_overflow_audit.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(R))
print(f"Report saved to {report_path} ({len(R)} lines)")
