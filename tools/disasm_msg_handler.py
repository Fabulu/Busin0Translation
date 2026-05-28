"""Disassemble the MSG control code handler and character rendering functions."""
import struct
import rabbitizer

exe = open('extracted/SLPM_653.78', 'rb').read()

P_OFFSET = 0x80
P_VADDR = 0x00100000

def file_to_vaddr(foff):
    return P_VADDR + (foff - P_OFFSET)

def vaddr_to_file(va):
    return va - P_VADDR + P_OFFSET

def disasm_func(start_va, max_len=0x400, label=""):
    """Disassemble a function from start_va until jr $ra + delay slot."""
    print(f"\n{'='*72}")
    if label:
        print(f"{label}")
    print(f"Start: 0x{start_va:08X}")
    print(f"{'='*72}")

    ret_count = 0
    for i in range(0, max_len, 4):
        va = start_va + i
        foff = vaddr_to_file(va)
        if foff < 0 or foff + 4 > len(exe):
            break
        raw = struct.unpack_from('<I', exe, foff)[0]
        instr = rabbitizer.Instruction(raw)
        instr.vram = va
        asm = instr.disassemble()

        # Decode PS2-specific instructions
        opcode_hi = (raw >> 26) & 0x3F
        if raw & 0xFC000000 == 0x7C000000:  # SQ (store quadword)
            rt = (raw >> 16) & 0x1F
            base = (raw >> 21) & 0x1F
            offset = raw & 0xFFFF
            if offset >= 0x8000:
                offset -= 0x10000
            asm = f"sq          ${['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra'][rt]}, 0x{offset & 0xFFFF:X}(${['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra'][base]})"

        marker = ""
        if instr.isJrRa():
            marker = " <-- RETURN"

        # Annotate JAL targets
        if (raw >> 26) == 0x03:  # JAL
            target = (raw & 0x03FFFFFF) << 2
            marker = f"  -> 0x{target:08X}"

        print(f"  {va:08X}:  {raw:08X}  {asm:50s}{marker}")

# 1. func_302990: reads 16-bit BE glyph code from MSG data
disasm_func(0x00302990, 0x20, "func_302990: Read 16-bit BE glyph code")

# 2. func_3029B0: control code dispatcher (the big switch on glyph values)
disasm_func(0x003029B0, 0x400, "func_3029B0: MSG control code dispatcher")

# 3. The main text renderer at 0x303C60 - let's get the full function
disasm_func(0x00303C60, 0x2000, "func_303C60: Main TextEvent renderer (full)")
