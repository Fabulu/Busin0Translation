#!/usr/bin/env python3
"""
R1188 auxiliary data (0x840-0xBFF) - interpret as structured coordinate data.
"""
import os, sys, struct

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R1188_PATH = os.path.join(BASE, "extracted", "packdata_resources", "1188_type01.bin")
r1188_data = open(R1188_PATH, 'rb').read()

# Full R1188 header is 0xC00 = 3072 bytes
# Let's look at the entire header structure
print("=== R1188 Header Analysis (0x000-0xBFF) ===\n")

# First 64 bytes
print("First 128 bytes (GIF tags etc.):")
for i in range(0, 128, 16):
    hex_str = ' '.join(f'{b:02X}' for b in r1188_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in r1188_data[i:i+16])
    print(f"  {i:04X}: {hex_str}  |{ascii_str}|")

# The R1188 header was identified as 3072 bytes (0xC00)
# Check what's at 0x800-0x840 (right before aux data)
print("\n\nData at 0x800-0x840 (before aux):")
for i in range(0x800, 0x840, 16):
    hex_str = ' '.join(f'{b:02X}' for b in r1188_data[i:i+16])
    print(f"  {i:04X}: {hex_str}")

# The auxiliary data at 0x840-0xBFF
print("\n\nAuxiliary data at 0x840-0xBFF (960 bytes):")
aux = r1188_data[0x840:0xC00]

# Try interpreting as groups of 16 bytes
print("\nAs 16-byte records (60 records):")
for i in range(0, len(aux), 16):
    chunk = aux[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    # As 4 x 32-bit
    w = [struct.unpack_from('<I', chunk, j)[0] for j in range(0, 16, 4)]
    # As 8 x 16-bit
    h = [struct.unpack_from('<H', chunk, j)[0] for j in range(0, 16, 2)]
    nz = sum(1 for b in chunk if b != 0)
    if nz > 0:
        print(f"  {0x840+i:04X}: {hex_str}")
        print(f"         u32: {w[0]:10d} {w[1]:10d} {w[2]:10d} {w[3]:10d}")
        print(f"         u16: {h[0]:6d} {h[1]:6d} {h[2]:6d} {h[3]:6d} {h[4]:6d} {h[5]:6d} {h[6]:6d} {h[7]:6d}")

# Also look at the data from 0x840 as pairs of bytes
# Many bytes are 0x00, 0x01, 0x10, 0x11, 0x0F, 0xF0
# These look like they could be nibble-pair flags
print("\n\nNibble analysis of aux data:")
for i in range(0, len(aux), 32):
    chunk = aux[i:min(i+32, len(aux))]
    nz = sum(1 for b in chunk if b != 0)
    if nz > 0:
        nibbles = []
        for b in chunk:
            nibbles.append(f'{(b>>4)&0xF:X}{b&0xF:X}')
        print(f"  {0x840+i:04X}: {' '.join(nibbles)}")

# Check what patterns we see in the last ~128 bytes (where most non-zero data is)
print("\n\nLast 128 bytes of aux data:")
for i in range(len(aux) - 128, len(aux), 16):
    chunk = aux[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    print(f"  {0x840+i:04X}: {hex_str}")

# These trailing bytes look very different from the leading bytes
# Let's check if they might be GIF register settings or TEX0/CLUT references
print("\n\nInterpreting trailing data as GIF/GS register values:")
trail = aux[-64:]
for i in range(0, 64, 16):
    chunk = trail[i:i+16]
    q0 = struct.unpack_from('<Q', chunk, 0)[0]
    q1 = struct.unpack_from('<Q', chunk, 8)[0]
    print(f"  QWORD pair: 0x{q0:016X}  0x{q1:016X}")

print("\n=== Done ===")
