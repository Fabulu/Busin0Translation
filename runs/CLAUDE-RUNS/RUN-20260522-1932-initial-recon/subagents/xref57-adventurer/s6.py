import struct, os, json
RESDIR = r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
HDR_F = r'C:/Programmieren/wizardrytranslation/dumps/msg_header_analysis.json'
CLS_F = r'C:/Programmieren/wizardrytranslation/dumps/resource_classification.json'
with open(CLS_F) as f: cls = json.load(f)
mi_list = cls['msg_resource_indices']
with open(HDR_F) as f: hdr = json.load(f)
gs_map = {r['index']: r.get('glyph_start_offset', 0) for r in hdr['resources']}
def frf(idx):
    p = '%04d_' % idx
    for fn in os.listdir(RESDIR):
        if fn.startswith(p) and fn.endswith('.bin'): return os.path.join(RESDIR, fn)
    return None
GLYPH_MAX = 0x035A
candidates = []
for idx in mi_list:
    fp = frf(idx)
    if not fp: continue
    with open(fp, 'rb') as f: data = f.read()
    gs = gs_map.get(idx, 0)
    region = data[gs:]
    if len(region) % 2: region = region[:-1]
    n = len(region) // 2
    if n < 2: continue
    vals = list(struct.unpack('>%dH' % n, region))
    msgs, cur = [], []
    for v in vals:
        if v == 0xFFFF:
            if cur: msgs.append(cur)
            cur = []
        else: cur.append(v)
    if cur: msgs.append(cur)
    for mi, msg in enumerate(msgs):
        fffe_c = msg.count(0xFFFE)
        if fffe_c != 2: continue
        go = [v for v in msg if v <= GLYPH_MAX and v != 0xFFFE]
        if len(go) < 22 or len(go) > 30: continue
        consec = []
        for i in range(len(msg) - 1):
            a, b = msg[i], msg[i+1]
            if a == b and a <= GLYPH_MAX and a > 0 and a != 0xFFFE: consec.append((i, a))
        if not consec: continue
        lines, cl = [], []
        for v in msg:
            if v == 0xFFFE: lines.append(cl); cl = []
            else: cl.append(v)
        lines.append(cl)
        ll = [len([v for v in l if v <= GLYPH_MAX]) for l in lines]
        candidates.append({'r': idx, 'mi': mi, 'gc': len(go), 'll': ll, 'consec': consec, 'msg': msg[:60]})
print('Found %d candidates' % len(candidates))
for c in candidates:
    ll = c['ll']
    m = len(ll) == 3 and 9 <= ll[0] <= 13 and 6 <= ll[1] <= 10 and 4 <= ll[2] <= 8
    if m:
        print('STRONG: res %d msg#%d gc=%d lines=%s consec=%s' % (c['r'], c['mi'], c['gc'], c['ll'], c['consec']))
        print('  msg: %s' % c['msg'])
if not any(len(c['ll'])==3 and 9<=c['ll'][0]<=13 and 6<=c['ll'][1]<=10 and 4<=c['ll'][2]<=8 for c in candidates):
    print('No strong. First 30:')
    for c in candidates[:30]:
        print('  res %d msg#%d gc=%d lines=%s' % (c['r'], c['mi'], c['gc'], c['ll']))