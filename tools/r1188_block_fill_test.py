#!/usr/bin/env python3
"""
R1188 block fill test: fill stat label VRAM block areas with solid 0x00
to verify VRAM block addressing is correct.

If palette index 0 is dark/opaque, the stat label areas should appear as
solid dark rectangles - very visible proof that the addressing works.

Bypasses deswizzle/reswizzle entirely - writes directly to raw binary offsets
computed from VRAM block addresses.
"""
import struct
import os
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)

SECTOR = 2048
ISO_SRC = 'build/BUSIN0_EN_v37.iso'
ISO_DST = 'build/BUSIN0_EN_v37_stat_fill.iso'

# 13 stat label VRAM block addresses from EXE cell data
VRAM_BLOCKS = [
    0xA450, 0xA270, 0xA480, 0xA328, 0xA490, 0xA380, 0xA7E8,
    0xA758, 0xA3D0, 0xA7F0, 0xA410, 0xA7F8, 0xA800,
]

HEADER_SIZE = 0xC00  # 3072 bytes R1188 header

def find_packdata_in_iso(iso_fh):
    """Find PACKDATA.DIG LBA and size in the ISO."""
    iso_fh.seek(16 * SECTOR)
    pvd = iso_fh.read(SECTOR)
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]
    iso_fh.seek(root_lba * SECTOR)
    root_dir = iso_fh.read(root_size)
    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        if 'PACKDATA' in name:
            pack_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
            pack_size = struct.unpack_from('<I', root_dir, pos + 10)[0]
            return pack_lba, pack_size
        pos += rec_len
    raise RuntimeError("PACKDATA.DIG not found in ISO")

def find_r1188_in_packdata(iso_fh, pack_lba):
    """Read PACKDATA TOC entry 1188 to get sector offset and size."""
    # TOC is at start of PACKDATA, each entry is 12 bytes: (sector_offset, sector_count, type_code)
    toc_offset = pack_lba * SECTOR + 1188 * 12
    iso_fh.seek(toc_offset)
    sector_off, sector_count, type_code = struct.unpack('<III', iso_fh.read(12))
    return sector_off, sector_count, type_code

def vram_block_to_file_offset(vram_block):
    """Compute raw binary file offset from VRAM block address.
    Formula: (vram_block/4 - 0x2840) * 256 + 0xC10
    The 0xC10 = 0xC00 header + 0x10 alignment? Actually just header + pixel data offset.
    Wait - the formula given is: (vram_block/4 - 0x2840) * 256 + 0xC10
    """
    return (vram_block // 4 - 0x2840) * 256 + 0xC10

def main():
    if not os.path.exists(ISO_SRC):
        print(f"ERROR: Source ISO not found: {ISO_SRC}")
        return

    # Step 1: Copy ISO
    print(f"Copying {ISO_SRC} -> {ISO_DST}")
    shutil.copy2(ISO_SRC, ISO_DST)
    print(f"  Done ({os.path.getsize(ISO_DST):,} bytes)")

    with open(ISO_DST, 'r+b') as iso:
        # Step 2: Find R1188 in ISO
        pack_lba, pack_size = find_packdata_in_iso(iso)
        print(f"PACKDATA at LBA {pack_lba} (byte offset 0x{pack_lba * SECTOR:X}), size {pack_size:,}")

        r1188_sect_off, r1188_sect_count, r1188_type = find_r1188_in_packdata(iso, pack_lba)
        print(f"R1188: sector_offset={r1188_sect_off}, sectors={r1188_sect_count}, type={r1188_type}")

        # R1188 absolute byte offset in ISO
        r1188_iso_offset = (pack_lba + r1188_sect_off) * SECTOR
        r1188_size = r1188_sect_count * SECTOR
        print(f"R1188 ISO offset: 0x{r1188_iso_offset:X}, size: {r1188_size:,} bytes")

        # Read R1188 data
        iso.seek(r1188_iso_offset)
        r1188_data = bytearray(iso.read(r1188_size))
        print(f"Read {len(r1188_data):,} bytes of R1188")

        # Step 3: Fill VRAM block areas with 0x00
        print(f"\nFilling {len(VRAM_BLOCKS)} stat label VRAM blocks with 0x00:")
        for i, vb in enumerate(VRAM_BLOCKS):
            offset = vram_block_to_file_offset(vb)
            print(f"  Block {i:2d}: VRAM 0x{vb:04X} -> file offset 0x{offset:05X} "
                  f"(+256 -> 0x{offset+256:05X})")

            if offset < 0 or offset + 512 > len(r1188_data):
                print(f"    WARNING: offset out of range! (file size={len(r1188_data)})")
                continue

            # Write 256 bytes of 0x00 at the block offset (16x16 tile)
            r1188_data[offset:offset+256] = b'\x00' * 256
            # Write 256 bytes of 0x00 at offset+256 (next block, for larger cells)
            r1188_data[offset+256:offset+512] = b'\x00' * 256

        # Step 4: Write modified R1188 back to ISO
        print(f"\nWriting modified R1188 back to ISO at offset 0x{r1188_iso_offset:X}")
        iso.seek(r1188_iso_offset)
        iso.write(r1188_data)
        print("Done!")

    print(f"\nOutput: {ISO_DST}")
    print("Boot this ISO FRESH (no save states!) and check the chargen stat labels.")
    print("If they appear as dark rectangles, the VRAM block addressing is correct.")

if __name__ == '__main__':
    main()
