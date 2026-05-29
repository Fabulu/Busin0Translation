#!/usr/bin/env python3
"""Scan PACKDATA resources for untranslated text."""
import json, struct, sys, os

sys.stdout.reconfigure(encoding='utf-8')

BASE = "C:/Programmieren/wizardrytranslation"
RES_DIR = f"{BASE}/extracted/packdata_resources"
MANIFEST = f"{RES_DIR}/manifest.json"
GLYPH_MAP = f"{BASE}/data/msg_glyph_map.json"
OUT_DIR = f"{BASE}/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese"

# Already translated/patched resources
ALREADY_DONE = {34, 35, 38, 39, 2124, 2654}
# Known text but excluded (unsafe)
EXCLUDED = {1053, 1908}

manifest = json.load(open(MANIFEST, 'r', encoding='utf-8'))
glyph_map = json.load(open(GLYPH_MAP, 'r', encoding='utf-8'))

# Build set of valid glyph indices
valid_glyphs = set()
for k in glyph_map.keys():
    try:
        valid_glyphs.add(int(k))
    except ValueError:
        pass

print(f"Loaded {len(manifest)} resources, {len(valid_glyphs)} glyph mappings")
print(f"Glyph index range: {min(valid_glyphs)}-{max(valid_glyphs)}")

# Count by type
types = {}
for r in manifest:
    if r.get('skipped'):
        continue
    t = r['type_code']
    types[t] = types.get(t, 0) + 1
print("\nResource type counts:")
for t in sorted(types.keys()):
    print(f"  type {t:02d}: {types[t]}")

# Types to scan
SCAN_TYPES = {1, 2, 15, 20, 44}

def scan_resource(filepath, glyph_set):
    """Scan a binary file for BE uint16 values matching glyph indices."""
    try:
        data = open(filepath, 'rb').read()
    except FileNotFoundError:
        return None

    if len(data) < 4:
        return None

    total_u16 = 0
    glyph_hits = 0
    hit_indices = []

    # Scan every 2-byte aligned position
    for i in range(0, len(data) - 1, 2):
        val = struct.unpack('>H', data[i:i+2])[0]
        if 32 <= val <= 3000:  # reasonable text range
            total_u16 += 1
            if val in glyph_set:
                glyph_hits += 1
                if len(hit_indices) < 50:
                    hit_indices.append((i, val))

    if total_u16 == 0:
        return None

    return {
        'total_u16': total_u16,
        'glyph_hits': glyph_hits,
        'hit_rate': glyph_hits / total_u16 if total_u16 > 0 else 0,
        'hit_indices': hit_indices,
        'file_size': len(data),
    }

def decode_glyphs(hit_indices, glyph_map_dict):
    """Try to decode glyph indices to characters."""
    chars = []
    for offset, idx in hit_indices:
        ch = glyph_map_dict.get(str(idx), None)
        if ch:
            chars.append(ch)
        else:
            chars.append(f'[{idx}]')
    return ''.join(chars)

# Scan all target type resources
results = []
print("\n--- Scanning resources ---")

for r in manifest:
    if r.get('skipped'):
        continue
    idx = r['index']
    tc = r['type_code']

    if tc not in SCAN_TYPES:
        continue
    if idx in ALREADY_DONE or idx in EXCLUDED:
        continue

    filepath = os.path.join(RES_DIR, r['filename'])
    scan = scan_resource(filepath, valid_glyphs)

    if scan is None:
        continue

    # Flag if >30% hit rate AND >20 glyph-range values
    if scan['glyph_hits'] >= 20 and scan['hit_rate'] >= 0.30:
        results.append({
            'index': idx,
            'type_code': tc,
            'filename': r['filename'],
            'payload_size': r['payload_size'],
            **scan,
        })

# Sort by hit rate descending
results.sort(key=lambda x: (-x['hit_rate'], -x['glyph_hits']))

print(f"\nFound {len(results)} resources with potential text")

# Generate report
lines = []
lines.append("# PACKDATA Missed Text Scan Results")
lines.append(f"\nScan date: 2026-05-28")
lines.append(f"Total resources: {len(manifest)}")
lines.append(f"Glyph mappings: {len(valid_glyphs)}")
lines.append(f"Already translated: {sorted(ALREADY_DONE)}")
lines.append(f"Excluded (unsafe): {sorted(EXCLUDED)}")
lines.append(f"\nScanned types: {sorted(SCAN_TYPES)}")
lines.append(f"Resources flagged: {len(results)}")
lines.append(f"\nThresholds: hit_rate >= 30%, glyph_hits >= 20")

lines.append("\n## Flagged Resources\n")

# Group by type
by_type = {}
for r in results:
    by_type.setdefault(r['type_code'], []).append(r)

for tc in sorted(by_type.keys()):
    lines.append(f"### Type {tc:02d}\n")
    for r in by_type[tc]:
        sample = decode_glyphs(r['hit_indices'][:30], glyph_map)
        lines.append(f"**R{r['index']}** ({r['filename']}, {r['payload_size']} bytes)")
        lines.append(f"- Glyph hits: {r['glyph_hits']}/{r['total_u16']} ({r['hit_rate']:.1%})")
        lines.append(f"- Sample decoded: `{sample}`")
        lines.append("")

# Also list type-01 resources in the R34-R49 system menu range that aren't done
lines.append("\n## Untranslated System Menu Resources (R34-R49 range)\n")
for r in manifest:
    if r.get('skipped'):
        continue
    idx = r['index']
    if 34 <= idx <= 49 and r['type_code'] == 1:
        if idx not in ALREADY_DONE:
            filepath = os.path.join(RES_DIR, r['filename'])
            scan = scan_resource(filepath, valid_glyphs)
            status = "no text detected"
            if scan and scan['glyph_hits'] > 5:
                sample = decode_glyphs(scan['hit_indices'][:20], glyph_map)
                status = f"hits={scan['glyph_hits']}, rate={scan['hit_rate']:.1%}, sample=`{sample}`"
            elif scan:
                status = f"low hits ({scan['glyph_hits']})"
            lines.append(f"- **R{idx}** ({r['filename']}): {status}")

# Summary of type-02 (MSG) resources - these are the main text
lines.append("\n## Type-02 (MSG) Resource Summary\n")
type2_count = 0
type2_done = 0
for r in manifest:
    if r.get('skipped'):
        continue
    if r['type_code'] == 2:
        type2_count += 1
lines.append(f"Total type-02 resources: {type2_count}")
lines.append(f"(Type-02 are MSG format and handled by the main translation pipeline)")

# Check for any other unusual types that might have text
lines.append("\n## Other Type Scan (types 15, 20, 44)\n")
other_found = False
for tc_check in [15, 20, 44]:
    count = types.get(tc_check, 0)
    if count > 0:
        lines.append(f"Type {tc_check:02d}: {count} resources exist")
        other_found = True
    else:
        lines.append(f"Type {tc_check:02d}: not present in PACKDATA")
if not other_found:
    lines.append("None of these types exist in PACKDATA.")

# Final verdict
lines.append("\n## Verdict\n")
type01_flagged = len(by_type.get(1, []))
other_flagged = len(results) - type01_flagged
lines.append(f"- Type-01 resources with potential text: {type01_flagged}")
lines.append(f"- Other type resources with potential text: {other_flagged}")

out_path = os.path.join(OUT_DIR, "packdata_missed_scan.md")
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
print(f"\nReport written to: {out_path}")

# Print top hits to console
print("\n=== TOP FLAGGED RESOURCES ===")
for r in results[:25]:
    sample = decode_glyphs(r['hit_indices'][:20], glyph_map)
    print(f"  R{r['index']:04d} type{r['type_code']:02d}  hits={r['glyph_hits']:4d}  rate={r['hit_rate']:.1%}  size={r['payload_size']:6d}  sample={sample[:60]}")
