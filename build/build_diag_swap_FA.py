#!/usr/bin/env python3
"""
Diagnostic build: swap vram_block values for glyphs A (cell 33) and F (cell 38)
in the R1188 cell data table.

This tests whether the VRAM position 0xA268 is being overwritten at runtime.
If A disappears from the keyboard after this swap, it confirms position-specific
VRAM corruption.

Builds on top of the normal v9 build, then patches the ISO's EXE with the swap.
"""
import os, sys, struct

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048

# Step 1: Run the normal build
print("=" * 60)
print("  DIAGNOSTIC BUILD: vram_block swap A<->F")
print("=" * 60)

print("\n=== Running normal v9 build ===")
ret = os.system('python tools/generate_font_atlas.py && python build/build_v9.py')
if ret != 0:
    print("ERROR: v9 build failed")
    sys.exit(1)

# Step 2: Read the patched EXE
exe_path = 'build/SLPM_653.78_patched'
if not os.path.exists(exe_path):
    print("ERROR: patched EXE not found")
    sys.exit(1)

data = bytearray(open(exe_path, 'rb').read())

# Cell data table at EXE offset 0x3DB180
# Page 0 VA pointer at offset 0x3DB184
page0_va = struct.unpack_from('<I', data, 0x3DB184)[0]
page0_off = page0_va - 0x100000 + 0x80
print(f"\nPage 0 VA: 0x{page0_va:08X}, file offset: 0x{page0_off:08X}")

# Cell 33 (A) and Cell 38 (F), each 8 bytes
# vram_block is the u16 LE at bytes 4-5 of each cell
cell_a_off = page0_off + 33 * 8
cell_f_off = page0_off + 38 * 8

vram_a = struct.unpack_from('<H', data, cell_a_off + 4)[0]
vram_f = struct.unpack_from('<H', data, cell_f_off + 4)[0]

print(f"Before swap:")
print(f"  Cell 33 (A) vram_block: 0x{vram_a:04X}")
print(f"  Cell 38 (F) vram_block: 0x{vram_f:04X}")

# Swap them
struct.pack_into('<H', data, cell_a_off + 4, vram_f)  # A gets F's value (0xA268)
struct.pack_into('<H', data, cell_f_off + 4, vram_a)  # F gets A's value (0xA240)

# Verify
vram_a2 = struct.unpack_from('<H', data, cell_a_off + 4)[0]
vram_f2 = struct.unpack_from('<H', data, cell_f_off + 4)[0]
print(f"After swap:")
print(f"  Cell 33 (A) vram_block: 0x{vram_a2:04X}")
print(f"  Cell 38 (F) vram_block: 0x{vram_f2:04X}")

# Write modified EXE back
open(exe_path, 'wb').write(data)
print(f"\nPatched EXE written: {exe_path}")

# Step 3: Copy v9 ISO to diagnostic ISO, then patch EXE into it
src_iso = 'build/BUSIN0_EN_v9.iso'
dst_iso = 'build/BUSIN0_DIAG_swap_FA.iso'

import shutil
print(f"\nCopying {src_iso} -> {dst_iso}")
shutil.copy2(src_iso, dst_iso)

# Patch EXE into the diagnostic ISO
with open(dst_iso, 'r+b') as iso:
    iso.seek(16 * SECTOR)
    pvd = iso.read(SECTOR)
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]
    iso.seek(root_lba * SECTOR)
    root_dir = iso.read(root_size)
    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        if 'SLPM' in name:
            exe_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
            # Update size in directory
            iso.seek(root_lba * SECTOR + pos + 10)
            iso.write(struct.pack('<I', len(data)))
            iso.write(struct.pack('>I', len(data)))
            # Write EXE data
            iso.seek(exe_lba * SECTOR)
            iso.write(data)
            print(f"EXE patched in ISO: {len(data):,} bytes at LBA {exe_lba}")
            break
        pos += rec_len

print(f"\n{'=' * 60}")
print(f"  DIAGNOSTIC ISO: {dst_iso}")
print(f"  A(33) now points to vram 0x{vram_f:04X} (was F's)")
print(f"  F(38) now points to vram 0x{vram_a:04X} (was A's)")
print(f"{'=' * 60}")
print()
print("TEST: Boot fresh, go to name entry screen.")
print("  If A disappears: VRAM at 0xA268 is overwritten (position-specific)")
print("  If F disappears: rendering uses cell index, not vram_block")
print("  If both work: something else is going on")
