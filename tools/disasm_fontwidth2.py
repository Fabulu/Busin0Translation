"""Disassemble a wider range around the font width reader to find function boundaries."""
import struct
import rabbitizer

exe = open('extracted/SLPM_653.78', 'rb').read()

# From ELF: Segment 0 LOAD offset=0x80 vaddr=0x00100000
# So file_offset = vaddr - 0x100000 + 0x80
# vaddr = file_offset - 0x80 + 0x100000
P_OFFSET = 0x80
P_VADDR = 0x00100000

def file_to_vaddr(foff):
    return P_VADDR + (foff - P_OFFSET)

def vaddr_to_file(va):
    return va - P_VADDR + P_OFFSET

# Disassemble wider range: 0x01A400 to 0x01A900
start_foff = 0x01A400
end_foff = 0x01A900

print(f"Disassembly from file offset 0x{start_foff:X} to 0x{end_foff:X}")
print(f"Vaddr range: 0x{file_to_vaddr(start_foff):08X} to 0x{file_to_vaddr(end_foff):08X}")
print(f"{'='*72}")

prev_was_jr_ra = False
for off in range(start_foff, end_foff, 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    vaddr = file_to_vaddr(off)
    instr = rabbitizer.Instruction(raw)
    instr.vram = vaddr
    asm = instr.disassemble()

    # Mark likely function boundaries
    marker = ""
    if prev_was_jr_ra and not instr.isNop():
        # Instruction after jr ra delay slot - likely new function
        pass
    if instr.isJrRa():
        marker = "  <-- return"
    if instr.isNop() and prev_was_jr_ra:
        marker = "  <-- func boundary?"

    print(f"  {vaddr:08X}:  {raw:08X}  {asm:40s}{marker}")
    prev_was_jr_ra = instr.isJrRa()
