"""
Isolation test: zero R2100 vs R1370 individually to determine which
resource controls the name entry screen blackout.

Creates two ISOs from the original Japanese disc:
  TEST_R2100_only_zero.iso — R2100 zeroed, R1370 intact
  TEST_R1370_only_zero.iso — R1370 zeroed, R2100 intact
"""

import shutil
import os

ORIG_ISO = r"C:\Programmieren\wizardrytranslation\Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso"
OUT_DIR  = r"C:\Programmieren\wizardrytranslation\build"

PACKDATA_LBA = 16029
SECTOR = 2048

# R2100: sectors 17-84 within PACKDATA (68 sectors = 139264 bytes)
R2100_OFFSET = (PACKDATA_LBA + 17) * SECTOR  # 32862208
R2100_SIZE   = 68 * SECTOR                    # 139264

# R1370: sectors 85-124 within PACKDATA (40 sectors = 81920 bytes)
R1370_OFFSET = (PACKDATA_LBA + 85) * SECTOR  # 33001472
R1370_SIZE   = 40 * SECTOR                    # 81920

def verify_region(path, offset, size, label, expect_zero):
    """Read back a region and verify it's zeroed (or not)."""
    with open(path, "rb") as f:
        f.seek(offset)
        data = f.read(size)
    is_zero = all(b == 0 for b in data)
    status = "ZEROED" if is_zero else "INTACT"
    expected = "ZEROED" if expect_zero else "INTACT"
    ok = "OK" if status == expected else "MISMATCH"
    print(f"  {label}: {status} (expected {expected}) [{ok}]")
    return status == expected

def create_test_iso(name, zero_r2100, zero_r1370):
    out_path = os.path.join(OUT_DIR, name)
    print(f"\nCreating {name}...")
    shutil.copy2(ORIG_ISO, out_path)

    with open(out_path, "r+b") as f:
        if zero_r2100:
            print(f"  Zeroing R2100 at offset 0x{R2100_OFFSET:X}, {R2100_SIZE} bytes")
            f.seek(R2100_OFFSET)
            f.write(b'\x00' * R2100_SIZE)
        if zero_r1370:
            print(f"  Zeroing R1370 at offset 0x{R1370_OFFSET:X}, {R1370_SIZE} bytes")
            f.seek(R1370_OFFSET)
            f.write(b'\x00' * R1370_SIZE)

    print(f"  Verifying {name}:")
    ok1 = verify_region(out_path, R2100_OFFSET, R2100_SIZE, "R2100", zero_r2100)
    ok2 = verify_region(out_path, R1370_OFFSET, R1370_SIZE, "R1370", zero_r1370)

    if ok1 and ok2:
        print(f"  -> {name} PASSED verification")
    else:
        print(f"  -> {name} FAILED verification!")

    sz = os.path.getsize(out_path)
    print(f"  File size: {sz:,} bytes")

def main():
    print(f"Original ISO: {ORIG_ISO}")
    print(f"R2100 offset: 0x{R2100_OFFSET:X} ({R2100_OFFSET:,}), size: {R2100_SIZE:,}")
    print(f"R1370 offset: 0x{R1370_OFFSET:X} ({R1370_OFFSET:,}), size: {R1370_SIZE:,}")

    # Verify original has non-zero data in both regions
    print("\nVerifying original ISO regions are non-zero:")
    verify_region(ORIG_ISO, R2100_OFFSET, R2100_SIZE, "R2100", expect_zero=False)
    verify_region(ORIG_ISO, R1370_OFFSET, R1370_SIZE, "R1370", expect_zero=False)

    # Test 1: Zero ONLY R2100, keep R1370
    create_test_iso("TEST_R2100_only_zero.iso", zero_r2100=True, zero_r1370=False)

    # Test 2: Zero ONLY R1370, keep R2100
    create_test_iso("TEST_R1370_only_zero.iso", zero_r2100=False, zero_r1370=True)

    print("\n=== DONE ===")
    print("Test plan:")
    print("  1. Boot TEST_R2100_only_zero.iso -> New Game -> name entry")
    print("     If black: R2100 matters for name entry screen")
    print("  2. Boot TEST_R1370_only_zero.iso -> New Game -> name entry")
    print("     If black: R1370 matters for name entry screen")

if __name__ == "__main__":
    main()
