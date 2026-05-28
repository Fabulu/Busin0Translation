import struct, json, sys
sys.stdout.reconfigure(encoding='utf-8')

exe = open('extracted/SLPM_653.78', 'rb').read()
gm = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# Search for stat labels as Shift-JIS
print("=== Shift-JIS search ===")
for label in ['力','知恵','信仰心','生命力','敏捷度','幸運度','性別','HP','ＨＰ']:
    try:
        sjis = label.encode('shift_jis')
    except:
        continue
    hits = []
    pos = 0
    while True:
        pos = exe.find(sjis, pos)
        if pos < 0:
            break
        hits.append(pos)
        pos += 1
    print(f"  {label} ({sjis.hex()}): {len(hits)} hits -> {[hex(h) for h in hits[:10]]}")

# Search for glyph sequences (BE uint16)
print("\n=== Glyph sequence search ===")
labels = {
    'chikara': [565],
    'chie': [535, 717],
    'shinkou': [363, 354, 458],
    'seimei': [718, 696, 565],
    'binsho': [582, 719, 590],
    'kouun': [720, 721, 590],
    'seibetsu': [785, 512],
}
for name, glyphs in labels.items():
    pattern = b''.join(struct.pack('>H', g) for g in glyphs)
    hits = []
    pos = 0
    while True:
        pos = exe.find(pattern, pos)
        if pos < 0:
            break
        hits.append(pos)
        pos += 2
    print(f"  {name} {glyphs}: {len(hits)} hits -> {[hex(h) for h in hits[:10]]}")

# Now check what R38 actually contains for the stat screen
print("\n=== R38 stat labels ===")
r38 = open('extracted/R38.bin', 'rb').read()
# Parse R38 header
entry_count = struct.unpack_from('<I', r38, 0)[0]
print(f"  R38 has {entry_count} entries")

# Look at first ~20 messages
for i in range(min(30, entry_count)):
    off = struct.unpack_from('<I', r38, 4 + i*4)[0]
    # Read glyphs until FFFF
    chars = []
    pos = off
    while pos < len(r38) - 1:
        v = struct.unpack_from('>H', r38, pos)[0]
        if v == 0xFFFF:
            break
        if str(v) in gm:
            chars.append(gm[str(v)])
        else:
            chars.append(f'[{v:04X}]')
        pos += 2
    text = ''.join(chars)
    if len(text) <= 30:
        print(f"  msg[{i}] @0x{off:X}: {text}")

# Also check: is the confirmation dialog text in R38?
print("\n=== Search for confirmation dialog ===")
# Search for ボタン in R38 as glyphs
rev = {v: k for k, v in gm.items()}
botan_glyphs = [rev.get(c) for c in 'ボタン']
print(f"  ボタン glyph IDs: {botan_glyphs}")
if all(botan_glyphs):
    pattern = b''.join(struct.pack('>H', int(g)) for g in botan_glyphs)
    pos = 0
    while True:
        pos = r38.find(pattern, pos)
        if pos < 0:
            break
        print(f"  Found ボタン in R38 at 0x{pos:X}")
        pos += 2

# Also search in EXE
    pos = 0
    while True:
        pos = exe.find(pattern, pos)
        if pos < 0:
            break
        print(f"  Found ボタン in EXE at 0x{pos:X}")
        pos += 2

# Search all MSG files for ボタン
print("\n=== Search all R*.bin for button dialog ===")
import glob
for f in sorted(glob.glob('extracted/R*.bin')):
    data = open(f, 'rb').read()
    if all(botan_glyphs):
        pattern = b''.join(struct.pack('>H', int(g)) for g in botan_glyphs)
        pos = 0
        while True:
            pos = data.find(pattern, pos)
            if pos < 0:
                break
            # Decode surrounding text
            start = max(0, pos - 20)
            end = min(len(data), pos + 40)
            chars = []
            p = start
            while p < end:
                v = struct.unpack_from('>H', data, p)[0]
                if v == 0xFFFF:
                    chars.append('#')
                elif str(v) in gm:
                    chars.append(gm[str(v)])
                else:
                    chars.append('.')
                p += 2
            import os
            print(f"  {os.path.basename(f)} @0x{pos:X}: {''.join(chars)}")
            pos += 2
