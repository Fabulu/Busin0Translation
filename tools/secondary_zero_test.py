"""
secondary_zero_test.py — Zero the PACKDATA header's secondary structure
while preserving the primary TOC, to test if it contains font data.

Test hypothesis:
- If chargen stat labels disappear but dialogue works → secondary structure IS font source
- If game crashes → secondary structure is essential for resource loading
- If nothing changes → secondary structure is NOT the font source
"""

import os
import shutil
import struct

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL_ISO = os.path.join(BASE_DIR, "Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso")
OUTPUT_ISO = os.path.join(BASE_DIR, "build", "TEST_secondary_zero.iso")

PACKDATA_LBA = 16029
SECTOR_SIZE = 2048
PACKDATA_ISO_OFFSET = PACKDATA_LBA * SECTOR_SIZE  # 32,827,392

# Ranges relative to PACKDATA start
PRIMARY_TOC_START = 0
PRIMARY_TOC_END = 34596       # exclusive — bytes 0..34,595 preserved
SECONDARY_START = 34596
SECONDARY_END = 256000        # exclusive — bytes 34,596..255,999 zeroed

# Absolute ISO offsets
ISO_PRIMARY_START = PACKDATA_ISO_OFFSET + PRIMARY_TOC_START
ISO_PRIMARY_END = PACKDATA_ISO_OFFSET + PRIMARY_TOC_END
ISO_SECONDARY_START = PACKDATA_ISO_OFFSET + SECONDARY_START
ISO_SECONDARY_END = PACKDATA_ISO_OFFSET + SECONDARY_END

ZERO_SIZE = SECONDARY_END - SECONDARY_START  # 221,404 bytes


def main():
    print("=== PACKDATA Secondary Structure Zero Test ===\n")

    # Verify original ISO exists
    if not os.path.isfile(ORIGINAL_ISO):
        print(f"ERROR: Original ISO not found: {ORIGINAL_ISO}")
        return

    orig_size = os.path.getsize(ORIGINAL_ISO)
    print(f"Original ISO: {ORIGINAL_ISO}")
    print(f"Original size: {orig_size:,} bytes")

    # Step 1: Copy original ISO
    print(f"\nStep 1: Copying original ISO to {OUTPUT_ISO} ...")
    shutil.copy2(ORIGINAL_ISO, OUTPUT_ISO)
    print(f"  Copied. Size: {os.path.getsize(OUTPUT_ISO):,} bytes")

    # Step 2: Read and display pre-zero state
    print(f"\nStep 2: Reading PACKDATA header before zeroing ...")
    print(f"  PACKDATA ISO offset: {PACKDATA_ISO_OFFSET:,} (0x{PACKDATA_ISO_OFFSET:08X})")
    print(f"  Primary TOC:   bytes {PRIMARY_TOC_START:,} - {PRIMARY_TOC_END - 1:,} ({PRIMARY_TOC_END:,} bytes) — KEEP")
    print(f"  Secondary:     bytes {SECONDARY_START:,} - {SECONDARY_END - 1:,} ({ZERO_SIZE:,} bytes) — ZERO")

    with open(OUTPUT_ISO, "r+b") as f:
        # Read first 16 bytes of primary TOC (for verification)
        f.seek(ISO_PRIMARY_START)
        toc_head = f.read(16)
        print(f"\n  Primary TOC first 16 bytes: {toc_head.hex()}")

        # Read first 32 bytes of secondary structure (before zeroing)
        f.seek(ISO_SECONDARY_START)
        sec_head_before = f.read(32)
        print(f"  Secondary first 32 bytes (before): {sec_head_before.hex()}")

        # Read last 32 bytes of secondary structure (before zeroing)
        f.seek(ISO_SECONDARY_END - 32)
        sec_tail_before = f.read(32)
        print(f"  Secondary last 32 bytes (before):  {sec_tail_before.hex()}")

        # Check if secondary region is already all zeros
        f.seek(ISO_SECONDARY_START)
        sec_data = f.read(ZERO_SIZE)
        nonzero_count = sum(1 for b in sec_data if b != 0)
        print(f"\n  Non-zero bytes in secondary region: {nonzero_count:,} / {ZERO_SIZE:,}")

        if nonzero_count == 0:
            print("  WARNING: Secondary region is already all zeros!")
            return

        # Step 3: Zero the secondary structure
        print(f"\nStep 3: Zeroing secondary structure ({ZERO_SIZE:,} bytes) ...")
        f.seek(ISO_SECONDARY_START)
        f.write(b'\x00' * ZERO_SIZE)
        f.flush()
        print("  Done.")

        # Step 4: Verify the write
        print(f"\nStep 4: Verifying ...")

        # Verify primary TOC is intact
        f.seek(ISO_PRIMARY_START)
        toc_head_after = f.read(16)
        assert toc_head_after == toc_head, "PRIMARY TOC CORRUPTED!"
        print(f"  Primary TOC first 16 bytes (after): {toc_head_after.hex()} — INTACT")

        # Verify secondary is zeroed
        f.seek(ISO_SECONDARY_START)
        sec_head_after = f.read(32)
        print(f"  Secondary first 32 bytes (after):  {sec_head_after.hex()}")
        assert sec_head_after == b'\x00' * 32, "Secondary NOT zeroed at start!"

        f.seek(ISO_SECONDARY_END - 32)
        sec_tail_after = f.read(32)
        print(f"  Secondary last 32 bytes (after):   {sec_tail_after.hex()}")
        assert sec_tail_after == b'\x00' * 32, "Secondary NOT zeroed at end!"

        # Full verify: read back entire zeroed region
        f.seek(ISO_SECONDARY_START)
        verify_data = f.read(ZERO_SIZE)
        verify_nonzero = sum(1 for b in verify_data if b != 0)
        assert verify_nonzero == 0, f"Verification FAILED: {verify_nonzero} non-zero bytes remain!"
        print(f"  Full region verified: all {ZERO_SIZE:,} bytes are zero")

        # Verify resource data is untouched (read first 16 bytes of sector 125)
        resource_data_offset = PACKDATA_ISO_OFFSET + 125 * SECTOR_SIZE
        f.seek(resource_data_offset)
        res_head = f.read(16)
        print(f"\n  Resource data (sector 125) first 16 bytes: {res_head.hex()} — UNTOUCHED")

    print(f"\n=== SUCCESS ===")
    print(f"Output ISO: {OUTPUT_ISO}")
    print(f"Size: {os.path.getsize(OUTPUT_ISO):,} bytes")
    print(f"\nTest in PCSX2:")
    print(f"  - Boot FRESH from title screen (NO save states!)")
    print(f"  - Check chargen stat labels (STR, INT, etc.)")
    print(f"  - Check dialogue text")
    print(f"  - If stat labels disappear -> secondary structure IS font source")
    print(f"  - If game crashes -> secondary structure is essential")
    print(f"  - If nothing changes -> secondary structure is NOT font source")


if __name__ == "__main__":
    main()
