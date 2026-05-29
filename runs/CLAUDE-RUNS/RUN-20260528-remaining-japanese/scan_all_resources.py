#!/usr/bin/env python3
"""
Comprehensive scan of ALL PACKDATA resources for untranslated Japanese dialogue.
Scans type-02, type-01, and all other types for FFFF-delimited glyph streams.
"""

import json, glob, os, struct, sys
from collections import Counter, defaultdict

BASE = "C:/Programmieren/wizardrytranslation"
RES_DIR = f"{BASE}/extracted/packdata_resources"
MANIFEST = f"{RES_DIR}/manifest.json"
GLYPH_MAP = f"{BASE}/data/msg_glyph_map.json"
BATCH_DIR = f"{BASE}/data/type2_translated"
OUT_DIR = f"{BASE}/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese"

# Load glyph map
with open(GLYPH_MAP, encoding="utf-8") as f:
    glyph_raw = json.load(f)
glyph_set = set()
for k in glyph_raw:
    try:
        glyph_set.add(int(k, 16) if isinstance(k, str) else int(k))
    except:
        pass
print(f"Glyph map: {len(glyph_set)} entries")

# Load manifest
with open(MANIFEST, encoding="utf-8") as f:
    manifest = json.load(f)
print(f"Manifest: {len(manifest)} resources")

# Load already-translated resource IDs
already_translated = set()
for bf in sorted(glob.glob(f"{BATCH_DIR}/batch_*.json")):
    if bf.endswith(".master"):
        continue
    with open(bf, encoding="utf-8") as f:
        data = json.load(f)
    for entry in data:
        r = entry.get("resource", "")
        if isinstance(r, str) and r.startswith("R"):
            already_translated.add(int(r[1:]))
        elif isinstance(r, int):
            already_translated.add(r)
print(f"Already translated: {len(already_translated)} resources")

def decode_glyph(gid):
    """Try to decode a glyph ID to character using the map."""
    hexkey = f"{gid:04X}"
    return glyph_raw.get(hexkey, glyph_raw.get(str(gid), None))

def scan_resource(filepath):
    """Scan a binary resource for FFFF-delimited glyph groups.
    Returns (groups, hit_rate, total_glyphs, mapped_glyphs, sample_texts)
    """
    with open(filepath, "rb") as f:
        data = f.read()

    if len(data) < 10:
        return [], 0.0, 0, 0, []

    # Find all FFFF positions
    ffff_positions = []
    for i in range(0, len(data) - 1, 2):
        val = struct.unpack_from(">H", data, i)[0]
        if val == 0xFFFF:
            ffff_positions.append(i)

    if len(ffff_positions) < 2:
        return [], 0.0, 0, 0, []

    # Extract glyph groups between consecutive FFFF markers
    groups = []
    for idx in range(len(ffff_positions) - 1):
        start = ffff_positions[idx] + 2
        end = ffff_positions[idx + 1]
        if end - start < 4:  # Need at least 2 glyphs
            continue
        if (end - start) % 2 != 0:
            continue

        glyphs = []
        for pos in range(start, end, 2):
            g = struct.unpack_from(">H", data, pos)[0]
            glyphs.append(g)

        if len(glyphs) >= 2:
            groups.append(glyphs)

    if not groups:
        return [], 0.0, 0, 0, []

    # Calculate hit rate
    total_glyphs = sum(len(g) for g in groups)
    mapped = 0
    for g in groups:
        for gid in g:
            if gid in glyph_set or (0xFB00 <= gid <= 0xFBFF) or (0xFC00 <= gid <= 0xFCFF):
                mapped += 1

    hit_rate = mapped / total_glyphs if total_glyphs > 0 else 0.0

    # Decode sample texts
    sample_texts = []
    for g in groups[:5]:
        text = ""
        for gid in g:
            ch = decode_glyph(gid)
            if ch:
                text += ch
            elif 0xFB00 <= gid <= 0xFBFF:
                text += f"[SPK:{gid&0xFF:02X}]"
            elif 0xFC00 <= gid <= 0xFCFF:
                text += f"[CTL:{gid&0xFF:02X}]"
            else:
                text += f"[{gid:04X}]"
        if len(text) > 80:
            text = text[:80] + "..."
        sample_texts.append(text)

    return groups, hit_rate, total_glyphs, mapped, sample_texts

# Scan all resources
results = []
type_counts = Counter()
scanned = 0

for entry in manifest:
    if entry.get("skipped"):
        continue

    idx = entry["index"]
    tc = entry["type_code"]
    fn = entry["filename"]
    filepath = f"{RES_DIR}/{fn}"

    if not os.path.exists(filepath):
        continue

    fsize = os.path.getsize(filepath)
    type_counts[tc] += 1
    scanned += 1

    groups, hit_rate, total_g, mapped_g, samples = scan_resource(filepath)

    # Criteria for "likely dialogue"
    groups_with_mapped = 0
    for g in groups:
        mapped_in_group = sum(1 for gid in g if gid in glyph_set or (0xFB00 <= gid <= 0xFBFF) or (0xFC00 <= gid <= 0xFCFF))
        if mapped_in_group >= 5:
            groups_with_mapped += 1

    is_dialogue = hit_rate > 0.40 and groups_with_mapped >= 3
    is_translated = idx in already_translated

    if is_dialogue or is_translated:
        results.append({
            "index": idx,
            "type": tc,
            "filename": fn,
            "size": fsize,
            "group_count": len(groups),
            "groups_5plus": groups_with_mapped,
            "total_glyphs": total_g,
            "mapped_glyphs": mapped_g,
            "hit_rate": hit_rate,
            "is_dialogue": is_dialogue,
            "is_translated": is_translated,
            "samples": samples[:3],
        })

print(f"\nScanned {scanned} resources")
print(f"Found {sum(1 for r in results if r['is_dialogue'])} with likely dialogue")
print(f"Of those, {sum(1 for r in results if r['is_dialogue'] and r['is_translated'])} already translated")
print(f"UNTRANSLATED dialogue: {sum(1 for r in results if r['is_dialogue'] and not r['is_translated'])}")

# Sort by type then index
results.sort(key=lambda r: (r["type"], r["index"]))

# Write JSON results
with open(f"{OUT_DIR}/scan_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=1, ensure_ascii=False)

# Generate markdown report
untranslated = [r for r in results if r["is_dialogue"] and not r["is_translated"]]
translated = [r for r in results if r["is_dialogue"] and r["is_translated"]]

# Group by type
by_type_untrans = defaultdict(list)
for r in untranslated:
    by_type_untrans[r["type"]].append(r)

by_type_trans = defaultdict(list)
for r in translated:
    by_type_trans[r["type"]].append(r)

md = []
md.append("# Remaining Untranslated Dialogue Scan")
md.append(f"\n**Date:** 2026-05-28")
md.append(f"\n## Summary")
md.append(f"\n- Total PACKDATA resources: {len(manifest)}")
md.append(f"- Resources scanned: {scanned}")
md.append(f"- Resources with likely dialogue: {sum(1 for r in results if r['is_dialogue'])}")
md.append(f"- Already translated: {len(translated)} resources")
md.append(f"- **Untranslated dialogue remaining: {len(untranslated)} resources**")

total_untrans_lines = sum(r["group_count"] for r in untranslated)
total_trans_lines = sum(r["group_count"] for r in translated)
md.append(f"- Estimated untranslated lines (glyph groups): ~{total_untrans_lines}")
md.append(f"- Estimated translated lines: ~{total_trans_lines}")
if total_untrans_lines + total_trans_lines > 0:
    pct = total_trans_lines / (total_untrans_lines + total_trans_lines) * 100
    md.append(f"- **Translation progress: ~{pct:.1f}%**")

md.append(f"\n## Resources by Type")
md.append(f"\n| Type | Total Resources | With Dialogue | Translated | Untranslated |")
md.append(f"|------|----------------|---------------|------------|--------------|")
all_types = sorted(set(list(by_type_untrans.keys()) + list(by_type_trans.keys())))
for tc in sorted(set(r["type"] for r in results)):
    total_of_type = type_counts.get(tc, 0)
    dial = sum(1 for r in results if r["type"] == tc and r["is_dialogue"])
    trans = len(by_type_trans.get(tc, []))
    untrans = len(by_type_untrans.get(tc, []))
    md.append(f"| {tc:02d} | {total_of_type} | {dial} | {trans} | {untrans} |")

md.append(f"\n## Untranslated Resources with Dialogue")
md.append(f"\nThese resources have high glyph-map hit rates and multiple coherent text groups.")

for tc in sorted(by_type_untrans.keys()):
    items = by_type_untrans[tc]
    md.append(f"\n### Type {tc:02d} ({len(items)} resources)")
    md.append(f"\n| Resource | Size | Groups | Hit Rate | Est. Lines | Sample |")
    md.append(f"|----------|------|--------|----------|------------|--------|")
    for r in sorted(items, key=lambda x: x["index"]):
        sample = r["samples"][0][:60].replace("|", "/") if r["samples"] else ""
        md.append(f"| R{r['index']} | {r['size']:,} | {r['group_count']} | {r['hit_rate']:.0%} | {r['groups_5plus']} | {sample} |")

md.append(f"\n## Already Translated Resources")
md.append(f"\n| Resource | Type | Groups | Hit Rate | Status |")
md.append(f"|----------|------|--------|----------|--------|")
for r in sorted(translated, key=lambda x: x["index"]):
    md.append(f"| R{r['index']} | {r['type']:02d} | {r['group_count']} | {r['hit_rate']:.0%} | Done |")

md.append(f"\n## Detailed Untranslated Samples")
md.append(f"\nShowing decoded sample text from each untranslated resource:")
for r in sorted(untranslated, key=lambda x: x["index"]):
    md.append(f"\n### R{r['index']} (type {r['type']:02d}, {r['group_count']} groups, {r['hit_rate']:.0%} hit rate)")
    for i, s in enumerate(r["samples"]):
        md.append(f"- Group {i}: `{s}`")

report = "\n".join(md)
with open(f"{OUT_DIR}/scan_remaining_dialogue.md", "w", encoding="utf-8") as f:
    f.write(report)

print(f"\nReport written to {OUT_DIR}/scan_remaining_dialogue.md")
print(f"JSON data written to {OUT_DIR}/scan_results.json")

# Print untranslated summary
print(f"\n=== UNTRANSLATED RESOURCES WITH DIALOGUE ===")
for r in sorted(untranslated, key=lambda x: x["index"]):
    print(f"  R{r['index']:04d} (type {r['type']:02d}): {r['group_count']} groups, {r['hit_rate']:.0%} hit, {r['size']:,} bytes")
    if r["samples"]:
        print(f"    Sample: {r['samples'][0][:80]}")
