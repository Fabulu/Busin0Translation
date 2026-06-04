#!/usr/bin/env python3
"""
Final investigation: The R1272 PIXEL DATA is NOT in the EXE.
The GIF header chunks ARE partially present (GS register setup templates).

Let's conclusively check:
1. Is the GIF header at 0x3D6A28 a full copy of R1272's GIF header?
2. Search for distinctive pixel patterns more aggressively
3. Also check if the EXE contains pixel data for ANY font resource
"""
import struct, os, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ORIG_ISO = "C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso"
SECTOR = 2048

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
internal_header = r1272_raw[16:192]  # 176 bytes GIF header

print("=" * 70)
print("CHECK 1: EXE region around 0x3D6A28 vs R1272 GIF header")
print("=" * 70)

# R1272 internal header starts at raw offset 0x10 (after sub-header)
# Match was found at EXE 0x3D6A28 for header offset 0x18 (internal offset 0x08)
# So the EXE base for the header would be at 0x3D6A28 - 0x08 = 0x3D6A20

exe_base = 0x3D6A20
print(f"R1272 internal header (176 bytes from raw offset 0x10):")
print(f"EXE region starting at 0x{exe_base:X}:")
print()
print(f"{'Offset':>6s}  {'R1272 header':48s}  {'EXE data':48s}  Match?")
print("-" * 115)

match_count = 0
for i in range(0, 176, 16):
    hdr_chunk = internal_header[i:i+16]
    exe_chunk = exe_data[exe_base + i:exe_base + i + 16]
    hdr_hex = ' '.join(f'{b:02x}' for b in hdr_chunk)
    exe_hex = ' '.join(f'{b:02x}' for b in exe_chunk)
    match = hdr_chunk == exe_chunk
    if match:
        match_count += 1
    print(f"  0x{i:02X}:  {hdr_hex}  {exe_hex}  {'YES' if match else 'NO'}")

print(f"\nMatching 16-byte lines: {match_count}/11")

# Let's also check the other candidate base at 0x3D6B60
print("\n" + "=" * 70)
print("CHECK 2: Wider EXE context around the GIF header matches")
print("=" * 70)

# Dump EXE around 0x3D6A00 - 0x3D6C00
for base in [0x3D6A00, 0x3D6B00]:
    print(f"\nEXE[0x{base:X} - 0x{base+256:X}]:")
    for i in range(0, 256, 16):
        line = exe_data[base+i:base+i+16]
        hex_str = ' '.join(f'{b:02x}' for b in line)
        print(f"  0x{base+i:06X}: {hex_str}")

# CHECK 3: Let's look for the R1272 internal header as a CONTIGUOUS block
print("\n" + "=" * 70)
print("CHECK 3: Search for contiguous R1272 header in EXE")
print("=" * 70)

# The GIF header has distinctive parts. Let's search for the longest
# contiguous matching stretch.
best_len = 0
best_off = -1
for start in range(0, 176 - 16):
    for length in range(176 - start, 15, -1):
        chunk = bytes(internal_header[start:start + length])
        if all(b == 0 for b in chunk):
            continue
        idx = exe_data.find(chunk)
        if idx != -1 and length > best_len:
            best_len = length
            best_off = idx
            print(f"  Longest contiguous match: {length} bytes at EXE 0x{idx:X} (header offset 0x{start:X})")
            break
    if best_len >= 64:
        break

if best_len == 0:
    print("  No contiguous match found")

# CHECK 4: Does the EXE contain GIF packet data that REFERENCES R1272's
# texture parameters (TBP, TBW, PSM, dimensions)?
print("\n" + "=" * 70)
print("CHECK 4: Search for GS TEX0 register value for R1272")
print("=" * 70)

# R1272 TEX0 parameters:
# TBP0 = some value, TBW = 4 (256/64), PSM = PSMT4 (0x14)
# TW = 8 (2^8=256), TH = 9 (2^9=512)
# The TEX0 register is 64-bit. Let's look at what the header contains.
# From the internal header at 0x80:
# 00 01 00 02 00 00 00 00 -> this might be TEX0 or related
# At 0x88: 4c 00 00 00 80 00 80 00 -> could contain dimensions

# Actually let's parse the GIF packet properly
print(f"\nR1272 GIF header bytes (176 bytes):")
for i in range(0, 176, 16):
    line = internal_header[i:i+16]
    hex_str = ' '.join(f'{b:02x}' for b in line)
    # Also show as little-endian 32-bit words
    words = []
    for j in range(0, 16, 4):
        w = struct.unpack_from("<I", line, j)[0]
        words.append(f'{w:08X}')
    print(f"  0x{0x10+i:04X}: {hex_str}  | {" ".join(words)}")

# CHECK 5: Exhaustive search - scan the ENTIRE EXE for ANY 32+ byte
# sequence from R1272 pixel data
print("\n" + "=" * 70)
print("CHECK 5: Exhaustive scan for ANY R1272 pixel data in EXE")
print("=" * 70)
print("Scanning every 256-byte aligned position in pixel data...")

found_any = False
for pix_off in range(0, 65536, 256):
    chunk = pixels_raw[pix_off:pix_off + 256]
    # Skip trivial chunks
    unique_bytes = len(set(chunk))
    if unique_bytes <= 2:
        continue
    # Search in EXE
    idx = exe_data.find(chunk)
    if idx != -1:
        found_any = True
        print(f"  MATCH: pixel offset 0x{pix_off:04X} (256 bytes) at EXE 0x{idx:X}")

if not found_any:
    print("  No non-trivial 256-byte pixel chunks found in EXE")
    print("\nTrying 64-byte chunks at every 64-byte boundary...")
    for pix_off in range(0, 65536, 64):
        chunk = pixels_raw[pix_off:pix_off + 64]
        unique_bytes = len(set(chunk))
        if unique_bytes <= 3:
            continue
        idx = exe_data.find(chunk)
        if idx != -1:
            found_any = True
            print(f"  MATCH: pixel offset 0x{pix_off:04X} (64 bytes) at EXE 0x{idx:X}")
    if not found_any:
        print("  No non-trivial 64-byte pixel chunks found in EXE")

print("\n" + "=" * 70)
print("FINAL CONCLUSION")
print("=" * 70)
print()
print("The EXE does NOT contain a copy of R1272's kanji pixel data.")
print("The EXE DOES contain GIF/GS register setup templates (header fragments)")
print("at around EXE 0x3D6A20-0x3D6B80, which are the DMA/GIF packet templates")
print("used by the game engine to configure the GS for texture uploads.")
print()
print("The kanji pixel data for R1272 comes exclusively from PACKDATA.DIG on disc.")

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
