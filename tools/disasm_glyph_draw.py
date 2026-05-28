"""Disassemble the actual glyph drawing code - the fallthrough for regular characters."""
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
    print(f"{'='*72}")
    for va in range(start_va, end_va, 4):
        foff = vaddr_to_file(va)
        if foff < 0 or foff + 4 > len(exe):
            break
        raw = struct.unpack_from('<I', exe, foff)[0]
        instr = rabbitizer.Instruction(raw)
        instr.vram = va
        asm = instr.disassemble()

        # Decode PS2-specific sq/lq
        if raw & 0xFC000000 == 0x7C000000:
            rt = (raw >> 16) & 0x1F
            base = (raw >> 21) & 0x1F
            offset = raw & 0xFFFF
            if offset >= 0x8000: offset -= 0x10000
            regs = ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
            asm = f"sq          ${regs[rt]}, 0x{offset & 0xFFFF:X}(${regs[base]})"
        elif raw & 0xFC000000 == 0x78000000:
            rt = (raw >> 16) & 0x1F
            base = (raw >> 21) & 0x1F
            offset = raw & 0xFFFF
            if offset >= 0x8000: offset -= 0x10000
            regs = ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
            asm = f"lq          ${regs[rt]}, 0x{offset & 0xFFFF:X}(${regs[base]})"

        marker = ""
        if instr.isJrRa():
            marker = " <-- RETURN"
        if (raw >> 26) == 0x03:
            target = (raw & 0x03FFFFFF) << 2
            marker = f"  -> 0x{target:08X}"

        print(f"  {va:08X}:  {raw:08X}  {asm:50s}{marker}")

# The fallthrough for regular glyph rendering at 0x305828
# (from the b instruction at 0x304380 which branches to 0x304384 + 0x14A4 = 0x305828)
disasm_range(0x00305828, 0x00305A00, "Regular glyph rendering code (fallthrough from switch)")

# Also look at func_303510 which is called multiple times for font display
disasm_range(0x00303510, 0x00303700, "func_303510 - FontDisp setup function")

# Look at the FontDispSetCnt area more carefully
disasm_range(0x00305880, 0x00305A00, "FontDispSetCnt reference area")
