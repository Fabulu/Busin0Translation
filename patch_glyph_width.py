import struct, sys, io, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

EXE_PATH = "C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"
OUT_PATH = "C:/Programmieren/wizardrytranslation/build/SLPM_653.78_patched"

# Read original
with open(EXE_PATH, "rb") as f:
    exe = bytearray(f.read())

FILE_TO_VADDR = 0x0FFF80
NEW_ADVANCE = 14  # Change from 24 to 14 pixels for narrower English glyphs

# The three x-advance sites (addiu $v0, $v0, 24)
# All three are: 24420018 = addiu $v0, $v0, 24
# We change them to: 2442000E = addiu $v0, $v0, 14 (or whatever NEW_ADVANCE is)

advance_offsets = [
    0x207A5C,  # vaddr 0x3079DC - first caller
    0x208D30,  # vaddr 0x308CB0 - second caller
    0x209824,  # vaddr 0x3097A4 - third caller
]

# Verify and patch
for off in advance_offsets:
    old = struct.unpack_from('<I', exe, off)[0]
    expected = 0x24420018  # addiu $v0, $v0, 24
    if old != expected:
        print("WARNING: Expected 0x%08X at file 0x%06X, got 0x%08X" % (expected, off, old))
        # Show what's actually there
        opcode = (old >> 26) & 0x3F
        rs = (old >> 21) & 0x1F
        rt = (old >> 16) & 0x1F
        imm = old & 0xFFFF
        if imm > 0x7FFF: imm -= 0x10000
        print("  Decoded: op=0x%02X rs=%d rt=%d imm=%d" % (opcode, rs, rt, imm))
    else:
        new_instr = 0x24420000 | (NEW_ADVANCE & 0xFFFF)
        struct.pack_into('<I', exe, off, new_instr)
        vaddr = off + FILE_TO_VADDR
        print("Patched file 0x%06X (vaddr 0x%08X): addiu $v0, $v0, 24 -> addiu $v0, $v0, %d" % (off, vaddr, NEW_ADVANCE))

# Also need to patch the float constant 0x3E75C28F (= 0.24 as float)
# This is used for proportional advance in the non-100% path
# 0.14 in float is approximately 0x3E0F5C29
import struct as s
new_float_val = NEW_ADVANCE / 100.0  # 0.14 (since 24/100 = 0.24 was the original ratio)
new_float_bytes = s.pack('<f', new_float_val)
new_float_int = s.unpack('<I', new_float_bytes)[0]
print()
print("Float advance: 0.24 -> %.2f (0x%08X -> 0x%08X)" % (new_float_val, 0x3E75C28F, new_float_int))

# Find all instances of 0x3E75C28F used in this function area
# The pattern is: lui $v0, 0x3E75; ori $v1, $v0, 0xC28F
# Search for lui 0x3E75 and ori 0xC28F pairs near the renderer
float_locations = []
for off in range(0x206000, 0x20A000, 4):  # Search in renderer area
    raw = struct.unpack_from('<I', exe, off)[0]
    opcode = (raw >> 26) & 0x3F
    if opcode == 0x0F:  # lui
        imm = raw & 0xFFFF
        if imm == 0x3E75:
            # Check next few instructions for ori with 0xC28F
            for off2 in range(off+4, min(off+20, len(exe)-3), 4):
                raw2 = struct.unpack_from('<I', exe, off2)[0]
                if (raw2 >> 26) & 0x3F == 0x0D:  # ori
                    if (raw2 & 0xFFFF) == 0xC28F:
                        float_locations.append((off, off2))
                        break

print()
print("Found %d float constant 0x3E75C28F locations in renderer area:" % len(float_locations))
new_high = (new_float_int >> 16) & 0xFFFF
new_low = new_float_int & 0xFFFF
for lui_off, ori_off in float_locations:
    # Patch LUI
    old_lui = struct.unpack_from('<I', exe, lui_off)[0]
    new_lui = (old_lui & 0xFFFF0000) | new_high
    struct.pack_into('<I', exe, lui_off, new_lui)

    # Patch ORI
    old_ori = struct.unpack_from('<I', exe, ori_off)[0]
    new_ori = (old_ori & 0xFFFF0000) | new_low
    struct.pack_into('<I', exe, ori_off, new_ori)

    vaddr_lui = lui_off + FILE_TO_VADDR
    vaddr_ori = ori_off + FILE_TO_VADDR
    print("  Patched LUI at file 0x%06X (vaddr 0x%08X): 0x3E75 -> 0x%04X" % (lui_off, vaddr_lui, new_high))
    print("  Patched ORI at file 0x%06X (vaddr 0x%08X): 0xC28F -> 0x%04X" % (ori_off, vaddr_ori, new_low))

# Write patched file
with open(OUT_PATH, "wb") as f:
    f.write(exe)
print()
print("Written patched EXE to: %s" % OUT_PATH)
print("Glyph x-advance changed from 24 to %d" % NEW_ADVANCE)

# Summary
print()
print("=" * 60)
print("PATCH SUMMARY")
print("=" * 60)
print("Target: PS2 game EXE (SLPM_653.78)")
print("Change: Glyph rendering x-advance from 24 to %d" % NEW_ADVANCE)
print()
print("File offsets patched (addiu $v0, $v0, 24 -> %d):" % NEW_ADVANCE)
for off in advance_offsets:
    print("  0x%06X (vaddr 0x%08X)" % (off, off + FILE_TO_VADDR))
print()
print("Float constants patched (0.24 -> %.4f):" % new_float_val)
for lui_off, ori_off in float_locations:
    print("  LUI at 0x%06X, ORI at 0x%06X" % (lui_off, ori_off))
print()
print("Atlas UV calculation (NOT changed - stays as 42 cols x 24px cells):")
print("  div-by-42: file 0x2061A8 (addiu $v0, $zero, 42)")
print("  div-by-42: file 0x206F08 (addiu $v0, $zero, 42)")
print("  *24 UV calc: sll+addu+sll pattern at multiple locations")
