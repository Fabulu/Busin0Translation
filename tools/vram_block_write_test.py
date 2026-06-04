#!/usr/bin/env python3
"""
VRAM Block Write Test: Bypass deswizzle/reswizzle and write directly to raw R1188 bytes.

Goal: Determine the correct formula mapping cell VRAM addresses to file byte offsets.

R1188 file layout:
  - Header: 0xC00 bytes (3072 bytes)
  - Pixel data: 0x80000 bytes (524,288 bytes) -- PSMCT32 upload format
  - Padding: 0x400 bytes (1024 bytes) to sector boundary
  Total: 528,384 bytes (258 sectors)

R1188 is uploaded to VRAM starting at TBP0 = 0x2840 (in 256-byte blocks).

Test target: Glyph 346 (STR / chikara), cell_vram = 0xA450

We test multiple formulas for converting cell_vram -> file byte offset, fill 512 bytes
with 0xAA at the computed offset, then build a test ISO.
"""

import struct, os, shutil

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048
HEADER_SIZE = 0xC00  # 3072 bytes
PIXEL_SIZE = 0x80000  # 524,288 bytes
R1188_TBP0 = 0x2840  # VRAM block address where R1188 pixel data starts

SRC_R1188 = 'extracted/packdata_raw/1188_type01.raw'
SRC_ISO = 'build/BUSIN0_EN_v37.iso'

# Cell data for glyph 346 (STR = chikara/power)
CELL_VRAM = 0xA450

# Also test a second glyph for comparison
# Glyph 535 (INT-1 = chi/wisdom), cell_vram = 0xA1F0
CELL_VRAM_2 = 0xA1F0

print("=" * 70)
print("VRAM Block Address -> File Offset Formula Comparison")
print("=" * 70)

# ---- Formula A: cell_vram/4 gives TBP0, subtract R1188 base, * 256 ----
def formula_a(cell_vram):
    """cell_vram is 4x TBP0 units; TBP0 = cell_vram/4; offset = (TBP0 - base) * 256"""
    tbp0 = cell_vram // 4
    offset_blocks = tbp0 - R1188_TBP0
    byte_offset = offset_blocks * 256
    return byte_offset

# ---- Formula B: cell_vram is in 64-byte units relative to some base ----
def formula_b(cell_vram):
    """cell_vram is in 64-byte units; base = 0xA100 (common starting point)"""
    base = 0xA100
    byte_offset = (cell_vram - base) * 64
    return byte_offset

# ---- Formula C: cell_vram is in 256-byte units (= TBP0 units) directly ----
def formula_c(cell_vram):
    """cell_vram IS a TBP0 value; offset = (cell_vram - R1188_TBP0) * 256"""
    byte_offset = (cell_vram - R1188_TBP0) * 256
    return byte_offset

# ---- Formula D: cell_vram * 4 = byte address in VRAM, subtract R1188 base ----
def formula_d(cell_vram):
    """cell_vram * 4 = linear VRAM byte address; base = R1188_TBP0 * 256"""
    vram_byte = cell_vram * 4
    base_byte = R1188_TBP0 * 256
    return vram_byte - base_byte

# ---- Formula E: cell_vram in 64-byte units, R1188 base also in 64-byte units ----
def formula_e(cell_vram):
    """cell_vram and R1188_TBP0*4 are both in 64-byte units"""
    r1188_base_64 = R1188_TBP0 * 4  # 0xA100
    byte_offset = (cell_vram - r1188_base_64) * 64
    return byte_offset

formulas = {
    'A: (vram/4 - 0x2840) * 256': formula_a,
    'B: (vram - 0xA100) * 64': formula_b,
    'C: (vram - 0x2840) * 256': formula_c,
    'D: vram*4 - 0x2840*256': formula_d,
    'E: (vram - 0x2840*4) * 64': formula_e,
}

print(f"\nR1188 TBP0 = 0x{R1188_TBP0:04X}")
print(f"R1188 TBP0 * 4 = 0x{R1188_TBP0 * 4:04X}")
print(f"Pixel data range: 0 to {PIXEL_SIZE - 1} (0x{PIXEL_SIZE - 1:X})")
print(f"File offset range: 0x{HEADER_SIZE:X} to 0x{HEADER_SIZE + PIXEL_SIZE - 1:X}")
print()

valid_formulas = {}

for test_vram, test_name in [(CELL_VRAM, "Glyph 346 (STR)"), (CELL_VRAM_2, "Glyph 535 (INT)")]:
    print(f"--- {test_name}: cell_vram = 0x{test_vram:04X} ---")
    for name, fn in formulas.items():
        pixel_offset = fn(test_vram)
        file_offset = HEADER_SIZE + pixel_offset
        in_range = 0 <= pixel_offset < PIXEL_SIZE
        marker = " <-- VALID" if in_range else " OUT OF RANGE"
        print(f"  {name}")
        print(f"    pixel_offset = {pixel_offset:>10} (0x{pixel_offset:08X})")
        print(f"    file_offset  = {file_offset:>10} (0x{file_offset:08X}){marker}")
        if in_range:
            valid_formulas.setdefault(name, []).append(test_vram)
    print()

print("=" * 70)
print("VALID FORMULAS (offset within pixel data for both test glyphs):")
for name in valid_formulas:
    if len(valid_formulas[name]) == 2:
        print(f"  {name}")
print("=" * 70)

# ---- Read original R1188 and dump bytes at each valid formula's offset ----
print("\nReading original R1188...")
orig_data = bytearray(open(SRC_R1188, 'rb').read())
print(f"  Size: {len(orig_data)} bytes")
print()

# Show hex dumps at each valid offset for glyph 346
print("Hex dump at each valid formula offset for glyph 346 (cell_vram=0xA450):")
print("(These should be non-zero if the formula is correct -- kanji pixels)")
print()

for name, fn in formulas.items():
    pixel_offset = fn(CELL_VRAM)
    if 0 <= pixel_offset < PIXEL_SIZE:
        file_offset = HEADER_SIZE + pixel_offset
        chunk = orig_data[file_offset:file_offset + 512]
        nonzero = sum(1 for b in chunk if b != 0)
        print(f"  {name}")
        print(f"    File offset 0x{file_offset:06X}, first 64 bytes:")
        print(f"    {chunk[:64].hex()}")
        print(f"    Non-zero bytes in 512-byte block: {nonzero}/512")
        print()

# ---- Create test files with 0xAA fill at EACH valid formula's offset ----
# We'll use ALL valid formulas and write separate test ISOs

# First, check which formulas are valid for BOTH glyphs
both_valid = [name for name, vrams in valid_formulas.items() if len(vrams) == 2]

if not both_valid:
    print("ERROR: No formula is valid for both test glyphs!")
    # Fall back to any valid for glyph 346
    both_valid = [name for name, vrams in valid_formulas.items() if CELL_VRAM in vrams]

# ---- Find R1188 position in PACKDATA TOC for direct ISO injection ----
print("Finding R1188 in PACKDATA TOC...")
with open('extracted/PACKDATA.DIG', 'rb') as f:
    f.seek(1188 * 12)
    r1188_sector, r1188_sectors, r1188_tc = struct.unpack('<III', f.read(12))
print(f"  R1188: sector {r1188_sector}, {r1188_sectors} sectors, type {r1188_tc}")

# Find PACKDATA.DIG position in ISO
print("Finding PACKDATA.DIG in ISO...")
with open(SRC_ISO, 'rb') as f:
    f.seek(16 * SECTOR)
    pvd = f.read(SECTOR)
    root_rec = pvd[156:156 + 34]
    root_extent = struct.unpack_from('<I', root_rec, 2)[0]
    root_size = struct.unpack_from('<I', root_rec, 10)[0]
    f.seek(root_extent * SECTOR)
    root_data = f.read(root_size)

packdata_extent = None
pos = 0
while pos < len(root_data):
    rec_len = root_data[pos]
    if rec_len == 0:
        break
    name_len = root_data[pos + 32]
    name = root_data[pos + 33: pos + 33 + name_len]
    if b'PACKDATA' in name:
        packdata_extent = struct.unpack_from('<I', root_data, pos + 2)[0]
        break
    pos += rec_len

if packdata_extent is None:
    print("ERROR: Could not find PACKDATA.DIG in ISO!")
    exit(1)

print(f"  PACKDATA.DIG at ISO sector {packdata_extent}")
r1188_iso_byte_offset = (packdata_extent + r1188_sector) * SECTOR
print(f"  R1188 at ISO byte offset {r1188_iso_byte_offset} (0x{r1188_iso_byte_offset:X})")

# ---- Build test ISOs ----
# For each valid formula, create a modified R1188 with 0xAA at the glyph 346 offset,
# then inject it into a copy of the v37 ISO.

# We'll fill ALL 13 stat label glyph positions with 0xAA for the winning formulas
ALL_STAT_GLYPHS = [
    ("STR",   346, 0xA450),
    ("INT-1", 535, 0xA1F0),
    ("INT-2", 717, 0xA700),
    ("PIE-1", 308, 0xA238),
    ("PIE-2", 354, 0xA390),
    ("PIE-3", 320, 0xA290),
    ("VIT-1", 718, 0xA708),
    ("VIT-2", 696, 0xA658),
    ("AGI-1", 582, 0xA2E0),
    ("AGI-2", 719, 0xA710),
    ("AGI-3", 590, 0xA318),
    ("LCK-1", 720, 0xA718),
    ("LCK-2", 721, 0xA720),
]

for formula_name in both_valid:
    fn = formulas[formula_name]
    short_name = formula_name.split(':')[0].strip()
    iso_out = f'build/BUSIN0_EN_v37_vram_test_{short_name}.iso'

    print(f"\n{'=' * 70}")
    print(f"Building test ISO for formula {formula_name}")
    print(f"Output: {iso_out}")
    print(f"{'=' * 70}")

    # Create modified R1188
    mod_data = bytearray(orig_data)

    all_in_range = True
    for label, glyph_id, vram_addr in ALL_STAT_GLYPHS:
        pixel_offset = fn(vram_addr)
        file_offset = HEADER_SIZE + pixel_offset
        if 0 <= pixel_offset < PIXEL_SIZE - 512:
            # Read original bytes for diagnostic
            orig_bytes = mod_data[file_offset:file_offset + 512]
            nonzero = sum(1 for b in orig_bytes if b != 0)
            print(f"  {label} (glyph {glyph_id}): vram=0x{vram_addr:04X} -> "
                  f"file_offset=0x{file_offset:06X}, orig non-zero: {nonzero}/512")
            # Fill with 0xAA
            mod_data[file_offset:file_offset + 512] = b'\xAA' * 512
        else:
            print(f"  {label} (glyph {glyph_id}): OUT OF RANGE (pixel_offset=0x{pixel_offset:X})")
            all_in_range = False

    if not all_in_range:
        print(f"  SKIPPING ISO build -- some glyphs out of range")
        continue

    # Copy ISO and inject modified R1188
    print(f"  Copying {SRC_ISO} -> {iso_out}...")
    shutil.copy2(SRC_ISO, iso_out)

    print(f"  Writing modified R1188 at ISO offset 0x{r1188_iso_byte_offset:X}...")
    with open(iso_out, 'r+b') as f:
        f.seek(r1188_iso_byte_offset)
        f.write(bytes(mod_data))

    print(f"  Done! ISO: {iso_out}")
    print(f"  Size: {os.path.getsize(iso_out):,} bytes")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print("""
Instructions:
1. Boot each test ISO FRESH from title screen in PCSX2
2. Navigate to character creation screen
3. Look at stat labels (STR/INT/PIE/VIT/AGI/LCK area)
4. If stat labels show noise/artifacts -> that formula is CORRECT
5. If stat labels unchanged -> that formula is WRONG
""")
