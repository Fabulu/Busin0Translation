#!/usr/bin/env python3
"""Scan PACKDATA resources for untranslated text - v2 with better heuristics."""
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

# Build char lookup
glyph_chars = {}
for k, v in glyph_map.items():
    try:
        glyph_chars[int(k)] = v
    except ValueError:
        pass

print(f"Loaded {len(manifest)} resources, {len(valid_glyphs)} glyph mappings")

def find_text_runs(data, glyph_set, min_run=4):
    """Find consecutive runs of BE uint16 values that decode as glyphs.

    Returns list of (offset, length, decoded_text) for runs >= min_run chars.
    This is much more reliable than overall hit rate for detecting real text.
    """
    runs = []
    current_run_start = None
    current_run_chars = []

    for i in range(0, len(data) - 1, 2):
        val = struct.unpack('>H', data[i:i+2])[0]
        if val in glyph_set and val >= 8:  # Skip control codes 0-7
            ch = glyph_chars.get(val, '?')
            if current_run_start is None:
                current_run_start = i
                current_run_chars = [ch]
            else:
                current_run_chars.append(ch)
        else:
            if current_run_start is not None and len(current_run_chars) >= min_run:
                text = ''.join(current_run_chars)
                runs.append((current_run_start, len(current_run_chars), text))
            current_run_start = None
            current_run_chars = []

    # Don't forget last run
    if current_run_start is not None and len(current_run_chars) >= min_run:
        text = ''.join(current_run_chars)
        runs.append((current_run_start, len(current_run_chars), text))

    return runs

def has_japanese_text(text):
    """Check if text contains actual Japanese (hiragana, katakana, kanji)."""
    jp_count = 0
    for ch in text:
        cp = ord(ch)
        if (0x3040 <= cp <= 0x309F or  # Hiragana
            0x30A0 <= cp <= 0x30FF or  # Katakana
            0x4E00 <= cp <= 0x9FFF or  # CJK
            0xFF01 <= cp <= 0xFF5E):   # Fullwidth
            jp_count += 1
    return jp_count >= 3

def score_resource(filepath, glyph_set):
    """Score a resource for text content. Returns detailed analysis."""
    try:
        data = open(filepath, 'rb').read()
    except FileNotFoundError:
        return None

    if len(data) < 10:
        return None

    runs = find_text_runs(data, glyph_set, min_run=4)

    if not runs:
        return None

    # Filter runs that contain actual Japanese
    jp_runs = [r for r in runs if has_japanese_text(r[2])]

    if not jp_runs:
        return None

    total_jp_chars = sum(r[1] for r in jp_runs)
    longest_run = max(r[1] for r in jp_runs)

    return {
        'file_size': len(data),
        'total_runs': len(runs),
        'jp_runs': len(jp_runs),
        'total_jp_chars': total_jp_chars,
        'longest_run': longest_run,
        'sample_runs': jp_runs[:8],  # First 8 Japanese text runs
    }

# Scan ALL resource types
print("\n--- Scanning all non-translated resources for Japanese text runs ---")

results = []
for r in manifest:
    if r.get('skipped'):
        continue
    idx = r['index']
    tc = r['type_code']

    if idx in ALREADY_DONE or idx in EXCLUDED:
        continue

    filepath = os.path.join(RES_DIR, r['filename'])
    score = score_resource(filepath, valid_glyphs)

    if score is None:
        continue

    # Only keep resources with meaningful text
    # At least 3 Japanese runs OR longest run >= 8 chars
    if score['jp_runs'] >= 3 or score['longest_run'] >= 8:
        results.append({
            'index': idx,
            'type_code': tc,
            'filename': r['filename'],
            'payload_size': r['payload_size'],
            **score,
        })

# Sort: prioritize resources with most readable text
results.sort(key=lambda x: (-x['total_jp_chars']))

print(f"Found {len(results)} resources with Japanese text runs")

# Categorize
CATEGORY_CONFIRMED_TEXT = []  # Clearly readable sentences
CATEGORY_LABELS = []          # Short labels/names
CATEGORY_MIXED = []           # Binary with some embedded text
CATEGORY_FALSE_POS = []       # Likely false positives (repetitive patterns)

for r in results:
    # Check if sample text looks like real sentences (has particles, punctuation)
    all_text = ' '.join(run[2] for run in r['sample_runs'])

    # Detect repetitive patterns (likely binary data)
    if r['sample_runs']:
        first_text = r['sample_runs'][0][2]
        unique_chars = len(set(first_text))
        if unique_chars <= 3 and len(first_text) > 10:
            CATEGORY_FALSE_POS.append(r)
            continue

    has_particles = any(p in all_text for p in ['の', 'は', 'が', 'を', 'に', 'で', 'と', 'も', 'へ', 'から', 'まで', 'より'])
    has_punctuation = any(p in all_text for p in ['。', '！', '？', '、', '…', '「', '」'])

    if has_particles and has_punctuation and r['longest_run'] >= 10:
        CATEGORY_CONFIRMED_TEXT.append(r)
    elif r['longest_run'] >= 6:
        CATEGORY_LABELS.append(r)
    else:
        CATEGORY_MIXED.append(r)

# Generate report
lines = []
lines.append("# PACKDATA Missed Text Scan Results (v2)")
lines.append(f"\nScan date: 2026-05-28")
lines.append(f"Total resources: {len(manifest)}")
lines.append(f"Already translated: R{', R'.join(str(x) for x in sorted(ALREADY_DONE))}")
lines.append(f"Excluded (unsafe): R{', R'.join(str(x) for x in sorted(EXCLUDED))}")
lines.append(f"\nMethod: Consecutive glyph-run detection (min 4 chars), filtered for Japanese content")
lines.append(f"Total resources with Japanese text: {len(results)}")

lines.append(f"\n## Category A: Confirmed Translatable Text ({len(CATEGORY_CONFIRMED_TEXT)} resources)\n")
lines.append("These contain readable Japanese sentences with particles and punctuation.\n")

for r in CATEGORY_CONFIRMED_TEXT:
    lines.append(f"### R{r['index']} (type-{r['type_code']:02d}, {r['payload_size']} bytes)")
    lines.append(f"- Japanese text runs: {r['jp_runs']}, total chars: {r['total_jp_chars']}, longest: {r['longest_run']}")
    lines.append(f"- Sample text:")
    for offset, length, text in r['sample_runs'][:5]:
        display = text[:80]
        lines.append(f"  - @{offset}: `{display}`")
    lines.append("")

lines.append(f"\n## Category B: Labels/Short Text ({len(CATEGORY_LABELS)} resources)\n")
lines.append("These contain shorter text fragments - possibly item names, menu labels, dungeon names.\n")

for r in CATEGORY_LABELS[:40]:  # Limit output
    sample_texts = [run[2][:40] for run in r['sample_runs'][:3]]
    lines.append(f"- **R{r['index']}** (type-{r['type_code']:02d}, {r['payload_size']}B) runs={r['jp_runs']} longest={r['longest_run']} | {' / '.join(sample_texts)}")

if len(CATEGORY_LABELS) > 40:
    lines.append(f"\n... and {len(CATEGORY_LABELS)-40} more")

lines.append(f"\n## Category C: Mixed/Embedded ({len(CATEGORY_MIXED)} resources)\n")
lines.append("Binary data with some embedded text fragments.\n")
for r in CATEGORY_MIXED[:20]:
    sample_texts = [run[2][:30] for run in r['sample_runs'][:2]]
    lines.append(f"- R{r['index']} (type-{r['type_code']:02d}) | {' / '.join(sample_texts)}")
if len(CATEGORY_MIXED) > 20:
    lines.append(f"\n... and {len(CATEGORY_MIXED)-20} more")

lines.append(f"\n## Category D: Likely False Positives ({len(CATEGORY_FALSE_POS)} resources)\n")
lines.append("Repetitive patterns, probably binary data.\n")

# Untranslated system menu range
lines.append("\n## Focus: Untranslated System Menus (R34-R49)\n")
lines.append("| Resource | Status | Sample |")
lines.append("|----------|--------|--------|")
for r in manifest:
    if r.get('skipped'):
        continue
    idx = r['index']
    if 34 <= idx <= 49 and r['type_code'] == 1:
        status = "TRANSLATED" if idx in ALREADY_DONE else "NOT TRANSLATED"
        filepath = os.path.join(RES_DIR, r['filename'])
        score = score_resource(filepath, valid_glyphs)
        sample = ""
        if score and score['sample_runs']:
            sample = score['sample_runs'][0][2][:50]
        lines.append(f"| R{idx} | {status} | `{sample}` |")

# Type-02 MSG coverage
lines.append("\n## Type-02 (MSG) Resources\n")
type2_list = [r for r in manifest if not r.get('skipped') and r['type_code'] == 2]
lines.append(f"Total type-02 resources: {len(type2_list)}")
lines.append("These are handled by the main MSG translation pipeline (12,725+ messages injected).")

# Non-standard types with text
lines.append("\n## Non-Standard Types with Text\n")
non_std = [r for r in results if r['type_code'] not in (1, 2)]
if non_std:
    for r in non_std:
        sample_texts = [run[2][:40] for run in r['sample_runs'][:3]]
        lines.append(f"- **R{r['index']}** type-{r['type_code']:02d} ({r['payload_size']}B) | {' / '.join(sample_texts)}")
else:
    lines.append("None found.")

# Action items
lines.append("\n## Action Items\n")
lines.append("### High Priority (confirmed translatable text, not yet translated)")
for r in CATEGORY_CONFIRMED_TEXT:
    if r['index'] not in ALREADY_DONE:
        lines.append(f"- [ ] R{r['index']} (type-{r['type_code']:02d}): {r['total_jp_chars']} JP chars, {r['jp_runs']} text runs")

lines.append("\n### Medium Priority (labels/names)")
menu_range = [r for r in CATEGORY_LABELS if 34 <= r['index'] <= 49]
for r in menu_range:
    if r['index'] not in ALREADY_DONE:
        lines.append(f"- [ ] R{r['index']} (system menu): {r['total_jp_chars']} JP chars")

out_path = os.path.join(OUT_DIR, "packdata_missed_scan.md")
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
print(f"\nReport written to: {out_path}")

# Console summary
print(f"\n=== SUMMARY ===")
print(f"Category A (confirmed text):    {len(CATEGORY_CONFIRMED_TEXT)}")
print(f"Category B (labels/short):      {len(CATEGORY_LABELS)}")
print(f"Category C (mixed/embedded):    {len(CATEGORY_MIXED)}")
print(f"Category D (false positives):   {len(CATEGORY_FALSE_POS)}")

print(f"\n=== TOP CONFIRMED TEXT (not yet translated) ===")
for r in CATEGORY_CONFIRMED_TEXT[:20]:
    sample = r['sample_runs'][0][2][:60] if r['sample_runs'] else ''
    print(f"  R{r['index']:04d} type{r['type_code']:02d}  runs={r['jp_runs']:3d}  chars={r['total_jp_chars']:5d}  longest={r['longest_run']:3d}  {sample}")

print(f"\n=== UNTRANSLATED SYSTEM MENUS (R36-R49) ===")
for r in CATEGORY_CONFIRMED_TEXT + CATEGORY_LABELS:
    if 34 <= r['index'] <= 49 and r['index'] not in ALREADY_DONE:
        sample = r['sample_runs'][0][2][:60] if r['sample_runs'] else ''
        print(f"  R{r['index']:04d}  runs={r['jp_runs']:3d}  chars={r['total_jp_chars']:5d}  {sample}")
