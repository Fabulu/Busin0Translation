#!/usr/bin/env python3
"""Search RAM for intro text using MSG glyph IDs."""
import zipfile
import struct
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

z = zipfile.ZipFile('C:/Programmieren/wizardrytranslation/ramdumps/intro.p2s', 'r')
ram = z.read('eeMemory.bin')

with open('C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json', 'r', encoding='utf-8') as f:
    glyph_map = json.load(f)

# Reverse map: char -> list of glyph IDs
char_to_ids = {}
for gid_str, char in glyph_map.items():
    gid = int(gid_str)
    if char not in char_to_ids:
        char_to_ids[char] = []
    char_to_ids[char].append(gid)

sentence = '\u305d\u306e\u60b2\u60e8\u306a\u6226\u4e89\u306f\u30d0\u30f3\u30af\u30a9\u30fc\u306e\u6226\u5f79\u3068\u4eba\u3005\u306b\u8a18\u61b6\u3055\u308c\u308b\u3002'
# sono hisan na sensou ha bankuoo- no seneki to hitobito ni kioku sareru.

print("=== Building glyph ID sequences ===")
for i, ch in enumerate(sentence):
    ids = char_to_ids.get(ch, [])
    print(f"  '{ch}': IDs = {ids}")

# Characters with known mappings
# そ=126, の=136, 悲=?, 惨=?, な=132, 戦=286/923/1017, 争=?
# は=137, バ=254, ン=238, ク=200, ォ=271, ー=93
# 戦=286, 役=?, と=131, 人=319, 々=?
# に=133, 記=801, 憶=?, さ=122, れ=153/435, る=152, 。=63

# Some chars are missing (悲, 惨, 争, 役, 々, 憶)
# Let's search for the known subsequences

# バンクォー = 254, 238, 200, 271, 93
bankuoo = [254, 238, 200, 271, 93]
print(f"\nSearching for bankuoo glyph sequence: {bankuoo}")

# As uint16 LE
pattern_le = struct.pack('<5H', *bankuoo)
print(f"  LE hex: {pattern_le.hex()}")
pos = 0
while True:
    pos = ram.find(pattern_le, pos)
    if pos < 0: break
    ctx = ram[max(0,pos-20):pos+30]
    vals_before = [struct.unpack_from('<H', ram, pos-i)[0] for i in range(20, 0, -2) if pos-i >= 0]
    vals_after = [struct.unpack_from('<H', ram, pos+10+i)[0] for i in range(0, 20, 2) if pos+10+i+1 < len(ram)]
    print(f"  FOUND LE at 0x{pos:08X}")
    print(f"    before: {vals_before}")
    print(f"    after: {vals_after}")
    pos += 1

# As uint16 BE
pattern_be = struct.pack('>5H', *bankuoo)
print(f"  BE hex: {pattern_be.hex()}")
pos = 0
while True:
    pos = ram.find(pattern_be, pos)
    if pos < 0: break
    print(f"  FOUND BE at 0x{pos:08X}")
    pos += 1

# Try shorter: バン = 254, 238
ban_le = struct.pack('<2H', 254, 238)
print(f"\nSearching for BaN (254, 238) LE: {ban_le.hex()}")
pos = 0
count = 0
while count < 20:
    pos = ram.find(ban_le, pos)
    if pos < 0: break
    # Check what follows
    next_val = struct.unpack_from('<H', ram, pos+4)[0] if pos+5 < len(ram) else -1
    print(f"  0x{pos:08X}: next={next_val} (expect 200 for ク)")
    if next_val == 200:
        # Full match check
        vals = [struct.unpack_from('<H', ram, pos+i)[0] for i in range(0, 20, 2) if pos+i+1 < len(ram)]
        print(f"    SEQUENCE: {vals}")
    pos += 2
    count += 1

# Try: の戦 = 136, 286 (or 923 or 1017)
print("\nSearching for 'no sen' subsequences")
for sen_id in [286, 923, 1017]:
    pattern = struct.pack('<2H', 136, sen_id)
    pos = 0
    count = 0
    while count < 10:
        pos = ram.find(pattern, pos)
        if pos < 0: break
        vals = [struct.unpack_from('<H', ram, pos+i)[0] for i in range(-8, 16, 2) if 0 <= pos+i and pos+i+1 < len(ram)]
        print(f"  no(136)+sen({sen_id}) at 0x{pos:08X}: {vals}")
        pos += 2
        count += 1

# Try: 記憶 - 記=801, but 憶 is not in map
# Try: される = 122, 153, 152 (sa, re, ru)
sareru = struct.pack('<3H', 122, 153, 152)
print(f"\nSearching for 'sareru' (122, 153, 152)")
pos = 0
count = 0
while count < 10:
    pos = ram.find(sareru, pos)
    if pos < 0: break
    vals = [struct.unpack_from('<H', ram, pos+i)[0] for i in range(-8, 14, 2) if 0 <= pos+i and pos+i+1 < len(ram)]
    print(f"  0x{pos:08X}: {vals}")
    pos += 2
    count += 1

# Alternative: される = 122, 435, 152 (sa, re_alt, ru)
sareru2 = struct.pack('<3H', 122, 435, 152)
print(f"\nSearching for 'sareru' alt (122, 435, 152)")
pos = 0
count = 0
while count < 10:
    pos = ram.find(sareru2, pos)
    if pos < 0: break
    vals = [struct.unpack_from('<H', ram, pos+i)[0] for i in range(-8, 14, 2) if 0 <= pos+i and pos+i+1 < len(ram)]
    print(f"  0x{pos:08X}: {vals}")
    pos += 2
    count += 1

# === Also search for glyph IDs as uint8 (single byte per char) ===
# If glyphs < 256, could be stored as bytes
print("\n=== Single-byte glyph search ===")
# bankuoo as bytes (all < 256 except 271 for ォ)
# 254=0xFE, 238=0xEE, 200=0xC8, 271 > 255 so can't fit
# But let's try just BaN = 0xFE, 0xEE
ban_bytes = bytes([254, 238, 200])
print(f"BaN bytes: {ban_bytes.hex()}")
pos = 0
count = 0
while count < 10:
    pos = ram.find(ban_bytes, pos)
    if pos < 0: break
    ctx = ram[pos:pos+10]
    print(f"  0x{pos:08X}: {ctx.hex()}")
    pos += 1
    count += 1

print("\n=== Done ===")
