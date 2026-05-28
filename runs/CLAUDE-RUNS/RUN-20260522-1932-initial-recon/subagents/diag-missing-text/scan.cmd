@echo off
python3 -c "
import struct, os, json, sys
sys.stdout.reconfigure(encoding='utf-8')
RESDIR = 'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
with open('C:/Programmieren/wizardrytranslation/dumps/resource_classification.json', encoding='utf-8') as f:
    cls = json.load(f)
msg_indices = set(cls['msg_resource_indices'])
files = os.listdir(RESDIR)
fmap = {}
for fn in files:
    try: fmap[int(fn[:4])] = os.path.join(RESDIR, fn)
    except: pass
decoded = {34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,720,1053,1908,2124,2654}
results = []
for idx in sorted(fmap.keys()):
    if idx not in msg_indices or idx in decoded: continue
    with open(fmap[idx],'rb') as fh: data=fh.read()
    segs=0; glyphs=0; ff01=0; i=0
    while i < len(data)-1:
        val = struct.unpack('>H', data[i:i+2])[0]
        if val == 0xFFFF:
            segs += 1
            j = i + 2
            while j < len(data)-1:
                g = struct.unpack('>H', data[j:j+2])[0]
                if g == 0xFFFF: break
                if g < 0xFF00: glyphs += 1
                if g == 0xFF01: ff01 += 1
                j += 2
            i = j
        else:
            i += 2
    if glyphs > 0:
        results.append((idx, segs, glyphs, len(data), ff01))
results.sort(key=lambda x: -x[2])
print('UNDECODED MSG RESOURCES WITH TEXT (%d total):' % len(results))
for idx, segs, glyphs, sz, ff01 in results[:50]:
    ff = ' FF01=%d' % ff01 if ff01 else ''
    print('  R%d: %d segs, %d glyphs, %d bytes%s' % (idx, segs, glyphs, sz, ff))
print()
print('WITH FF01 TAGS:')
for idx, segs, glyphs, sz, ff01 in results:
    if ff01 > 0:
        print('  R%d: %d FF01, %d segs, %d glyphs' % (idx, ff01, segs, glyphs))
print()
# Range summary
for rname, lo, hi in [('600-900',600,900),('901-999',901,999),('1000-1400',1000,1400),('1401-2100',1401,2100),('2100-2900',2100,2900)]:
    r = [(i,s,g,z,f) for i,s,g,z,f in results if lo<=i<=hi]
    tg = sum(x[2] for x in r)
    print('%s: %d undecoded resources, %d total glyphs' % (rname, len(r), tg))
"
