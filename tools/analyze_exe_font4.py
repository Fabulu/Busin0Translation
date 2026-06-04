#!/usr/bin/env python3
"""
Deeper analysis of the cell data - these look like they contain glyph IDs
paired with screen/VRAM coordinates. Let's decode the structure.

Also: search the EXE for references TO the font bitmap at 0x3D6C10
to understand what code uses it.
"""
import os, sys, struct

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE_PATH = os.path.join(BASE, "extracted", "SLPM_653.78")
exe_data = open(EXE_PATH, 'rb').read()

# ---- Cell data at 0x3D8D10 ----
CELL_OFF = 0x3D8D10
CELL_END = 0x3DAF70
cell_data = exe_data[CELL_OFF:CELL_END]

print("=== Cell Data Deep Analysis ===\n")

# Records appear to be 8 bytes each:
# Bytes: [0] [1] [2] [3] [4] [5] [6] [7]
# Byte 0: always 0 (or rarely non-zero)
# Byte 1: values 60-69 (0x3C-0x49) -- these look like ASCII codes starting at 0x3C = '<'
#   60='<', 61='=', 62='>', 63='?', 64='@', 65='A', 66='B', 67='C', 68='D', 69='E'
#   But wait - the font starts at '!' (0x21). So byte 1 might be a glyph index into the font.
#   If glyph 0 = '!', then glyph 60 = 'a'-2 = '_' (0x5F). Hmm.
# Byte 2: 100 (0x64) usually -- could be a width, y-coordinate, or flag
# Byte 3: 0 or 1
# Bytes 4-5: large values ~41000 (0xA100-range) -- VRAM or screen address?
# Byte 6: 79 (0x4F) usually -- could be height or another dimension
# Byte 7: always 0

# Let's re-interpret byte 1 as character code
print("Records as (byte0, charcode_byte1, byte2, byte3, word4_5, byte6, byte7):")
records = []
for i in range(0, len(cell_data), 8):
    if i + 8 > len(cell_data):
        break
    b = cell_data[i:i+8]
    records.append(b)

# Count unique patterns
print(f"Total 8-byte records: {len(records)}")

# Find all zero records (separators?)
zero_count = sum(1 for r in records if all(b == 0 for b in r))
print(f"All-zero records: {zero_count}")

# Group by consecutive non-zero records (separated by zero records)
groups = []
current_group = []
for i, r in enumerate(records):
    if all(b == 0 for b in r):
        if current_group:
            groups.append(current_group)
            current_group = []
    else:
        current_group.append((i, r))
if current_group:
    groups.append(current_group)

print(f"Number of groups (separated by zero records): {len(groups)}")
print(f"Group sizes: {[len(g) for g in groups]}")

# Print first 5 groups in detail
for gi, group in enumerate(groups[:10]):
    print(f"\n--- Group {gi} ({len(group)} records) ---")
    text = ""
    for idx, (rec_i, r) in enumerate(group):
        b0, b1, b2, b3 = r[0], r[1], r[2], r[3]
        w45 = struct.unpack_from('<H', r, 4)[0]
        b6, b7 = r[6], r[7]

        # If byte1 is a glyph index into the font atlas:
        # The font atlas has glyphs arranged in rows of ~16
        # Row 0: !"#$%&'()*+,-./  (ASCII 0x21-0x2F, glyphs 0-14)
        # Row 1: 0123456789:;<=>?  (ASCII 0x30-0x3F, glyphs 15-30)
        # Row 2: @ABCDEFGHIJKLMNO  (ASCII 0x40-0x4F, glyphs 31-46)
        # Row 3: PQRSTUVWXYZ[\]^_  (ASCII 0x50-0x5F, glyphs 47-62)
        # Row 4: `abcdefghijklmno  (ASCII 0x60-0x6F, glyphs 63-78)
        # Row 5: pqrstuvwxyz{|}    (ASCII 0x70-0x7E, glyphs 79-93)
        # Row 6: special chars     (glyphs 94+)

        # So glyph_index = b1 maps to ASCII 0x21 + b1?
        # b1=60 -> 0x21+60 = 0x5D = ']'  -- doesn't match
        # Maybe b1 IS the ASCII code? b1=60 = 0x3C = '<' -- but font starts at '!'
        # Or maybe it's a different mapping

        # Actually b1 values range 60-69 (0x3C-0x45)
        # 0x3C='<', 0x3D='=', 0x3E='>', 0x3F='?', 0x40='@',
        # 0x41='A', 0x42='B', 0x43='C', 0x44='D', 0x45='E'
        # But we see full alphabet in font...

        # Maybe byte 1 is NOT a char code but a different field
        char_guess = chr(b1) if 0x20 <= b1 < 0x7F else '?'
        print(f"  [{rec_i:4d}] b0={b0:3d} b1={b1:3d}('{char_guess}') b2={b2:3d} b3={b3:3d} w45=0x{w45:04X}({w45:5d}) b6={b6:3d} b7={b7:3d}")
        text += char_guess
    print(f"  Text guess: {text}")


# ---- Also check the data at 0x3DAF70+ (right after cell data) ----
print("\n\n=== Data after cell data (0x3DAF70) ===")
post_data = exe_data[0x3DAF70:0x3DAF70 + 256]
# More of the same structure?
for i in range(0, 256, 8):
    r = post_data[i:i+8]
    if any(b != 0 for b in r):
        b1 = r[1]
        char_guess = chr(b1) if 0x20 <= b1 < 0x7F else '?'
        print(f"  0x{0x3DAF70+i:X}: {' '.join(f'{b:02X}' for b in r)}  b1='{char_guess}'")


# ---- Search for MIPS code references to font bitmap address ----
# The EXE loads at 0x100000 on PS2. So the font at file offset 0x3D6C10
# would be at RAM address 0x100000 + 0x3D6C10 = 0x4D6C10
# But the ELF header might shift this. Let's check the ELF header.
print("\n\n=== EXE ELF Header ===")
# ELF magic
print(f"Magic: {exe_data[:4]}")
# e_entry (offset 0x18, 4 bytes)
e_entry = struct.unpack_from('<I', exe_data, 0x18)[0]
print(f"Entry point: 0x{e_entry:08X}")
# Program header (offset 0x1C, phoff)
e_phoff = struct.unpack_from('<I', exe_data, 0x1C)[0]
print(f"PH offset: 0x{e_phoff:X}")

# Read first program header
ph_off = e_phoff
p_type = struct.unpack_from('<I', exe_data, ph_off)[0]
p_offset = struct.unpack_from('<I', exe_data, ph_off + 4)[0]
p_vaddr = struct.unpack_from('<I', exe_data, ph_off + 8)[0]
p_paddr = struct.unpack_from('<I', exe_data, ph_off + 12)[0]
p_filesz = struct.unpack_from('<I', exe_data, ph_off + 16)[0]
p_memsz = struct.unpack_from('<I', exe_data, ph_off + 20)[0]
print(f"Segment: type={p_type} file_off=0x{p_offset:X} vaddr=0x{p_vaddr:08X} filesz=0x{p_filesz:X}")

# So RAM address = vaddr + (file_offset - p_offset)
font_ram = p_vaddr + (0x3D6C10 - p_offset)
cell_ram = p_vaddr + (0x3D8D10 - p_offset)
pal_ram = p_vaddr + (0x3D8C10 - p_offset)
print(f"\nFont bitmap RAM address: 0x{font_ram:08X}")
print(f"Palette RAM address: 0x{pal_ram:08X}")
print(f"Cell data RAM address: 0x{cell_ram:08X}")

# Search for these addresses in the EXE code
# MIPS loads 32-bit addresses in two parts: lui $reg, hi16 ; ori/addiu $reg, lo16
font_hi = (font_ram >> 16) & 0xFFFF
font_lo = font_ram & 0xFFFF
print(f"\nSearching for references to font address 0x{font_ram:08X}...")
print(f"  lui pattern: hi=0x{font_hi:04X}, lo=0x{font_lo:04X}")

# Search for the lo16 value in lui instructions
# MIPS lui: 0011 11ss ssst tttt iiii iiii iiii iiii
# lui $t, imm16: opcode=0x3C, so byte pattern is imm16_lo imm16_hi 0x?? 0x3C
# Actually: lui rd, imm = 0x3C000000 | (rd << 16) | imm
# In little-endian: imm_lo, imm_hi, rd|00, 0x3C

count = 0
for i in range(0, len(exe_data) - 4, 4):
    word = struct.unpack_from('<I', exe_data, i)[0]
    opcode = (word >> 26) & 0x3F
    imm = word & 0xFFFF

    if opcode == 0x0F and imm == font_hi:  # lui
        rd = (word >> 16) & 0x1F
        # Look for matching ori/addiu with font_lo nearby
        for j in range(i+4, min(i+32, len(exe_data)-4), 4):
            w2 = struct.unpack_from('<I', exe_data, j)[0]
            op2 = (w2 >> 26) & 0x3F
            imm2 = w2 & 0xFFFF
            rs2 = (w2 >> 21) & 0x1F
            if rs2 == rd and imm2 == font_lo:
                if op2 in (0x0D, 0x09):  # ori or addiu
                    ram_addr = p_vaddr + (i - p_offset)
                    print(f"  Found reference at file 0x{i:X} (RAM 0x{ram_addr:08X}): lui ${rd}, 0x{font_hi:04X} + {'ori' if op2==0x0D else 'addiu'} 0x{font_lo:04X}")
                    count += 1

# Also search for palette and cell references
for name, addr in [("palette", pal_ram), ("cell_data", cell_ram)]:
    hi = (addr >> 16) & 0xFFFF
    lo = addr & 0xFFFF
    for i in range(0, len(exe_data) - 4, 4):
        word = struct.unpack_from('<I', exe_data, i)[0]
        opcode = (word >> 26) & 0x3F
        imm = word & 0xFFFF
        if opcode == 0x0F and imm == hi:
            rd = (word >> 16) & 0x1F
            for j in range(i+4, min(i+32, len(exe_data)-4), 4):
                w2 = struct.unpack_from('<I', exe_data, j)[0]
                op2 = (w2 >> 26) & 0x3F
                imm2 = w2 & 0xFFFF
                rs2 = (w2 >> 21) & 0x1F
                if rs2 == rd and imm2 == lo:
                    if op2 in (0x0D, 0x09):
                        ram_addr = p_vaddr + (i - p_offset)
                        print(f"  Found {name} ref at file 0x{i:X} (RAM 0x{ram_addr:08X})")

if count == 0:
    print("  No exact references found. Trying with adjusted addresses...")
    # Maybe the address needs +/- adjustment due to signed lo16
    # If lo16 >= 0x8000, lui loads hi16+1 and addiu uses negative lo16
    if font_lo >= 0x8000:
        adj_hi = font_hi + 1
        adj_lo = font_lo - 0x10000  # negative
        adj_lo_u = adj_lo & 0xFFFF
        print(f"  Adjusted: lui 0x{adj_hi:04X}, addiu 0x{adj_lo_u:04X}")
        for i in range(0, len(exe_data) - 4, 4):
            word = struct.unpack_from('<I', exe_data, i)[0]
            opcode = (word >> 26) & 0x3F
            imm = word & 0xFFFF
            if opcode == 0x0F and imm == adj_hi:
                rd = (word >> 16) & 0x1F
                for j in range(i+4, min(i+32, len(exe_data)-4), 4):
                    w2 = struct.unpack_from('<I', exe_data, j)[0]
                    op2 = (w2 >> 26) & 0x3F
                    imm2 = w2 & 0xFFFF
                    rs2 = (w2 >> 21) & 0x1F
                    if rs2 == rd and imm2 == adj_lo_u and op2 in (0x0D, 0x09):
                        ram_addr = p_vaddr + (i - p_offset)
                        print(f"  Found reference at file 0x{i:X} (RAM 0x{ram_addr:08X})")

print(f"\nTotal references found: {count}")
print("\n=== Done ===")
