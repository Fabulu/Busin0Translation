import os, struct, sys
sys.stdout.reconfigure(encoding='utf-8')
O = r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon44-kanji-ram'
with open(os.path.join(O, 'eeMemory.bin'), 'rb') as f:
    ram = f.read()
print('=== Raw bytes of kanji table ===')
b2 = 0x4C9D20
for i in range(10):
    a = b2 + i*4
    d = ram[a:a+4]
    print('  [%3d] %02X %02X %02X %02X' % (i, d[0], d[1], d[2], d[3]))
print('')
print('=== Name entry base glyphs ===')
ub = set()
for i in range(0, 200, 6):
    g = [struct.unpack_from('<H', ram, 0x4C9AB0 + (i+j)*2)[0] for j in range(6)]
    nz = [v for v in g if v != 0]
    if len(nz) >= 2:
        diffs = [g[j+1]-g[j] for j in range(5) if g[j]!=0 and g[j+1]!=0]
        if len(diffs)>0 and all(d==57 for d in diffs):
            ub.add(nz[0])
sb = sorted(ub)
print('Count: %d, Range: %d-%d' % (len(sb), min(sb), max(sb)))
print('Bases: %s' % sb)
print('Max glyph: %d' % (max(sb)+285))
print('')
print('=== Glyph property atlas coords ===')
rc = {}
for i in range(133):
    a = 0x4C0DF8 + i * 28
    r, c = ram[a+17], ram[a+18]
    k = (r, c)
    rc[k] = rc.get(k, 0) + 1
for k in sorted(rc.keys()):
    print('  (%d,%d)->%d' % (k[0], k[1], rc[k]))
print('')
print('Done.')
