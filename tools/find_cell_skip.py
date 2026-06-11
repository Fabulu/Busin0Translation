"""
Search for the cell skip mechanism more broadly.

Key facts:
- The keyboard has ~95 cells (glyph IDs 0-94)
- Glyph IDs 38 (F) and 45 (M) produce zero GS draw calls
- The unrolled setup at VA 0x463800 area sets up ALL 95 glyphs
- The skip must be in the rendering path

Strategy: Search for data tables that might encode which cells to skip.
A table of 95 entries (one per cell) where entries 38 and 45 have special values.

Also: maybe the glyph mapping function 0x3A2D10 returns 0 for certain inputs,
and a 0 return causes the renderer to skip drawing.
"""
import struct

EXE_PATH = r"C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE = 0x0FFF80

def fo2va(fo): return fo + VA_BASE
def va2fo(va): return va - VA_BASE

with open(EXE_PATH, "rb") as f:
    exe = f.read()

# =================================================================
# Strategy 1: Check the third jump table function (VA 0x46c7F0)
# This function returns values 0, 1, or 2 for categories 0-20.
# Categories 3, 10-20 return 0. What if category 3 maps to
# glyph rows containing F and M?
# =================================================================
print("=" * 90)
print("ANALYSIS: Jump table function at VA 0x46c7F0")
print("This returns 0/1/2 per category. 0 might mean 'skip drawing'.")
print("Categories returning 0: 3, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20")
print("Categories returning 1: 1, 2, 4, 5, 6, 7, 8, 9")
print("Categories returning 2: 0")
print("=" * 90)

# =================================================================
# Strategy 2: Look at the R1188 font resource data itself
# The function 0x3A2D10 reads from a pointer passed in $a0
# If the font data has zeros for cells 38 and 45, those would
# cause 0 returns -> renderer skips them
# =================================================================

# =================================================================
# Strategy 3: Search for tables of ~95 bytes/halfwords/words
# where positions 38 and 45 have special (zero) values
# =================================================================
print()
print("=" * 90)
print("SEARCHING for ~95-entry tables with zeros at indices 38 and 45")
print("=" * 90)

# Search data section and code section for byte tables
for region_name, start, end in [
    ("Data section", 0x3C0000, min(0x400000, len(exe))),
    ("Code section (keyboard area)", 0x350000, 0x3A0000),
    ("Full EXE", 0, len(exe)),
]:
    print(f"\n--- {region_name} ---")
    found = 0

    # Byte tables: look for 95+ consecutive bytes where [38]=0 and [45]=0
    # but most others are non-zero
    for base in range(start, min(end, len(exe) - 95)):
        chunk = exe[base:base+95]
        if chunk[38] == 0 and chunk[45] == 0:
            # Count non-zeros
            non_zero = sum(1 for b in chunk if b != 0)
            if non_zero >= 80:  # At least 80 of 93 remaining should be non-zero
                print(f"  BYTE TABLE at file {base:#08x} VA {fo2va(base):#08x}: "
                      f"{non_zero}/95 non-zero, [38]=0, [45]=0")
                print(f"    First 50: {list(chunk[:50])}")
                print(f"    35-50: {list(chunk[35:50])}")
                found += 1
                if found >= 10:
                    print(f"  ... (truncated)")
                    break

    if found == 0:
        # Also try halfword tables
        for base in range(start, min(end, len(exe) - 190), 2):
            val38 = struct.unpack_from("<H", exe, base + 38*2)[0]
            val45 = struct.unpack_from("<H", exe, base + 45*2)[0]
            if val38 == 0 and val45 == 0:
                # Check if most others are non-zero
                non_zero = 0
                for i in range(95):
                    v = struct.unpack_from("<H", exe, base + i*2)[0]
                    if v != 0:
                        non_zero += 1
                if non_zero >= 80:
                    vals = [struct.unpack_from("<H", exe, base + i*2)[0] for i in range(95)]
                    print(f"  HALFWORD TABLE at file {base:#08x} VA {fo2va(base):#08x}: "
                          f"{non_zero}/95 non-zero")
                    print(f"    35-50: {vals[35:50]}")
                    found += 1
                    if found >= 5:
                        print(f"  ... (truncated)")
                        break

    if found == 0:
        print("  (none found)")

# =================================================================
# Strategy 4: The glyph IDs for the Japanese keyboard are different
# from ASCII positions. What if cells 38 and 45 in the original
# Japanese keyboard map to characters that don't exist in R1188?
# Let me check the halfword table built by the unrolled setup.
# The setup stores results at $s4+offset where:
#   glyph 0 -> $s4+0x26 (first call at VA 0x4638B4 stores at sh $v0, 38($s4)
#     wait, 38 decimal = 0x26)
# Actually let me re-read the code: li $a3, 16 then sh $v0, 36($s4)
# li $a3, 17 then sh $v0, 38($s4)
# The $a3 values go 0,1,2,...94 and the store offsets go 0,2,4,...188
# Wait no, let me check more carefully
# =================================================================

print()
print("=" * 90)
print("CHECKING: Glyph ID to struct offset mapping in unrolled setup")
print("=" * 90)

# The pattern is:
# li $a3, N
# jal 0x3a2d10
# sh $v0, OFFSET($s4)
# Let me extract all these triplets

setup_start = va2fo(0x4636F0)
setup_end = va2fo(0x464400)

# Find all "li $a3, N" instructions
glyph_to_offset = {}
i = setup_start
while i < setup_end:
    instr = struct.unpack_from("<I", exe, i)[0]
    op = (instr >> 26) & 0x3F
    rs = (instr >> 21) & 0x1F
    rt = (instr >> 16) & 0x1F
    imm = instr & 0xFFFF
    imm_s = imm - 0x10000 if imm & 0x8000 else imm

    # li $a3, N (addiu $a3, $zero, N)
    if op == 9 and rs == 0 and rt == 7 and 0 <= imm_s <= 94:
        glyph_id = imm_s
        # Next should be jal 0x3a2d10
        next_instr = struct.unpack_from("<I", exe, i+4)[0]
        if (next_instr >> 26) == 3:  # JAL
            # After jal + delay slot, look for sh/sw $v0, OFFSET($s4)
            # Actually the delay slot is at i+8, then the store is at i+12
            # Wait: jal is at i+4, delay slot at i+8, then next instruction at i+12
            for delta in range(3, 8):
                store_instr = struct.unpack_from("<I", exe, i + delta*4)[0]
                store_op = (store_instr >> 26) & 0x3F
                store_rs = (store_instr >> 21) & 0x1F
                store_rt = (store_instr >> 16) & 0x1F
                store_imm = store_instr & 0xFFFF
                store_imm_s = store_imm - 0x10000 if store_imm & 0x8000 else store_imm
                if store_op in (41, 43) and store_rt == 2 and store_rs == 20:  # sh/sw $v0, X($s4)
                    store_type = "sh" if store_op == 41 else "sw"
                    glyph_to_offset[glyph_id] = (store_imm_s, store_type)
                    break
    i += 4

print(f"Found {len(glyph_to_offset)} glyph->offset mappings:")
for gid in sorted(glyph_to_offset.keys()):
    off, stype = glyph_to_offset[gid]
    marker = " <<<" if gid in (38, 45) else ""
    print(f"  Glyph {gid:3d}: {stype} at $s4+{off}{marker}")

# =================================================================
# Strategy 5: Search the ENTIRE EXE for sequences that look like
# glyph exclusion lists: small arrays containing values 38 and 45
# =================================================================
print()
print("=" * 90)
print("SEARCHING for small exclusion lists containing 38 AND 45 within 16 bytes")
print("=" * 90)

# Look for byte 38 where byte 45 appears within 16 bytes
for i in range(len(exe) - 16):
    if exe[i] == 38:
        for j in range(i+1, min(i+16, len(exe))):
            if exe[j] == 45:
                # Check if this looks like a small list of indices
                # (not random data - all values in the range should be small)
                chunk = exe[max(0,i-4):j+5]
                if all(b < 96 for b in chunk):
                    print(f"  File {i:#08x} VA {fo2va(i):#08x}: [{38}] at +0, [{45}] at +{j-i}")
                    context = exe[max(0,i-8):j+8]
                    print(f"    Context: {list(context)}")
                    break

print("\nDone.")
