"""
Diagnostic ISO: Zero R2100 sub-blocks 1 and 2, keep sub-block 0 intact.

If F/M appear with sub1+sub2 zeroed: those uploads overwrite F/M in VRAM.
If F/M still missing: cause is elsewhere.

R2100 is in PACKDATA header sectors 17-84.
ISO byte offset = (16029 + 17) * 2048 = 16046 * 2048 = 32,862,208

Sub-block pixel offsets within R2100:
  Sub 0: 0x500   (KEEP - ASCII keyboard)
  Sub 1: 0x8C40  (ZERO - stat patches)
  Sub 2: 0x11380 (ZERO - gender patches)
  Sub 3: 0x19AC0 (leave as-is)

Each sub-block pixel area: 32768 bytes (0x8000).
"""

import shutil
import os

SRC_ISO = r"C:\Programmieren\wizardrytranslation\Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso"
DST_ISO = r"C:\Programmieren\wizardrytranslation\build\BUSIN0_DIAG_r2100_sub12_zero.iso"

PACKDATA_SECTOR = 16029
R2100_SECTOR_OFFSET = 17
SECTOR_SIZE = 2048

R2100_ISO_OFFSET = (PACKDATA_SECTOR + R2100_SECTOR_OFFSET) * SECTOR_SIZE

SUB1_PIXEL_OFFSET = 0x8C40
SUB2_PIXEL_OFFSET = 0x11380
SUB_BLOCK_SIZE = 32768  # 0x8000

print(f"Source ISO: {SRC_ISO}")
print(f"Dest ISO:   {DST_ISO}")
print(f"R2100 ISO offset: 0x{R2100_ISO_OFFSET:X} ({R2100_ISO_OFFSET})")
print(f"Sub1 absolute: 0x{R2100_ISO_OFFSET + SUB1_PIXEL_OFFSET:X}")
print(f"Sub2 absolute: 0x{R2100_ISO_OFFSET + SUB2_PIXEL_OFFSET:X}")
print(f"Each sub-block: {SUB_BLOCK_SIZE} bytes")

# Copy source ISO
print("\nCopying source ISO...")
shutil.copy2(SRC_ISO, DST_ISO)
print("Copy complete.")

# Zero sub-blocks 1 and 2 in-place
with open(DST_ISO, "r+b") as f:
    # Read sub0 header area to verify we're at the right spot
    f.seek(R2100_ISO_OFFSET)
    header = f.read(16)
    print(f"\nR2100 header bytes: {header[:16].hex()}")

    # Zero sub-block 1
    abs_sub1 = R2100_ISO_OFFSET + SUB1_PIXEL_OFFSET
    f.seek(abs_sub1)
    old_sub1 = f.read(16)
    print(f"Sub1 before (first 16 bytes): {old_sub1.hex()}")
    f.seek(abs_sub1)
    f.write(b'\x00' * SUB_BLOCK_SIZE)
    print(f"Sub1 zeroed: {SUB_BLOCK_SIZE} bytes at 0x{abs_sub1:X}")

    # Zero sub-block 2
    abs_sub2 = R2100_ISO_OFFSET + SUB2_PIXEL_OFFSET
    f.seek(abs_sub2)
    old_sub2 = f.read(16)
    print(f"Sub2 before (first 16 bytes): {old_sub2.hex()}")
    f.seek(abs_sub2)
    f.write(b'\x00' * SUB_BLOCK_SIZE)
    print(f"Sub2 zeroed: {SUB_BLOCK_SIZE} bytes at 0x{abs_sub2:X}")

    # Verify sub0 is untouched
    f.seek(R2100_ISO_OFFSET + 0x500)
    sub0_check = f.read(16)
    print(f"\nSub0 verification (first 16 bytes at 0x500): {sub0_check.hex()}")
    if sub0_check == b'\x00' * 16:
        print("WARNING: Sub0 appears to be all zeros - may already be empty!")
    else:
        print("Sub0 looks intact (non-zero data present).")

    # Verify sub1 is zeroed
    f.seek(abs_sub1)
    verify1 = f.read(16)
    print(f"Sub1 verify (should be zeros): {verify1.hex()}")

    # Verify sub2 is zeroed
    f.seek(abs_sub2)
    verify2 = f.read(16)
    print(f"Sub2 verify (should be zeros): {verify2.hex()}")

dst_size = os.path.getsize(DST_ISO)
src_size = os.path.getsize(SRC_ISO)
print(f"\nSource size: {src_size:,} bytes")
print(f"Output size: {dst_size:,} bytes")
print(f"Size match: {src_size == dst_size}")
print(f"\nDiagnostic ISO written to: {DST_ISO}")
