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
        if fn.startswith(p) and fn.endswith('.bin'):
            return os.path.join(RESDIR, fn)
    return None

total_checked = 0
for idx in mi_list:
    fp = frf(idx)
    if not fp:
        continue
    with open(fp, 'rb') as f:
        data = f.read()
    gs = gs_map.get(idx, 0)
    region = data[gs:]
    if len(region) % 2:
        region = region[:-1]
    n = len(region) // 2
    if n < 2:
        continue
    vals = list(struct.unpack('>%dH' % n, region))
    total_checked += 1
    for i in range(len(vals) - 1):
        if vals[i] == 91 and vals[i+1] == 91:
            print('FOUND: res %d pos %d vals[%d:%d]=%s' % (idx, i, max(0,i-5), min(len(vals),i+10), vals[max(0,i-5):min(len(vals),i+10)]))
            break

print('Checked %d resources, done.' % total_checked)