#!/usr/bin/env python3
"""
Search for R1272 kanji pixel data in the EXE.

1. Extract ORIGINAL R1272 from the ORIGINAL ISO
2. Deswizzle it (PSMT4 256x512, dbw_ct32=256)
3. Extract 12x12 glyph for 力 at position 346 -> pixel (120, 192)
4. Re-swizzle just that glyph's pixels back to raw bytes
5. Search the EXE for those raw bytes
6. Also search for the first 64 bytes of raw R1272 pixel data
"""
import struct, os, sys, io

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, "C:/Programmieren/wizardrytranslation/tools")
from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4

ORIG_ISO = "C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso"
SECTOR = 2048

# R1272 format from the user's spec:
# header 192 bytes, pixels 65536 bytes (PSMT4 256x512), palette 64 bytes
# But wait - R1272 is a type-01 resource with sub-header. Let me extract from ISO first.

print("=" * 70)
print("  KANJI PIXEL SEARCH IN EXE")
print("=" * 70)

# Step 1: Extract from original ISO
with open(ORIG_ISO, "rb") as f:
    # PVD
    f.seek(16 * SECTOR)
    pvd = f.read(SECTOR)
    root_lba = struct.unpack_from("<I", pvd, 158)[0]
    root_size = struct.unpack_from("<I", pvd, 166)[0]

    # Root dir
    f.seek(root_lba * SECTOR)
    root_dir = f.read(root_size)

    pack_lba = None
    exe_lba = None
    exe_size = None
    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode("ascii", errors="replace")
        file_lba = struct.unpack_from("<I", root_dir, pos + 2)[0]
        file_size = struct.unpack_from("<I", root_dir, pos + 10)[0]
        if "PACKDATA" in name:
            pack_lba = file_lba
        if "SLPM" in name:
            exe_lba = file_lba
            exe_size = file_size
        pos += rec_len

    print(f"PACKDATA LBA: {pack_lba}")
    print(f"EXE LBA: {exe_lba}, size: {exe_size:,}")

    # Read TOC
    f.seek(pack_lba * SECTOR)
    toc_data = f.read(2883 * 12)
    toc = []
    for i in range(2883):
        so, sc, tc = struct.unpack_from("<III", toc_data, i * 12)
        toc.append((so, sc, tc))

    # Extract R1272
    r1272_so, r1272_sc, r1272_tc = toc[1272]
    r1272_abs = pack_lba * SECTOR + r1272_so * SECTOR
    r1272_bytesize = r1272_sc * SECTOR
    print(f"\nR1272: sector_offset={r1272_so}, sector_count={r1272_sc}, type={r1272_tc}")
    print(f"  Absolute offset: {r1272_abs:,} (0x{r1272_abs:X})")
    print(f"  Byte size: {r1272_bytesize:,}")

    f.seek(r1272_abs)
    r1272_raw = f.read(r1272_bytesize)

    # Extract EXE
    f.seek(exe_lba * SECTOR)
    exe_data = f.read(exe_size)
    print(f"EXE: {len(exe_data):,} bytes loaded")

# Step 2: Parse R1272 structure
# Type-01 resource: 16-byte sub-header, then payload
sub_hdr = struct.unpack_from("<IIII", r1272_raw, 0)
print(f"\nR1272 sub-header: {sub_hdr}")
payload_size = sub_hdr[1]
payload = r1272_raw[16:16 + payload_size]
print(f"Payload size: {len(payload):,}")

# The user says: header 192 bytes, pixels 65536 bytes (PSMT4 256x512), palette 64 bytes
# But this may be relative to the payload (after sub-header).
# R1272 as raw file would have: 16-byte sub-header + header + pixels + palette
# Let's check the user's numbers: 192 + 65536 + 64 = 65792
# Total resource: 16 + 65792 = 65808
# But sector count is 33 sectors = 67584 bytes
# Let's check what the payload contains

# Actually: the user says "R1272 format: header 192 bytes, pixels 65536 bytes, palette 64 bytes"
# These offsets are probably within the resource itself (after 16-byte sub-header)
# So: payload starts at offset 16, then within payload:
#   header at 0, pixels at 192, palette at 192+65536=65728

# But the user also says the resource is at "PACKDATA LBA 16029 + sector 211292, 33 sectors"
# 33 sectors = 67584 bytes
# 16 (sub-hdr) + 192 (hdr) + 65536 (pixels) + 64 (palette) = 65808 bytes
# Plus padding to sector boundary

# Let's verify
print(f"\n--- Analyzing R1272 structure ---")
print(f"First 32 bytes: {r1272_raw[:32].hex()}")
print(f"Bytes 16-48: {r1272_raw[16:48].hex()}")

# The pixel data within the payload should start at offset 192
# Or alternatively, the user's header_size=192 might be from the start of the raw resource
# Let's try both:

# Option A: header from start of raw data (includes sub-header)
pixel_start_a = 192
pixels_a = r1272_raw[pixel_start_a:pixel_start_a + 65536]

# Option B: sub-header (16) + header within payload (192)
pixel_start_b = 16 + 192
pixels_b = r1272_raw[pixel_start_b:pixel_start_b + 65536]

# Check which has more non-zero data (likely the pixel data)
nz_a = sum(1 for b in pixels_a[:1024] if b != 0)
nz_b = sum(1 for b in pixels_b[:1024] if b != 0)
print(f"\nOption A (offset 192): non-zero in first 1024 = {nz_a}")
print(f"Option B (offset 208): non-zero in first 1024 = {nz_b}")

# Let's also check the generate_font_atlas.py for how it reads R1272
# But first, let's try the user's exact spec: header 192, pixels 65536, palette 64
# The "header" likely includes the 16-byte sub-header + 176 bytes of internal header = 192

# Let's go with what the user said directly
HEADER_SIZE = 192
PIXEL_SIZE = 65536  # 256*512/2
PALETTE_SIZE = 64

pixels_raw = r1272_raw[HEADER_SIZE:HEADER_SIZE + PIXEL_SIZE]
palette_raw = r1272_raw[HEADER_SIZE + PIXEL_SIZE:HEADER_SIZE + PIXEL_SIZE + PALETTE_SIZE]

print(f"\nUsing header_size={HEADER_SIZE}")
print(f"Pixel data: {len(pixels_raw)} bytes at offset 0x{HEADER_SIZE:X}")
print(f"First 32 bytes of pixels: {pixels_raw[:32].hex()}")
print(f"Palette (64 bytes): {palette_raw.hex()}")

# Step 3: Deswizzle
print("\n--- Deswizzling R1272 (256x512, dbw_ct32=256) ---")
pixels_lin = deswizzle_psmt4(pixels_raw, 256, 512, bw_psmt4=256, dbw_ct32=256)

# Step 4: Extract 力 glyph at position 346
# Grid: 21 columns (256/12=21.3... but the user says col=346%21=10)
# Actually the user says: col=346%21=10, row=346//21=16, pixel (120, 192)
# So 21 columns, each cell is 12 pixels wide: 21*12 = 252 (fits in 256)
# Each cell is 12 pixels tall: row 16 * 12 = 192
GRID_COLS = 21
CELL_W = 12
CELL_H = 12
GLYPH_POS = 346
col = GLYPH_POS % GRID_COLS  # 10
row = GLYPH_POS // GRID_COLS  # 16
px_x = col * CELL_W  # 120
px_y = row * CELL_H  # 192

print(f"\nGlyph 力 at position {GLYPH_POS}: col={col}, row={row}, pixel=({px_x}, {px_y})")

# Extract 12x12 block from linear pixels
glyph_pixels = bytearray(CELL_W * CELL_H)
for dy in range(CELL_H):
    for dx in range(CELL_W):
        src_idx = (px_y + dy) * 256 + (px_x + dx)
        glyph_pixels[dy * CELL_W + dx] = pixels_lin[src_idx]

print(f"Glyph pixel values (12x12):")
for row_i in range(CELL_H):
    row_vals = glyph_pixels[row_i * CELL_W:(row_i + 1) * CELL_W]
    print(f"  Row {row_i:2d}: {' '.join(f'{v:X}' for v in row_vals)}")

# Check if glyph is non-zero
nz = sum(1 for p in glyph_pixels if p != 0)
print(f"Non-zero pixels: {nz}/{CELL_W * CELL_H}")

# Step 5: Now we need to find the RAW BYTES for this glyph region
# The raw (swizzled) bytes corresponding to these pixels are NOT contiguous
# in the raw data. We need to find where each pixel maps in the swizzled data.
#
# Strategy: identify which bytes in the raw pixel data correspond to the
# 12x12 region at (120, 192). We do this by tracing the PSMT4 nibble addresses.

print("\n--- Finding raw byte positions for glyph pixels ---")
from psmt4_deswizzle import _psmct32_word_addr, _psmt4_nibble_addr

# For each pixel (x, y) in the glyph, find its position in the raw data
# The deswizzle process:
#   1. Raw data written to VRAM via PSMCT32 (dbw_ct32=256)
#   2. Read back via PSMT4 (bw_psmt4=256)
# To find which raw byte contains a given PSMT4 pixel:
#   - Find PSMT4 nibble address in VRAM for pixel (x, y)
#   - Find which PSMCT32 word contains that VRAM address
#   - Map back to host data offset

# Actually, a simpler approach: re-swizzle the full atlas and then find
# the byte ranges. But even simpler: just take the known raw pixel data
# and search for distinctive byte sequences.

# Let's identify the exact raw bytes that encode the glyph region.
# We can do this by modifying the glyph pixels and re-swizzling:
# 1. Create a copy of the linear pixels
# 2. Zero out everything EXCEPT the glyph region
# 3. Re-swizzle -> the non-zero bytes in the result are the glyph's raw bytes

pixels_lin_mask = bytearray(256 * 512)  # all zero
for dy in range(CELL_H):
    for dx in range(CELL_W):
        src_idx = (px_y + dy) * 256 + (px_x + dx)
        pixels_lin_mask[src_idx] = pixels_lin[src_idx]

# Re-swizzle
print("Re-swizzling masked pixels...")
swizzled_mask = swizzle_psmt4(pixels_lin_mask, 256, 512, bw_psmt4=256, dbw_ct32=256)

# Find non-zero byte ranges
nonzero_positions = [i for i in range(len(swizzled_mask)) if swizzled_mask[i] != 0]
if nonzero_positions:
    print(f"Non-zero bytes in swizzled mask: {len(nonzero_positions)} bytes")
    print(f"Range: 0x{min(nonzero_positions):X} - 0x{max(nonzero_positions):X}")

    # Group into contiguous ranges
    ranges = []
    start = nonzero_positions[0]
    prev = start
    for pos in nonzero_positions[1:]:
        if pos != prev + 1:
            ranges.append((start, prev))
            start = pos
        prev = pos
    ranges.append((start, prev))

    print(f"Contiguous ranges: {len(ranges)}")
    for r_start, r_end in ranges:
        length = r_end - r_start + 1
        raw_bytes = swizzled_mask[r_start:r_end + 1]
        print(f"  0x{r_start:05X}-0x{r_end:05X} ({length} bytes): {raw_bytes[:16].hex()}...")
else:
    print("WARNING: No non-zero bytes in swizzled mask!")

# Step 6: Also get the ACTUAL raw bytes from the original for these positions
# (the mask version has zeros where other glyphs' nibbles share the same byte)
print("\n--- Extracting actual raw bytes from original for glyph region ---")
actual_glyph_raw_chunks = []
for r_start, r_end in ranges:
    chunk = pixels_raw[r_start:r_end + 1]
    actual_glyph_raw_chunks.append((r_start, chunk))
    print(f"  0x{r_start:05X}-0x{r_end:05X}: {chunk[:32].hex()}")

# Step 7: Search the EXE
print("\n" + "=" * 70)
print("  SEARCHING EXE FOR GLYPH RAW BYTES")
print("=" * 70)

# Search for each contiguous chunk of raw bytes
for r_start, chunk in actual_glyph_raw_chunks:
    if len(chunk) < 4:
        continue
    # Search for this exact byte sequence
    search_len = min(len(chunk), 64)  # search with up to 64 bytes
    needle = bytes(chunk[:search_len])
    print(f"\nSearching for {search_len}-byte chunk from raw offset 0x{r_start:X}: {needle[:16].hex()}...")

    pos = 0
    found = False
    while True:
        idx = exe_data.find(needle, pos)
        if idx == -1:
            break
        found = True
        print(f"  FOUND at EXE offset 0x{idx:X} ({idx:,})")
        # Show context
        ctx_start = max(0, idx - 8)
        ctx_end = min(len(exe_data), idx + search_len + 8)
        print(f"  Context: ...{exe_data[ctx_start:idx].hex()} [{exe_data[idx:idx+search_len].hex()}] {exe_data[idx+search_len:ctx_end].hex()}...")
        pos = idx + 1
    if not found:
        # Try shorter sequences
        for try_len in [32, 16, 8]:
            if try_len >= len(chunk):
                continue
            needle_short = bytes(chunk[:try_len])
            idx = exe_data.find(needle_short)
            if idx != -1:
                print(f"  Found {try_len}-byte prefix at EXE offset 0x{idx:X}")
                break
        else:
            print(f"  NOT FOUND in EXE")

# Step 8: Search for first 64 bytes of raw pixel data
print("\n" + "=" * 70)
print("  SEARCHING EXE FOR FIRST 64 BYTES OF R1272 PIXEL DATA")
print("=" * 70)

needle64 = bytes(pixels_raw[:64])
print(f"First 64 bytes: {needle64.hex()}")

pos = 0
found_any = False
while True:
    idx = exe_data.find(needle64, pos)
    if idx == -1:
        break
    found_any = True
    print(f"  FOUND at EXE offset 0x{idx:X} ({idx:,})")
    pos = idx + 1

if not found_any:
    print("  NOT FOUND")
    # Try shorter prefixes
    for try_len in [32, 16, 8]:
        needle_short = bytes(pixels_raw[:try_len])
        idx = exe_data.find(needle_short)
        if idx != -1:
            print(f"  {try_len}-byte prefix found at EXE offset 0x{idx:X}")
            # Count total matches
            count = 0
            p = 0
            while True:
                i = exe_data.find(needle_short, p)
                if i == -1:
                    break
                count += 1
                p = i + 1
            print(f"    ({count} total matches for {try_len}-byte prefix)")
            break

# Step 9: Also search for larger chunks of raw pixel data from various offsets
print("\n" + "=" * 70)
print("  SEARCHING EXE FOR VARIOUS R1272 RAW PIXEL CHUNKS")
print("=" * 70)

# Search at various offsets in the pixel data to see if ANY of R1272 pixel data is in the EXE
for test_off in [0, 1024, 2048, 4096, 8192, 16384, 32768, 49152, 65536-64]:
    if test_off + 64 > len(pixels_raw):
        continue
    needle = bytes(pixels_raw[test_off:test_off + 64])
    idx = exe_data.find(needle)
    if idx != -1:
        print(f"  R1272 pixel offset 0x{test_off:X} (64 bytes) found at EXE 0x{idx:X}")

# Step 10: Search for the glyph's swizzled bytes using the ACTUAL original raw data
# (not the masked version)
print("\n" + "=" * 70)
print("  SEARCHING EXE FOR R1272 RAW DATA (BULK)")
print("=" * 70)

# Try searching the ENTIRE 65536-byte pixel blob in the EXE
idx = exe_data.find(pixels_raw)
if idx != -1:
    print(f"  ENTIRE R1272 pixel data (65536 bytes) found at EXE offset 0x{idx:X} !!!")
else:
    print("  Full 65536-byte pixel data NOT found in EXE")
    # Try progressively smaller chunks from the start
    for chunk_size in [8192, 4096, 2048, 1024, 512, 256, 128]:
        needle = bytes(pixels_raw[:chunk_size])
        idx = exe_data.find(needle)
        if idx != -1:
            print(f"  First {chunk_size} bytes of pixel data found at EXE 0x{idx:X}")
            break
    else:
        print("  No prefix of pixel data found in EXE (tried down to 128 bytes)")

# Step 11: Also try searching for the R1272 header
print("\n" + "=" * 70)
print("  SEARCHING EXE FOR R1272 HEADER")
print("=" * 70)

r1272_header = r1272_raw[:192]
# Skip sub-header, search for internal header
internal_header = r1272_raw[16:192]
needle = bytes(internal_header[:64])
print(f"Internal header first 64 bytes: {needle.hex()}")
idx = exe_data.find(needle)
if idx != -1:
    print(f"  Found at EXE offset 0x{idx:X}")
else:
    print("  NOT FOUND")

# Also search the sub-header pattern
sub_hdr_bytes = r1272_raw[:16]
print(f"Sub-header: {sub_hdr_bytes.hex()}")
idx = exe_data.find(sub_hdr_bytes)
if idx != -1:
    print(f"  Sub-header found at EXE offset 0x{idx:X}")
else:
    print("  Sub-header NOT FOUND")

print("\n" + "=" * 70)
print("  DONE")
print("=" * 70)
