import zipfile, os, struct
OUTDIR = r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon44-kanji-ram'
SAVSTATE = r'C:\Programmieren\wizardrytranslation\randomdialogue.p2s'
ram_path = os.path.join(OUTDIR, 'eeMemory.bin')
if not os.path.exists(ram_path):
    with zipfile.ZipFile(SAVSTATE, 'r') as z:
        z.extract('eeMemory.bin', OUTDIR)
with open(ram_path, 'rb') as f:
    ram = f.read()
def decode_sjis(v):
    try:
        return struct.pack('>H', v).decode('shift_jis')
    except:
        return '?'
print('=== BSS Character Struct Table at 0x5191F0 ===')
base = 0x005191F0
for i in range(50):
    addr = base + i * 80
    if addr + 80 > len(ram):
        print('  Out of RAM bounds at struct %d' % i)
        break
    data = ram[addr:addr+80]
    if all(b == 0 for b in data):
        if i < 5 or i % 10 == 0:
            print('  [%3d] 0x%08X: ALL ZEROS' % (i, addr))
        continue
    hex16 = ' '.join(['%04X' % struct.unpack_from('<H', data, j)[0] for j in range(0, 40, 2)])
    hex16b = ' '.join(['%04X' % struct.unpack_from('<H', data, j)[0] for j in range(40, 80, 2)])
    print('  [%3d] 0x%08X: %s | %s' % (i, addr, hex16, hex16b))
print('')
print('=== Scan BSS 0x4FDC80-0x579800 for SJIS 0x82A0 ===')
bss_start = 0x4FDC80
bss_end = 0x579800
for offset in range(bss_start, bss_end - 20, 2):
    v = struct.unpack_from('<H', ram, offset)[0]
    if v == 0x82A0:
        vals = [struct.unpack_from('<H', ram, offset + i*2)[0] for i in range(10)]
        sjis_count = sum(1 for vv in vals if 0x8140 <= vv <= 0xEFFC)
        if sjis_count >= 5:
            cs = ''.join(decode_sjis(v) for v in vals)
            print('  0x%08X: %s' % (offset, cs))
print('')
print('=== Font ptr table at 0x4C08A0 ===')
base = 0x004C08A0
for i in range(20):
    addr = base + i * 4
    val = struct.unpack_from('<I', ram, addr)[0]
    print('  [%2d] 0x%08X: 0x%08X' % (i, addr, val))
print('')
print('=== Name entry table at 0x4C9AB0 ===')
base = 0x4C9AB0
for row in range(15):
    vals = [struct.unpack_from('<H', ram, base + (row*10+col)*2)[0] for col in range(10)]
    cs = []
    for v in vals:
        if v == 0:
            cs.append('.')
        else:
            cs.append(decode_sjis(v))
    print('  row %2d: %s' % (row, ' '.join(cs)))
print('')
print('Part 3 done.')
