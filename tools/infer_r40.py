# -*- coding: utf-8 -*-
import struct, json, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RES_PATH = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources/0040_type01.bin"
MAP_PATH = "C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json"
INF_PATH = "C:/Programmieren/wizardrytranslation/tools/_inferred_raw.json"
OUT_PATH = "C:/Programmieren/wizardrytranslation/data/inferred_r40.json"
FINDINGS_PATH = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/infer-r40/FINDINGS.md"

with open(RES_PATH, "rb") as f:
    data = f.read()
with open(MAP_PATH, "r", encoding="utf-8") as f:
    glyph_map = json.load(f)
with open(INF_PATH, "r", encoding="utf-8") as f:
    inferred = json.load(f)

first_ffff = None
for off in range(0, len(data) - 1, 2):
    val = struct.unpack(">H", data[off:off+2])[0]
    if val == 0xFFFF:
        first_ffff = off
        break

stream = data[first_ffff:]
n = len(stream) // 2
vals = struct.unpack(f">{n}H", stream[:n*2])

messages = []
cur = []
for v in vals:
    if v == 0xFFFF:
        if cur: messages.append(cur)
        cur = []
    elif v == 0xFFFE:
        if cur: messages.append(cur)
        cur = []
    elif v >= 0xFFC0:
        pass
    else:
        cur.append(v)
if cur: messages.append(cur)

combined_map = dict(glyph_map)
for gid, info in inferred.items():
    combined_map[gid] = info["char"]

HIGH_IDS = {259,211,232,504,506,507,491,492,486,487,287,379,707,708,500,501,549,550,797,798,879,713,714,715,716,709,710,367,497}
MED_IDS = {205,208,488,489,490,502,503,510,515,511,517,546,576,691,799,893,705,543,544,547,548,613,704,728,257,234,233,258}

print("=== DECODED WITH INFERRED MAP ===")
decoded_messages = []
remaining_unknowns = set()
for i, msg in enumerate(messages):
    decoded = ""
    unknowns = []
    for g in msg:
        gs = str(g)
        if gs in combined_map:
            decoded += combined_map[gs]
        else:
            decoded += f"[{g}]"
            unknowns.append(g)
    print(f"MSG {i:3d}: {decoded}")
    decoded_messages.append({"index": i, "glyphs": list(msg), "decoded": decoded, "unknowns": sorted(set(unknowns))})
    if unknowns:
        print(f"         still unknown: {sorted(set(unknowns))}")
        remaining_unknowns.update(unknowns)

print(f"\nRemaining unknown glyph IDs ({len(remaining_unknowns)}): {sorted(remaining_unknowns)}")

output = {
    "_metadata": {
        "resource": "0040_type01.bin",
        "resource_index": 40,
        "context": "Adventurer Guild party management UI - Busin 0 (Wizardry Alternative Neo)",
        "total_messages": len(messages),
        "total_inferred_glyphs": len(inferred),
        "remaining_unknowns": sorted(remaining_unknowns)
    },
    "inferred_mappings": {},
    "decoded_messages": decoded_messages
}

for gid in sorted(inferred.keys(), key=lambda x: int(x)):
    info = inferred[gid]
    gid_int = int(gid)
    char = info["char"]
    if '\u3040' <= char <= '\u309F':
        ctype = "hiragana"
    elif '\u30A0' <= char <= '\u30FF':
        ctype = "katakana"
    elif '\u4E00' <= char <= '\u9FFF':
        ctype = "kanji"
    elif char.startswith("["):
        ctype = "control"
    else:
        ctype = "symbol"
    if gid_int in HIGH_IDS:
        confidence = "HIGH"
    elif gid_int in MED_IDS:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    output["inferred_mappings"][gid] = {"character": char, "type": ctype, "confidence": confidence, "evidence": info["evidence"]}

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print(f"\nSaved to {OUT_PATH}")

os.makedirs(os.path.dirname(FINDINGS_PATH), exist_ok=True)
high = sum(1 for v in output["inferred_mappings"].values() if v["confidence"] == "HIGH")
med = sum(1 for v in output["inferred_mappings"].values() if v["confidence"] == "MEDIUM")
low = sum(1 for v in output["inferred_mappings"].values() if v["confidence"] == "LOW")

with open(FINDINGS_PATH, "w", encoding="utf-8") as f:
    f.write("# Inferred Glyph Mappings for Resource 0040_type01.bin\n\n")
    f.write("## Context\n\n")
    f.write("Resource 40 is the **Adventurer Guild party management UI** in Busin 0.\n")
    f.write("84 messages covering: welcome, party composition, registration, class change,\n")
    f.write("delete member, party join/withdraw, sort options, error messages.\n\n")
    f.write("## Statistics\n\n")
    f.write(f"- Total messages: {len(messages)}\n")
    f.write(f"- Total inferred glyphs: {len(inferred)}\n")
    f.write(f"- Remaining unknowns: {len(remaining_unknowns)}\n")
    f.write(f"- HIGH confidence: {high}\n")
    f.write(f"- MEDIUM confidence: {med}\n")
    f.write(f"- LOW confidence: {low}\n\n")
    f.write("## Key Vocabulary\n\n")
    f.write("| Japanese | Reading | Glyph IDs | Meaning |\n")
    f.write("|----------|---------|-----------|----------|\n")
    vocab_items = [
        ("\u30d1\u30fc\u30c6\u30a3", "paatii", "259,93,211,268", "Party"),
        ("\u30ea\u30fc\u30c0\u30fc", "riidaa", "232,93,249,93", "Leader"),
        ("\u5192\u967a\u8005", "boukensha", "486,487,287", "Adventurer"),
        ("\u767b\u9332", "touroku", "491,492", "Registration"),
        ("\u8ee2\u8077", "tenshoku", "379,504", "Class change"),
        ("\u524a\u9664", "sakujo", "506,507", "Delete"),
        ("\u53ec\u559a", "shoukan", "500,501", "Summon"),
        ("\u9078\u629e", "sentaku", "707,708", "Select"),
        ("\u52a0\u5165", "kanyuu", "549,550", "Join"),
        ("\u96e2\u8131", "ridatsu", "797,798", "Withdrawal"),
        ("\u5909\u66f4", "henkou", "652,879", "Change"),
        ("\u8077\u696d", "shokugyou", "504,517", "Occupation"),
        ("\u5fc5\u8981", "hitsuyou", "709,710", "Necessary"),
        ("\u540d\u524d", "namae", "713,714", "Name"),
        ("\u9ad8\u30ec\u30d9\u30eb", "kou reberu", "715,234,257,233", "High level"),
        ("\u4f4e\u30ec\u30d9\u30eb", "tei reberu", "716,234,257,233", "Low level"),
        ("\u80fd\u529b", "nouryoku", "502,503", "Ability"),
        ("\u30b9\u30c6\u30fc\u30bf\u30b9", "suteetasu", "205,211,93,208,205", "Status"),
    ]
    for jp, rd, gids, meaning in vocab_items:
        f.write(f"| {jp} | {rd} | {gids} | {meaning} |\n")
    f.write("\n## Methodology\n\n")
    f.write("1. Decoded resource 40 using known glyph map (msg_glyph_map.json)\n")
    f.write("2. Cross-referenced with English guide Adventurer Guild section\n")
    f.write("3. Guide menu items: WITHDRAW FROM PARTY, CHANGE NAME, DELETE REGISTERED MEMBER,\n")
    f.write("   CHANGE CLASS, SORT (alphabetical, highest/lowest level, occupation)\n")
    f.write("4. Used Japanese compound word patterns and particles\n")
    f.write("5. Verified consistency across all 84 messages\n\n")
    f.write("## Decoded Messages\n\n```\n")
    for dm in decoded_messages:
        f.write(f"MSG {dm['index']:3d}: {dm['decoded']}\n")
    f.write("```\n")
print(f"Saved findings to {FINDINGS_PATH}")
