import os, struct, sys
sys.stdout.reconfigure(encoding='utf-8')
OUTDIR = r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon44-kanji-ram'
ram_path = os.path.join(OUTDIR, 'eeMemory.bin')
with open(ram_path, 'rb') as f:
    ram = f.read()
base2 = 0x4C9D20
results = []
for i in range(500):
    addr = base2 + i*4
    if addr + 4 > len(ram): break
    v = struct.unpack_from('<I', ram, addr)[0]
    if v == 0xFFFFFFFF or v == 0: continue
    msg_id = v & 0xFFFF
    sjis_row_offset = i // 44
    sjis_col_offset = i % 44
    sjis_hi = 0x88 + sjis_row_offset
    sjis_lo = 0x9F + sjis_col_offset
    try:
        char = bytes([sjis_hi, sjis_lo]).decode('shift_jis')
    except:
        char = '?'
    results.append((i, sjis_hi, sjis_lo, char, msg_id))
print('=== SJIS -> MSG_ID mapping ===')
for slot, hi, lo, char, mid in results:
    print('  slot[%3d] SJIS 0x%02X%02X [%s] -> msg_id=0x%04X' % (slot, hi, lo, char, mid))
print('\nTotal: %d' % len(results))
pages = set(r[4] >> 8 for r in results)
print('Pages: %s' % sorted(pages))
print('\n=== After kanji table 0x4CA4E0-0x4CA600 ===')
for offset in range(0x4CA4E0, 0x4CA600, 16):
    data = ram[offset:offset+16]
    vals = [struct.unpack_from('<I', data, j)[0] for j in range(0, 16, 4)]
    hx = ' '.join(['%08X' % v for v in vals])
    print('  0x%08X: %s' % (offset, hx))
print('\n=== Before name entry 0x4C9900-0x4C9980 ===')
for offset in range(0x4C9900, 0x4C9980, 16):
    data = ram[offset:offset+16]
    vals = [struct.unpack_from('<H', data, j)[0] for j in range(0, 16, 2)]
    hx = ' '.join(['%04X' % v for v in vals])
    print('  0x%08X: %s' % (offset, hx))
print('\nDone.')
