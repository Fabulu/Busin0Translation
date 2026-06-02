"""
EXE Data Section Zero Test
Creates two test ISOs from the ORIGINAL (unmodified) disc image.
Only the EXE embedded in the ISO is modified; PACKDATA is untouched.

Test A: Zero EXE bytes 0x200000-0x300000 (data section first half)
Test B: Zero EXE bytes 0x300000-0x3FFFF0 (data section second half, minus last 16 bytes)

If stat labels vanish in A -> font data lives in 0x200000-0x300000
If stat labels vanish in B -> font data lives in 0x300000-0x3FFFF0
If both crash -> data section is essential for basic boot
"""

import shutil
import struct
import os

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
ORIGINAL_ISO = os.path.join(BASE_DIR, 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso')
SECTOR = 2048
EXE_SIZE = 4_185_776  # 0x3FD3B0

TESTS = {
    'A': {
        'output': os.path.join(BASE_DIR, 'build', 'TEST_exe_data_zero_A.iso'),
        'zero_start': 0x200000,
        'zero_end':   0x300000,
        'desc': 'data section first half (0x200000-0x300000)',
    },
    'B': {
        'output': os.path.join(BASE_DIR, 'build', 'TEST_exe_data_zero_B.iso'),
        'zero_start': 0x300000,
        'zero_end':   0x3FFFF0,  # leave last 16 bytes intact
        'desc': 'data section second half (0x300000-0x3FFFF0)',
    },
}


def find_exe_lba(iso_path):
    """Find the EXE (SLPM_653.78) LBA from the ISO's root directory."""
    with open(iso_path, 'rb') as f:
        # Read primary volume descriptor
        f.seek(16 * SECTOR)
        pvd = f.read(SECTOR)
        assert pvd[0] == 1, "Not a PVD"
        root_record = pvd[156:156+34]
        root_lba = struct.unpack_from('<I', root_record, 2)[0]

        # Read root directory
        f.seek(root_lba * SECTOR)
        root_dir = f.read(SECTOR * 4)  # read a few sectors

        pos = 0
        while pos < len(root_dir):
            rec_len = root_dir[pos]
            if rec_len == 0:
                # skip to next sector boundary
                next_sector = ((pos // SECTOR) + 1) * SECTOR
                if next_sector >= len(root_dir):
                    break
                pos = next_sector
                continue
            name_len = root_dir[pos + 32]
            name = root_dir[pos + 33: pos + 33 + name_len].decode('ascii', errors='replace')
            if 'SLPM' in name or 'slpm' in name:
                file_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
                file_size = struct.unpack_from('<I', root_dir, pos + 10)[0]
                print(f"  Found EXE: {name} at LBA {file_lba}, size {file_size:,}")
                return file_lba, file_size
            pos += rec_len

    raise RuntimeError("Could not find EXE in ISO root directory")


def create_test_iso(test_id, cfg):
    print(f"\n=== Test {test_id}: {cfg['desc']} ===")
    output = cfg['output']

    # Copy original ISO
    print(f"  Copying original ISO -> {os.path.basename(output)} ...")
    shutil.copy2(ORIGINAL_ISO, output)

    # Find EXE location
    exe_lba, exe_size = find_exe_lba(output)
    exe_offset = exe_lba * SECTOR

    zero_start = cfg['zero_start']
    zero_end = cfg['zero_end']
    zero_len = zero_end - zero_start

    if zero_end > exe_size:
        print(f"  WARNING: zero_end (0x{zero_end:X}) > exe_size (0x{exe_size:X}), clamping")
        zero_end = exe_size
        zero_len = zero_end - zero_start

    print(f"  Zeroing EXE offset 0x{zero_start:X} - 0x{zero_end:X} ({zero_len:,} bytes)")

    with open(output, 'r+b') as f:
        f.seek(exe_offset + zero_start)
        f.write(b'\x00' * zero_len)

    # Verify
    with open(output, 'rb') as f:
        f.seek(exe_offset + zero_start)
        check = f.read(64)
        assert check == b'\x00' * 64, "Verification failed: bytes not zeroed"

        # Check code section is intact
        f.seek(exe_offset)
        code_header = f.read(16)
        print(f"  EXE header (first 16 bytes): {code_header[:16].hex()}")

        # Check a spot in the code section is NOT zeroed
        f.seek(exe_offset + 0x1000)
        code_check = f.read(16)
        assert code_check != b'\x00' * 16, "Code section appears zeroed - something is wrong!"

    print(f"  OK: {os.path.basename(output)} created")
    iso_size = os.path.getsize(output)
    print(f"  ISO size: {iso_size:,} bytes")


if __name__ == '__main__':
    if not os.path.isfile(ORIGINAL_ISO):
        print(f"ERROR: Original ISO not found: {ORIGINAL_ISO}")
        exit(1)

    for test_id, cfg in TESTS.items():
        create_test_iso(test_id, cfg)

    print("\n=== DONE ===")
    print("Test A: Zero 0x200000-0x300000 (data first half)")
    print("Test B: Zero 0x300000-0x3FFFF0 (data second half)")
    print()
    print("Boot each in PCSX2 FRESH (no save states!) and check stat labels.")
    print("  - Labels gone in A -> font data is in 0x200000-0x300000")
    print("  - Labels gone in B -> font data is in 0x300000-0x3FFFF0")
    print("  - Both crash -> data section needed for boot")
