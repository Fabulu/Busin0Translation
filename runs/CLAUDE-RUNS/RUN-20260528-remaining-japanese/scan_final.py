#!/usr/bin/env python3
"""
Final comprehensive scan for untranslated Japanese dialogue.

Strategy:
- Type-02 resources: Primary dialogue containers. Use MSG section structure +
  glyph analysis to find real text.
- Known non-type-02 text resources: R34-R49, R720, R1053, R1908, R2124, R2654
  (system/menu text, already known)
- Other types: Only flag if they pass strict criteria (high FB00+FFFE density
  relative to file size, indicating MSG structure rather than coincidental bytes)
"""

import json, glob, os, struct, sys, io
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "C:/Programmieren/wizardrytranslation"
RES_DIR = f"{BASE}/extracted/packdata_resources"
MANIFEST = f"{RES_DIR}/manifest.json"
GLYPH_MAP = f"{BASE}/data/msg_glyph_map.json"
BATCH_DIR = f"{BASE}/data/type2_translated"
OUT_DIR = f"{BASE}/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese"

# Known non-type-02 resources with real text
KNOWN_TEXT_NONTYPE2 = {34,36,37,38,39,40,41,42,43,44,45,46,47,48,49,720,1053,1908,2124,2654}

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

# Load already-translated resource IDs + line counts
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

# Also add known-translated type-01/other text resources
known_translated_other = {34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,720,1053,1908,2124,2654}


def decode_glyph(gid):
    hexkey = f"{gid:04X}"
    return glyph_raw.get(hexkey, glyph_raw.get(str(gid), None))


def scan_type02_msg(filepath):
    """Scan a type-02 resource for MSG dialogue structure.

    Type-02 MSG format:
    - Header with section offsets (LE uint32)
    - Section 1: script opcodes
    - Section 2: FFFF/FFFE delimited glyph streams (the text)
    - Section 3: additional data

    Real MSG text has:
    - FFFE line separators within messages
    - FFFF message terminators
    - FB00-range speaker tags
    - High glyph map coverage
    """
    with open(filepath, "rb") as f:
        data = f.read()

    if len(data) < 32:
        return None

    # Read header - first uint32 LE should be 1 (version) for MSG resources
    first_word = struct.unpack_from("<I", data, 0)[0]

    # Scan for all markers
    ffff_count = 0
    fffe_count = 0
    fb_count = 0
    fc_count = 0

    ffff_positions = []

    for i in range(0, len(data) - 1, 2):
        val = struct.unpack_from(">H", data, i)[0]
        if val == 0xFFFF:
            ffff_count += 1
            ffff_positions.append(i)
        elif val == 0xFFFE:
            fffe_count += 1
        elif 0xFB00 <= val <= 0xFBFF:
            fb_count += 1
        elif 0xFC00 <= val <= 0xFCFF:
            fc_count += 1

    if ffff_count < 2:
        return None

    # Extract glyph groups between consecutive FFFF markers
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
                 if gid in glyph_set or (0xFB00 <= gid <= 0xFBFF) or
                 (0xFC00 <= gid <= 0xFCFF) or gid == 0xFFFE)
    hit_rate = mapped / total_glyphs if total_glyphs > 0 else 0.0

    # Count meaningful groups (5+ mapped glyphs)
    meaningful = sum(1 for g in groups
                     if sum(1 for gid in g if gid in glyph_set or
                            (0xFB00 <= gid <= 0xFBFF)) >= 5)

    # Decode sample texts (prefer groups with speaker tags)
    sample_texts = []
    for g in groups:
        has_speaker = any(0xFB00 <= gid <= 0xFBFF for gid in g)
        if has_speaker and len(sample_texts) < 3:
            text = decode_group(g)
            sample_texts.append(text)
    if not sample_texts:
        for g in groups[:3]:
            sample_texts.append(decode_group(g))

    return {
        "size": len(data),
        "first_word": first_word,
        "ffff_count": ffff_count,
        "fffe_count": fffe_count,
        "fb_count": fb_count,
        "fc_count": fc_count,
        "group_count": len(groups),
        "meaningful_groups": meaningful,
        "total_glyphs": total_glyphs,
        "mapped_glyphs": mapped,
        "hit_rate": hit_rate,
        "sample_texts": sample_texts,
    }


def decode_group(glyphs):
    text = ""
    for gid in glyphs:
        ch = decode_glyph(gid)
        if ch:
            text += ch
        elif 0xFB00 <= gid <= 0xFBFF:
            text += f"[SPK:{gid&0xFF:02X}]"
        elif 0xFC00 <= gid <= 0xFCFF:
            text += f"[CTL:{gid&0xFF:02X}]"
        elif gid == 0xFFFE:
            text += "[NL]"
        else:
            text += f"[{gid:04X}]"
    return text[:120]


def is_real_dialogue(result, type_code):
    """Determine if scan result represents real dialogue vs binary noise."""
    if result is None:
        return False

    fb = result["fb_count"]
    fffe = result["fffe_count"]
    hr = result["hit_rate"]
    mg = result["meaningful_groups"]
    gc = result["group_count"]
    size = result["size"]
    ffff = result["ffff_count"]

    # For type-02 resources: almost always real text if they have FFFF structure
    # The game engine puts all dialogue in type-02 containers
    if type_code == 2:
        # Strong: has speaker tags
        if fb >= 5 and hr > 0.40:
            return True
        # Has FFFF delimiters and decent glyph hit rate
        if ffff >= 3 and hr > 0.50 and mg >= 2:
            return True
        # Even small type-02 with FFFF structure
        if ffff >= 2 and hr > 0.55:
            return True
        # Type-02 with few/no FFFF but has speaker tags
        if fb >= 1 and hr > 0.40:
            return True

    # Non-type-02: need stronger evidence (FB tags + FFFE + high hit rate)
    if fb >= 10 and fffe >= 5 and hr > 0.60:
        return True
    if fb >= 5 and hr > 0.60 and mg >= 5:
        return True

    return False


def is_maybe_text(result, type_code):
    """Weaker criteria for possible text."""
    if result is None:
        return False
    fb = result["fb_count"]
    fffe = result["fffe_count"]
    hr = result["hit_rate"]
    mg = result["meaningful_groups"]

    # Type-02 with any FFFF structure
    if type_code == 2 and result["ffff_count"] >= 1 and hr > 0.40:
        return True
    # Non-type-02 with some evidence
    if fb >= 1 and hr > 0.50 and mg >= 2:
        return True
    if fffe >= 5 and hr > 0.55 and mg >= 3:
        return True
    return False


# ========================
# MAIN SCAN
# ========================
print("=== Scanning all resources ===")
all_results = []
type_stats = defaultdict(lambda: {"total": 0, "dialogue": 0, "translated": 0, "maybe": 0})

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

    # Known non-type-02 text resources
    if idx in KNOWN_TEXT_NONTYPE2:
        is_trans = idx in known_translated_other
        fsize = os.path.getsize(filepath)
        all_results.append({
            "index": idx, "type": tc, "filename": fn,
            "category": "KNOWN_TEXT", "is_translated": is_trans,
            "translated_lines": translated_line_counts.get(idx, 0),
            "size": fsize, "fb_count": 0, "fffe_count": 0,
            "group_count": 0, "hit_rate": 0, "meaningful_groups": 0,
            "sample_texts": ["(known system/menu text)"],
            "note": "Previously identified system/menu text"
        })
        type_stats[tc]["dialogue"] += 1
        if is_trans:
            type_stats[tc]["translated"] += 1
        continue

    # Scan all types - the scan function works generically
    result = scan_type02_msg(filepath)

    if result is None:
        continue

    is_trans = idx in already_translated

    if is_real_dialogue(result, tc):
        category = "DIALOGUE"
        type_stats[tc]["dialogue"] += 1
        if is_trans:
            type_stats[tc]["translated"] += 1
    elif is_maybe_text(result, tc):
        category = "MAYBE_TEXT"
        type_stats[tc]["maybe"] += 1
    else:
        continue  # Skip binary noise

    result.update({
        "index": idx, "type": tc, "filename": fn,
        "category": category, "is_translated": is_trans,
        "translated_lines": translated_line_counts.get(idx, 0),
    })
    all_results.append(result)

# Save JSON
with open(f"{OUT_DIR}/scan_final_results.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=1, ensure_ascii=False)

# ========================
# GENERATE REPORT
# ========================
dialogue = [r for r in all_results if r["category"] in ("DIALOGUE", "KNOWN_TEXT")]
maybe = [r for r in all_results if r["category"] == "MAYBE_TEXT"]

dial_untrans = [r for r in dialogue if not r["is_translated"]]
dial_trans = [r for r in dialogue if r["is_translated"]]

# Line estimates
total_lines = sum(r.get("group_count", 0) for r in dialogue)
trans_lines = sum(r.get("group_count", 0) for r in dial_trans)
untrans_lines = sum(r.get("group_count", 0) for r in dial_untrans)

md = []
md.append("# Comprehensive Untranslated Dialogue Scan")
md.append(f"\n**Date:** 2026-05-28")
md.append(f"\n**Classification method:** MSG structure analysis (FFFF/FFFE delimiters,")
md.append(f"FB00 speaker tags, glyph map hit rate). Filters out binary/3D data that")
md.append(f"coincidentally contains marker-like byte patterns.")

md.append(f"\n## Executive Summary")
md.append(f"\n| Metric | Count |")
md.append(f"|--------|-------|")
md.append(f"| Total PACKDATA resources | {len(manifest)} |")
md.append(f"| Resources scanned | {sum(s['total'] for s in type_stats.values())} |")
md.append(f"| **Resources with real dialogue** | **{len(dialogue)}** |")
md.append(f"| - Already translated | {len(dial_trans)} |")
md.append(f"| - **UNTRANSLATED** | **{len(dial_untrans)}** |")
md.append(f"| Possibly text (weak signal) | {len(maybe)} |")
md.append(f"| Estimated total dialogue lines | ~{total_lines} |")
md.append(f"| Estimated translated lines | ~{trans_lines} |")
md.append(f"| Estimated untranslated lines | ~{untrans_lines} |")
if total_lines > 0:
    pct = trans_lines / total_lines * 100
    md.append(f"| **Translation progress** | **~{pct:.1f}%** |")

md.append(f"\n## Resource Type Breakdown")
md.append(f"\n| Type | Total | Dialogue | Translated | Untranslated | Maybe |")
md.append(f"|------|-------|----------|------------|--------------|-------|")
for tc in sorted(type_stats.keys()):
    s = type_stats[tc]
    md.append(f"| {tc:02d} | {s['total']} | {s['dialogue']} | {s['translated']} | {s['dialogue'] - s['translated']} | {s['maybe']} |")

# --- UNTRANSLATED TYPE-02 DIALOGUE ---
type02_untrans = [r for r in dial_untrans if r["type"] == 2]
type02_trans = [r for r in dial_trans if r["type"] == 2]

md.append(f"\n## Untranslated Type-02 Dialogue ({len(type02_untrans)} resources)")
md.append(f"\nThese are the primary dialogue containers with confirmed MSG structure.\n")
md.append(f"| Resource | Size | FB Tags | FFFE | Groups | Hit Rate | Sample |")
md.append(f"|----------|------|---------|------|--------|----------|--------|")
for r in sorted(type02_untrans, key=lambda x: x["index"]):
    sample = r["sample_texts"][0][:50].replace("|", "/").replace("\n", " ") if r.get("sample_texts") else ""
    md.append(f"| R{r['index']} | {r['size']:,} | {r.get('fb_count',0)} | {r.get('fffe_count',0)} | {r.get('group_count',0)} | {r.get('hit_rate',0):.0%} | `{sample}` |")

# --- UNTRANSLATED NON-TYPE-02 ---
nontype02_untrans = [r for r in dial_untrans if r["type"] != 2]
if nontype02_untrans:
    md.append(f"\n## Untranslated Non-Type-02 Text ({len(nontype02_untrans)} resources)")
    md.append(f"\n| Resource | Type | Size | FB Tags | FFFE | Groups | Hit Rate | Note |")
    md.append(f"|----------|------|------|---------|------|--------|----------|------|")
    for r in sorted(nontype02_untrans, key=lambda x: x["index"]):
        note = r.get("note", "")
        md.append(f"| R{r['index']} | {r['type']:02d} | {r.get('size',0):,} | {r.get('fb_count',0)} | {r.get('fffe_count',0)} | {r.get('group_count',0)} | {r.get('hit_rate',0):.0%} | {note} |")

# --- MAYBE TEXT ---
if maybe:
    md.append(f"\n## Possibly Text - Weak Signal ({len(maybe)} resources)")
    md.append(f"\nThese have some FB00 tags or FFFE markers but don't meet full dialogue criteria.\n")
    md.append(f"| Resource | Type | Size | FB Tags | FFFE | Groups | Hit Rate | Sample |")
    md.append(f"|----------|------|------|---------|------|--------|----------|--------|")
    for r in sorted(maybe, key=lambda x: x["index"]):
        sample = r["sample_texts"][0][:45].replace("|", "/") if r.get("sample_texts") else ""
        md.append(f"| R{r['index']} | {r['type']:02d} | {r['size']:,} | {r.get('fb_count',0)} | {r.get('fffe_count',0)} | {r.get('group_count',0)} | {r.get('hit_rate',0):.0%} | `{sample}` |")

# --- ALREADY TRANSLATED ---
md.append(f"\n## Already Translated ({len(dial_trans)} resources)")
md.append(f"\n| Resource | Type | FB Tags | Groups | Trans Lines | Batch Lines |")
md.append(f"|----------|------|---------|--------|-------------|-------------|")
for r in sorted(dial_trans, key=lambda x: x["index"]):
    md.append(f"| R{r['index']} | {r['type']:02d} | {r.get('fb_count',0)} | {r.get('group_count',0)} | {r.get('translated_lines',0)} | {translated_line_counts.get(r['index'],0)} |")

# --- SAMPLE TEXT ---
md.append(f"\n## Sample Decoded Text from Top Untranslated Resources")
md.append(f"\nShowing samples from untranslated resources with most dialogue:\n")
top_untrans = sorted(dial_untrans, key=lambda x: -x.get("fb_count", 0))[:25]
for r in top_untrans:
    md.append(f"### R{r['index']} (type {r['type']:02d}, {r.get('fb_count',0)} speakers, {r.get('group_count',0)} groups, {r.get('hit_rate',0):.0%})")
    for i, s in enumerate(r.get("sample_texts", [])[:3]):
        md.append(f"- `{s}`")
    md.append("")

# --- COVERAGE ANALYSIS ---
md.append(f"\n## Coverage Analysis")
md.append(f"\n### By Resource Count")
t02_total = len(type02_trans) + len(type02_untrans)
t02_pct = len(type02_trans) / t02_total * 100 if t02_total else 0
dial_pct = len(dial_trans) / len(dialogue) * 100 if dialogue else 0
line_pct = trans_lines / total_lines * 100 if total_lines else 0
md.append(f"- Type-02 translated: {len(type02_trans)} / {t02_total} ({t02_pct:.1f}%)")
md.append(f"- Overall translated: {len(dial_trans)} / {len(dialogue)} ({dial_pct:.1f}%)")
md.append(f"\n### By Line Count (glyph groups)")
md.append(f"- Total estimated lines: {total_lines}")
md.append(f"- Translated lines: {trans_lines} ({line_pct:.1f}%)")
md.append(f"- Remaining lines: {untrans_lines}")

report = "\n".join(md)
with open(f"{OUT_DIR}/scan_remaining_dialogue.md", "w", encoding="utf-8") as f:
    f.write(report)

# Console summary
print(f"\n{'='*60}")
print(f"RESULTS")
print(f"{'='*60}")
print(f"Resources with real dialogue: {len(dialogue)}")
print(f"  Translated: {len(dial_trans)}")
print(f"  UNTRANSLATED: {len(dial_untrans)}")
print(f"    Type-02: {len(type02_untrans)}")
print(f"    Other types: {len(nontype02_untrans)}")
print(f"Possibly text (weak): {len(maybe)}")
print(f"Estimated lines: {total_lines} total, {trans_lines} done, {untrans_lines} remaining")
if total_lines > 0:
    print(f"Progress: {trans_lines/total_lines*100:.1f}%")
print(f"\nReport: {OUT_DIR}/scan_remaining_dialogue.md")
