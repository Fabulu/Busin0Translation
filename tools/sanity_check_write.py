#!/usr/bin/env python3
"""
Sanity check: zero the first half of R1188 pixel data in a fresh ISO copy,
then VERIFY the write actually landed at the correct bytes.
"""
import struct
import os
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)

SECTOR = 2048
ORIGINAL_ISO = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
SANITY_ISO = 'build/BUSIN0_EN_sanity_check.iso'
HEADER_SIZE = 0xC00   # 3072 bytes
PIXEL_START = 0xC10   # pixel data starts at 0xC10 (header + 0x10 alignment)
NUKE_SIZE = 262144    # 256 KB = first half of pixel data


def find_packdata_in_iso(fh):
    """Parse ISO PVD at sector 16 to find PACKDATA.DIG directory entry."""
    fh.seek(16 * SECTOR)
    pvd = fh.read(SECTOR)

    # Print PVD signature
    sig = pvd[1:6]
    print(f"  PVD signature: {sig}")

    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]
    print(f"  Root directory: LBA={root_lba}, size={root_size}")

    fh.seek(root_lba * SECTOR)
    root_dir = fh.read(root_size)

    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        file_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
        file_size = struct.unpack_from('<I', root_dir, pos + 10)[0]
        if 'PACKDATA' in name:
            print(f"  Found: {name} -> LBA={file_lba}, size={file_size:,} bytes")
            return file_lba, file_size
        pos += rec_len
    raise RuntimeError("PACKDATA.DIG not found in ISO root directory")


def find_r1188_toc(fh, pack_lba):
    """Read TOC entry 1188 from PACKDATA."""
    toc_offset = pack_lba * SECTOR + 1188 * 12
    fh.seek(toc_offset)
    sector_off, sector_count, type_code = struct.unpack('<III', fh.read(12))
    return sector_off, sector_count, type_code


def main():
    print("=" * 70)
    print("R1188 WRITE SANITY CHECK")
    print("=" * 70)

    if not os.path.exists(ORIGINAL_ISO):
        print(f"ERROR: Original ISO not found: {ORIGINAL_ISO}")
        return

    # ---- Step 1: Copy original ISO ----
    print(f"\n[1] Copying original ISO -> {SANITY_ISO}")
    shutil.copy2(ORIGINAL_ISO, SANITY_ISO)
    iso_size = os.path.getsize(SANITY_ISO)
    print(f"  ISO size: {iso_size:,} bytes ({iso_size / (1024*1024):.1f} MB)")

    # ---- Step 4 (first): Find PACKDATA from PVD ----
    print(f"\n[4] Reading ISO PVD to find PACKDATA.DIG...")
    with open(SANITY_ISO, 'rb') as fh:
        pack_lba, pack_size = find_packdata_in_iso(fh)

    pack_byte_offset = pack_lba * SECTOR
    pack_end = pack_byte_offset + pack_size
    print(f"  PACKDATA byte range: 0x{pack_byte_offset:X} - 0x{pack_end:X}")
    print(f"  PACKDATA LBA: {pack_lba} (expected ~16029)")

    # ---- Read R1188 TOC ----
    print(f"\n[TOC] Reading PACKDATA TOC entry 1188...")
    with open(SANITY_ISO, 'rb') as fh:
        r1188_sect, r1188_count, r1188_type = find_r1188_toc(fh, pack_lba)
    print(f"  R1188: sector_offset={r1188_sect}, sector_count={r1188_count}, type={r1188_type}")

    r1188_abs_offset = (pack_lba + r1188_sect) * SECTOR
    r1188_total_size = r1188_count * SECTOR
    print(f"  R1188 absolute ISO offset: 0x{r1188_abs_offset:X} ({r1188_abs_offset:,})")
    print(f"  R1188 total size: {r1188_total_size:,} bytes")

    # ---- Step 5: Verify write offset is within PACKDATA ----
    write_offset = r1188_abs_offset + PIXEL_START
    write_end = write_offset + NUKE_SIZE
    print(f"\n[5] Write location analysis:")
    print(f"  Write offset:   0x{write_offset:X} ({write_offset:,})")
    print(f"  Write end:      0x{write_end:X} ({write_end:,})")
    print(f"  PACKDATA start: 0x{pack_byte_offset:X} ({pack_byte_offset:,})")
    print(f"  PACKDATA end:   0x{pack_end:X} ({pack_end:,})")
    print(f"  ISO size:       0x{iso_size:X} ({iso_size:,})")

    if write_offset >= pack_byte_offset and write_end <= pack_end:
        print(f"  -> GOOD: Write is within PACKDATA region")
    else:
        print(f"  -> BAD: Write is OUTSIDE PACKDATA region!")

    if write_end <= iso_size:
        print(f"  -> GOOD: Write is within ISO file")
    else:
        print(f"  -> BAD: Write extends BEYOND ISO file!")

    # ---- Step 3: Read R1188 header BEFORE nuking ----
    print(f"\n[3] Reading R1188 header (before nuke)...")
    with open(SANITY_ISO, 'rb') as fh:
        fh.seek(r1188_abs_offset)
        header_bytes = fh.read(64)
        print(f"  R1188 header first 64 bytes:")
        for i in range(0, 64, 16):
            hex_str = ' '.join(f'{b:02X}' for b in header_bytes[i:i+16])
            print(f"    +0x{i:03X}: {hex_str}")

    # ---- Read original data at nuke zone BEFORE write ----
    print(f"\n[PRE] Reading 64 bytes at pixel data start BEFORE nuke (offset 0x{write_offset:X})...")
    with open(SANITY_ISO, 'rb') as fh:
        fh.seek(write_offset)
        pre_data = fh.read(64)
        hex_str = ' '.join(f'{b:02X}' for b in pre_data[:32])
        print(f"  First 32 bytes: {hex_str}")
        non_zero = sum(1 for b in pre_data if b != 0)
        print(f"  Non-zero bytes: {non_zero}/64")

    # ---- Step 1 continued: NUKE first half of pixel data ----
    print(f"\n[NUKE] Writing {NUKE_SIZE:,} zero bytes at offset 0x{write_offset:X}...")
    with open(SANITY_ISO, 'r+b') as fh:
        fh.seek(write_offset)
        fh.write(b'\x00' * NUKE_SIZE)
        fh.flush()
    print(f"  Write complete.")

    # ---- Step 2: VERIFY the write ----
    print(f"\n[2] VERIFICATION - Re-reading ISO to confirm write...")
    with open(SANITY_ISO, 'rb') as fh:
        # Read 64 bytes at write start - should be ALL zeros
        fh.seek(write_offset)
        verify_zeroed = fh.read(64)
        all_zero = all(b == 0 for b in verify_zeroed)
        hex_str = ' '.join(f'{b:02X}' for b in verify_zeroed[:32])
        print(f"  At write start (0x{write_offset:X}):")
        print(f"    First 32 bytes: {hex_str}")
        print(f"    All zeros: {all_zero} {'PASS' if all_zero else 'FAIL!!!'}")

        # Read 64 bytes just past the nuke zone - should be NON-zero
        past_nuke = write_offset + NUKE_SIZE
        fh.seek(past_nuke)
        verify_nonzero = fh.read(64)
        has_nonzero = any(b != 0 for b in verify_nonzero)
        hex_str = ' '.join(f'{b:02X}' for b in verify_nonzero[:32])
        print(f"\n  Just past nuke zone (0x{past_nuke:X}):")
        print(f"    First 32 bytes: {hex_str}")
        non_zero_count = sum(1 for b in verify_nonzero if b != 0)
        print(f"    Non-zero bytes: {non_zero_count}/64 {'PASS' if has_nonzero else 'FAIL - also zeroed!'}")

        # Read header again - should NOT be zeroed
        fh.seek(r1188_abs_offset)
        verify_header = fh.read(64)
        header_intact = any(b != 0 for b in verify_header)
        hex_str = ' '.join(f'{b:02X}' for b in verify_header[:32])
        print(f"\n  R1188 header (0x{r1188_abs_offset:X}):")
        print(f"    First 32 bytes: {hex_str}")
        print(f"    Header intact (non-zero): {header_intact} {'PASS' if header_intact else 'FAIL - header nuked!'}")

    # ---- Summary ----
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(f"  PACKDATA LBA:        {pack_lba}")
    print(f"  R1188 sector offset: {r1188_sect}")
    print(f"  R1188 ISO offset:    0x{r1188_abs_offset:X}")
    print(f"  Pixel data offset:   0x{write_offset:X}")
    print(f"  Nuked bytes:         {NUKE_SIZE:,}")
    print(f"  Write verified:      {'YES' if all_zero else 'NO'}")
    print(f"  Past-nuke non-zero:  {'YES' if has_nonzero else 'NO'}")
    print(f"  Header preserved:    {'YES' if header_intact else 'NO'}")
    print(f"\nOutput ISO: {SANITY_ISO}")
    print("Boot FRESH from title screen (NO save states!) to test.")


if __name__ == '__main__':
    main()
