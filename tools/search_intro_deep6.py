#!/usr/bin/env python3
"""Search for intro text - look at PACKDATA resources and try msg-style glyph IDs."""
import zipfile
import struct
import json
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

z = zipfile.ZipFile('C:/Programmieren/wizardrytranslation/ramdumps/intro.p2s', 'r')
ram = z.read('eeMemory.bin')

# Load glyph map
with open('C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json', 'r', encoding='utf-8') as f:
    glyph_map = json.load(f)

# Reverse: char -> first glyph ID
char_to_id = {}
for gid_str, char in glyph_map.items():
    gid = int(gid_str)
    if char not in char_to_id:
        char_to_id[char] = gid

# The text: その悲惨な戦争はバンクォーの戦役と人々に記憶される。
# Missing chars: 悲, 惨, 争, 役, 々, 憶
# Known: そ=126, の=136, な=132, 戦=286, は=137, バ=254, ン=238, ク=200, ォ=271, ー=93
# と=131, 人=319, に=133, 記=801, さ=122, れ=153, る=152, 。=63

# The chars 悲惨争役々憶 are NOT in the MSG glyph map.
# This suggests the intro uses either:
# 1. A completely different glyph system (different font)
# 2. The text is pre-rendered into a texture

# Let's check approach 2: look for DMA transfer records or texture upload data
# In PS2, textures are uploaded to GS VRAM via GIF path
# The intro text might be rendered into a texture on the EE side and then uploaded

# Let's look for image data that could be the rendered text
# The text is white/light colored on dark background
# A 640x200 region at 32bpp would be ~512KB

# Actually, let's look at the PACKDATA TOC to find intro-related files
print("=== Looking for PACKDATA.DIG TOC in RAM ===")
# The TOC typically starts with a count and then offsets/sizes
# PACKDATA.DIG;1 reference at 0x00504B48
# Let's look at the game's file table

# Search for a table of uint32 offsets that looks like PACKDATA.DIG TOC
# We know PACKDATA.DIG has 296 resources
# A TOC with 296 entries of (offset, size) would be 296 * 8 = 2368 bytes
# Or just offsets: 296 * 4 = 1184 bytes

# Let's try to find sequences of increasing uint32 values (file offsets)
print("\n=== Looking for TOC-like tables ===")
for start in range(0x004C0000, 0x00600000, 4):
    # Read first entry
    v0 = struct.unpack_from('<I', ram, start)[0]
    if v0 != 0:
        continue
    # Check if next values are increasing
    vals = [struct.unpack_from('<I', ram, start + i*4)[0] for i in range(10)]
    increasing = all(vals[i] <= vals[i+1] for i in range(9))
    if increasing and vals[9] > 0x1000 and vals[9] < 0x10000000:
        # Could be a TOC. Check more entries.
        count = 0
        for i in range(300):
            v = struct.unpack_from('<I', ram, start + i*4)[0]
            if i > 0 and v < struct.unpack_from('<I', ram, start + (i-1)*4)[0]:
                break
            count += 1
        if count > 50:
            print(f"  TOC candidate at 0x{start:08X}: {count} increasing entries")
            print(f"    First 10: {vals}")
            last_10 = [struct.unpack_from('<I', ram, start + (count-10+i)*4)[0] for i in range(10)]
            print(f"    Last 10: {last_10}")

# === Different approach: search for the PACKDATA.DIG TOC ===
# Read the actual PACKDATA.DIG file header if available
dig_path = 'C:/Programmieren/wizardrytranslation/PACKDATA.DIG'
alt_path = 'C:/Programmieren/wizardrytranslation/build/PACKDATA.DIG'
for p in [dig_path, alt_path]:
    if os.path.exists(p):
        print(f"\n=== Reading {p} ===")
        with open(p, 'rb') as f:
            header = f.read(256)
        print(f"Header: {header[:64].hex()}")
        break

# === Let's try yet another approach ===
# Look at what changed between the v3 savestate and intro savestate
# The file introv3stilljap.p2s exists - compare RAM
print("\n=== Comparing with introv3stilljap.p2s ===")
v3_path = 'C:/Programmieren/wizardrytranslation/build/introv3stilljap.p2s'
if os.path.exists(v3_path):
    z2 = zipfile.ZipFile(v3_path, 'r')
    print(f"  Files: {z2.namelist()}")
    ram2 = z2.read('eeMemory.bin')
    # Find regions that differ
    diff_regions = []
    for offset in range(0, min(len(ram), len(ram2)), 4096):
        block1 = ram[offset:offset+4096]
        block2 = ram2[offset:offset+4096]
        if block1 != block2:
            # Count differing bytes
            diff_count = sum(1 for a, b in zip(block1, block2) if a != b)
            if diff_count > 100:
                diff_regions.append((offset, diff_count))

    print(f"  {len(diff_regions)} regions with >100 differing bytes")
    diff_regions.sort(key=lambda x: -x[1])
    for offset, count in diff_regions[:30]:
        print(f"    0x{offset:08X}: {count} bytes differ")
else:
    print(f"  {v3_path} not found")

# === The intro text style is different from regular MSG ===
# The screenshot shows larger, stylized text with shadow/outline
# This is very likely using a different font/rendering system
# Let's search for any UNIQUE byte patterns that exist in this savestate
# but might represent text data

# Actually, let's just exhaustively search for the hiragana sequence
# その (glyph IDs 126, 136) followed by anything, then な (132)
# with various data sizes between characters
print("\n=== Exhaustive glyph ID search with variable spacing ===")
# Search for 126 as uint16 LE followed by 136 as uint16 LE within 4-32 bytes
target1 = struct.pack('<H', 126)  # そ
target2 = struct.pack('<H', 136)  # の

pos = 0
found = []
while True:
    pos = ram.find(target1, pos)
    if pos < 0:
        break
    # Check if 136 follows at various offsets
    for gap in [2, 4, 6, 8, 12, 16]:
        if pos + gap + 1 < len(ram):
            val = struct.unpack_from('<H', ram, pos + gap)[0]
            if val == 136:
                # Check further: after "の", look for "な"=132 or kanji
                for gap2 in [gap, gap*2, gap*3]:
                    next_offset = pos + gap + gap2
                    if next_offset + 1 < len(ram):
                        val2 = struct.unpack_from('<H', ram, next_offset)[0]
                        if val2 == 132:  # な
                            # This looks promising!
                            seq = []
                            for i in range(15):
                                off = pos + i * gap
                                if off + 1 < len(ram):
                                    v = struct.unpack_from('<H', ram, off)[0]
                                    seq.append(v)
                            found.append((pos, gap, seq))
    pos += 2

print(f"  Found {len(found)} candidates")
for pos, gap, seq in found[:20]:
    # Decode using glyph map
    decoded = []
    for v in seq:
        ch = glyph_map.get(str(v), f'[{v}]')
        decoded.append(ch)
    print(f"  0x{pos:08X} gap={gap}: {seq}")
    print(f"    decoded: {''.join(decoded)}")

print("\n=== Done ===")
