import zipfile, os, struct
OUTDIR = r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon44-kanji-ram'
SAVSTATE = r'C:\Programmieren\wizardrytranslation\randomdialogue.p2s'
with zipfile.ZipFile(SAVSTATE, 'r') as z:
    z.extract('eeMemory.bin', OUTDIR)
ram_path = os.path.join(OUTDIR, 'eeMemory.bin')
with open(ram_path, 'rb') as f:
    ram = f.read()
def decode_sjis(v):
    try:
        return struct.pack('>H', v).decode('shift_jis')
    except:
        return '?'
DQ = chr(34)
print('=== TASK 4: Glyph property structs at 0x4C0DF8 ===')
base = 0x004C0DF8
for i in range(133):
    addr = base + i * 28
    data = ram[addr:addr+28]
    fields = [struct.unpack_from('<H', data, j)[0] for j in range(0, 28, 2)]
    f26 = struct.unpack_from('<H', data, 26)[0]
    f24 = struct.unpack_from('<H', data, 24)[0]
    c26 = decode_sjis(f26)
    c24 = decode_sjis(f24)
    fmt = '%04X'
    fstr = ' '.join([fmt % f for f in fields])
    print('  [%3d] %s  f24=%s f26=%s' % (i, fstr, c24, c26))
print('')
print('=== Raw hex first 20 ===')
for i in range(20):
    addr = base + i * 28
    data = ram[addr:addr+28]
    hex_str = ' '.join(['%02X' % b for b in data])
    print('  [%3d] 0x%08X: %s' % (i, addr, hex_str))
print('Part 2a done.')
