import os, struct, sys
sys.stdout.reconfigure(encoding='utf-8')
OUTDIR = r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon44-kanji-ram'
ram_path = os.path.join(OUTDIR, 'eeMemory.bin')
with open(ram_path, 'rb') as f:
    ram = f.read()
print('=== COMPLETE KANJI TABLE ===')
base2 = 0x4C9D20
km = {}
for i in range(520):
    addr = base2 + i*4
    if addr + 4 > len(ram): break
    v = struct.unpack_from('<I', ram, addr)[0]
    if v == 0xFFFFFFFF or v == 0: continue
    mid = v & 0xFFFF
    sh = 0x88 + (i // 44)
    sl = 0x9F + (i % 44)
    try: ch = bytes([sh, sl]).decode('shift_jis')
    except: ch = '?'
    sc = (sh << 8) | sl
    km[mid] = (sc, ch)
    print('  0x%04X -> 0x%04X [%s]' % (mid, sc, ch))
print('Total kanji: %d' % len(km))
print('')
print('=== Name entry dump 0x4C99B0-0x4C9CE0 as 6-tuples ===')
idx = 0
for offset in range(0x4C99B0, 0x4C9CE0, 12):
    g = [struct.unpack_from('<H', ram, offset + j*2)[0] for j in range(6)]
    nz = [v for v in g if v != 0]
    gs = ' '.join(['%04X' % v for v in g])
    if len(nz) == 0:
        tag = 'EMPTY'
    elif len(nz) >= 2:
        diffs = [g[j+1] - g[j] for j in range(5) if g[j] != 0 and g[j+1] != 0]
        ok = len(diffs) > 0 and all(d == 57 for d in diffs)
        tag = 'base=%d%s' % (nz[0], ' V6' if ok else '')
    else:
        tag = 'base=%d' % nz[0]
    print('  [%3d] 0x%08X: %s %s' % (idx, offset, gs, tag))
    idx += 1
print('')
print('Done.')
