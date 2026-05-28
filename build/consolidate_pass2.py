import json
from collections import defaultdict

with open("data/msg_glyph_map.json", "r", encoding="utf-8") as f:
    master = json.load(f)
print(f"Starting master map has {len(master)} entries")

agent_inferences = defaultdict(list)

json_files = {
    "r38": "data/inferred_r38.json",
    "r39": "data/inferred_r39.json",
    "r40": "data/inferred_r40.json",
    "r41": "data/inferred_r41.json",
    "r43": "data/inferred_r43.json",
    "r44": "data/inferred_r44.json",
    "r46": "data/inferred_r46.json",
    "r47": "data/inferred_r47.json",
}

for agent_name, filepath in json_files.items():
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    mappings = data.get("inferred_mappings", data)
    for gid, info in mappings.items():
        if gid.startswith("_"): continue
        if not isinstance(info, dict): continue
        ch = info.get("char") or info.get("character")
        conf = (info.get("confidence") or "LOW").upper()
        if ch is None or ch.startswith("[") or ch in ("", "\u3000"): continue
        if "HIGH" in conf: conf = "HIGH"
        elif "MED" in conf: conf = "MEDIUM"
        else: conf = "LOW"
        agent_inferences[gid].append((ch, conf, agent_name))

added = {}
corrected = {}
skipped_already = 0

# === CORRECTIONS ===
if master.get("198") != "\u30ab":
    old = master.get("198")
    master["198"] = "\u30ab"
    corrected["198"] = {"old": old, "new": "\u30ab", "reason": "Katakana grid; r38+r46 agree"}
    print(f"CORRECTION: 198: {old} -> \u30ab")

if master.get("358") != "\u5916":
    old = master.get("358")
    master["358"] = "\u5916"
    corrected["358"] = {"old": old, "new": "\u5916", "reason": "r40: all contexts require hazusu/remove"}
    print(f"CORRECTION: 358: {old} -> \u5916")

if master.get("369") == "\u898b":
    print("369 already correct")
else:
    old = master.get("369")
    master["369"] = "\u898b"
    corrected["369"] = {"old": old, "new": "\u898b", "reason": "r38+r46 agree"}

if master.get("341") == "\u4e0d":
    print("341 already correct")

# === MERGE FROM JSON FILES ===
for gid, inferences in agent_inferences.items():
    if gid in master:
        existing = master[gid]
        disagrees = [x for x in inferences if x[0] != existing]
        if not disagrees:
            skipped_already += 1
        continue
    char_votes = defaultdict(list)
    for ch, conf, agent in inferences:
        char_votes[ch].append((conf, agent))
    best_char = None
    best_score = 0
    best_voters = []
    for ch, voters in char_votes.items():
        high_count = sum(1 for c, a in voters if c == "HIGH")
        med_count = sum(1 for c, a in voters if c == "MEDIUM")
        score = high_count * 3 + med_count * 2 + len(voters)
        if score > best_score:
            best_score = score
            best_char = ch
            best_voters = voters
    if best_char is None: continue
    high_voters = [v for v in best_voters if v[0] == "HIGH"]
    med_voters = [v for v in best_voters if v[0] == "MEDIUM"]
    if len(high_voters) >= 1 or len(med_voters) >= 2 or len(best_voters) >= 2:
        master[gid] = best_char
        added[gid] = {"char": best_char, "agents": [v[1] for v in best_voters]}

# === EXTRAS FROM FINDINGS (not always in JSON) ===
extras = {
    "972": "\u901a", "765": "\u5730", "766": "\u5e74", "578": "\u8857",
    "1012": "\u9854", "397": "\u6bd2", "355": "\u6bba", "423": "\u826f",
    "860": "\u5fd8", "309": "\u5fcd", "525": "\u5b64", "526": "\u72ec",
    "343": "\u52d9", "843": "\u5834", "868": "\u9023", "869": "\u643a",
    "636": "\u9055", "637": "\u5fdc", "677": "\u9451", "994": "\u4ee5",
    "328": "\u4e0a", "535": "\u5fcd", "969": "\u4e86", "698": "\u7d42",
    "610": "\u601d", "618": "\u8003", "534": "\u611f",
    "344": "\u6094", "887": "\u4fa1",
    "505": "\u5730", "515": "\u6761", "547": "\u8a72",
    "576": "\u540c", "691": "\u4e26", "706": "\u54e1",
    "944": "\u53d6", "665": "\u640d",
    "669": "\u5fa1", "670": "\u7528", "913": "\u8abf", "928": "\u8a2d",
    "315": "\u76d7", "833": "\u623b", "857": "\u7a81", "858": "\u7136",
    "406": "\u5c01", "590": "\u5ea6", "398": "\u5e30",
}
for gid, ch in extras.items():
    if gid not in master:
        master[gid] = ch
        added[gid] = {"char": ch, "agents": ["findings"]}

sorted_master = dict(sorted(master.items(), key=lambda x: int(x[0])))

with open("data/msg_glyph_map.json", "w", encoding="utf-8") as f:
    json.dump(sorted_master, f, ensure_ascii=False, indent=2)

print(f"\n=== SECOND CONSOLIDATION SUMMARY ===")
print(f"Previous count: 428")
print(f"Corrections applied: {len(corrected)}")
for gid, info in corrected.items():
    print(f"  {gid}: {info['old']} -> {info['new']} ({info['reason']})")
print(f"New mappings added: {len(added)}")
print(f"Skipped (already in master): {skipped_already}")
print(f"Final count: {len(sorted_master)}")

report = {
    "previous_count": 428,
    "corrections": corrected,
    "added_count": len(added),
    "added": {k: v for k, v in sorted(added.items(), key=lambda x: int(x[0]))},
    "final_count": len(sorted_master),
}
with open("data/consolidation2_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
