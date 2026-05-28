#!/usr/bin/env python3
"""Deep analysis of TextEventImage resources R1192 and R2361."""
import struct, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'C:/Programmieren/wizardrytranslation'

def analyze_textevent_resource(idx, tc=2):
    rawfile = f"{BASE}/extracted/packdata_raw/{idx}_type{tc:02d}.raw"
    data = open(rawfile, 'rb').read()
    s2o = struct.unpack_from('<I', data, 24)[0]
    s2t = struct.unpack_from('<I', data, 20)[0]
    s2 = data[s2o:s2o+s2t]

    print(f"=== R{idx} TextEventImage Analysis ===")
    print(f"Total: {len(data)} bytes, S2: {s2t} bytes at 0x{s2o:X}")

    # Parse header
    magic = s2[0:4]
    val1 = struct.unpack_from('<H', s2, 4)[0]  # always 1?
    count = struct.unpack_from('<H', s2, 6)[0]
    print(f"Magic: {magic.hex()}, val1={val1}, count={count}")

    # Bytes 8-15: zeros
    print(f"Bytes 8-15: {s2[8:16].hex()}")

    # GS transfer entries from offset 0x10
    # Each is 12 bytes. How many?
    # The first entry starts at 0x10, and they seem to go to ~0xA8 for R1192
    # 0xA8 - 0x10 = 0x98 = 152 bytes / 12 = 12.67 -> actually 13 entries
    # For R1192: 13 entries from 0x10 to 0xA8 (13 * 12 = 156 = 0x9C)
    # 0x10 + 0x9C = 0xAC

    # Let's figure out the structure more carefully
    # Offset 0xA8 in R1192 has: 0C FC 00 02 60 02 8F 01
    # The 12-byte entries contain GIF/GS register setup

    # Let's look at the bytes from 0x10 as 4-byte words
    print(f"\nS2 data from 0x10 to 0x100:")
    for i in range(0x10, min(0x100, len(s2)), 4):
        val = struct.unpack_from('<I', s2, i)[0]
        print(f"  +{i:03X}: {s2[i:i+4].hex()} = {val:10d} (0x{val:08X})")

    # Now analyze the data region
    # After the header/GS setup + animation table, there should be texture pixel data
    # The textures are for text overlay -- likely 8bpp or 4bpp with CLUT

    # Let's look for patterns: find blocks separated by zeros
    print(f"\nSearching for data block boundaries (16+ consecutive zeros):")
    i = 0x100
    in_data = False
    block_start = 0
    blocks = []
    while i < len(s2) - 16:
        all_zero = all(s2[i+j] == 0 for j in range(16))
        if in_data and all_zero:
            # End of a block
            blocks.append((block_start, i))
            in_data = False
        elif not in_data and not all_zero:
            block_start = i
            in_data = True
        i += 1
    if in_data:
        blocks.append((block_start, len(s2)))

    print(f"Found {len(blocks)} data blocks")
    for start, end in blocks[:20]:
        size = end - start
        print(f"  +{start:05X} to +{end:05X}: {size} bytes")

    # Look at the first texture data block
    if blocks:
        first = blocks[0]
        print(f"\nFirst data block ({first[1]-first[0]} bytes):")
        print(f"  Start: {s2[first[0]:first[0]+32].hex()}")

    return s2, count, blocks

print("="*60)
s2_1192, count_1192, blocks_1192 = analyze_textevent_resource(1192)

print("\n" + "="*60)
s2_2361, count_2361, blocks_2361 = analyze_textevent_resource(2361)

# Now let's try to understand the control table better for R1192
# The table from ~0xB4 in R1192 has entries that look like (frame, offset) pairs
# Let's re-examine with different byte groupings
print("\n" + "="*60)
print("=== R1192 Control Table Analysis ===")
# From 0xAC: bytes look like 3-byte entries
# 00 00 00 00 00 01 20 00 02 20 00 02
# Let's try interpreting as sequence of (byte, u16) or (u16, byte) triples

# Actually looking at the hex dump again:
# +0B4: 00 00 00 00 (4 zeros)
# +0B8: 00 01 - entry 0
# +0BA: 20 00 02 - entry with values
# Let me try 3-byte entries
print("\nTrying 3-byte entries from +0xB8:")
for i in range(0xB8, min(0xB8 + 199*3, 0xB8 + 100), 3):
    a = s2_1192[i]
    b = struct.unpack_from('>H', s2_1192, i+1)[0]
    print(f"  +{i:03X}: timing={a:3d} offset=0x{b:04X} ({b})")

# Try 2-byte entries instead
print("\nTrying 2-byte entries (LE) from +0xB8:")
for i in range(0xB8, min(0xB8 + 199*2, 0xB8 + 60), 2):
    v = struct.unpack_from('<H', s2_1192, i)[0]
    print(f"  +{i:03X}: 0x{v:04X} ({v})")
