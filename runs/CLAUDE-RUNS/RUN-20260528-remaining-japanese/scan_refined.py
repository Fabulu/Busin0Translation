#!/usr/bin/env python3
"""
Refined scan for untranslated dialogue in PACKDATA resources.
Uses FB00-range speaker tags as the primary indicator of real dialogue.
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

# Load manifest
with open(MANIFEST, encoding="utf-8") as f:
    manifest = json.load(f)

# Load already-translated resource IDs
already_translated = set()
translated_line_counts = Counter()
for bf in sorted(glob.glob(f"{BATCH_DIR}/batch_*.json")):
    if bf.endswith(".master"):
        continue
    with open(bf, encoding="utf-8") as f:
        data = json.load(f)
    for entry in data:
        r = entry.get("resource", "")
        if isinstance(r, str) and r.startswith("R"):
            rid = int(r[1:])
        elif isinstance(r, int):
            rid = r
        else:
            continue
        already_translated.add(rid)
        translated_line_counts[rid] += 1


def decode_glyph(gid):
    hexkey = f"{gid:04X}"
    return glyph_raw.get(hexkey, glyph_raw.get(str(gid), None))


def scan_resource_detailed(filepath):
    """Detailed scan: speaker tags, glyph groups with context."""
    with open(filepath, "rb") as f:
        data = f.read()

    if len(data) < 10:
        return None

    # Count FB00-range speaker tags
    fb_tags = []
    fc_controls = 0
    ffff_positions = []

    for i in range(0, len(data) - 1, 2):
        val = struct.unpack_from(">H", data, i)[0]
        if 0xFB00 <= val <= 0xFBFF:
            fb_tags.append((i, val))
        elif 0xFC00 <= val <= 0xFCFF:
            fc_controls += 1
        elif val == 0xFFFF:
            ffff_positions.append(i)

    if len(ffff_positions) < 2:
        return None

    # Extract glyph groups between FFFF markers
    groups = []
    for idx in range(len(ffff_positions) - 1):
        start = ffff_positions[idx] + 2
        end = ffff_positions[idx + 1]
        if end - start < 4 or (end - start) % 2 != 0:
            continue
        glyphs = []
        for pos in range(start, end, 2):
            g = struct.unpack_from(">H", data, pos)[0]
            glyphs.append(g)
        if len(glyphs) >= 2:
            groups.append(glyphs)

    if not groups:
        return None

    # Calculate glyph map hit rate
    total_glyphs = sum(len(g) for g in groups)
    mapped = sum(1 for g in groups for gid in g
                 if gid in glyph_set or (0xFB00 <= gid <= 0xFBFF) or (0xFC00 <= gid <= 0xFCFF))
    hit_rate = mapped / total_glyphs if total_glyphs > 0 else 0.0

    # Decode sample texts (up to 3 groups with speaker tags, or first 3)
    sample_groups = []
    # Prefer groups near speaker tags
    for g in groups:
        has_speaker = any(0xFB00 <= gid <= 0xFBFF for gid in g)
        if has_speaker:
            sample_groups.append(g)
            if len(sample_groups) >= 3:
                break
    if not sample_groups:
        sample_groups = groups[:3]

    sample_texts = []
    for g in sample_groups:
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
        sample_texts.append(text[:120])

    # Count groups with meaningful text (5+ mapped glyphs)
    meaningful_groups = 0
    for g in groups:
        mg = sum(1 for gid in g if gid in glyph_set or (0xFB00 <= gid <= 0xFBFF))
        if mg >= 5:
            meaningful_groups += 1

    return {
        "fb_tag_count": len(fb_tags),
        "fc_control_count": fc_controls,
        "group_count": len(groups),
        "meaningful_groups": meaningful_groups,
        "total_glyphs": total_glyphs,
        "mapped_glyphs": mapped,
        "hit_rate": hit_rate,
        "sample_texts": sample_texts,
        "size": len(data),
    }


# === SCAN ALL RESOURCES ===
print("Scanning all resources...")
all_results = []
type_stats = defaultdict(lambda: {"total": 0, "with_dialogue": 0, "translated": 0})

for entry in manifest:
    if entry.get("skipped"):
        continue

    idx = entry["index"]
    tc = entry["type_code"]
    fn = entry["filename"]
    filepath = f"{RES_DIR}/{fn}"

    if not os.path.exists(filepath):
        continue

    type_stats[tc]["total"] += 1

    result = scan_resource_detailed(filepath)
    if result is None:
        continue

    # Classification:
    # STRONG DIALOGUE: FB00 speaker tags >= 5, or (FB >= 1 AND hit_rate > 60% AND meaningful_groups >= 3)
    # WEAK DIALOGUE: FB00 >= 1 AND meaningful_groups >= 1
    # POSSIBLE: hit_rate > 50% AND meaningful_groups >= 5 AND no speaker tags (could be menu/system text)

    fb = result["fb_tag_count"]
    hr = result["hit_rate"]
    mg = result["meaningful_groups"]

    if fb >= 5:
        category = "STRONG_DIALOGUE"
    elif fb >= 1 and hr > 0.50 and mg >= 3:
        category = "STRONG_DIALOGUE"
    elif fb >= 1:
        category = "WEAK_DIALOGUE"
    elif hr > 0.60 and mg >= 10:
        category = "POSSIBLE_TEXT"
    else:
        category = "BINARY_DATA"
        continue  # Skip binary data from results

    is_translated = idx in already_translated

    result.update({
        "index": idx,
        "type": tc,
        "filename": fn,
        "category": category,
        "is_translated": is_translated,
        "translated_lines": translated_line_counts.get(idx, 0),
    })

    all_results.append(result)

    if category in ("STRONG_DIALOGUE", "WEAK_DIALOGUE"):
        type_stats[tc]["with_dialogue"] += 1
        if is_translated:
            type_stats[tc]["translated"] += 1

# Save JSON
with open(f"{OUT_DIR}/scan_refined_results.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=1, ensure_ascii=False)

# === GENERATE REPORT ===
strong = [r for r in all_results if r["category"] == "STRONG_DIALOGUE"]
weak = [r for r in all_results if r["category"] == "WEAK_DIALOGUE"]
possible = [r for r in all_results if r["category"] == "POSSIBLE_TEXT"]

strong_untrans = [r for r in strong if not r["is_translated"]]
strong_trans = [r for r in strong if r["is_translated"]]
weak_untrans = [r for r in weak if not r["is_translated"]]
weak_trans = [r for r in weak if r["is_translated"]]

total_strong_lines = sum(r["group_count"] for r in strong)
trans_strong_lines = sum(r["group_count"] for r in strong_trans)
untrans_strong_lines = sum(r["group_count"] for r in strong_untrans)

md = []
md.append("# Remaining Untranslated Dialogue Scan")
md.append(f"\n**Date:** 2026-05-28")
md.append(f"\n**Method:** Speaker-tag-based classification (FB00 range = dialogue indicator)")

md.append(f"\n## Executive Summary")
md.append(f"\n| Metric | Count |")
md.append(f"|--------|-------|")
md.append(f"| Total PACKDATA resources | {len(manifest)} |")
md.append(f"| Resources scanned | {sum(s['total'] for s in type_stats.values())} |")
md.append(f"| Strong dialogue (FB00 tags) | {len(strong)} resources |")
md.append(f"| - Already translated | {len(strong_trans)} resources |")
md.append(f"| - **UNTRANSLATED** | **{len(strong_untrans)} resources** |")
md.append(f"| Weak dialogue (few FB00 tags) | {len(weak)} resources |")
md.append(f"| - Already translated | {len(weak_trans)} resources |")
md.append(f"| - Untranslated | {len(weak_untrans)} resources |")
md.append(f"| Possible system text (no FB00) | {len(possible)} resources |")
md.append(f"| Est. strong dialogue lines total | ~{total_strong_lines} |")
md.append(f"| Est. strong lines translated | ~{trans_strong_lines} |")
md.append(f"| Est. strong lines untranslated | ~{untrans_strong_lines} |")
if total_strong_lines > 0:
    pct = trans_strong_lines / total_strong_lines * 100
    md.append(f"| **Translation progress (strong)** | **~{pct:.1f}%** |")

md.append(f"\n## Type Breakdown")
md.append(f"\n| Type | Total | With Dialogue | Translated | Untranslated |")
md.append(f"|------|-------|---------------|------------|--------------|")
for tc in sorted(type_stats.keys()):
    s = type_stats[tc]
    md.append(f"| {tc:02d} | {s['total']} | {s['with_dialogue']} | {s['translated']} | {s['with_dialogue'] - s['translated']} |")

# --- UNTRANSLATED STRONG DIALOGUE ---
md.append(f"\n## Untranslated Strong Dialogue ({len(strong_untrans)} resources)")
md.append(f"\nThese resources have FB00-range speaker tags and high glyph map hit rates.")
md.append(f"They contain real in-game dialogue that needs translation.\n")

by_type = defaultdict(list)
for r in strong_untrans:
    by_type[r["type"]].append(r)

for tc in sorted(by_type.keys()):
    items = by_type[tc]
    md.append(f"\n### Type {tc:02d} ({len(items)} resources, ~{sum(r['group_count'] for r in items)} lines)")
    md.append(f"\n| Resource | Size | FB Tags | Groups | Hit Rate | Sample |")
    md.append(f"|----------|------|---------|--------|----------|--------|")
    for r in sorted(items, key=lambda x: x["index"]):
        sample = r["sample_texts"][0][:55].replace("|", "/").replace("\n", " ") if r["sample_texts"] else ""
        md.append(f"| R{r['index']} | {r['size']:,} | {r['fb_tag_count']} | {r['group_count']} | {r['hit_rate']:.0%} | `{sample}` |")

# --- UNTRANSLATED WEAK DIALOGUE ---
md.append(f"\n## Untranslated Weak Dialogue ({len(weak_untrans)} resources)")
md.append(f"\nThese have 1-4 FB00 speaker tags. May be minor text or edge cases.\n")
md.append(f"| Resource | Type | Size | FB Tags | Groups | Hit Rate | Sample |")
md.append(f"|----------|------|------|---------|--------|----------|--------|")
for r in sorted(weak_untrans, key=lambda x: x["index"]):
    sample = r["sample_texts"][0][:50].replace("|", "/").replace("\n", " ") if r["sample_texts"] else ""
    md.append(f"| R{r['index']} | {r['type']:02d} | {r['size']:,} | {r['fb_tag_count']} | {r['group_count']} | {r['hit_rate']:.0%} | `{sample}` |")

# --- POSSIBLE SYSTEM TEXT ---
if possible:
    md.append(f"\n## Possible System/Menu Text ({len(possible)} resources)")
    md.append(f"\nHigh glyph hit rate but no speaker tags. Could be menus, item names, etc.\n")
    md.append(f"| Resource | Type | Size | Groups | Hit Rate | Sample |")
    md.append(f"|----------|------|------|--------|----------|--------|")
    for r in sorted(possible, key=lambda x: x["index"]):
        sample = r["sample_texts"][0][:50].replace("|", "/").replace("\n", " ") if r["sample_texts"] else ""
        md.append(f"| R{r['index']} | {r['type']:02d} | {r['size']:,} | {r['group_count']} | {r['hit_rate']:.0%} | `{sample}` |")

# --- ALREADY TRANSLATED ---
md.append(f"\n## Already Translated ({len(strong_trans) + len(weak_trans)} resources)")
md.append(f"\n| Resource | Type | FB Tags | Groups | Trans Lines | Status |")
md.append(f"|----------|------|---------|--------|-------------|--------|")
for r in sorted(strong_trans + weak_trans, key=lambda x: x["index"]):
    md.append(f"| R{r['index']} | {r['type']:02d} | {r['fb_tag_count']} | {r['group_count']} | {r['translated_lines']} | Done |")

# --- SAMPLE DECODED TEXT ---
md.append(f"\n## Sample Decoded Text from Untranslated Resources")
md.append(f"\nShowing decoded text samples from each untranslated strong dialogue resource:\n")
for r in sorted(strong_untrans, key=lambda x: -x["fb_tag_count"])[:30]:
    md.append(f"### R{r['index']} (type {r['type']:02d}, {r['fb_tag_count']} speaker tags, {r['group_count']} groups)")
    for i, s in enumerate(r["sample_texts"][:3]):
        md.append(f"- `{s}`")
    md.append("")

report = "\n".join(md)
with open(f"{OUT_DIR}/scan_remaining_dialogue.md", "w", encoding="utf-8") as f:
    f.write(report)

print(f"\n=== RESULTS ===")
print(f"Strong dialogue: {len(strong)} ({len(strong_trans)} translated, {len(strong_untrans)} untranslated)")
print(f"Weak dialogue: {len(weak)} ({len(weak_trans)} translated, {len(weak_untrans)} untranslated)")
print(f"Possible text: {len(possible)}")
print(f"Estimated lines: {total_strong_lines} total, {trans_strong_lines} translated, {untrans_strong_lines} remaining")
if total_strong_lines > 0:
    print(f"Progress: {trans_strong_lines/total_strong_lines*100:.1f}%")
print(f"\nReport: {OUT_DIR}/scan_remaining_dialogue.md")
