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
        breaks = [v for v in msg if v in (0xFFFE, 0xFFF9)]
        if len(breaks) < 2: continue
        lines, cl = [], []
        for v in msg:
            if v in (0xFFFE, 0xFFF9): lines.append(cl); cl = []
            else: cl.append(v)
        lines.append(cl)
        gl = [[v for v in l if 0 < v <= GLYPH_MAX] for l in lines]
        ll = [len(g) for g in gl]
        if len(ll) >= 3 and ll[0] == 11 and ll[1] == 8 and ll[2] == 6:
            hx = ' '.join('%04X' % v for v in msg[:50])
            print('res %d msg#%d ll=%s' % (idx, mi, ll[:5]))
            print('  %s' % hx)
