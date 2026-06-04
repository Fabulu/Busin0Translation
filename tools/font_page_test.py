#!/usr/bin/env python3
"""
font_page_test.py - Identify which PACKDATA resource provides the texture at TBP0=0x3327.

GS dump evidence:
  TBP0=0x3327 has 112 draw calls on the chargen stat screen.
  TBP0=0x2840 is R1188 (name entry font) - PROVED to have NO EFFECT on stat labels.
  TBP0=0x3000 is likely R1272 (main dialogue font) during gameplay.

Strategy:
  Zero pixel data of candidate resources in the ORIGINAL ISO, then boot
  fresh from the title screen. If stat labels disappear, we found the resource.

Test candidates:
  1. R1272 (main dialogue font, 256x512 PSMT4) - PRIME SUSPECT
     The chargen's VRAM allocator may place R1272 at TBP0=0x3327 rather than 0x3000.
     Menu struct records (EXE 0x3C3000) reference R1272 glyph IDs 683-866+.
     112 draws is consistent with glyph-by-glyph rendering of stat/menu labels.

  2. Font page R1248 (page 34, contains kanji for VIT/AGI stat labels)
  3. Font page R1250 (page 36, contains kanji for INT stat label)

Font page table (EXE file offset 0x3CA790, VA 0x4CA710):
  700 entries of 8 bytes each. Upper 16 bits of each entry = resource ID.
  Pages 1-54 -> R1215-R1268, pages 58-99 -> R1269-R1311 (with gaps/reordering).
  R1272 is NOT in this table - it's loaded separately as a companion to page 40.
"""

import struct
import os
import sys
import shutil

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ORIGINAL_ISO = os.path.join(BASE_DIR, "Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso")
DIG_PATH = os.path.join(BASE_DIR, "extracted", "PACKDATA.DIG")
OUTPUT_DIR = os.path.join(BASE_DIR, "build")

SECTOR = 2048
TOC_ENTRIES = 2883


def find_packdata_lba(iso_path):
    """Find the LBA of PACKDATA.DIG in the ISO filesystem."""
    with open(iso_path, "rb") as f:
        # Read primary volume descriptor at sector 16
        f.seek(16 * SECTOR)
        pvd = f.read(SECTOR)

        # Root directory record is at offset 156 in PVD
        root_lba = struct.unpack_from("<I", pvd, 156 + 2)[0]
        root_size = struct.unpack_from("<I", pvd, 156 + 10)[0]

        # Read root directory
        f.seek(root_lba * SECTOR)
        root_data = f.read(root_size)

        # Parse directory entries to find PACKDATA.DIG
        pos = 0
        while pos < len(root_data):
            rec_len = root_data[pos]
            if rec_len == 0:
                # Skip to next sector boundary
                pos = ((pos // SECTOR) + 1) * SECTOR
                if pos >= len(root_data):
                    break
                rec_len = root_data[pos]
                if rec_len == 0:
                    break

            name_len = root_data[pos + 32]
            name = root_data[pos + 33: pos + 33 + name_len]

            # Strip version number (;1)
            name_str = name.decode("ascii", errors="replace").split(";")[0]

            if name_str.upper() == "PACKDATA.DIG":
                lba = struct.unpack_from("<I", root_data, pos + 2)[0]
                size = struct.unpack_from("<I", root_data, pos + 10)[0]
                return lba, size

            pos += rec_len

    raise RuntimeError("PACKDATA.DIG not found in ISO")


def get_resource_offset_in_iso(iso_path, resource_id):
    """Get the byte offset within the ISO where a PACKDATA resource starts."""
    packdata_lba, packdata_size = find_packdata_lba(iso_path)
    packdata_offset = packdata_lba * SECTOR

    # Read TOC from PACKDATA
    with open(iso_path, "rb") as f:
        f.seek(packdata_offset)
        toc_data = f.read(TOC_ENTRIES * 12)

    so, sc, tc = struct.unpack_from("<III", toc_data, resource_id * 12)

    if sc == 0:
        raise ValueError(f"R{resource_id} has zero sectors")

    resource_offset = packdata_offset + so * SECTOR
    resource_size = sc * SECTOR

    return resource_offset, resource_size, tc


def zero_resource_pixels(iso_path, output_path, resource_id, pixel_offset, pixel_size, label=""):
    """Copy ISO and zero pixel data of a specific resource."""
    print(f"\n{'='*60}")
    print(f"  Test: Zero R{resource_id} pixel data {label}")
    print(f"{'='*60}")

    # Copy ISO
    print(f"  Copying ISO to {output_path}...")
    shutil.copy2(iso_path, output_path)

    # Find resource in ISO
    res_offset, res_size, type_code = get_resource_offset_in_iso(output_path, resource_id)
    print(f"  R{resource_id}: ISO offset=0x{res_offset:X}, size={res_size}, type={type_code}")

    # Zero the pixel data
    abs_pixel_start = res_offset + pixel_offset
    print(f"  Zeroing {pixel_size} bytes at ISO offset 0x{abs_pixel_start:X}")
    print(f"    (resource offset 0x{pixel_offset:X} to 0x{pixel_offset + pixel_size:X})")

    with open(output_path, "r+b") as f:
        f.seek(abs_pixel_start)
        f.write(b"\x00" * pixel_size)

    print(f"  Done. ISO: {output_path}")
    print(f"  Boot FRESH from title screen, navigate to chargen stat screen.")
    print(f"  If stat labels disappear -> R{resource_id} IS the source of TBP0=0x3327")


def analyze_font_page_table():
    """Read and display the font page table from the EXE."""
    exe_path = os.path.join(BASE_DIR, "extracted", "SLPM_653.78")

    with open(exe_path, "rb") as f:
        f.seek(0x3CA790)
        data = f.read(700 * 8)

    page_to_res = {}
    for i in range(700):
        v1, v2 = struct.unpack_from("<II", data, i * 8)
        if v1 != 0:
            page_to_res[i] = v1 >> 16

    return page_to_res


def main():
    print("=" * 60)
    print("  TBP0=0x3327 Resource Identification Test")
    print("=" * 60)

    if not os.path.exists(ORIGINAL_ISO):
        print(f"ERROR: Original ISO not found: {ORIGINAL_ISO}")
        sys.exit(1)

    # Analyze font page table
    print("\n--- Font Page Table Analysis ---")
    page_to_res = analyze_font_page_table()
    print(f"Total font pages: {len(page_to_res)}")
    print(f"R1272 (main font) is NOT in font page table - loaded separately")
    print(f"Special case: page 40 triggers loading R1272 alongside R1254")

    # VRAM analysis
    print("\n--- VRAM TBP Analysis ---")
    print("Known TBP allocations from GS dump:")
    print("  TBP0=0x2840 -> R1188 (name entry, 1024x1024 PSMT4) [PROVED: no effect on stat labels]")
    print("  TBP0=0x3000 -> R1272 during gameplay (256x512 PSMT4)")
    print("  TBP0=0x310F -> Unknown (4 draws)")
    print("  TBP0=0x319F -> Unknown (44 draws)")
    print("  TBP0=0x3220 -> Unknown (40 draws)")
    print("  TBP0=0x3327 -> TARGET (112 draws) - stat labels")
    print("  TBP0=0x34D8 -> Unknown (8 draws)")
    print()
    print("R1272 PSMT4 256x512 = 0x100 VRAM blocks")
    print("If R1272 allocated at 0x3327, it spans 0x3327-0x3427")
    print("Gap to next TBP (0x34D8 - 0x3427 = 0xB1) leaves room for CLUT + another texture")

    # ===== TEST 1: Zero R1272 (prime suspect) =====
    # R1272 structure:
    #   0x000-0x0CF: Sub-header (208 bytes)
    #   0x0D0-0x100CF: Pixel data (PSMT4 256x512 = 65536 bytes)
    #   0x100D0+: CLUT + padding
    test1_iso = os.path.join(OUTPUT_DIR, "TEST_zero_R1272.iso")
    zero_resource_pixels(
        ORIGINAL_ISO, test1_iso,
        resource_id=1272,
        pixel_offset=0x0D0,
        pixel_size=65536,
        label="(main dialogue font, PSMT4 256x512 - PRIME SUSPECT)"
    )

    # ===== TEST 2: Zero R1248 (font page 34, VIT/AGI kanji) =====
    # R1248 is 258KB, type-01 (512x512 PSMT8)
    # Pixel data starts after sub-header at 0x0D0, size = 262144 bytes
    test2_iso = os.path.join(OUTPUT_DIR, "TEST_zero_R1248.iso")
    zero_resource_pixels(
        ORIGINAL_ISO, test2_iso,
        resource_id=1248,
        pixel_offset=0x0D0,
        pixel_size=262144,
        label="(font page 34, PSMT8 512x512 - VIT/AGI kanji)"
    )

    # ===== TEST 3: Zero R1260 (font page 46, STR kanji) =====
    # R1260 is 258KB, type-01 (512x512 PSMT8)
    test3_iso = os.path.join(OUTPUT_DIR, "TEST_zero_R1260.iso")
    zero_resource_pixels(
        ORIGINAL_ISO, test3_iso,
        resource_id=1260,
        pixel_offset=0x0D0,
        pixel_size=262144,
        label="(font page 46, PSMT8 512x512 - STR kanji)"
    )

    print("\n" + "=" * 60)
    print("  TESTING INSTRUCTIONS")
    print("=" * 60)
    print()
    print("For EACH test ISO:")
    print("1. Mount in PCSX2 (do NOT load save states!)")
    print("2. Boot FRESH from title screen")
    print("3. Navigate to character creation / stat screen")
    print("4. Check if stat labels are visible or blank")
    print()
    print("Test ISOs created:")
    print(f"  1. {test1_iso}")
    print(f"     -> If stat labels disappear: R1272 IS at TBP0=0x3327")
    print(f"  2. {test2_iso}")
    print(f"     -> If some kanji disappear: Font pages contribute to stat labels")
    print(f"  3. {test3_iso}")
    print(f"     -> If STR kanji disappears: Font pages contribute to stat labels")
    print()
    print("EXPECTED RESULT: Test 1 (R1272) will show blank stat labels.")
    print("R1272 contains menu tile glyphs 683-866+ used for stat/menu labels.")
    print("The chargen's VRAM allocator places R1272 at TBP0=0x3327")
    print("(different from the 0x3000 used during regular gameplay).")

    # Also dump the key findings
    print("\n" + "=" * 60)
    print("  KEY FINDINGS SUMMARY")
    print("=" * 60)
    print()
    print("Font Page Table (EXE 0x3CA790 / VA 0x4CA710):")
    print("  700 entries, 667 non-zero, maps page_index -> resource_handle")
    print("  Pages 1-54 -> R1215-R1268")
    print("  Pages 55-99 -> R1269-R1311 (reordered)")
    print("  Pages 100+ -> R1312-R1907+ (extended kanji)")
    print("  R1272 is NOT in the table (loaded as companion to page 40)")
    print()
    print("Font Page Resource Sizes:")
    print("  258KB (129 sectors): PSMT8 512x512 = 0x400 VRAM blocks")
    print("  130KB (65 sectors):  PSMT8 256x512 = 0x200 VRAM blocks")
    print("  R1272: 66KB (33 sectors): PSMT4 256x512 = 0x100 VRAM blocks")
    print()
    print("Chargen Font Loading Code (VA 0x30B210-0x30B3EC):")
    print("  State machine with 4 states that loads font pages on demand")
    print("  Uses JAL 0x4924A0 (resource acquire) and JAL 0x492640 (check loaded)")
    print("  Special case: page_index == 40 triggers additional R1272 load")
    print("  Iterates glyph slots (32 max) with 50-byte stride")


if __name__ == "__main__":
    main()
