import os, struct
OUTDIR = r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon44-kanji-ram'
ram_path = os.path.join(OUTDIR, 'eeMemory.bin')
with open(ram_path, 'rb') as f:
    ram = f.read()
print('=== Name entry glyph index analysis at 0x4C9AB0 ===')
base = 0x4C9AB0
for i in range(0, 300, 6):
    group = [struct.unpack_from('<H', ram, base + (i+j)*2)[0] for j in range(6)]
    gstr = ' '.join(['%04X' % v for v in group])
    nonzero = [v for v in group if v != 0]
    if len(nonzero) >= 2:
        diffs = [group[j+1] - group[j] for j in range(5) if group[j] != 0 and group[j+1] != 0]
        valid = len(diffs) > 0 and all(d == 57 for d in diffs)
        tag = ' VALID6' if valid else ''
        bg = nonzero[0]
        print('  [%3d] %s  base=%d%s' % (i//6, gstr, bg, tag))
    elif len(nonzero) == 0:
        print('  [%3d] %s  EMPTY' % (i//6, gstr))
    else:
        print('  [%3d] %s  base=%d' % (i//6, gstr, nonzero[0]))
print('')
print('=== JIS-like table at 0x4C9D20 ===')
base2 = 0x4C9D20
entries = []
for i in range(500):
    addr = base2 + i*4
    if addr + 4 > len(ram):
        break
    v = struct.unpack_from('<I', ram, addr)[0]
    if v != 0xFFFFFFFF and v != 0:
        hi = (v >> 8) & 0xFF
        lo = v & 0xFF
        entries.append((i, v, hi, lo))
print('Total non-FFFF/non-zero entries: %d' % len(entries))
for slot, v, hi, lo in entries:
    print('  slot[%3d] val=0x%08X (0x%02X, 0x%02X)' % (slot, v, hi, lo))
print('')
print('Done.')
