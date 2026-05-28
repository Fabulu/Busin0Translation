import struct, os, json
RESDIR = r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
HDR_F = r'C:/Programmieren/wizardrytranslation/dumps/msg_header_analysis.json'
with open(HDR_F) as f: hdr = json.load(f)
gs_map = {r['index']: r.get('glyph_start_offset', 0) for r in hdr['resources']}
idx = 45
fp = next(os.path.join(RESDIR,fn) for fn in os.listdir(RESDIR) if fn.startswith('0045_') and fn.endswith('.bin'))
with open(fp,'rb') as f: data = f.read()
gs = gs_map.get(idx, 0)
region = data[gs:]
n = len(region) // 2
vals = list(struct.unpack('>%dH' % n, region))
msgs, cur = [], []
for v in vals:
    if v == 0xFFFF:
        if cur: msgs.append(cur)
        cur = []
    else: cur.append(v)
if cur: msgs.append(cur)
for mi in range(4, min(len(msgs), 12)):
    msg = msgs[mi]
    hexvals = ' '.join('%04X' % v for v in msg[:60])
    print('msg[%d] len=%d: %s' % (mi, len(msg), hexvals))