import json, struct, os

BASE = "C:/Programmieren/wizardrytranslation"
RESDIR = os.path.join(BASE, "extracted/packdata_resources")
DIG_PATH = os.path.join(BASE, "extracted/PACKDATA.DIG")
DECODED_PATH = os.path.join(BASE, "data/full_decoded_text.json")
SECTOR = 2048
TOC_ENTRIES = 2883
OUTLIER_INDICES = {1370, 2100}

with open(DECODED_PATH, "r", encoding="utf-8") as f:
    decoded = json.load(f)

res_messages = {}
for entry in decoded:
    r, m, ja = entry["resource"], entry["message"], entry["japanese"]
    if r not in res_messages:
        res_messages[r] = {}
    res_messages[r][m] = {"japanese": ja}

en_lookup = {}
with open(os.path.join(BASE, "data/translations_items_monsters.json"), "r", encoding="utf-8") as f:
    for entry in json.load(f):
        en_lookup[(entry["resource"], entry["message"])] = entry["english"]

with open(os.path.join(BASE, "data/translations_menus.json"), "r", encoding="utf-8") as f:
    menus_data = json.load(f)
for key, section in menus_data.items():
    if key.startswith("_"): continue
    parts = key.split("_")
    try: r = int(parts[1])
    except: continue
    for msg_id, val in section.items():
        if msg_id.startswith("_"): continue
        try: m = int(msg_id)
        except: continue
        if isinstance(val, dict) and "en" in val:
            en_lookup[(r, m)] = val["en"]

with open(os.path.join(BASE, "data/translations_dungeon_story.json"), "r", encoding="utf-8") as f:
    dungeon_data = json.load(f)
for key, section in dungeon_data.items():
    if key.startswith("_"): continue
    parts = key.split("_")
    try: r = int(parts[1])
    except: continue
    if "messages" in section:
        for msg_id, val in section["messages"].items():
            try: m = int(msg_id)
            except: continue
            if isinstance(val, dict) and "english" in val:
                en_lookup[(r, m)] = val["english"]

with open(os.path.join(BASE, "data/translations_shop_church.json"), "r", encoding="utf-8") as f:
    shops_data = json.load(f)
for key, section in shops_data.items():
    if key.startswith("_"): continue
    parts = key.split("_")
    try: r = int(parts[1])
    except: continue
    if "entries" in section:
        for entry in section["entries"]:
            mid, en = entry.get("id"), entry.get("english")
            if mid is not None and en is not None:
                en_lookup[(r, mid)] = en

with open(DIG_PATH, "rb") as f:
    toc_data = f.read(TOC_ENTRIES * 12)
toc = []
for i in range(TOC_ENTRIES):
    so, sc, tc = struct.unpack_from("<III", toc_data, i * 12)
    toc.append((so, sc, tc))

res_file_cache = {}
for fname in os.listdir(RESDIR):
    try: res_file_cache[int(fname[:4])] = os.path.join(RESDIR, fname)
    except: pass

results = []
overflow_resources = []
resources_to_check = set(range(34, 50))
for r, m in en_lookup:
    resources_to_check.add(r)

for r in sorted(resources_to_check):
    if r not in res_messages: continue
    msgs = res_messages[r]
    res_ja_total = 0
    res_en_total = 0
    has_translation = False
    for m in sorted(msgs.keys()):
        ja_clean = msgs[m]["japanese"].rstrip(" /").rstrip()
        ja_chars = len(ja_clean)
        en_text = en_lookup.get((r, m))
        if en_text:
            has_translation = True
            res_en_total += len(en_text)
        else:
            res_en_total += int(ja_chars * 2.0)
        res_ja_total += ja_chars

    allocated_payload = None
    allocated_bytes = None
    if r < TOC_ENTRIES and r not in OUTLIER_INDICES:
        so, sc, tc = toc[r]
        allocated_bytes = sc * SECTOR
        allocated_payload = allocated_bytes - 16

    p = res_file_cache.get(r)
    payload_size = os.path.getsize(p) if p else None
    glyph_expansion = (res_en_total - res_ja_total) * 2
    new_payload_size = payload_size + glyph_expansion if payload_size else None

    overflow = False
    overflow_amount = 0
    padding_available = 0
    if allocated_payload is not None and payload_size is not None:
        padding_available = allocated_payload - payload_size
        if new_payload_size > allocated_payload:
            overflow = True
            overflow_amount = new_payload_size - allocated_payload

    result = {
        "resource": r, "msg_count": len(msgs),
        "ja_total_chars": res_ja_total, "en_total_chars": res_en_total,
        "expansion_ratio": round(res_en_total / res_ja_total, 3) if res_ja_total > 0 else 0,
        "payload_size": payload_size, "allocated_bytes": allocated_bytes,
        "allocated_payload": allocated_payload, "padding_available": padding_available,
        "padding_pct": round((padding_available / payload_size * 100), 1) if payload_size and payload_size > 0 else 0,
        "glyph_expansion_bytes": glyph_expansion, "new_payload_size": new_payload_size,
        "overflow": overflow, "overflow_amount": overflow_amount,
        "has_translations": has_translation,
    }
    results.append(result)
    if overflow:
        overflow_resources.append(result)

ratios = []
for (r, m), en in en_lookup.items():
    if r in res_messages and m in res_messages[r]:
        ja = res_messages[r][m]["japanese"].rstrip(" /").rstrip()
        if len(ja) > 0:
            ratios.append(len(en) / len(ja))

avg_ratio = sum(ratios) / len(ratios) if ratios else 0
median_ratio = sorted(ratios)[len(ratios)//2] if ratios else 0
max_ratio = max(ratios) if ratios else 0
min_ratio = min(ratios) if ratios else 0

output = {
    "expansion_stats": {"count": len(ratios), "avg": round(avg_ratio,3), "median": round(median_ratio,3), "min": round(min_ratio,3), "max": round(max_ratio,3)},
    "resources_34_49": [r for r in results if 34 <= r["resource"] <= 49],
    "all_overflow": overflow_resources,
    "all_results": results,
    "ratio_distribution": {},
}
buckets = [0]*10
for ratio in ratios:
    buckets[min(int(ratio / 0.5), 9)] += 1
labels = ["0.0-0.5","0.5-1.0","1.0-1.5","1.5-2.0","2.0-2.5","2.5-3.0","3.0-3.5","3.5-4.0","4.0-4.5","4.5+"]
for label, count in zip(labels, buckets):
    output["ratio_distribution"][label] = count

out_path = os.path.join(BASE, "runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/recon-text-fitting/fitting_results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print("DONE")
