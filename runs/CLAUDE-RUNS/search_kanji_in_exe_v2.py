#!/usr/bin/env python3
"""
Deeper investigation: Are the EXE matches at 0x3AF6E8 real R1272 data
or just coincidental runs of 00/FF bytes?

Also: search for MORE distinctive R1272 pixel data patterns.
"""
import struct, os, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, "C:/Programmieren/wizardrytranslation/tools")
from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4

ORIG_ISO = "C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso"
SECTOR = 2048

# Extract R1272 and EXE
with open(ORIG_ISO, "rb") as f:
    f.seek(16 * SECTOR)
    pvd = f.read(SECTOR)
    root_lba = struct.unpack_from("<I", pvd, 158)[0]
    root_size = struct.unpack_from("<I", pvd, 166)[0]
    f.seek(root_lba * SECTOR)
    root_dir = f.read(root_size)
    pack_lba = exe_lba = exe_size = None
    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0: break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode("ascii", errors="replace")
        file_lba = struct.unpack_from("<I", root_dir, pos + 2)[0]
        file_size = struct.unpack_from("<I", root_dir, pos + 10)[0]
        if "PACKDATA" in name: pack_lba = file_lba
        if "SLPM" in name: exe_lba = file_lba; exe_size = file_size
        pos += rec_len

    f.seek(pack_lba * SECTOR)
    toc_data = f.read(2883 * 12)
    toc = []
    for i in range(2883):
        so, sc, tc = struct.unpack_from("<III", toc_data, i * 12)
        toc.append((so, sc, tc))

    r1272_so, r1272_sc, r1272_tc = toc[1272]
    f.seek((pack_lba + r1272_so) * SECTOR)
    r1272_raw = f.read(r1272_sc * SECTOR)

    f.seek(exe_lba * SECTOR)
    exe_data = f.read(exe_size)

HEADER_SIZE = 192
pixels_raw = r1272_raw[HEADER_SIZE:HEADER_SIZE + 65536]

print("=" * 70)
print("INVESTIGATION 1: What's at EXE 0x3AF6E8?")
print("=" * 70)
off = 0x3AF6E8
print(f"EXE[0x3AF6E8 - 0x3AF6E8+256]:")
for i in range(0, 256, 16):
    line = exe_data[off+i:off+i+16]
    hex_str = ' '.join(f'{b:02x}' for b in line)
    print(f"  0x{off+i:06X}: {hex_str}")

# Check: is this just a 00/FF pattern?
print(f"\nR1272 pixels[0:128]:")
for i in range(0, 128, 16):
    line = pixels_raw[i:i+16]
    hex_str = ' '.join(f'{b:02x}' for b in line)
    print(f"  0x{i:04X}: {hex_str}")

print("\nConclusion: The match at 0x3AF6E8 is likely just 0x00 followed by 0xFF runs")
print("which would be coincidental.\n")

# Now let's be smarter: find byte sequences in R1272 pixel data that are
# DISTINCTIVE (not all 00 or all FF), then search for those.
print("=" * 70)
print("INVESTIGATION 2: Find distinctive R1272 pixel data patterns")
print("=" * 70)

# Scan R1272 pixel data for 16-byte windows that aren't trivial
distinctive_patterns = []
for off in range(0, len(pixels_raw) - 16):
    window = pixels_raw[off:off+16]
    # Skip if all same byte
    if len(set(window)) <= 2 and (0x00 in set(window) or 0xFF in set(window)):
        continue
    # Skip if all zero or all FF
    if all(b == 0 for b in window) or all(b == 0xFF for b in window):
        continue
    distinctive_patterns.append((off, window))

print(f"Found {len(distinctive_patterns)} distinctive 16-byte patterns in R1272 pixel data")

# Search for the first N distinctive patterns in the EXE
matches_found = 0
for off, pattern in distinctive_patterns[:200]:  # check first 200
    needle = bytes(pattern)
    idx = exe_data.find(needle)
    if idx != -1:
        matches_found += 1
        print(f"  R1272 pixel offset 0x{off:04X} found at EXE 0x{idx:X}: {needle.hex()}")

if matches_found == 0:
    print("  No distinctive patterns found in EXE")
    # Try 8-byte patterns
    print("\nTrying 8-byte distinctive patterns...")
    for off in range(0, len(pixels_raw) - 8, 8):
        window = pixels_raw[off:off+8]
        if len(set(window)) <= 2:
            continue
        needle = bytes(window)
        idx = exe_data.find(needle)
        if idx != -1:
            matches_found += 1
            print(f"  R1272 pixel offset 0x{off:04X} found at EXE 0x{idx:X}: {needle.hex()}")
            if matches_found >= 20:
                break
    if matches_found == 0:
        print("  No distinctive 8-byte patterns found either")

# INVESTIGATION 3: Search for the ENTIRE R1272 resource (header+pixels+palette)
# in the EXE, not just pixels
print("\n" + "=" * 70)
print("INVESTIGATION 3: Search for R1272 resource chunks in EXE")
print("=" * 70)

# The full R1272 resource data
r1272_full = r1272_raw[:HEADER_SIZE + 65536 + 64]
print(f"Full R1272 resource size: {len(r1272_full)}")

# Search for distinctive chunks from the header
for off in range(0, min(192, len(r1272_raw)) - 16, 4):
    chunk = r1272_raw[off:off+16]
    if len(set(chunk)) <= 2:
        continue
    idx = exe_data.find(chunk)
    if idx != -1:
        print(f"  R1272 header offset 0x{off:02X} found at EXE 0x{idx:X}: {chunk.hex()}")

# INVESTIGATION 4: What about the palette?
print("\n" + "=" * 70)
print("INVESTIGATION 4: Search for R1272 palette in EXE")
print("=" * 70)
palette = r1272_raw[HEADER_SIZE + 65536:HEADER_SIZE + 65536 + 64]
print(f"Palette: {palette.hex()}")
idx = exe_data.find(palette)
if idx != -1:
    print(f"  FOUND at EXE 0x{idx:X} !!!")
else:
    print("  Full palette NOT found")
    # Try first 32 bytes
    idx = exe_data.find(palette[:32])
    if idx != -1:
        print(f"  First 32 bytes of palette found at EXE 0x{idx:X}")
    # Try 16 bytes
    idx = exe_data.find(palette[:16])
    if idx != -1:
        print(f"  First 16 bytes of palette found at EXE 0x{idx:X}")

# INVESTIGATION 5: Search for larger distinctive chunks (32+ bytes)
print("\n" + "=" * 70)
print("INVESTIGATION 5: 32-byte distinctive pixel patterns")
print("=" * 70)
match32 = 0
for off in range(0, len(pixels_raw) - 32, 32):
    window = pixels_raw[off:off+32]
    if len(set(window)) <= 3:
        continue
    idx = exe_data.find(window)
    if idx != -1:
        match32 += 1
        print(f"  R1272 pixel offset 0x{off:04X} found at EXE 0x{idx:X}: {window[:16].hex()}...")
        if match32 >= 20:
            break
if match32 == 0:
    print("  None found")

# INVESTIGATION 6: What about the GIF/GS register setup data in the header?
print("\n" + "=" * 70)
print("INVESTIGATION 6: R1272 internal header analysis")
print("=" * 70)
# After the 16-byte sub-header, there should be GS setup data
internal = r1272_raw[16:192]
print(f"Internal header ({len(internal)} bytes):")
for i in range(0, len(internal), 16):
    line = internal[i:i+16]
    hex_str = ' '.join(f'{b:02x}' for b in line)
    print(f"  0x{16+i:04X}: {hex_str}")

# Search for each 16-byte chunk of the header
print("\nSearching each 16-byte header chunk in EXE:")
for i in range(0, len(internal), 16):
    chunk = internal[i:i+16]
    if len(set(chunk)) <= 1:
        continue
    idx = exe_data.find(chunk)
    if idx != -1:
        print(f"  Header[0x{16+i:02X}] found at EXE 0x{idx:X}: {chunk.hex()}")

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
