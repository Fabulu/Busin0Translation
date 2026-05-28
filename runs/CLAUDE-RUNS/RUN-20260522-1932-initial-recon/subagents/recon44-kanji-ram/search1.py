import zipfile, os, struct

OUTDIR = r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon44-kanji-ram'
SAVSTATE = r'C:\Programmieren\wizardrytranslation\randomdialogue.p2s'

with zipfile.ZipFile(SAVSTATE, 'r') as z:
    z.extract('eeMemory.bin', OUTDIR)

ram_path = os.path.join(OUTDIR, 'eeMemory.bin')
print(f'RAM dump: {os.path.getsize(ram_path)} bytes')

with open(ram_path, 'rb') as f:
    ram = f.read()

def decode_sjis(v):
    try:
        return struct.pack('>H', v).decode('shift_jis')
    except:
        return '?'

print('\n=== TASK 1a: SJIS hiragana blocks ===')
hits = []
for offset in range(0, len(ram) - 20, 2):
    vals = [struct.unpack_from('<H', ram, offset + i*2)[0] for i in range(10)]
    hc = sum(1 for v in vals if 0x82A0 <= v <= 0x82F1)
    if hc >= 7:
        hits.append((offset, vals))
print(f'Found {len(hits)} locations')
for offset, vals in hits[:30]:
    cs = ''.join(decode_sjis(v) for v in vals)
    print(f'  0x{offset:08X}: {cs}')

print('\n=== TASK 1b: Mixed hira+kata blocks ===')
mixed = []
for offset in range(0, len(ram) - 120, 2):
    vals = [struct.unpack_from('<H', ram, offset + i*2)[0] for i in range(60)]
    hira = sum(1 for v in vals if 0x82A0 <= v <= 0x82F1)
    kata = sum(1 for v in vals if 0x8340 <= v <= 0x8396)
    if hira >= 20 and kata >= 20:
        mixed.append((offset, hira, kata))
print(f'Found {len(mixed)} locations')
for offset, hc, kc in mixed[:10]:
    vals = [struct.unpack_from('<H', ram, offset + i*2)[0] for i in range(60)]
    cs = ''.join(decode_sjis(v) for v in vals)
    print(f'  0x{offset:08X}: {hc}h {kc}k  [{cs}]')

print('\n=== TASK 1c: SJIS kanji blocks ===')
kanji_hits = []
for offset in range(0, len(ram) - 40, 2):
    vals = [struct.unpack_from('<H', ram, offset + i*2)[0] for i in range(20)]
    kc = sum(1 for v in vals if 0x889F <= v <= 0x9FFC)
    if kc >= 15:
        kanji_hits.append((offset, vals))
print(f'Found {len(kanji_hits)} locations')
for offset, vals in kanji_hits[:30]:
    cs = ''.join(decode_sjis(v) for v in vals)
    print(f'  0x{offset:08X}: [{cs}]')

print('\n=== TASK 2: Sorted SJIS tables ===')
sorted_hits = []
for offset in range(0, len(ram) - 60, 2):
    vals = [struct.unpack_from('<H', ram, offset + i*2)[0] for i in range(30)]
    if all(0x8140 <= v <= 0xEFFC for v in vals):
        inc = sum(1 for i in range(1, 30) if vals[i] > vals[i-1])
        if inc >= 25:
            sorted_hits.append((offset, vals))
print(f'Found {len(sorted_hits)} locations')
for offset, vals in sorted_hits[:20]:
    cs = ''.join(decode_sjis(v) for v in vals)
    print(f'  0x{offset:08X}: [{cs}]')

print('\nPart 1 done.')
