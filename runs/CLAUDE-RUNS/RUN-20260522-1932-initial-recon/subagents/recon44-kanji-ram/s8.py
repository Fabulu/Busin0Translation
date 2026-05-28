import os, struct, sys
sys.stdout.reconfigure(encoding='utf-8')
OUTDIR = r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon44-kanji-ram'
ram_path = os.path.join(OUTDIR, 'eeMemory.bin')
with open(ram_path, 'rb') as f:
    ram = f.read()
print('=== Pointer table at 0x4C9930 ===')
ptrs = []
for i in range(20):
    addr = 0x4C9930 + i*4
    ptr = struct.unpack_from('<I', ram, addr)[0]
    ptrs.append(ptr)
    print('  [%2d] ptr=0x%08X' % (i, ptr))
print('')
for idx, ptr in enumerate(ptrs):
    if ptr < 0x100000 or ptr >= len(ram): continue
    data = ram[ptr:ptr+64]
    v16 = [struct.unpack_from('<H', data, j)[0] for j in range(0, 64, 2)]
    hx = ' '.join(['%04X' % v for v in v16])
    print('  ptr[%2d]->0x%08X: %s' % (idx, ptr, hx))
print('')
print('=== Dump 0x4C9670-0x4C9900 ===')
for offset in range(0x4C9670, 0x4C9900, 32):
    v16 = [struct.unpack_from('<H', ram, offset + j)[0] for j in range(0, 32, 2)]
    hx = ' '.join(['%04X' % v for v in v16])
    print('  0x%08X: %s' % (offset, hx))
print('')
print('=== Extended kanji (484-600) ===')
base2 = 0x4C9D20
for i in range(484, 600):
    addr = base2 + i*4
    if addr + 4 > len(ram): break
    v = struct.unpack_from('<I', ram, addr)[0]
    if v == 0xFFFFFFFF or v == 0: continue
    mid = v & 0xFFFF
    sr = i // 44
    sc = i % 44
    sh = 0x88 + sr
    sl = 0x9F + sc
    try:
        ch = bytes([sh, sl]).decode('shift_jis')
    except:
        ch = '?'
    print('  slot[%3d] 0x%02X%02X [%s] -> 0x%04X' % (i, sh, sl, ch, mid))
print('')
print('Done.')
