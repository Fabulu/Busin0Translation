"""Disassemble func_302910 (glyph setup) and func_302DB0 (glyph render)."""
import struct
import rabbitizer

exe = open('extracted/SLPM_653.78', 'rb').read()

P_OFFSET = 0x80
P_VADDR = 0x00100000

def vaddr_to_file(va):
    return va - P_VADDR + P_OFFSET

def file_to_vaddr(foff):
    return P_VADDR + (foff - P_OFFSET)

regs = ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
        's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']

def disasm_func_until_ret(start_va, label="", max_instrs=300):
    print(f"\n{'='*72}")
    if label:
        print(f"{label}")
    print(f"Start: 0x{start_va:08X}")
    print(f"{'='*72}")

    found_ret = False
    for i in range(max_instrs):
        va = start_va + i * 4
        foff = vaddr_to_file(va)
        if foff < 0 or foff + 4 > len(exe):
            break
        raw = struct.unpack_from('<I', exe, foff)[0]
        instr = rabbitizer.Instruction(raw)
        instr.vram = va
        asm = instr.disassemble()

        # PS2-specific sq/lq
        op_hi = (raw >> 26) & 0x3F
        if op_hi == 0x1F:  # SQ
            rt = (raw >> 16) & 0x1F
            base = (raw >> 21) & 0x1F
            offset = raw & 0xFFFF
            if offset >= 0x8000: offset -= 0x10000
            asm = f"sq          ${regs[rt]}, 0x{offset & 0xFFFF:X}(${regs[base]})"
        elif op_hi == 0x1E:  # LQ
            rt = (raw >> 16) & 0x1F
            base = (raw >> 21) & 0x1F
            offset = raw & 0xFFFF
            if offset >= 0x8000: offset -= 0x10000
            asm = f"lq          ${regs[rt]}, 0x{offset & 0xFFFF:X}(${regs[base]})"

        marker = ""
        if instr.isJrRa():
            marker = " <-- RETURN"
        if (raw >> 26) == 0x03:
            target = (raw & 0x03FFFFFF) << 2
            marker = f"  -> 0x{target:08X}"

        print(f"  {va:08X}:  {raw:08X}  {asm:50s}{marker}")

        if found_ret:
            break  # printed delay slot
        if instr.isJrRa():
            found_ret = True

# func_302910 - appears to set up the glyph for rendering
disasm_func_until_ret(0x00302910, "func_302910 - Glyph character setup")

# func_302DB0 - appears to handle glyph rendering/drawing
disasm_func_until_ret(0x00302DB0, "func_302DB0 - Glyph render/draw")
