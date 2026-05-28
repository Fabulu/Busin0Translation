import os, struct
OUTDIR = r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon44-kanji-ram'
ram_path = os.path.join(OUTDIR, 'eeMemory.bin')
with open(ram_path, 'rb') as f:
    ram = f.read()
print('=== Pre-name-entry 0x4C9980-0x4C9AB0 ===')
for offset in range(0x4C9980, 0x4C9AB0, 16):
    data = ram[offset:offset+16]
    vals = [struct.unpack_from('<H', data, j)[0] for j in range(0, 16, 2)]
    hx = ' '.join(['%04X' % v for v in vals])
    print('  0x%08X: %s' % (offset, hx))
print('')
print('=== 0x4C9A00-0x4C9AB0 as 6-groups ===')
for i in range(0, 88, 6):
    group = [struct.unpack_from('<H', ram, 0x4C9A00 + (i+j)*2)[0] for j in range(6)]
    nonzero = [v for v in group if v != 0]
    gstr = ' '.join(['%04X' % v for v in group])
    if len(nonzero) >= 2:
        diffs = [group[j+1] - group[j] for j in range(5) if group[j] != 0 and group[j+1] != 0]
        valid = len(diffs) > 0 and all(d == 57 for d in diffs)
        tag = ' V6' if valid else ''
        print('  [%2d] %s base=%d%s' % (i//6, gstr, nonzero[0], tag))
    else:
        print('  [%2d] %s' % (i//6, gstr))
print('')
print('=== JIS table row analysis ===')
import collections
base2 = 0x4C9D20
row_slots = collections.defaultdict(list)
for i in range(500):
    addr = base2 + i*4
    if addr + 4 > len(ram): break
    v = struct.unpack_from('<I', ram, addr)[0]
    if v != 0xFFFFFFFF and v != 0:
        hi = (v >> 8) & 0xFF
        row_slots[hi].append(i)
for row in sorted(row_slots.keys()):
    slots = row_slots[row]
    print('  row 0x%02X: %d entries, slots %d-%d (span=%d)' % (row, len(slots), min(slots), max(slots), max(slots)-min(slots)))
    print('    slots: %s' % slots)
print('')
print('Done.')
