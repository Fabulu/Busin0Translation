import struct, json, sys, glob, os
sys.stdout.reconfigure(encoding='utf-8')

gm = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# Decode ALL R37 messages to see what's missing
print("=== ALL R37 messages ===")
fname = 'extracted/packdata_resources/0037_type01.bin'
data = open(fname, 'rb').read()
count = struct.unpack_from('>H', data, 0)[0]

# Collect all translations
trans = {}
for f in sorted(glob.glob('data/translate_chunks/*.json')):
    for e in json.load(open(f, encoding='utf-8')):
        if e.get('resource') == 37 and e.get('english', '').strip():
            trans[e['message']] = e['english'][:50]

for i in range(count):
    off = struct.unpack_from('>I', data, 2 + i*4)[0]
    chars = []
    pos = off
    while pos < len(data) - 1:
        v = struct.unpack_from('>H', data, pos)[0]
        if v == 0xFFFF: break
        if v == 0xFFFE: chars.append(' / ')
        elif str(v) in gm: chars.append(gm[str(v)])
        else: chars.append(f'[{v:04X}]')
        pos += 2
    text = ''.join(chars)
    status = "TRANSLATED" if i in trans else "UNTRANSLATED"
    if len(text) > 0:
        print(f"  msg[{i:3d}] [{status:12s}]: {text[:80]}")
        if i in trans:
            print(f"           -> {trans[i]}")

# Check what build actually does with R37
print("\n=== R37 in build output ===")
for f in glob.glob('build/packdata_resources/0037*'):
    print(f"  {f}: {os.path.getsize(f)} bytes")

# Original size
print(f"  Original: extracted/packdata_raw/0037_type01.raw: {os.path.getsize('extracted/packdata_raw/0037_type01.raw')} bytes")
