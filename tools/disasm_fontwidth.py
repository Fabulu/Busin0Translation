"""Disassemble the font width reader function from the PS2 game EXE using rabbitizer."""
import struct
import rabbitizer

exe = open('extracted/SLPM_653.78', 'rb').read()

# PS2 EXE base address: the ELF loads at 0x00100000 typically
# File offset 0x01A5C0 corresponds to vaddr 0x00100000 + 0x01A5C0 = 0x001BA5C0
# But let's check - PS2 ELF header tells us the actual load address
# For now, use a reasonable base

# Read ELF header to find text segment load address
# e_entry is at offset 0x18 (4 bytes for 32-bit ELF)
e_entry = struct.unpack_from('<I', exe, 0x18)[0]
print(f"ELF entry point: 0x{e_entry:08X}")

# Program header offset
e_phoff = struct.unpack_from('<I', exe, 0x1C)[0]
e_phentsize = struct.unpack_from('<H', exe, 0x2A)[0]
e_phnum = struct.unpack_from('<H', exe, 0x2C)[0]
print(f"Program headers: {e_phnum} entries at offset 0x{e_phoff:X}, size {e_phentsize}")

# Read first LOAD segment to find base vaddr and file offset
for i in range(e_phnum):
    ph_off = e_phoff + i * e_phentsize
    p_type = struct.unpack_from('<I', exe, ph_off)[0]
    p_offset = struct.unpack_from('<I', exe, ph_off + 4)[0]
    p_vaddr = struct.unpack_from('<I', exe, ph_off + 8)[0]
    p_filesz = struct.unpack_from('<I', exe, ph_off + 16)[0]
    p_memsz = struct.unpack_from('<I', exe, ph_off + 20)[0]
    type_name = {1: "LOAD", 0x70000000: "MIPS_REGINFO"}.get(p_type, f"0x{p_type:X}")
    print(f"  Segment {i}: type={type_name} offset=0x{p_offset:X} vaddr=0x{p_vaddr:08X} filesz=0x{p_filesz:X} memsz=0x{p_memsz:X}")

# For PS2 SLPM EXEs, the text typically starts at file offset 0x1000 mapping to some vaddr
# Let's find the LOAD segment that contains our offset
file_offset = 0x01A5C0
for i in range(e_phnum):
    ph_off = e_phoff + i * e_phentsize
    p_type = struct.unpack_from('<I', exe, ph_off)[0]
    if p_type != 1:  # LOAD
        continue
    p_offset = struct.unpack_from('<I', exe, ph_off + 4)[0]
    p_vaddr = struct.unpack_from('<I', exe, ph_off + 8)[0]
    p_filesz = struct.unpack_from('<I', exe, ph_off + 16)[0]
    if p_offset <= file_offset < p_offset + p_filesz:
        vaddr_base = p_vaddr + (file_offset - p_offset)
        print(f"\nFile offset 0x{file_offset:X} maps to vaddr 0x{vaddr_base:08X}")
        break

print(f"\n{'='*60}")
print(f"Font width reader function (file offset 0x01A5C0 - 0x01A700):")
print(f"{'='*60}")

for off in range(0x01A5C0, 0x01A700, 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    # Calculate vaddr
    vaddr = p_vaddr + (off - p_offset)
    instr = rabbitizer.Instruction(raw)
    instr.vram = vaddr
    asm = instr.disassemble()
    raw_hex = f"{raw:08X}"
    print(f"  {vaddr:08X}:  {raw_hex}  {asm}")
