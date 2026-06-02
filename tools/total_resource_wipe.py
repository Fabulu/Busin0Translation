"""
Brute-force test: zero ALL PACKDATA resources EXCEPT R1272 (dialogue font).
Keep the 125-sector header (TOC + R2100 + R1370) intact.

If stat labels still show kanji after this, kanji must come from:
  - R2100, R1370 (in header), or
  - The EXE itself / runtime generation

Output: build/TEST_everything_but_header.iso
"""

import struct, os, shutil

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048
PACKDATA_LBA = 16029  # LBA of PACKDATA.DIG on disc
HEADER_SECTORS = 125  # TOC + R2100 + R1370

# Source ISO (original)
ORIG_ISO = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
OUT_ISO = 'build/TEST_everything_but_header.iso'

# Step 1: Read TOC to find R1272
print("Reading TOC from original PACKDATA...")
with open('extracted/PACKDATA.DIG', 'rb') as f:
    toc = []
    for i in range(2883):
        data = f.read(12)
        so, sc, tc = struct.unpack('<III', data)
        toc.append((so, sc, tc))

r1272_so, r1272_sc, r1272_tc = toc[1272]
print(f"R1272: sector_offset={r1272_so}, sector_count={r1272_sc}")

# Find total PACKDATA size
max_end = max(so + sc for so, sc, tc in toc)
print(f"PACKDATA total sectors: {max_end}")

# Step 2: Copy original ISO
print(f"Copying {ORIG_ISO} -> {OUT_ISO}...")
shutil.copy2(ORIG_ISO, OUT_ISO)

# Step 3: Zero everything from sector 125 to end of PACKDATA, EXCEPT R1272
print("Zeroing all resources (sectors 125 onwards) except R1272...")

with open(OUT_ISO, 'r+b') as f:
    packdata_byte_offset = PACKDATA_LBA * SECTOR

    # Zero from sector 125 to R1272 start
    zero_start = HEADER_SECTORS
    zero_end = r1272_so
    if zero_end > zero_start:
        count = zero_end - zero_start
        f.seek(packdata_byte_offset + zero_start * SECTOR)
        # Write in chunks to avoid huge memory allocation
        CHUNK = 1024  # sectors per chunk
        remaining = count
        while remaining > 0:
            n = min(CHUNK, remaining)
            f.write(b'\x00' * (n * SECTOR))
            remaining -= n
        print(f"  Zeroed sectors {zero_start}-{zero_end-1} ({count} sectors)")

    # Skip R1272 (sectors r1272_so to r1272_so+r1272_sc-1)
    print(f"  Preserving R1272: sectors {r1272_so}-{r1272_so+r1272_sc-1}")

    # Zero from after R1272 to end
    zero_start2 = r1272_so + r1272_sc
    zero_end2 = max_end
    if zero_end2 > zero_start2:
        count2 = zero_end2 - zero_start2
        f.seek(packdata_byte_offset + zero_start2 * SECTOR)
        remaining = count2
        while remaining > 0:
            n = min(CHUNK, remaining)
            f.write(b'\x00' * (n * SECTOR))
            remaining -= n
        print(f"  Zeroed sectors {zero_start2}-{zero_end2-1} ({count2} sectors)")

total_zeroed = (zero_end - HEADER_SECTORS) + (zero_end2 - zero_start2)
total_preserved = r1272_sc
print(f"\nTotal zeroed: {total_zeroed} sectors ({total_zeroed*SECTOR/1024/1024:.1f} MB)")
print(f"Total preserved: header={HEADER_SECTORS} sectors + R1272={total_preserved} sectors")
print(f"Output: {OUT_ISO}")
print("Done!")
