import struct, json, sys, glob, os
sys.stdout.reconfigure(encoding='utf-8')

exe = open('extracted/SLPM_653.78', 'rb').read()
gm = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
rev = {v: k for k, v in gm.items()}

# 1. Search for ボタン as SJIS in EXE
print("=== Search EXE for SJIS strings ===")
for term in ['ボタン', '最終確認', '移ります', '○ボタン']:
    sjis = term.encode('shift_jis')
    pos = 0
    hits = []
    while True:
        pos = exe.find(sjis, pos)
        if pos < 0: break
        hits.append(pos)
        pos += 1
    print(f"  {term} (SJIS {sjis.hex()}): {len(hits)} hits at {[hex(h) for h in hits[:5]]}")

# 2. Search for ボタン as glyph sequence in all extracted MSG resources
print("\n=== Search MSG resources for ボタン glyphs ===")
botan_glyphs = [rev.get(c) for c in 'ボタン']
print(f"  Glyph IDs: {botan_glyphs}")
if all(botan_glyphs):
    pattern = b''.join(struct.pack('>H', int(g)) for g in botan_glyphs)
    for f in sorted(glob.glob('extracted/packdata_resources/*.bin')):
        data = open(f, 'rb').read()
        pos = 0
        while True:
            pos = data.find(pattern, pos)
            if pos < 0: break
            # Decode context
            start = max(0, pos - 10) & ~1
            end = min(len(data), pos + 30)
            chars = []
            p = start
            while p < end - 1:
                v = struct.unpack_from('>H', data, p)[0]
                if v == 0xFFFF: chars.append('#')
                elif v == 0xFFFE: chars.append('/')
                elif str(v) in gm: chars.append(gm[str(v)])
                else: chars.append(f'[{v:04X}]')
                p += 2
            print(f"  {os.path.basename(f)} @0x{pos:X}: {''.join(chars)}")
            pos += 2

# 3. Check if R38 translations are actually being applied in the build
print("\n=== Check build pipeline for R38 ===")
for f in glob.glob('tools/*.py') + glob.glob('build/*.py') + glob.glob('*.py'):
    try:
        content = open(f, encoding='utf-8').read()
    except:
        continue
    if '0038' in content or 'r38' in content.lower() or 'resource.*38' in content.lower():
        # Find relevant lines
        for i, line in enumerate(content.split('\n')):
            if '0038' in line or ('38' in line and ('resource' in line.lower() or 'chunk' in line.lower())):
                print(f"  {f}:{i+1}: {line.strip()[:100]}")

# 4. Look for the chargen MSG resource - which resource has the confirmation dialog?
# Try R48, R49, R40 etc
print("\n=== Decode first few messages of chargen-adjacent resources ===")
for res_id in ['0038', '0040', '0048', '0049']:
    fname = f'extracted/packdata_resources/{res_id}_type01.bin'
    if not os.path.exists(fname):
        print(f"  {fname}: NOT FOUND")
        continue
    data = open(fname, 'rb').read()
    if len(data) < 4:
        continue
    # Parse header: count as BE uint16, then BE uint32 offsets
    count = struct.unpack_from('>H', data, 0)[0]
    if count > 1000 or count < 1:
        # Try LE uint32
        count = struct.unpack_from('<I', data, 0)[0]
        if count > 1000:
            print(f"  R{res_id}: header unclear (first 4 bytes: {data[:4].hex()})")
            continue
    print(f"  R{int(res_id)} has {count} messages (first 4 bytes: {data[:4].hex()})")
