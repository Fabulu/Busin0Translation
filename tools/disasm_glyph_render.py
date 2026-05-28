"""Disassemble the glyph/character rendering functions.
Focus on the TextEvent message processing that reads glyph indices and renders them."""
import struct
import rabbitizer

exe = open('extracted/SLPM_653.78', 'rb').read()

P_OFFSET = 0x80
P_VADDR = 0x00100000

def file_to_vaddr(foff):
    return P_VADDR + (foff - P_OFFSET)

def vaddr_to_file(va):
    return va - P_VADDR + P_OFFSET

def disasm_range(start_va, end_va, label=""):
    print(f"\n{'='*72}")
    if label:
        print(f"{label}")
    print(f"Vaddr range: 0x{start_va:08X} - 0x{end_va:08X}")
    print(f"{'='*72}")
    for va in range(start_va, end_va, 4):
        foff = vaddr_to_file(va)
        if foff < 0 or foff + 4 > len(exe):
            print(f"  {va:08X}:  (out of range)")
            continue
        raw = struct.unpack_from('<I', exe, foff)[0]
        instr = rabbitizer.Instruction(raw)
        instr.vram = va
        asm = instr.disassemble()
        marker = ""
        if instr.isJrRa():
            marker = " <-- RETURN"
        elif instr.isJump() or instr.isBranch():
            marker = ""
        print(f"  {va:08X}:  {raw:08X}  {asm:45s}{marker}")

# The R5900 (PS2 EE) has sq/lq instructions that rabbitizer might not decode
# 0x7Fxxxxxx = sq (store quadword) - this is PS2 specific
# Let's enable R5900 mode if possible

# Key functions to examine:
# 1. The function at 0x00303C60 references FontDispSetCnt (already seen - it's the main text event processor)
# 2. Look for the function that actually reads MSG data and converts glyph indices

# The TextEventMsgIdle function (referenced at 0x004F3D06) likely processes message characters
# Let's find where that string is referenced

target_str_va = 0x004F3D06  # "TextEventMsgIdle : ControlPtr = NULL"
target_hi = (target_str_va >> 16) & 0xFFFF  # 0x004F
target_lo = target_str_va & 0xFFFF  # 0x3D06
# With addiu, the low part needs sign adjustment
# If lo >= 0x8000: lui loads hi+1 and addiu subtracts
# 0x3D06 < 0x8000, so lui 0x004F, addiu 0x3D06

print("Looking for references to 'TextEventMsgIdle' string (0x004F3D06)...")
for foff in range(P_OFFSET, len(exe) - 8, 4):
    raw = struct.unpack_from('<I', exe, foff)[0]
    opcode = (raw >> 26) & 0x3F
    if opcode == 0x09:  # addiu
        imm = raw & 0xFFFF
        if imm == (target_lo & 0xFFFF):
            # Check if preceded by lui with matching hi
            for back in range(4, 20, 4):
                if foff - back >= P_OFFSET:
                    prev = struct.unpack_from('<I', exe, foff - back)[0]
                    if (prev >> 26) == 0x0F and (prev & 0xFFFF) == target_hi:
                        va = file_to_vaddr(foff)
                        print(f"  Found reference at vaddr 0x{va:08X}")

# Let's also look at what function 0x302990 does (called from 0x303C60)
# and the FontDispSetCnt function area
# The jal at 0x303C90 calls func_302990 - let's disassemble that
disasm_range(0x00302990, 0x00302A80, "func_302990 - called from main text renderer")

# Now let's look at the area around 0x305890 which references FontDispSetCnt
# Find function boundary
scan_start = vaddr_to_file(0x305800)
for scan in range(scan_start, max(scan_start - 0x200, P_OFFSET), -4):
    raw = struct.unpack_from('<I', exe, scan)[0]
    opcode = (raw >> 26) & 0x3F
    rs = (raw >> 21) & 0x1F
    rt = (raw >> 16) & 0x1F
    imm = raw & 0xFFFF
    if opcode == 0x09 and rs == 29 and rt == 29 and imm >= 0xFF00:
        func_va = file_to_vaddr(scan)
        disasm_range(func_va, func_va + 0x200, f"FontDispSetCnt function at 0x{func_va:08X}")
        break

# Let's search for where glyph width values (like 16, 24 pixel widths) are loaded
# and where character data pointers are computed
# Common pattern: multiply glyph index by glyph size to get texture offset

# Search for multiply-by-constant patterns (glyph_size * index)
# Typical glyph sizes: 16x16, 24x24, 32x32
print(f"\n{'='*72}")
print("Searching for glyph size multiplication patterns (sll by 8=256, 9=512)...")
print(f"{'='*72}")

# sll $reg, $reg, 8 (multiply by 256 = 16*16 bytes per glyph)
# sll $reg, $reg, 9 (multiply by 512 = 16*32 or 32*16)
count = 0
for foff in range(P_OFFSET, min(len(exe) - 4, 0x300000), 4):
    raw = struct.unpack_from('<I', exe, foff)[0]
    if (raw & 0xFC00003F) == 0x00000000:  # SLL
        sa = (raw >> 6) & 0x1F
        if sa in (7, 8, 9, 10):  # multiply by 128, 256, 512, 1024
            # Check surrounding context for texture/font related ops
            # Look for lbu/lhu nearby (loading pixel data)
            has_load = False
            for delta in range(-16, 20, 4):
                if foff + delta >= P_OFFSET and foff + delta + 4 <= len(exe):
                    nearby = struct.unpack_from('<I', exe, foff + delta)[0]
                    nearby_op = (nearby >> 26) & 0x3F
                    if nearby_op in (0x24, 0x25, 0x20, 0x21):  # lbu, lhu, lb, lh
                        has_load = True
                        break
            if has_load and sa == 8 and count < 10:
                va = file_to_vaddr(foff)
                instr = rabbitizer.Instruction(raw)
                instr.vram = va
                print(f"  {va:08X}: {instr.disassemble()}")
                count += 1
