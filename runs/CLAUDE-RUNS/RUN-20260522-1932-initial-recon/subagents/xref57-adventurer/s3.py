import struct, os, json
RESDIR = r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
CLS_F = r'C:/Programmieren/wizardrytranslation/dumps/resource_classification.json'
HDR_F = r'C:/Programmieren/wizardrytranslation/dumps/msg_header_analysis.json'
OUT_F = r'C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/xref57-adventurer/search_results.json'
with open(CLS_F) as f: cls = json.load(f)
mi_list = cls['msg_resource_indices']
with open(HDR_F) as f: hdr = json.load(f)
gs_map = {r['index']: r.get('glyph_start_offset', 0) for r in hdr['resources']}
def frf(idx):
    p = f'{idx:04d}_'
    for fn in os.listdir(RESDIR):
        if fn.startswith(p) and fn.endswith('.bin'): return os.path.join(RESDIR, fn)
    return None
def exm(idx):
    fp = frf(idx)
    if not fp: return []
    with open(fp, 'rb') as f: data = f.read()
    gs = gs_map.get(idx, 0)
    reg = data[gs:]
    if len(reg) % 2: reg = reg[:-1]
    n = len(reg) // 2
    if n == 0: return []
    vals = list(struct.unpack(f'>{n}H', reg))
    msgs, cur = [], []
    for v in vals:
        if v == 0xFFFF:
            if cur: msgs.append(cur)
            cur = []
        else: cur.append(v)
    if cur: msgs.append(cur)
    return msgs
hits = []
for idx in mi_list:
    msgs = exm(idx)
    for mi, msg in enumerate(msgs):
        for i in range(len(msg) - 1):
            if msg[i] == 91 and msg[i+1] == 91:
                fc = msg.count(0xFFFE)
                nc = [v for v in msg if v != 0xFFFE]
                gs = set(msg)
                hits.append({'r': idx, 'mi': mi, 'gc': len(nc), 'fc': fc,
                    'h95': 95 in gs, 'h89': 89 in gs, 'h126': 126 in gs, 'msg': msg})
                break
print('Found %d messages with consecutive 91,91' % len(hits))
for h in hits:
    fl = ''
    if h['h95']: fl += ' [95]'
    if h['h89']: fl += ' [89]'
    if h['h126']: fl += ' [126]'
    print('  Res %d msg#%d: gc=%d fc=%d%s' % (h['r'], h['mi'], h['gc'], h['fc'], fl))
    print('    %s' % str(h['msg'][:80]))
with open(OUT_F, 'w') as f: json.dump(hits, f, indent=2, default=str)