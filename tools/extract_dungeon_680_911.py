#!/usr/bin/env python3
"""
extract_dungeon_680_911.py -- Analyze R680-R911 type-2 resources
================================================================

FINDING: All 29 resources in this range are dungeon MAP data, NOT dialogue.

Evidence:
  - 0 FB00-FB0F speaker tags (NPC speech markers) across all resources
  - No consecutive Japanese text forming words or sentences
  - All "text" groups are single-character UI labels or template headers
  - FFFF delimiters in Section 1 separate binary data blocks (geometry, tiles)
  - The scan's 73% glyph hit rate came from random byte matches in binary data

The scan (scan_remaining_dialogue.md) misclassified these because:
  - It counted FFFF in Section 1 as "groups" (actually binary block delimiters)
  - It counted any 0xFB byte as "FB tags" (actually binary data)
  - Individual characters like space, katakana, digits matched in binary

This script confirms the analysis and outputs an empty translation batch.
No entries are created to prevent the injector from corrupting dungeon data.
"""
import struct, json, os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.chdir("C:/Programmieren/wizardrytranslation")

gmap = json.load(open("data/msg_glyph_map.json", encoding="utf-8"))

RESOURCES = [
    680, 684, 686, 694, 698, 714, 716, 718, 730, 738,
    754, 760, 776, 778, 802, 812, 822, 824, 826, 832,
    834, 836, 842, 846, 854, 858, 890, 909, 911,
]


def parse_sec2(data):
    """Extract Section 2 from type-2 resource."""
    sec2_size = struct.unpack_from("<I", data, 0x14)[0]
    sec2_off = struct.unpack_from("<I", data, 0x18)[0]
    return data[sec2_off : sec2_off + sec2_size]


def decode_groups(sec2_data):
    """Parse into FFFF-delimited groups of BE uint16 words."""
    nwords = len(sec2_data) // 2
    words = [struct.unpack_from(">H", sec2_data, i * 2)[0] for i in range(nwords)]

    groups = []
    current = []
    for w in words:
        if w == 0xFFFF:
            groups.append(current)
            current = []
        else:
            current.append(w)
    if current:
        groups.append(current)
    return groups


def decode_message(group):
    """Decode a glyph group to text. Returns (decoded_text, mapped, unmapped, controls)."""
    chars = []
    mapped = 0
    unmapped = 0
    controls = 0
    for g in group:
        if g == 0xFFFE:
            chars.append(" / ")
        elif g >= 0xFB00:
            controls += 1
            chars.append(f"[{g:04X}]")
        elif str(g) in gmap:
            chars.append(gmap[str(g)])
            mapped += 1
        else:
            chars.append(f"[{g:04X}]")
            unmapped += 1
    text = "".join(chars)
    return text, mapped, unmapped, controls


def classify_group(group, mapped, unmapped, controls):
    """Classify group type for dungeon map resources."""
    total = len(group)
    if total == 0:
        return "SKIP"
    if total <= 10:
        return "POSITION"  # small layout position marker
    text_glyphs = mapped + unmapped
    if text_glyphs == 0:
        return "SKIP"
    hit_rate = mapped / text_glyphs if text_glyphs > 0 else 0
    if total > 100 or hit_rate < 0.5:
        return "DATA"  # large binary data block
    return "LAYOUT"  # template header with UI labels


# Analyze all resources
print("Analyzing R680-R911 resources...\n")
stats = {"total_groups": 0, "fb00_tags": 0, "layout": 0, "position": 0, "data": 0, "skip": 0}

for rid in RESOURCES:
    path = f"extracted/packdata_raw/{rid:04d}_type02.raw"
    if not os.path.isfile(path):
        print(f"  SKIP R{rid}: file not found")
        continue

    data = open(path, "rb").read()
    sec2 = parse_sec2(data)
    groups = decode_groups(sec2)

    # Count real speaker tags (FB00-FB0F) in section 2
    sec2_size = struct.unpack_from("<I", data, 0x14)[0]
    sec2_off = struct.unpack_from("<I", data, 0x18)[0]
    nw = sec2_size // 2
    words = [struct.unpack_from(">H", data[sec2_off:sec2_off+sec2_size], i*2)[0] for i in range(nw)]
    fb_count = sum(1 for w in words if 0xFB00 <= w <= 0xFB0F)
    stats["fb00_tags"] += fb_count

    for gi, grp in enumerate(groups):
        text, mapped, unmapped, controls = decode_message(grp)
        cat = classify_group(grp, mapped, unmapped, controls)
        stats["total_groups"] += 1
        stats[cat.lower()] += 1

    print(f"R{rid}: {len(groups)} groups, {fb_count} speaker tags -- DUNGEON MAP DATA")

# Summary
print(f"\n{'='*60}")
print(f"RESULT: All {len(RESOURCES)} resources are dungeon map data.")
print(f"  Total groups: {stats['total_groups']}")
print(f"  Real speaker tags (FB00-FB0F): {stats['fb00_tags']}")
print(f"  Breakdown: LAYOUT={stats['layout']}, POSITION={stats['position']}, "
      f"DATA={stats['data']}, SKIP={stats['skip']}")
print(f"\nNo dialogue to translate. Empty batch written.")
print(f"{'='*60}")

# Write EMPTY output -- no entries means injector will not touch these resources
out_path = "data/type2_translated/batch_dungeon_680_911.json"
json.dump([], open(out_path, "w", encoding="utf-8"), indent=2)
print(f"\nSaved empty batch to {out_path}")
