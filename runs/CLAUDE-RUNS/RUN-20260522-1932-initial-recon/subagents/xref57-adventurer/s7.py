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
        go = [v for v in msg if 0 < v <= GLYPH_MAX]
        if len(go) < 20 or len(go) > 35: continue
        for p in range(6, min(11, len(go)-1)):
            if go[p] == go[p+1] and 86 <= go[p] <= 300:
                fffe_c = sum(1 for v in msg if v == 0xFFFE)
                fff9_c = sum(1 for v in msg if v == 0xFFF9)
                candidates.append({'r':idx,'mi':mi,'gc':len(go),'fffe':fffe_c,'fff9':fff9_c,'dp':p,'dv':go[p],'msg':msg[:60],'go':go[:40]})
                break
print('Found %d candidates' % len(candidates))
for c in candidates[:50]:
    print('  res %d msg#%d gc=%d fffe=%d fff9=%d dup@%d=%d' % (c['r'],c['mi'],c['gc'],c['fffe'],c['fff9'],c['dp'],c['dv']))
    print('    go: %s' % c['go'][:30])