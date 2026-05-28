import struct, json, sys, glob, os
sys.stdout.reconfigure(encoding='utf-8')

gm = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# 1. Check if R37 has translations
print("=== R37 translations ===")
found_r37 = False
for f in sorted(glob.glob('data/translate_chunks/*.json')):
    data = json.load(open(f, encoding='utf-8'))
    for entry in data:
        if entry.get('resource') == 37:
            if not found_r37:
                print(f"  Found in {os.path.basename(f)}")
                found_r37 = True
            if 'ボタン' in entry.get('japanese', '') or 'button' in entry.get('english', '').lower():
                print(f"    msg[{entry['message']}]: {entry['japanese'][:50]} -> {entry['english'][:50]}")

if not found_r37:
    print("  NO translations found for R37!")

# 2. Decode R37 to see the confirmation dialog message
print("\n=== R37 messages containing ボタン ===")
fname = 'extracted/packdata_resources/0037_type01.bin'
if os.path.exists(fname):
    data = open(fname, 'rb').read()
    count = struct.unpack_from('>H', data, 0)[0]
    print(f"  R37 has {count} messages")

    for i in range(min(count, 300)):
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
        if 'ボタン' in text or '確認' in text or '移' in text:
            print(f"  msg[{i}] @0x{off:X}: {text[:100]}")

# 3. Check R40 similarly
print("\n=== R40 messages containing ボタン ===")
fname = 'extracted/packdata_resources/0040_type01.bin'
if os.path.exists(fname):
    data = open(fname, 'rb').read()
    count = struct.unpack_from('>H', data, 0)[0]
    print(f"  R40 has {count} messages")

    for i in range(min(count, 300)):
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
        if 'ボタン' in text or '確認' in text or '移' in text:
            print(f"  msg[{i}] @0x{off:X}: {text[:100]}")

# 4. Check if R37 and R40 translations exist at all
print("\n=== Translation coverage for R37, R38, R40 ===")
all_translations = {}
for f in sorted(glob.glob('data/translate_chunks/*.json')):
    data = json.load(open(f, encoding='utf-8'))
    for entry in data:
        r = entry.get('resource')
        if r in [37, 38, 40]:
            key = (r, entry.get('message'))
            all_translations[key] = entry.get('english', '')[:40]

for r in [37, 38, 40]:
    count = sum(1 for k in all_translations if k[0] == r)
    print(f"  R{r}: {count} translated messages")
    # Show a few
    for k in sorted(all_translations):
        if k[0] == r and count <= 10:
            print(f"    msg[{k[1]}]: {all_translations[k]}")

# 5. Check what the build script actually outputs for R38
print("\n=== Check if patched R38 exists ===")
for pattern in ['build/**/0038*', 'build/**/*38*', 'output/**/*38*']:
    for f in glob.glob(pattern, recursive=True):
        size = os.path.getsize(f)
        print(f"  {f}: {size} bytes")
