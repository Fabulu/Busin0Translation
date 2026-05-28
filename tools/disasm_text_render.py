"""Find and disassemble text rendering functions by locating references to font debug strings."""
import struct
import rabbitizer

exe = open('extracted/SLPM_653.78', 'rb').read()

P_OFFSET = 0x80
P_VADDR = 0x00100000

def file_to_vaddr(foff):
    return P_VADDR + (foff - P_OFFSET)

def vaddr_to_file(va):
    return va - P_VADDR + P_OFFSET

# Key debug strings and their vaddrs:
# "FontDispSetCnt Max Over !!!" at vaddr 0x004F3D40
# "SysFont Init!!!" at vaddr ~0x004FC753
# "FCD_battle_font" at vaddr 0x004F0336
# "FCD_event_font" at vaddr 0x004F3452

# To find functions that reference these strings, search for lui/addiu pairs
# lui $reg, 0x004F followed by addiu/ori $reg, $reg, 0x3D40 etc.

# Search for lui 0x004F which loads the upper half of these addresses
target_his = [0x004F, 0x0050]  # addresses in 0x004Fxxxx and 0x004Fxxxx+0x10000 range

print("Searching for lui instructions loading 0x004F (font string area)...")
lui_refs = []
for off in range(P_OFFSET, len(exe) - 4, 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    opcode = (raw >> 26) & 0x3F
    if opcode == 0x0F:  # LUI
        imm = raw & 0xFFFF
        if imm == 0x004F:
            rt = (raw >> 16) & 0x1F
            vaddr = file_to_vaddr(off)
            # Check next few instructions for addiu with font-related low addresses
            for delta in range(4, 20, 4):
                if off + delta >= len(exe):
                    break
                next_raw = struct.unpack_from('<I', exe, off + delta)[0]
                next_op = (next_raw >> 26) & 0x3F
                if next_op == 0x09:  # ADDIU
                    next_imm = next_raw & 0xFFFF
                    if next_imm >= 0x8000:
                        next_imm = next_imm - 0x10000
                    full_addr = 0x004F0000 + next_imm
                    # Check if this is near any of our font strings
                    if 0x004F3D00 <= full_addr <= 0x004F3E00:
                        lui_refs.append((off, vaddr, full_addr))
                    elif 0x004F0300 <= full_addr <= 0x004F0400:
                        lui_refs.append((off, vaddr, full_addr))
                    elif 0x004F3400 <= full_addr <= 0x004F3500:
                        lui_refs.append((off, vaddr, full_addr))

print(f"Found {len(lui_refs)} references to font string area:")
for foff, va, target in lui_refs:
    print(f"  vaddr 0x{va:08X} (file 0x{foff:06X}) -> target 0x{target:08X}")

# Now disassemble the most interesting function - the one referencing FontDispSetCnt
if lui_refs:
    # Pick the first reference to FontDispSetCnt area
    font_disp_refs = [r for r in lui_refs if 0x004F3D00 <= r[2] <= 0x004F3E00]
    if font_disp_refs:
        target_foff = font_disp_refs[0][0]
        # Search backward for function prologue (addiu $sp, $sp, -N)
        func_start = target_foff
        for scan in range(target_foff, max(target_foff - 0x400, P_OFFSET), -4):
            raw = struct.unpack_from('<I', exe, scan)[0]
            opcode = (raw >> 26) & 0x3F
            rs = (raw >> 21) & 0x1F
            rt = (raw >> 16) & 0x1F
            imm = raw & 0xFFFF
            # addiu $sp, $sp, -N (negative offset = stack frame setup)
            if opcode == 0x09 and rs == 29 and rt == 29 and imm >= 0xFF00:
                func_start = scan
                break

        print(f"\n{'='*72}")
        print(f"Font display function near vaddr 0x{file_to_vaddr(func_start):08X}:")
        print(f"{'='*72}")

        # Disassemble ~128 instructions from function start
        for off in range(func_start, min(func_start + 512, len(exe)), 4):
            raw = struct.unpack_from('<I', exe, off)[0]
            vaddr = file_to_vaddr(off)
            instr = rabbitizer.Instruction(raw)
            instr.vram = vaddr
            asm = instr.disassemble()
            marker = ""
            if instr.isJrRa():
                marker = "  <-- RETURN"
            print(f"  {vaddr:08X}:  {raw:08X}  {asm:45s}{marker}")
            # Stop after first jr $ra + delay slot
            if instr.isJrRa():
                # Print delay slot
                off2 = off + 4
                if off2 < len(exe):
                    raw2 = struct.unpack_from('<I', exe, off2)[0]
                    instr2 = rabbitizer.Instruction(raw2)
                    instr2.vram = file_to_vaddr(off2)
                    print(f"  {file_to_vaddr(off2):08X}:  {raw2:08X}  {instr2.disassemble():45s}  (delay slot)")
                break

# Also search for the text event / message rendering functions
print(f"\n{'='*72}")
print("Searching for TextEvent / message rendering functions...")
print(f"{'='*72}")

# Search for "TextEvent" string
for i in range(len(exe) - 9):
    if exe[i:i+9] == b'TextEvent':
        context = exe[i:i+60]
        printable = ''.join(chr(b) if 32 <= b < 127 else '.' for b in context)
        vaddr = file_to_vaddr(i)
        print(f"  vaddr 0x{vaddr:08X}: {printable}")
