import zipfile, os, struct
OUTDIR = r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon44-kanji-ram'
ram_path = os.path.join(OUTDIR, 'eeMemory.bin')
with open(ram_path, 'rb') as f:
    ram = f.read()

print('=== Font ptr targets ===')
base = 0x004C08A0
for i in range(20):
    ptr = struct.unpack_from('<I', ram, base + i * 4)[0]
    if ptr < len(ram):
        data = ram[ptr:ptr+64]
        hx = ' '.join(['%02X' % b for b in data])
        print('  ptr[%2d] -> 0x%08X: %s' % (i, ptr, hx))

print('')
print('=== Dump 0x4EA100-0x4EAA00 ===')
for offset in range(0x4EA100, 0x4EAA00, 32):
    data = ram[offset:offset+32]
    hx = ' '.join(['%02X' % b for b in data])
    print('  0x%08X: %s' % (offset, hx))

print('')
print('=== Dump name entry area 0x4C9A00-0x4CA000 ===')
for offset in range(0x4C9A00, 0x4CA000, 32):
    data = ram[offset:offset+32]
    vals = [struct.unpack_from('<H', data, j)[0] for j in range(0, 32, 2)]
    sjis_ct = sum(1 for v in vals if 0x8140 <= v <= 0xEFFC)
    marker = ' *' if sjis_ct >= 4 else ''
    hx = ' '.join(['%04X' % v for v in vals])
    print('  0x%08X: %s%s' % (offset, hx, marker))

print('')
print('Part 4 done.')
