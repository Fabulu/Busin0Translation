#!/usr/bin/env python3
"""
Diagnostic ISO B: R2100 completely ORIGINAL (no patches at all).
All other translations (R37/R38/R1272/dialogue/EXE) remain from v55.

Start from latest translated build, then REPLACE R2100 in the ISO header
with the byte-for-byte ORIGINAL R2100 from the extracted PACKDATA.DIG.

If F/M appear:    SOME R2100 patch in the full build destroys them.
If F/M missing:   R2100 patches are NOT the cause — look elsewhere.
"""

import os, struct, shutil

BASE = r"C:\Programmieren\wizardrytranslation"

SRC_ISO = os.path.join(BASE, "build", "BUSIN0_EN_v55.iso")
DST_ISO = os.path.join(BASE, "build", "BUSIN0_DIAG_r2100_original.iso")
DIG_PATH = os.path.join(BASE, "extracted", "PACKDATA.DIG")

SECTOR = 2048
PACKDATA_SECTOR = 16029
R2100_HEADER_OFFSET = 17
R2100_ISO_OFFSET = (PACKDATA_SECTOR + R2100_HEADER_OFFSET) * SECTOR

TOC_ENTRIES = 2883
R2100_TOC_INDEX = 2100

def main():
    print("=== Diagnostic ISO B: R2100 Completely Original ===\n")

    # 1. Read ORIGINAL R2100 from extracted PACKDATA.DIG
    print(f"Reading original R2100 from {DIG_PATH}...")
    with open(DIG_PATH, "rb") as f:
        toc_data = f.read(TOC_ENTRIES * 12)
        so, sc, tc = struct.unpack_from("<III", toc_data, R2100_TOC_INDEX * 12)
        byte_off = so * SECTOR
        byte_size = sc * SECTOR
        print(f"  TOC: sector_offset=0x{so:X}, count={sc}, type={tc}")
        print(f"  Byte offset: {byte_off}, size: {byte_size}")
        f.seek(byte_off)
        r2100_orig = f.read(byte_size)
        assert len(r2100_orig) == byte_size

    # 2. Copy the latest translated ISO
    print(f"\nCopying {SRC_ISO}...")
    shutil.copy2(SRC_ISO, DST_ISO)

    # 3. Overwrite R2100 in the ISO with the ORIGINAL (unpatched) version
    r2100_padded = r2100_orig + b'\x00' * (68 * SECTOR - len(r2100_orig))
    with open(DST_ISO, "r+b") as f:
        # Verify we're at the right spot
        f.seek(R2100_ISO_OFFSET)
        existing = f.read(16)
        print(f"  Existing R2100 header in ISO: {existing.hex()}")

        f.seek(R2100_ISO_OFFSET)
        f.write(r2100_padded)
        print(f"  Wrote original R2100 at ISO offset 0x{R2100_ISO_OFFSET:X} ({len(r2100_padded)} bytes)")

        # Verify
        f.seek(R2100_ISO_OFFSET)
        verify = f.read(16)
        print(f"  Verification header: {verify.hex()}")
        orig_header = r2100_orig[:16]
        print(f"  Original header:     {orig_header.hex()}")
        assert verify == orig_header, "MISMATCH!"

    print(f"\nOutput: {DST_ISO}")
    print(f"Size: {os.path.getsize(DST_ISO):,} bytes")
    print("\nR2100 = BYTE-FOR-BYTE ORIGINAL. No stat patches, no gender patches, no ASCII patches.")
    print("All other translations (R37/R38/R1272/dialogue/EXE) remain from v55.")
    print("DONE!")

if __name__ == "__main__":
    main()
