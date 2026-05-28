import json, struct, os
from collections import Counter, defaultdict

RES_DIR = r'C:\Programmieren\wizardrytranslation\extracted\packdata_resources'
CLASS_FILE = r'C:\Programmieren\wizardrytranslation\dumps\resource_classification.json'
OUT_TXT = r'C:\Programmieren\wizardrytranslation\dumps\msg_frequency_analysis.txt'
OUT_JSON = r'C:\Programmieren\wizardrytranslation\dumps\glyph_frequency.json'
FINDINGS = r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon22-msg-freq\FINDINGS.md'

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

gf = Counter()
cc = Counter()
tm = 0
tg = 0
ugg = set()
mpr = {}
aml = []
stc = 0
rp = 0
rs_list = []
CC_SET = {0xFFFF, 0xFFFE, 0xFFD2, 0xFFD3, 0xFFE0, 0xFFE1}

for ri in msg_indices:
    fp = find_resource_file(ri)
    if fp is None:
        print(f'  WARNING: No file for index {ri}')
        continue
    vals = parse_msg(fp)
    for v in vals:
        if v in CC_SET:
            cc[v] += 1
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
    tm += mc
    mpr[ri] = mc
    rp += 1
    ru = set()
    rg = 0
    for mi, msg in enumerate(msgs):
        aml.append((len(msg), ri, mi))
        if len(msg) >= 2 and msg[0] == 0x011e and msg[1] == 0x0247:
            stc += 1
        for v in msg:
            if v < 0xFF00:
                gf[v] += 1
                ugg.add(v)
                ru.add(v)
                rg += 1
                tg += 1
    rs_list.append({'idx': ri, 'messages': mc, 'glyphs': rg, 'unique': len(ru), 'file': os.path.basename(fp)})

aml.sort(key=lambda x: x[0], reverse=True)
top200 = gf.most_common(200)
top100 = top200[:100]
mcd = Counter()
for idx, count in mpr.items():
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

gs = sorted(ugg)
ming = min(gs) if gs else 0
maxg = max(gs) if gs else 0

L = []
L.append('=' * 70)
L.append('MSG FREQUENCY ANALYSIS - BUSIN 0: Wizardry Alternative Neo')
L.append('=' * 70)
L.append('')
L.append(f'Resources processed: {rp} / {len(msg_indices)} expected')
L.append(f'Total messages across all resources: {tm}')
L.append(f'Total glyph tokens (non-control): {tg}')
L.append(f'Unique glyph indices used: {len(ugg)}')
L.append(f'Glyph index range: 0x{ming:04X} - 0x{maxg:04X}')
L.append('')
L.append('-' * 70)
L.append('CONTROL CODE COUNTS')
L.append('-' * 70)
nm = {0xFFFF: '(message delimiter)', 0xFFFE: '(line/page break)', 0xFFD2: '', 0xFFD3: '', 0xFFE0: '', 0xFFE1: ''}
for code in sorted(CC_SET, reverse=True):
    L.append(f'  0x{code:04X} {nm.get(code,"")}: {cc.get(code,0)}')
L.append('')
L.append('-' * 70)
L.append('SPEAKER TAG ANALYSIS')
L.append('-' * 70)
L.append(f'Messages starting with 011E 0247 (speaker tag): {stc}')
if tm > 0:
    L.append(f'Percentage of all messages: {stc/tm*100:.1f}%')
L.append('')
L.append('-' * 70)
L.append('MESSAGE LENGTH STATISTICS')
L.append('-' * 70)
if aml:
    lo = [x[0] for x in aml]
    av = sum(lo)/len(lo)
    L.append(f'Average message length (uint16 tokens): {av:.1f}')
    L.append(f'Median message length: {sorted(lo)[len(lo)//2]}')
    lg = aml[0]
    L.append(f'Longest message: {lg[0]} tokens (resource {lg[1]}, msg #{lg[2]})')
    sh = aml[-1]
    L.append(f'Shortest message: {sh[0]} tokens (resource {sh[1]}, msg #{sh[2]})')
    L.append('')
    L.append('Top 10 longest messages:')
    for length, ridx, midx in aml[:10]:
        L.append(f'  {length} tokens - resource {ridx}, message #{midx}')
L.append('')
L.append('-' * 70)
L.append('MESSAGE COUNT PER RESOURCE DISTRIBUTION')
L.append('-' * 70)
for b in ['0','1-5','6-10','11-20','21-50','51-100','101-200','201-500','500+']:
    if b in mcd:
        L.append(f'  {b:>8s} messages: {mcd[b]:>4d} resources')
L.append('')
rss = sorted(rs_list, key=lambda x: x['messages'], reverse=True)
L.append('Top 10 resources by message count:')
for r in rss[:10]:
    L.append(f"  Resource {r['idx']:04d} ({r['file']}): {r['messages']} messages, {r['unique']} unique glyphs")
L.append('')
L.append('-' * 70)
L.append('TOP 100 MOST FREQUENT GLYPHS')
L.append('-' * 70)
L.append(f"{'Rank':>4s}  {'Index':>6s}  {'Hex':>6s}  {'Count':>8s}  {'%':>6s}")
for rank, (gl, cnt) in enumerate(top100, 1):
    pct = cnt / tg * 100
    L.append(f'{rank:>4d}  {gl:>6d}  0x{gl:04X}  {cnt:>8d}  {pct:>5.2f}%')
L.append('')
L.append('-' * 70)
L.append('GLYPH MAPPING HYPOTHESES')
L.append('-' * 70)
L.append('Most common Japanese text characters (typical frequency order):')
L.append('  Hiragana: no ha i wo ta te ni ga ru de shi to na ka tsu')
L.append('  Katakana: - n ru su a to ku ri i ra')
L.append('  Kanji: jin dai nichi chuu nen shutsu ue sei ko hon')
L.append('  Punctuation: . , ! ? brackets')
L.append('')
gr2 = defaultdict(int)
for g, c in top200:
    rs2 = (g // 0x40) * 0x40
    gr2[rs2] += c
L.append('Glyph index clustering (by 64-glyph blocks, top 200 only):')
for rng in sorted(gr2.keys()):
    L.append(f'  0x{rng:04X}-0x{rng+0x3F:04X}: {gr2[rng]:>8d} occurrences')
L.append('')
frc = defaultdict(int)
fru = defaultdict(int)
for g, c in gf.items():
    rs2 = (g // 0x40) * 0x40
    frc[rs2] += c
    fru[rs2] += 1
L.append('Full glyph density (all glyphs, 64-glyph blocks):')
for rng in sorted(frc.keys()):
    L.append(f'  0x{rng:04X}-0x{rng+0x3F:04X}: {frc[rng]:>8d} total, {fru[rng]:>3d} unique')

ot = '\n'.join(L)
os.makedirs(os.path.dirname(OUT_TXT), exist_ok=True)
with open(OUT_TXT, 'w', encoding='utf-8') as f:
    f.write(ot)

gj = {
    'metadata': {'total_resources': rp, 'total_messages': tm, 'total_glyphs': tg, 'unique_glyphs': len(ugg), 'glyph_range': f'0x{ming:04X}-0x{maxg:04X}'},
    'control_codes': {f'0x{k:04X}': v for k, v in sorted(cc.items(), reverse=True)},
    'top_200_glyphs': [{'rank': i+1, 'index': g, 'hex': f'0x{g:04X}', 'count': c, 'pct': round(c/tg*100,3)} for i, (g, c) in enumerate(top200)]
}
with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(gj, f, indent=2, ensure_ascii=False)

F = []
F.append('# MSG Frequency Analysis Findings')
F.append('')
F.append('## Overview')
F.append('')
F.append(f'- **Resources processed**: {rp} / {len(msg_indices)}')
F.append(f'- **Total messages**: {tm}')
F.append(f'- **Total glyph tokens**: {tg}')
F.append(f'- **Unique glyph indices**: {len(ugg)}')
F.append(f'- **Glyph index range**: 0x{ming:04X} - 0x{maxg:04X}')
F.append('')
F.append('## Control Codes')
F.append('')
for code in sorted(CC_SET, reverse=True):
    F.append(f'- 0x{code:04X}: {cc.get(code, 0)}')
F.append('')
F.append('## Speaker Tags')
F.append('')
if tm > 0:
    F.append(f'- Messages starting with 0x011E 0x0247: {stc} ({stc/tm*100:.1f}% of all messages)')
F.append('')
F.append('## Message Statistics')
F.append('')
if aml:
    F.append(f'- Average length: {av:.1f} tokens')
    F.append(f'- Longest: {aml[0][0]} tokens (resource {aml[0][1]})')
    F.append(f'- Shortest: {aml[-1][0]} tokens (resource {aml[-1][1]})')
F.append('')
F.append('## Top 20 Most Frequent Glyphs')
F.append('')
F.append('| Rank | Index | Hex | Count | % |')
F.append('|------|-------|-----|-------|---|')
for rank, (gl, cnt) in enumerate(top100[:20], 1):
    pct = cnt / tg * 100
    F.append(f'| {rank} | {gl} | 0x{gl:04X} | {cnt} | {pct:.2f}% |')
F.append('')
F.append('## Glyph Block Density')
F.append('')
F.append('Major populated blocks (64-glyph chunks with >1000 occurrences):')
F.append('')
for rng in sorted(frc.keys()):
    if frc[rng] > 1000:
        F.append(f'- 0x{rng:04X}-0x{rng+0x3F:04X}: {frc[rng]} total, {fru[rng]} unique')
F.append('')
F.append('## Key Observations')
F.append('')
F.append('1. Glyph indices likely map to a custom font atlas (see font recon tasks)')
F.append('2. The glyph range suggests a fixed-size character set in the font texture')
F.append('3. Speaker tags (011E 0247) mark dialogue lines with character names')
F.append('4. 0xFFFE serves as line/page break within messages, 0xFFFF as message delimiter')
F.append('')
F.append('## Output Files')
F.append('')
F.append('- dumps/msg_frequency_analysis.txt - Full analysis')
F.append('- dumps/glyph_frequency.json - Top 200 glyph frequencies as JSON')

os.makedirs(os.path.dirname(FINDINGS), exist_ok=True)
with open(FINDINGS, 'w', encoding='utf-8') as f:
    f.write('\n'.join(F))

print(ot[:5000])
print('\n... (truncated)')
print(f'\nFiles written: {OUT_TXT}, {OUT_JSON}, {FINDINGS}')
