#!/usr/bin/env python3
"""Analyze TextEventImage resources in PACKDATA."""
import struct, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'C:/Programmieren/wizardrytranslation'

# Load manifest
manifest = json.load(open(f'{BASE}/extracted/packdata_resources/manifest.json'))

# Analyze R1192 Section 2 in detail
data = open(f'{BASE}/extracted/packdata_raw/1192_type02.raw', 'rb').read()
s2o = struct.unpack_from('<I', data, 24)[0]
s2t = struct.unpack_from('<I', data, 20)[0]
s2 = data[s2o:s2o+s2t]

print(f"=== R1192 Analysis ===")
print(f"Total size: {len(data)} bytes")
print(f"Section 1: 0x20 to 0x{s2o:X} ({s2o - 0x20} bytes)")
print(f"Section 2: 0x{s2o:X}, size {s2t} bytes")
print()

# Parse section 2 header
print("S2 header:")
print(f"  Magic: {s2[0:4].hex()}")
print(f"  Bytes 4-7: {s2[4:8].hex()}")
# 0x01 0x00 = 1, 0xC7 0x00 = 199
val1 = struct.unpack_from('<H', s2, 4)[0]
val2 = struct.unpack_from('<H', s2, 6)[0]
print(f"  val1={val1}, val2={val2} (C7=199)")
print()

# 12-byte entries from offset 0x10
print("12-byte GS transfer entries (0x10 to ~0xA8):")
for i in range(0x10, 0xA8, 12):
    chunk = s2[i:i+12]
    # Parse as: u32, u16, u16, u32
    a = struct.unpack_from('<I', chunk, 0)[0]
    b = struct.unpack_from('<H', chunk, 4)[0]
    c = struct.unpack_from('<H', chunk, 6)[0]
    d = struct.unpack_from('<I', chunk, 8)[0]
    print(f"  +{i:03X}: addr=0x{a:08X} val1=0x{b:04X} val2=0x{c:04X} val3=0x{d:08X}")
print()

# The data from 0xA8 onwards - what is it?
# First few bytes: 60 02 8F 01 00 00 00 00 00 00 00 00
print(f"Data at 0xA8-0xBF: {s2[0xA8:0xC0].hex()}")
# Offset 0xA8: 0x0260 = 608, 0x018F = 399
# Then 8 bytes of zeros
# Then from 0xB4: repeating 2-byte values

# Let's look at the data as a timeline/animation table
# Starting at 0xB4, pairs of bytes
print()
print("Table from 0xB4 (2-byte entries, first 50):")
for i in range(0xB4, min(0xB4 + 100, len(s2)), 2):
    val = struct.unpack_from('>H', s2, i)[0]
    print(f"  +{i:03X}: 0x{val:04X} ({val})")

# Now let's look at what comes after the table
# The table likely has 199 entries (C7) of some size
# Let's search for where the actual texture/image data begins
# Look for large blocks of non-zero pixel data
print()
print("=== Searching for texture data blocks ===")
# After the header+table area, look for blocks with specific patterns
for offset in range(0x300, len(s2), 0x100):
    block = s2[offset:offset+256]
    # Check if this looks like pixel data (varied bytes, not all zeros)
    nonzero = sum(1 for b in block if b != 0)
    unique = len(set(block))
    if nonzero > 200 and unique > 50:
        print(f"  Dense block at +{offset:05X} ({offset}): {nonzero}/256 nonzero, {unique} unique values")
        if offset < 0x500:
            print(f"    First 32 bytes: {block[:32].hex()}")

# Check for TIM2 markers
print()
print("=== TIM2 search ===")
for i in range(len(s2) - 4):
    if s2[i:i+4] == b'TIM2':
        print(f"  TIM2 at S2+{i:05X}")

# Check the end of section 2
print()
print(f"S2 last 64 bytes: {s2[-64:].hex()}")
