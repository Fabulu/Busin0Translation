#!/usr/bin/env python3
"""Search RAM dump for intro narration glyph stream."""
import zipfile
import struct
import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
os.chdir("C:/Programmieren/wizardrytranslation")

z = zipfile.ZipFile('ramdumps/intro.p2s', 'r')
ram = z.read('eeMemory.bin')
print(f"RAM: {len(ram)} bytes")

# R1193 M0 starts with: 117, 129, 130, 337, 1186, 684, 146, 136, 404
# As BE uint16 that's: 0x0075 0x0081 0x0082 0x0151 0x04A2 0x02AC 0x0092 0x0088 0x0194
# Let's search for this byte sequence in RAM
r1193_start = struct.pack('>HHHHHHHHH', 117, 129, 130, 337, 1186, 684, 146, 136, 404)
pos = ram.find(r1193_start)
count = 0
while pos >= 0 and count < 10:
    print(f"R1193 M0 pattern found in RAM at 0x{pos:08X}")
    # Show surrounding context
    ctx = ram[max(0,pos-16):pos+40]
    vals = []
    for i in range(0, len(ctx)-1, 2):
        v = struct.unpack_from('>H', ctx, i)[0]
        vals.append(v)
    print(f"  BE uint16 context: {vals}")
    count += 1
    pos = ram.find(r1193_start, pos + 1)

if count == 0:
    print("R1193 M0 start pattern NOT found in RAM")
    # Try shorter pattern
    r1193_short = struct.pack('>HHHH', 117, 129, 130, 337)
    pos = ram.find(r1193_short)
    count2 = 0
    while pos >= 0 and count2 < 10:
        print(f"  Short pattern at 0x{pos:08X}")
        count2 += 1
        pos = ram.find(r1193_short, pos + 2)

# Also search for FFFF-terminated sequences that look like text in the
# intro memory region. The intro save state should have loaded resource data.
# Let's look at what PACKDATA resources are loaded into RAM
print("\n=== Searching for R1193 raw data in RAM ===")
r1193_data = open('extracted/packdata_raw/1193_type02.raw', 'rb').read()
# Search for first 32 bytes of R1193
target = r1193_data[:32]
pos = ram.find(target)
count = 0
while pos >= 0 and count < 5:
    print(f"R1193 first 32 bytes found at RAM 0x{pos:08X}")
    count += 1
    pos = ram.find(target, pos + 1)

# Search for R1193 section 2 data
sec2_off = struct.unpack_from('<I', r1193_data, 24)[0]
sec2 = r1193_data[sec2_off:]
target2 = sec2[:16]
print(f"\nR1193 sec2 first 16 bytes: {target2.hex()}")
pos = ram.find(target2)
count = 0
while pos >= 0 and count < 5:
    print(f"R1193 sec2 start found at RAM 0x{pos:08X}")
    count += 1
    pos = ram.find(target2, pos + 1)

# Now let's try the REVERSE approach: search RAM for text being displayed
# The game renders glyph IDs. Let's find FFFF-terminated glyph streams in RAM
# that contain IDs in the 60-850 range (typical kanji/kana)
# Focus on regions that look like the intro resource
print("\n=== Scanning RAM for glyph streams with FFFE (line breaks) ===")
# Search for FFFE followed by text-range glyphs
fffe = struct.pack('>H', 0xFFFE)
pos = 0
results = []
while pos < len(ram) - 20:
    pos = ram.find(fffe, pos)
    if pos < 0:
        break
    if pos % 2 != 0:
        pos += 1
        continue
    # Check surrounding values
    valid_before = 0
    valid_after = 0
    for j in range(1, 6):
        off = pos - j * 2
        if off >= 0:
            v = struct.unpack_from('>H', ram, off)[0]
            if 60 < v < 858:
                valid_before += 1
    for j in range(1, 6):
        off = pos + 2 + j * 2
        if off + 2 <= len(ram):
            v = struct.unpack_from('>H', ram, off)[0]
            if 60 < v < 858:
                valid_after += 1
    if valid_before >= 3 and valid_after >= 3:
        # This looks like a line break in actual text
        # Get more context
        start = pos - 20
        if start < 0:
            start = 0
        end = min(pos + 22, len(ram))
        vals = []
        for k in range(start, end - 1, 2):
            v = struct.unpack_from('>H', ram, k)[0]
            vals.append(v)
        results.append((pos, vals))
    pos += 2

print(f"Found {len(results)} potential text line breaks")
for addr, vals in results[:30]:
    print(f"  0x{addr:08X}: {vals}")

print("\nDone.")
