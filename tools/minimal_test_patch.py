#!/usr/bin/env python3
"""
minimal_test_patch.py -- Minimal single-byte ISO patch test
============================================================

Purpose: Bypass the entire build pipeline. Copy the original ISO, then
directly modify ONE glyph in resource R38 (the character-creation MSG
resource) to prove that direct ISO binary patching works.

What it does:
  1. Copies original ISO -> build/BUSIN0_EN_minimal_test.iso
  2. Opens the copy for in-place editing (r+b)
  3. Finds PACKDATA.DIG via the ISO9660 PVD -> root directory
  4. Reads R38 TOC entry from PACKDATA
  5. Navigates to R38's glyph stream
  6. Finds the first non-control glyph in the first real message
  7. Overwrites that single glyph with 'X' (glyph 56 = 0x0038 BE)
  8. Does NOT change any sizes, offsets, or the directory -- same bytes, same sectors

If the game shows "X" where the original Japanese character was, we know
the ISO binary layout is correct and the build pipeline is the problem.
If the original character still shows, something fundamental is wrong
with how the game loads data.
"""

import struct
import shutil
import os
import sys

SECTOR = 2048
TOC_ENTRIES = 2883
R38_INDEX = 38

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ISO_PATH = os.path.join(BASE, "Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso")
OUTPUT_ISO = os.path.join(BASE, "build", "BUSIN0_EN_minimal_test.iso")

GLYPH_X = 56  # 'X' in the game's glyph table -> 0x0038 BE


def find_packdata_in_iso(f):
    """Parse ISO9660 PVD -> root directory -> find PACKDATA.DIG extent and size."""
    # Read Primary Volume Descriptor at sector 16
    f.seek(16 * SECTOR)
    pvd = f.read(SECTOR)

    # Root directory record is at PVD offset 156, length 34
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]
    print(f"  Root directory: LBA={root_lba}, size={root_size}")

    # Read root directory
    f.seek(root_lba * SECTOR)
    root_dir = f.read(root_size)

    # Walk directory entries to find PACKDATA.DIG
    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        file_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
        file_size = struct.unpack_from('<I', root_dir, pos + 10)[0]
        print(f"  Dir entry: '{name}' LBA={file_lba} size={file_size:,}")
        if 'PACKDATA' in name:
            return file_lba, file_size, root_lba, pos
        pos += rec_len

    raise RuntimeError("PACKDATA.DIG not found in ISO root directory!")


def count_sequential_table(data, base=0):
    """Count 16-byte sequential-ID entries starting at `base`."""
    if len(data) - base < 16:
        return 0
    first4 = struct.unpack_from("<I", data, base)[0]
    if first4 != 1:
        return 0
    count = 0
    for e in range(256):
        off = base + e * 16
        if off + 16 > len(data):
            break
        entry_id = struct.unpack_from("<I", data, off)[0]
        if entry_id == e + 1:
            count = e + 1
        else:
            break
    return count


def main():
    print("=" * 60)
    print("  MINIMAL ISO PATCH TEST")
    print("  Changes exactly ONE glyph in R38 to 'X'")
    print("=" * 60)
    print()

    # Verify source ISO exists
    if not os.path.exists(ISO_PATH):
        print(f"ERROR: Source ISO not found: {ISO_PATH}")
        sys.exit(1)

    iso_size = os.path.getsize(ISO_PATH)
    print(f"Source ISO: {ISO_PATH}")
    print(f"  Size: {iso_size:,} bytes")

    # Step 1: Copy ISO
    print(f"\nStep 1: Copying ISO to {OUTPUT_ISO} ...")
    os.makedirs(os.path.dirname(OUTPUT_ISO), exist_ok=True)
    shutil.copy2(ISO_PATH, OUTPUT_ISO)
    print(f"  Done. Copy size: {os.path.getsize(OUTPUT_ISO):,} bytes")

    # Step 2-7: Open copy and patch ONE glyph
    print(f"\nStep 2: Opening ISO for in-place editing ...")
    with open(OUTPUT_ISO, "r+b") as f:
        # Find PACKDATA.DIG
        print("\nStep 3: Finding PACKDATA.DIG in ISO ...")
        pack_lba, pack_size, root_lba, pack_dir_pos = find_packdata_in_iso(f)
        pack_offset = pack_lba * SECTOR
        print(f"  PACKDATA.DIG: LBA={pack_lba}, byte offset={pack_offset:,}, size={pack_size:,}")

        # Read R38 TOC entry
        print(f"\nStep 4: Reading R38 TOC entry ...")
        toc_offset = pack_offset + R38_INDEX * 12
        f.seek(toc_offset)
        toc_entry = f.read(12)
        r38_so, r38_sc, r38_tc = struct.unpack('<III', toc_entry)
        print(f"  R38: sector_offset=0x{r38_so:X} ({r38_so}), sector_count={r38_sc}, type_code={r38_tc}")

        # Read R38 data
        r38_abs_offset = pack_offset + r38_so * SECTOR
        r38_raw_size = r38_sc * SECTOR
        print(f"  R38 absolute offset in ISO: 0x{r38_abs_offset:X} ({r38_abs_offset:,})")

        f.seek(r38_abs_offset)
        r38_raw = f.read(r38_raw_size)

        # Parse sub-header
        print(f"\nStep 5: Parsing R38 sub-header ...")
        h_zero1, h_payload_size, h_stride, h_zero2 = struct.unpack_from('<IIII', r38_raw, 0)
        print(f"  zero1={h_zero1}, payload_size={h_payload_size}, stride={h_stride}, zero2={h_zero2}")

        payload = r38_raw[16:16 + h_payload_size]

        # Find sequential table
        seq_count = count_sequential_table(payload)
        seq_table_size = seq_count * 16
        print(f"  Sequential table: {seq_count} entries ({seq_table_size} bytes)")

        # Find the glyph stream (after seq table, find first FFFF)
        glyph_region = payload[seq_table_size:]
        print(f"  Glyph region: {len(glyph_region)} bytes starting at payload offset {seq_table_size}")

        # Find first FFFF in glyph region (message delimiter)
        first_ffff = None
        for off in range(0, len(glyph_region) - 1, 2):
            val = struct.unpack_from(">H", glyph_region, off)[0]
            if val == 0xFFFF:
                first_ffff = off
                break

        if first_ffff is None:
            print("ERROR: Could not find any FFFF delimiter in glyph region!")
            sys.exit(1)

        print(f"  First FFFF at glyph region offset: {first_ffff}")

        # Now find the first JAPANESE glyph (ID >= 95, not a control code)
        # We need a glyph that is visually obviously Japanese so we can
        # confirm the patch works when it shows 'X' instead.
        stream_start = first_ffff + 2
        print(f"\nStep 6: Finding first Japanese glyph in R38 messages ...")
        print(f"  Scanning from glyph region offset {stream_start} ...")

        target_offset = None
        target_old_glyph = None
        msg_num = 0

        for off in range(stream_start, len(glyph_region) - 1, 2):
            val = struct.unpack_from(">H", glyph_region, off)[0]
            if val == 0xFFFF:
                msg_num += 1
                continue
            if val >= 0xFF00:
                # Control code, skip
                continue
            # We want a Japanese glyph (ID >= 95) for a visible test
            if val >= 95:
                target_offset = off
                target_old_glyph = val
                print(f"  Found Japanese glyph in message {msg_num}")
                break

        if target_offset is None:
            print("ERROR: Could not find any non-control glyph in R38!")
            sys.exit(1)

        # Compute the absolute ISO file offset of this glyph
        # r38_abs_offset + 16 (sub-header) + seq_table_size + target_offset
        iso_glyph_offset = r38_abs_offset + 16 + seq_table_size + target_offset

        print(f"  Found glyph at glyph region offset {target_offset}")
        print(f"  Old glyph value: {target_old_glyph} (0x{target_old_glyph:04X})")
        print(f"  New glyph value: {GLYPH_X} (0x{GLYPH_X:04X}) = 'X'")
        print(f"  ISO file offset: 0x{iso_glyph_offset:X} ({iso_glyph_offset:,})")

        # Also decode what the old glyph is
        if 0 <= target_old_glyph <= 94:
            old_char = chr(target_old_glyph + 0x20)
            print(f"  Old glyph decodes to ASCII: '{old_char}'")
        else:
            print(f"  Old glyph is Japanese/special (ID >= 95)")

        # Verify by reading the byte at that offset
        f.seek(iso_glyph_offset)
        verify_bytes = f.read(2)
        verify_val = struct.unpack(">H", verify_bytes)[0]
        print(f"  Verification read at ISO offset: 0x{verify_val:04X} (expect 0x{target_old_glyph:04X})")
        assert verify_val == target_old_glyph, \
            f"Verification FAILED: read 0x{verify_val:04X} != expected 0x{target_old_glyph:04X}"

        # Step 7: Write the new glyph
        print(f"\nStep 7: Writing glyph 0x{GLYPH_X:04X} ('X') at ISO offset 0x{iso_glyph_offset:X} ...")
        f.seek(iso_glyph_offset)
        f.write(struct.pack(">H", GLYPH_X))

        # Verify the write
        f.seek(iso_glyph_offset)
        written = f.read(2)
        written_val = struct.unpack(">H", written)[0]
        assert written_val == GLYPH_X, \
            f"Write verification FAILED: read 0x{written_val:04X} != expected 0x{GLYPH_X:04X}"
        print(f"  Write verified: 0x{written_val:04X}")

        # NO size updates needed -- we changed exactly 2 bytes in-place, same sector count
        print(f"\n  NOTE: No directory size update needed.")
        print(f"  We changed 2 bytes in-place. Same file size, same sector count.")

    # Final verification: confirm ISO size unchanged
    final_size = os.path.getsize(OUTPUT_ISO)
    assert final_size == iso_size, f"ISO size changed! {iso_size} -> {final_size}"

    print(f"\n{'=' * 60}")
    print(f"  PATCH COMPLETE")
    print(f"  Output: {OUTPUT_ISO}")
    print(f"  Size: {final_size:,} bytes (unchanged)")
    print(f"  Changed: glyph {target_old_glyph} (0x{target_old_glyph:04X}) -> {GLYPH_X} (0x{GLYPH_X:04X}, 'X')")
    print(f"  At ISO offset: 0x{iso_glyph_offset:X}")
    print(f"{'=' * 60}")
    print()
    print("TEST PROTOCOL:")
    print("  1. Load build/BUSIN0_EN_minimal_test.iso in PCSX2")
    print("  2. Go to character creation screen")
    print("  3. Look for an 'X' where a Japanese character should be")
    print("  4. If 'X' appears: pipeline is the problem, ISO patching works")
    print("  5. If original JP char appears: game loads data differently")


if __name__ == "__main__":
    main()
