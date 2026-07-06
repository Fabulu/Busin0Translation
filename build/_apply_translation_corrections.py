"""Apply reviewed translation corrections. Verify-before-replace per record.
Reports CHANGED / SKIPPED. UTF-8 file IO, ASCII stdout only."""
import json, io, sys

ROOT = r"C:\programmieren\wizardrytranslation"
changed = []
skipped = []

def load(rel):
    with io.open(ROOT + "\\" + rel, "r", encoding="utf-8") as f:
        return json.load(f)

def save(rel, data):
    with io.open(ROOT + "\\" + rel, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

# ---- helpers operating on list-of-dict files keyed by (resource,message) or (resource,msg_index)
def patch_list(rel, matchkeys, idfields, oldval, newval, valfield="english", label=None):
    """matchkeys: dict of field->value to identify record. oldval expected current value."""
    data = load(rel)
    found = None
    for rec in data:
        if all(rec.get(k) == v for k, v in matchkeys.items()):
            found = rec
            break
    tag = label or (rel + " " + str(matchkeys))
    if found is None:
        skipped.append((tag, "not-found"))
        return data, False
    cur = found.get(valfield)
    if cur != oldval:
        skipped.append((tag, "drift: current=%r expected=%r" % (cur, oldval)))
        return data, False
    found[valfield] = newval
    changed.append((tag, oldval, newval))
    return data, True

# ---- helper for dict-keyed file (name_labels.json)
def patch_namelabel(rel, key, oldval, newval):
    data = load(rel)
    tag = rel + " key=%r" % key
    if key not in data:
        skipped.append((tag, "not-found"))
        return data, False
    if data[key] != oldval:
        skipped.append((tag, "drift: current=%r expected=%r" % (data[key], oldval)))
        return data, False
    data[key] = newval
    changed.append((tag, oldval, newval))
    return data, True

# =========================================================
# 1. name_labels.json  kai-kyuu glyph-corrupted -> Priest
rel = "data\\name_labels.json"
data, ok = patch_namelabel(rel, "開救", "Receptionist", "Priest")
if ok: save(rel, data)

# 2. chunk_r38_fix.json r38 m54 Coward -> Brave (budget ~6: "Brave" fits)
rel = "data\\translate_chunks\\chunk_r38_fix.json"
data, ok = patch_list(rel, {"resource": 38, "message": 54}, None,
                       "Coward / ", "Brave / ", label="r38 m54 personality")
if ok: save(rel, data)

# 3. chunk_00 r34 m26 Knight's Wristband -> Soldier's Wristband (budget OK, 19<=21 siblings)
rel = "data\\translate_chunks\\chunk_00_translated.json"
data, ok = patch_list(rel, {"resource": 34, "message": 26}, None,
                       "Knight's Wristband / ", "Soldier's Wristband / ",
                       label="r34 m26 item")
if ok: save(rel, data)

# 4. batch_03 r1203 msg_index 504 & 511 guard -> minding the store
rel = "data\\type2_translated\\batch_03.json"
data = load(rel)
for mi in (504, 511):
    rec = next((r for r in data if r.get("resource") == 1203 and r.get("msg_index") == mi), None)
    tag = "r1203 mi=%d" % mi
    old = "Me's Ade. I work / at the Vigger / Shop as a guard."
    new = "Me's Ade. I work / at the Vigger Shop, / minding the store."
    if rec is None:
        skipped.append((tag, "not-found")); continue
    if rec.get("english") != old:
        skipped.append((tag, "drift: %r" % rec.get("english"))); continue
    rec["english"] = new
    changed.append((tag, old, new))
save(rel, data)

# 5. batch_06 r1208 mi=826 Captain -> Simzon (name)
rel = "data\\type2_translated\\batch_06.json"
data = load(rel)
rec = next((r for r in data if r.get("resource") == 1208 and r.get("msg_index") == 826), None)
tag = "r1208 mi=826"
if rec is None:
    skipped.append((tag, "not-found"))
elif rec.get("english") != "But, Captain!":
    skipped.append((tag, "drift: %r" % rec.get("english")))
else:
    old = rec["english"]; rec["english"] = "But, Simzon!"
    changed.append((tag, old, "But, Simzon!"))
# 13. r1209 mi 259 & 261 (same file)
for mi, old, new in (
    (259, "Thank you very much. Whose fortune do you want me to read?",
          "Thank you! Whose fortune shall I read?"),
    (261, "So whose fortune do you want me to read?",
          "Whose fortune shall I read?"),
):
    rec = next((r for r in data if r.get("resource") == 1209 and r.get("msg_index") == mi), None)
    tag = "r1209 mi=%d" % mi
    if rec is None:
        skipped.append((tag, "not-found")); continue
    if rec.get("english") != old:
        skipped.append((tag, "drift: %r" % rec.get("english"))); continue
    rec["english"] = new
    changed.append((tag, old, new))
save(rel, data)

# 6. chunk_r34_fix r34 m388 Divine Lord Sword -> Shrine Priest Sword
#    budget: siblings up to ~21 chars ship. "Shrine Priest Sword"=19 OK.
rel = "data\\translate_chunks\\chunk_r34_fix.json"
data = load(rel)
def r34(mi, old, new, jpcheck=None):
    rec = next((r for r in data if r.get("resource") == 34 and r.get("message") == mi), None)
    tag = "r34 m%d" % mi
    if rec is None:
        skipped.append((tag, "not-found")); return
    if jpcheck is not None and jpcheck not in rec.get("japanese", ""):
        skipped.append((tag, "jp-mismatch: %r lacks %r" % (rec.get("japanese"), jpcheck))); return
    if rec.get("english") != old:
        skipped.append((tag, "drift: %r" % rec.get("english"))); return
    rec["english"] = new
    changed.append((tag, old, new))

r34(388, "Divine Lord Sword / ", "Shrine Priest Sword / ")
# 9. equipment 兵士 -> Soldier; verify JP contains 兵士 (NOT 騎士)
HEISHI = "兵士"   # 兵士
r34(157, "Holy Knight Armor / ",     "Holy Soldier Armor / ",     jpcheck=HEISHI)
r34(170, "Holy Knight Helm / ",      "Holy Soldier Helm / ",      jpcheck=HEISHI)
r34(191, "Holy Knight Shield / ",    "Holy Soldier Shield / ",    jpcheck=HEISHI)
r34(203, "Holy Knight Gauntlets / ", "Holy Soldier Gauntlets / ", jpcheck=HEISHI)
r34(391, "Holy Knight Sword / ",     "Holy Soldier Sword / ",     jpcheck=HEISHI)
r34(437, "Holy Knight Axe / ",       "Holy Soldier Axe / ",       jpcheck=HEISHI)
r34(726, "Knight Soul / ",           "Soldier Soul / ",           jpcheck=HEISHI)
r34(731, "Holy Knight Soul / ",      "Holy Soldier Soul / ",      jpcheck=HEISHI)
r34(732, "Dark Knight Soul / ",      "Dark Soldier Soul / ",      jpcheck=HEISHI)
save(rel, data)

# 7. R39 兵士団 Knight Order -> Soldier Corps  (actually in batch_r39_equip_a.json)
rel = "data\\type2_translated\\batch_r39_equip_a.json"
data = load(rel)
def r39(mi, find, repl):
    rec = next((r for r in data if r.get("resource") == 39 and r.get("msg_index") == mi), None)
    tag = "r39 mi=%d (batch_r39_equip_a)" % mi
    if rec is None:
        skipped.append((tag, "not-found")); return
    cur = rec.get("english", "")
    if find not in cur:
        skipped.append((tag, "drift: %r lacks %r" % (cur, find))); return
    old = cur; rec["english"] = cur.replace(find, repl)
    changed.append((tag, old, rec["english"]))
r39(398, "Knight Order", "Soldier Corps")
r39(353, "Knight Order", "Soldier Corps")
r39(360, "Knight Order", "Soldier Corps")
save(rel, data)

# 8. chunk_r36 r36 m112 Open God -> Reaper (死神 corrupted to 開神)
rel = "data\\translate_chunks\\chunk_r36_translated.json"
data, ok = patch_list(rel, {"resource": 36, "message": 112}, None,
                      "Open God", "Reaper", label="r36 m112 monster")
if ok: save(rel, data)

# 10. chunk_r40_r42 R41 narrow-box shortenings
rel = "data\\translate_chunks\\chunk_r40_r42_translated.json"
data = load(rel)
def r41(mi, old, new):
    rec = next((r for r in data if r.get("resource") == 41 and r.get("message") == mi), None)
    tag = "r41 m%d" % mi
    if rec is None:
        skipped.append((tag, "not-found")); return
    if rec.get("english") != old:
        skipped.append((tag, "drift: %r" % rec.get("english"))); return
    rec["english"] = new
    changed.append((tag, old, new))
r41(1,  "Salem Church. What / business do you / have here? /",
        "Salem Church. / What is your / business here? /")
r41(2,  "Welcome to Salem / Church. Looks like / you need our help. /",
        "Welcome to Salem / Church. You seem / to need help. /")
r41(4,  "Then we shall accept / the offering the / church requires. /",
        "Then we accept / the offering the / church asks. /")
r41(13, "Need our help? Bring / an offering and / come see us. /",
        "Need help? Bring / an offering / and come back. /")
save(rel, data)

# 11. batch_02 R1202 M85 narrow-box
rel = "data\\type2_translated\\batch_02.json"
data, ok = patch_list(rel, {"resource": 1202, "msg_index": 85}, None,
    "Why do you want to work here? / Tell / Don't tell",
    "Why work here? / Tell / Don't tell", label="r1202 mi=85")
if ok: save(rel, data)

# 12. chunk_r37_r48_r49 R49 M61/M62 ladder prompts
rel = "data\\translate_chunks\\chunk_r37_r48_r49_translated.json"
data = load(rel)
def r49(mi, old, new):
    rec = next((r for r in data if r.get("resource") == 49 and r.get("message") == mi), None)
    tag = "r49 m%d" % mi
    if rec is None:
        skipped.append((tag, "not-found")); return
    if rec.get("english") != old:
        skipped.append((tag, "drift: %r" % rec.get("english"))); return
    rec["english"] = new
    changed.append((tag, old, new))
r49(62, "Climb down ladder? / confirm: o  cancel: / x /", "Climb down? / O: Yes  X: No")
r49(61, "Climb up the ladder? / confirm: o  cancel: / x /", "Climb up? / O: Yes  X: No")
save(rel, data)

# 14. chunk_05 R43 M8/M15, R44 M2/M8 narrow-box
rel = "data\\translate_chunks\\chunk_05_translated.json"
data = load(rel)
def chunk05(res, mi, old, new):
    rec = next((r for r in data if r.get("resource") == res and r.get("message") == mi), None)
    tag = "r%d m%d" % (res, mi)
    if rec is None:
        skipped.append((tag, "not-found")); return
    if rec.get("english") != old:
        skipped.append((tag, "drift: %r" % rec.get("english"))); return
    rec["english"] = new
    changed.append((tag, old, new))
chunk05(43, 8,  "Oh! / Wanna play a game? /   / ", "Oh! / Care for a game? /")
chunk05(43, 15, "Hey, you can't / play without gold. /   / ", "Hey, no gold, / no game. /")
chunk05(44, 2,  "I've been waiting. / How is the Automata / doing? / ",
                "I've been waiting. / How's the / Automata doing? /")
chunk05(44, 8,  "Combine weapons / and armor to create / Automata chips. / ",
                "Combine weapons / and armor into / Automata chips. /")
save(rel, data)

# ----- report
out = io.open(1, "w", encoding="ascii", errors="replace", closefd=False)
out.write("=== CHANGED (%d) ===\n" % len(changed))
for tag, o, n in changed:
    out.write("[OK] %s\n     %r -> %r\n" % (tag, o, n))
out.write("\n=== SKIPPED (%d) ===\n" % len(skipped))
for tag, reason in skipped:
    out.write("[SKIP] %s : %s\n" % (tag, reason))
out.flush()
