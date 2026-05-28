#!/usr/bin/env python3
"""Search for intro text - focused diff between intro and v3 savestates."""
import zipfile
import struct
import sys
sys.stdout.reconfigure(encoding='utf-8')

z1 = zipfile.ZipFile('C:/Programmieren/wizardrytranslation/ramdumps/intro.p2s', 'r')
z2 = zipfile.ZipFile('C:/Programmieren/wizardrytranslation/build/introv3stilljap.p2s', 'r')
ram1 = z1.read('eeMemory.bin')
ram2 = z2.read('eeMemory.bin')

# Extract v3 screenshot
with open('C:/Programmieren/wizardrytranslation/ramdumps/v3_screenshot.png', 'wb') as f:
    f.write(z2.read('Screenshot.png'))
print("v3 screenshot extracted")

# Focus on lower RAM (non-texture areas) that differ
# Below 0x00800000 is typically code + data
print("\n=== Differences in low RAM (0-8MB) ===")
for offset in range(0, 0x00800000, 256):
    block1 = ram1[offset:offset+256]
    block2 = ram2[offset:offset+256]
    if block1 != block2:
        diff_count = sum(1 for a, b in zip(block1, block2) if a != b)
        if diff_count > 10:
            print(f"  0x{offset:08X}: {diff_count} bytes differ")
            # Show the differences
            for i in range(0, 256, 4):
                v1 = struct.unpack_from('<I', block1, i)[0]
                v2 = struct.unpack_from('<I', block2, i)[0]
                if v1 != v2:
                    print(f"    +{i:03X}: intro=0x{v1:08X} v3=0x{v2:08X}")
                    if i > 20:
                        print(f"    ... (more)")
                        break

# === Focus on what data structures reference the intro text ===
# The intro display is managed by the game's event system
# Look for active event/script state in RAM
print("\n=== Active event/script state search ===")
# Games often have a global state struct. Let's look for pointers
# that point into data areas and changed between states

# Search for uint32 values in low RAM that point into the
# range 0x00560000-0x00580000 (where we saw interesting TOC data)
print("\n=== Pointers to intro data areas ===")
for base in range(0x00550000, 0x00600000, 0x10000):
    count = 0
    for offset in range(0, 0x00500000, 4):
        v = struct.unpack_from('<I', ram1, offset)[0]
        if base <= v < base + 0x10000:
            count += 1
    if count > 5:
        print(f"  {count} pointers to 0x{base:08X}-0x{base+0x10000:08X}")

# === Let's look at 0x00560000 area more carefully ===
# We found TOC-like data and interesting structures there
print("\n=== Examining 0x00560000-0x00570000 ===")
for i in range(0x00560000, 0x00570000, 64):
    block = ram1[i:i+64]
    # Check if this contains interesting data (not all zeros, not all FF)
    if block == b'\x00' * 64 or block == b'\xff' * 64:
        continue
    # Check if it looks like text data (uint16 values in glyph range)
    vals = [struct.unpack_from('<H', block, j)[0] for j in range(0, min(32, len(block)), 2)]
    glyph_like = sum(1 for v in vals if 0 < v < 1500)
    if glyph_like > 8:
        print(f"  0x{i:08X}: {vals}")

# === Search for the intro text in PACKDATA.DIG itself ===
print("\n=== Searching PACKDATA.DIG for intro text ===")
import os
dig_path = 'C:/Programmieren/wizardrytranslation/build/PACKDATA.DIG'
if os.path.exists(dig_path):
    # Read TOC
    with open(dig_path, 'rb') as f:
        data = f.read(4096)  # Read first 4KB
    # Parse TOC entries
    # Format from header: seems to be (id, ?, ?, ...) entries
    print(f"  First 128 bytes: {data[:128].hex()}")
    # The header starts with resource descriptors
    # Let's parse as 12-byte entries
    for i in range(0, min(len(data), 1200), 12):
        entry = data[i:i+12]
        if len(entry) < 12:
            break
        vals = struct.unpack_from('<3I', entry, 0)
        if vals[0] == 0 and vals[1] == 0 and vals[2] == 0:
            continue
        if i < 120 or (vals[1] > 0 and vals[1] < 0x10000):
            pass  # skip printing most entries

# === Let's try to find loaded resource data in the diff region ===
# The v3 intro might be a different frame of the intro
# Let's look for small data blocks that exist in intro but not v3
print("\n=== Data blocks unique to intro state ===")
# Check 0x00540000-0x005C0000 area
for offset in range(0x00540000, 0x005C0000, 256):
    block1 = ram1[offset:offset+256]
    block2 = ram2[offset:offset+256]
    if block1 != block2:
        diff_count = sum(1 for a, b in zip(block1, block2) if a != b)
        if diff_count > 20:
            # Check if this looks like text-related data
            vals = [struct.unpack_from('<H', block1, j)[0] for j in range(0, 32, 2)]
            glyph_like = sum(1 for v in vals if 0 < v < 1500)
            if glyph_like > 4 or diff_count > 200:
                print(f"  0x{offset:08X}: {diff_count} bytes differ, glyphs={glyph_like}")
                if glyph_like > 4:
                    print(f"    vals: {vals}")

print("\n=== Done ===")
