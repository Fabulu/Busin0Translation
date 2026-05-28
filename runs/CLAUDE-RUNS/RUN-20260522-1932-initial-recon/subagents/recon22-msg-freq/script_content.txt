import json, struct, os
from collections import Counter, defaultdict

RES_DIR = r'C:\Programmieren\wizardrytranslation\extracted\packdata_resources'
CLASS_FILE = r'C:\Programmieren\wizardrytranslation\dumps\resource_classification.json'
OUT_TXT = r'C:\Programmieren\wizardrytranslation\dumps\msg_frequency_analysis.txt'
OUT_JSON = r'C:\Programmieren\wizardrytranslation\dumps\glyph_frequency.json'
FINDINGS = r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon22-msg-freq\FINDINGS.md'

GLYPH_MAX = 0x035A  # max glyph index per MSG format spec
CONTROL_MIN = 0xFFC0  # min control code

with open(CLASS_FILE, 'r') as f:
    classification = json.load(f)
msg_indices = classification['msg_resource_indices']
print(f'MSG resource indices count: {len(msg_indices)}')

def find_resource_file(idx):
    prefix = f'{idx:04d}_'
    for fn in os.listdir(RES_DIR):
        if fn.startswith(prefix) and fn.endswith('.bin'):
            return os.path.join(RES_DIR, fn)
    return None

def parse_msg(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    if len(data) % 2 != 0:
        data = data[:-1]
    n = len(data) // 2
    return struct.unpack(f'>{n}H', data)

def is_valid_msg_resource(vals):
    """Check if resource looks like genuine MSG data.
    Valid MSG: most non-zero values should be either glyphs (0-0x035A) or controls (0xFFC0+)."""
    if len(vals) < 4:
        return False
    # Count how many values fall in valid ranges
    valid = 0
    total_nonzero = 0
    ffff_count = 0
    for v in vals:
        if v == 0:
            continue
        total_nonzero += 1
        if v == 0xFFFF:
            ffff_count += 1
            valid += 1
        elif v <= GLYPH_MAX:
            valid += 1
        elif v >= CONTROL_MIN:
            valid += 1
    if total_nonzero == 0:
        return False
    ratio = valid / total_nonzero
    # Need at least 70% of non-zero values in valid ranges, and at least 2 FFFF delimiters
    return ratio >= 0.70 and ffff_count >= 2

# Global counters
glyph_freq = Counter()
control_codes = Counter()
total_messages = 0
total_glyphs = 0
unique_glyphs = set()
messages_per_resource = {}
all_message_lengths = []
speaker_tag_count = 0
resources_processed = 0
resources_skipped = 0
resource_stats = []
skipped_resources = []

CC_TO_COUNT = {0xFFFF, 0xFFFE, 0xFFD2, 0xFFD3, 0xFFE0, 0xFFE1, 0xFFF9, 0xFFD4, 0xFFC0, 0xFFC1, 0xFFD0, 0xFFD1, 0xFFE2, 0xFFE3, 0xFFE7}
all_control_codes = Counter()

for ri in msg_indices:
    fp = find_resource_file(ri)
    if fp is None:
        print(f'  WARNING: No file for index {ri}')
        continue

    vals = parse_msg(fp)

    if not is_valid_msg_resource(vals):
        resources_skipped += 1
        skipped_resources.append(ri)
        continue

    # Count ALL control codes
    for v in vals:
        if v >= CONTROL_MIN:
            all_control_codes[v] += 1

    # Split on 0xFFFF to get messages
    msgs = []
    cur = []
    for v in vals:
        if v == 0xFFFF:
            if cur:
                msgs.append(cur)
            cur = []
        else:
            cur.append(v)
    if cur:
        msgs.append(cur)

    mc = len(msgs)
    total_messages += mc
    messages_per_resource[ri] = mc
    resources_processed += 1
    ru = set()
    rg = 0

    for mi, msg in enumerate(msgs):
        # Filter out trailing zero-padding "messages"
        non_zero = [v for v in msg if v != 0]
        if len(non_zero) == 0:
            total_messages -= 1  # don't count empty/padding
            continue

        msg_glyph_count = 0
        for v in msg:
            if v <= GLYPH_MAX:
                glyph_freq[v] += 1
                unique_glyphs.add(v)
                ru.add(v)
                msg_glyph_count += 1
                total_glyphs += 1
                rg += 1

        all_message_lengths.append((len(non_zero), ri, mi))

        # Check speaker tag pattern
        if len(msg) >= 2 and msg[0] == 0x011e and msg[1] == 0x0247:
            speaker_tag_count += 1

    resource_stats.append({'idx': ri, 'messages': mc, 'glyphs': rg, 'unique': len(ru), 'file': os.path.basename(fp)})

all_message_lengths.sort(key=lambda x: x[0], reverse=True)
top200 = glyph_freq.most_common(200)
top100 = top200[:100]

# Message count distribution
mcd = Counter()
for idx, count in messages_per_resource.items():
    if count == 0: b = '0'
    elif count <= 5: b = '1-5'
    elif count <= 10: b = '6-10'
    elif count <= 20: b = '11-20'
    elif count <= 50: b = '21-50'
    elif count <= 100: b = '51-100'
    elif count <= 200: b = '101-200'
    elif count <= 500: b = '201-500'
    else: b = '500+'
    mcd[b] += 1

gs = sorted(unique_glyphs)
ming = min(gs) if gs else 0
maxg = max(gs) if gs else 0

# Build output
L = []
L.append('=' * 70)
L.append('MSG FREQUENCY ANALYSIS - BUSIN 0: Wizardry Alternative Neo')
L.append('=' * 70)
L.append('')
L.append(f'Resources processed (valid MSG): {resources_processed} / {len(msg_indices)} classified')
L.append(f'Resources skipped (not valid MSG data): {resources_skipped}')
L.append(f'Total messages across all resources: {total_messages}')
L.append(f'Total glyph tokens (0x0000-0x{GLYPH_MAX:04X}): {total_glyphs}')
L.append(f'Unique glyph indices used: {len(unique_glyphs)}')
L.append(f'Glyph index range observed: 0x{ming:04X} - 0x{maxg:04X}')
L.append('')

L.append('-' * 70)
L.append('SKIPPED RESOURCES (not valid MSG format)')
L.append('-' * 70)
L.append(f'Count: {len(skipped_resources)}')
if skipped_resources:
    L.append(f'Indices: {", ".join(str(x) for x in skipped_resources[:50])}')
    if len(skipped_resources) > 50:
        L.append(f'  ... and {len(skipped_resources)-50} more')
L.append('')

L.append('-' * 70)
L.append('CONTROL CODE COUNTS (all observed)')
L.append('-' * 70)
nm = {0xFFFF: 'message delimiter', 0xFFFE: 'line break', 0xFFD2: 'page break', 0xFFD3: 'page break variant', 0xFFD4: 'page break variant 2', 0xFFE0: 'format off', 0xFFE1: 'format on', 0xFFF9: 'wait+newline', 0xFFC0: 'rare ctrl', 0xFFC1: 'rare ctrl'}
for code, count in all_control_codes.most_common(30):
    name = nm.get(code, '')
    L.append(f'  0x{code:04X} ({name}): {count}')
L.append('')

L.append('-' * 70)
L.append('SPEAKER TAG ANALYSIS')
L.append('-' * 70)
L.append(f'Messages starting with 011E 0247 (speaker tag): {speaker_tag_count}')
if total_messages > 0:
    L.append(f'Percentage of all messages: {speaker_tag_count/total_messages*100:.1f}%')
L.append('')

L.append('-' * 70)
L.append('MESSAGE LENGTH STATISTICS')
L.append('-' * 70)
if all_message_lengths:
    lo = [x[0] for x in all_message_lengths]
    av = sum(lo)/len(lo)
    slo = sorted(lo)
    L.append(f'Average message length (non-zero tokens): {av:.1f}')
    L.append(f'Median message length: {slo[len(slo)//2]}')
    lg = all_message_lengths[0]
    L.append(f'Longest message: {lg[0]} tokens (resource {lg[1]}, msg #{lg[2]})')
    sh = all_message_lengths[-1]
    L.append(f'Shortest message: {sh[0]} tokens (resource {sh[1]}, msg #{sh[2]})')
    L.append('')
    L.append('Top 10 longest messages:')
    for length, ridx, midx in all_message_lengths[:10]:
        L.append(f'  {length} tokens - resource {ridx}, message #{midx}')
    L.append('')
    L.append('Message length distribution:')
    len_buckets = Counter()
    for length in lo:
        if length <= 5: lb = '1-5'
        elif length <= 10: lb = '6-10'
        elif length <= 20: lb = '11-20'
        elif length <= 50: lb = '21-50'
        elif length <= 100: lb = '51-100'
        elif length <= 200: lb = '101-200'
        elif length <= 500: lb = '201-500'
        else: lb = '500+'
        len_buckets[lb] += 1
    for b in ['1-5', '6-10', '11-20', '21-50', '51-100', '101-200', '201-500', '500+']:
        if b in len_buckets:
            L.append(f'  {b:>8s} tokens: {len_buckets[b]:>6d} messages')
L.append('')

L.append('-' * 70)
L.append('MESSAGE COUNT PER RESOURCE DISTRIBUTION')
L.append('-' * 70)
for b in ['0','1-5','6-10','11-20','21-50','51-100','101-200','201-500','500+']:
    if b in mcd:
        L.append(f'  {b:>8s} messages: {mcd[b]:>4d} resources')
L.append('')
rss = sorted(resource_stats, key=lambda x: x['messages'], reverse=True)
L.append('Top 10 resources by message count:')
for r in rss[:10]:
    L.append(f"  Resource {r['idx']:04d} ({r['file']}): {r['messages']} messages, {r['unique']} unique glyphs")
L.append('')

L.append('-' * 70)
L.append('TOP 100 MOST FREQUENT GLYPHS')
L.append('-' * 70)
L.append(f"{'Rank':>4s}  {'Index':>6s}  {'Hex':>6s}  {'Count':>8s}  {'%':>6s}")
for rank, (gl, cnt) in enumerate(top100, 1):
    pct = cnt / total_glyphs * 100
    L.append(f'{rank:>4d}  {gl:>6d}  0x{gl:04X}  {cnt:>8d}  {pct:>5.2f}%')
L.append('')

L.append('-' * 70)
L.append('GLYPH MAPPING HYPOTHESES')
L.append('-' * 70)
L.append('Based on Japanese text frequency analysis:')
L.append('Most common hiragana in descending frequency:')
L.append('  no, ha/wa, i, shi, ta, te, ni, na, to, ka, ru, wo, de, ga, tsu')
L.append('')
L.append('If top glyph = most common char, hypothesized mappings:')
for i, (gl, cnt) in enumerate(top100[:15]):
    hyp = ['<space/null>', 'no?', 'ha?', 'i?', 'shi?', 'ta?', 'te?', 'ni?', 'na?', 'to?', 'ka?', 'ru?', 'wo?', 'de?', 'ga?']
    h = hyp[i] if i < len(hyp) else '?'
    L.append(f'  0x{gl:04X} (count={cnt}) -> likely: {h}')
L.append('  NOTE: Glyph 0x0000 may be space/null rather than a printable character')
L.append('  NOTE: Need font atlas to confirm actual character mappings')
L.append('')

# Glyph clustering
L.append('-' * 70)
L.append('GLYPH RANGE DENSITY')
L.append('-' * 70)
frc = defaultdict(int)
fru = defaultdict(int)
for g, c in glyph_freq.items():
    rs2 = (g // 0x40) * 0x40
    frc[rs2] += c
    fru[rs2] += 1
for rng in sorted(frc.keys()):
    L.append(f'  0x{rng:04X}-0x{rng+0x3F:04X}: {frc[rng]:>8d} total, {fru[rng]:>3d} unique glyphs')
L.append('')

# 16-glyph blocks for finer analysis
L.append('Fine-grained density (16-glyph blocks, top 30):')
frc16 = defaultdict(int)
fru16 = defaultdict(int)
for g, c in glyph_freq.items():
    rs2 = (g // 0x10) * 0x10
    frc16[rs2] += c
    fru16[rs2] += 1
top_blocks = sorted(frc16.items(), key=lambda x: x[1], reverse=True)[:30]
for rng, total in top_blocks:
    L.append(f'  0x{rng:04X}-0x{rng+0x0F:04X}: {total:>8d} total, {fru16[rng]:>3d} unique')

ot = '\n'.join(L)
os.makedirs(os.path.dirname(OUT_TXT), exist_ok=True)
with open(OUT_TXT, 'w', encoding='utf-8') as f:
    f.write(ot)

# JSON output
gj = {
    'metadata': {
        'total_resources_classified': len(msg_indices),
        'valid_msg_resources': resources_processed,
        'skipped_resources': resources_skipped,
        'total_messages': total_messages,
        'total_glyphs': total_glyphs,
        'unique_glyphs': len(unique_glyphs),
        'glyph_range': f'0x{ming:04X}-0x{maxg:04X}',
        'speaker_tag_messages': speaker_tag_count
    },
    'control_codes': {f'0x{k:04X}': v for k, v in all_control_codes.most_common()},
    'top_200_glyphs': [{'rank': i+1, 'index': g, 'hex': f'0x{g:04X}', 'count': c, 'pct': round(c/total_glyphs*100,3)} for i, (g, c) in enumerate(top200)]
}
with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(gj, f, indent=2, ensure_ascii=False)

# FINDINGS.md
F = []
F.append('# MSG Frequency Analysis Findings')
F.append('')
F.append('## Overview')
F.append('')
F.append(f'- **Resources classified as MSG**: {len(msg_indices)}')
F.append(f'- **Valid MSG resources**: {resources_processed}')
F.append(f'- **Skipped (non-MSG binary data)**: {resources_skipped}')
F.append(f'- **Total messages**: {total_messages}')
F.append(f'- **Total glyph tokens**: {total_glyphs}')
F.append(f'- **Unique glyph indices**: {len(unique_glyphs)}')
F.append(f'- **Glyph index range**: 0x{ming:04X} - 0x{maxg:04X}')
F.append('')
F.append('## Control Codes')
F.append('')
for code, count in all_control_codes.most_common(10):
    name = nm.get(code, '')
    F.append(f'- 0x{code:04X} ({name}): {count}')
F.append('')
F.append('## Speaker Tags')
F.append('')
if total_messages > 0:
    F.append(f'- Messages starting with 0x011E 0x0247: {speaker_tag_count} ({speaker_tag_count/total_messages*100:.1f}% of all messages)')
F.append('')
F.append('## Message Statistics')
F.append('')
if all_message_lengths:
    F.append(f'- Average length: {av:.1f} tokens')
    F.append(f'- Median length: {slo[len(slo)//2]} tokens')
    F.append(f'- Longest: {all_message_lengths[0][0]} tokens (resource {all_message_lengths[0][1]})')
    F.append(f'- Shortest: {all_message_lengths[-1][0]} tokens (resource {all_message_lengths[-1][1]})')
F.append('')
F.append('## Top 20 Most Frequent Glyphs')
F.append('')
F.append('| Rank | Index | Hex | Count | % |')
F.append('|------|-------|-----|-------|---|')
for rank, (gl, cnt) in enumerate(top100[:20], 1):
    pct = cnt / total_glyphs * 100
    F.append(f'| {rank} | {gl} | 0x{gl:04X} | {cnt} | {pct:.2f}% |')
F.append('')
F.append('## Glyph Block Density (64-glyph chunks)')
F.append('')
for rng in sorted(frc.keys()):
    if frc[rng] > 100:
        F.append(f'- 0x{rng:04X}-0x{rng+0x3F:04X}: {frc[rng]} total, {fru[rng]} unique')
F.append('')
F.append('## Key Observations')
F.append('')
F.append('1. Glyph indices map to a custom font atlas; range 0x0000-0x035A (~858 possible tiles)')
F.append('2. Many of the 296 "MSG" resources contain non-text binary data that happens to have FFFF patterns')
F.append('3. Valid MSG resources use a flat BE uint16 stream: [glyphs...] FFFF [glyphs...] FFFF ...')
F.append('4. Speaker tags (011E 0247) identify dialogue lines with named speakers')
F.append('5. Control codes 0xFFFE (line break) and 0xFFFF (message end) are the most common controls')
F.append('6. Glyph 0x0000 is by far the most frequent -- may represent space or be a padding value')
F.append('7. Frequency distribution can guide hypothetical character mapping against known Japanese frequencies')
F.append('')
F.append('## Output Files')
F.append('')
F.append('- `dumps/msg_frequency_analysis.txt` - Full analysis with all statistics')
F.append('- `dumps/glyph_frequency.json` - Top 200 glyph frequencies as structured JSON')

os.makedirs(os.path.dirname(FINDINGS), exist_ok=True)
with open(FINDINGS, 'w', encoding='utf-8') as f:
    f.write('\n'.join(F))

print(ot[:6000])
print('\n... (truncated, full output in file)')
print(f'\nFiles written: {OUT_TXT}, {OUT_JSON}, {FINDINGS}')
