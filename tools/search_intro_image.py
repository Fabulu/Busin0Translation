#!/usr/bin/env python3
"""Confirm intro text is in pre-rendered images within PACKDATA resources."""
import struct
import sys
import zipfile
sys.stdout.reconfigure(encoding='utf-8')

# Read RAM
z = zipfile.ZipFile('C:/Programmieren/wizardrytranslation/ramdumps/intro.p2s', 'r')
ram = z.read('eeMemory.bin')

# The TMOpening code references TextEvent images
# Let's find the TMOpening functions in RAM and trace what PACKDATA resources they load

# Search for TMOpening strings and nearby code
print("=== TMOpening references ===")
for keyword in [b'TMOpening', b'TMOpening Start', b'TMOpening MakeStart']:
    pos = ram.find(keyword)
    if pos >= 0:
        print(f"  '{keyword.decode()}' at 0x{pos:08X}")

# The TextEvent system has Image data management
# TextEventImageDrawRequest, SetTextEventImageData
# These indicate that the intro text IS pre-rendered images

# Let's look at the PACKDATA.DIG TOC more carefully
# We know it has 296 resources. Let's find and read the TOC
print("\n=== PACKDATA.DIG TOC ===")
import os
dig_path = 'C:/Programmieren/wizardrytranslation/build/PACKDATA.DIG'
with open(dig_path, 'rb') as f:
    # Read first few KB for TOC
    toc_data = f.read(8192)

# Parse TOC - the format from earlier analysis
# Header: 7d000000 01000000 01000000 7e000000 01000000 01000000
# This looks like: resource_id, type?, count?, ...
# Let's try parsing as 12-byte entries
print("First 240 bytes as 12-byte entries:")
for i in range(0, min(240, len(toc_data)), 12):
    vals = struct.unpack_from('<3I', toc_data, i)
    print(f"  [{i//12:3d}] {vals[0]:8d} {vals[1]:8d} {vals[2]:8d}")

# Actually, let's check existing analysis
print("\n=== Checking existing PACKDATA analysis ===")
analysis_paths = [
    'C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon',
    'C:/Programmieren/wizardrytranslation/dumps',
    'C:/Programmieren/wizardrytranslation/data',
]
for base in analysis_paths:
    if os.path.exists(base):
        for f in os.listdir(base):
            fl = f.lower()
            if 'packdata' in fl or 'toc' in fl or 'resource' in fl or 'catalogue' in fl:
                print(f"  {os.path.join(base, f)}")

# Let's look for a resource map/catalogue
for root, dirs, files in os.walk('C:/Programmieren/wizardrytranslation/runs'):
    for f in files:
        fl = f.lower()
        if 'packdata' in fl or 'resource' in fl:
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            if sz < 100000:
                print(f"  {fp} ({sz} bytes)")
    if root.count(os.sep) > 8:
        dirs.clear()

# === Let's actually check which PACKDATA resources are loaded during intro ===
# Search RAM for what looks like currently-loaded PACKDATA resource descriptors
# The game likely has an array of loaded resource info structs
print("\n=== Searching for loaded resource tracking ===")
# In RAM, around 0x00560000-0x00580000, we saw interesting data
# Let's look at 0x00563BFC area (which had 58 increasing entries - could be resource offsets)
addr = 0x00563BFC
vals = [struct.unpack_from('<I', ram, addr + i*4)[0] for i in range(60)]
print(f"Table at 0x{addr:08X}:")
for i in range(0, 60, 10):
    row = vals[i:i+10]
    print(f"  [{i:2d}-{i+9:2d}]: {row}")

# Let's also check what index the TextEvent system loads
# Search for references to resource indices near TextEvent code
# The ELF base is 0x00100000
# TextEvent strings are at ELF+0x3F34B0 = RAM 0x004F34B0
# Let's look at the code before these strings for PACKDATA resource load calls

# Actually, let's search for specific resource numbers
# The game has ~296 PACKDATA resources. The TextEvent system would load
# event-related resources. Let's see which resources are currently loaded.

# Search for the magic pattern of a loaded PACKDATA resource in RAM
# After loading, the game likely stores the loaded data pointer somewhere
# Let's look at the region around 0x0056 where we saw data earlier
print("\n=== Data at 0x00560000 region ===")
for addr in range(0x00560000, 0x00570000, 64):
    block = ram[addr:addr+64]
    if block == b'\x00' * 64:
        continue
    # Print as uint32
    vals = [struct.unpack_from('<I', block, i)[0] for i in range(0, 64, 4)]
    # Check if any look like pointers into RAM (0x00100000-0x02000000)
    ptrs = sum(1 for v in vals if 0x00100000 < v < 0x02000000)
    if ptrs > 0:
        print(f"  0x{addr:08X}: {[f'0x{v:08X}' for v in vals[:8]]}")

# === Let's search for the actual image dimensions that match the intro text ===
# The text in the screenshot spans roughly 400x150 pixels
# If stored as a texture, it would be a specific dimension
# PS2 textures are typically power-of-2 (256, 512, etc.)
# At 4bpp (16 colors), a 512x256 texture = 65536 bytes
# At 8bpp (256 colors), a 512x256 texture = 131072 bytes

# Let's look for texture-sized data blocks in the diff region
print("\n=== Looking for intro-specific textures in RAM ===")
# The text is rendered in white with shadow/outline
# In a 4bpp/8bpp texture, white pixels would be the max palette value (0xF or 0xFF)

# Search for blocks that are mostly 0x00 (transparent/black) with some 0xFF (white)
for offset in range(0x00800000, 0x01400000, 0x10000):
    block = ram[offset:offset+0x10000]
    zero_count = block.count(b'\x00'[0])
    ff_count = block.count(b'\xff'[0])
    total = len(block)
    # A text texture would be mostly transparent (>80% zeros) with some white (~5-15%)
    if zero_count > total * 0.7 and ff_count > total * 0.01 and ff_count < total * 0.2:
        # Could be a text texture
        # Check if it has a structured pattern (horizontal lines of text)
        print(f"  0x{offset:08X}: zeros={zero_count/total*100:.0f}% ff={ff_count/total*100:.0f}%")

print("\n=== Done ===")
