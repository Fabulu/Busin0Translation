import sys
sys.stdout.reconfigure(encoding='utf-8')
data = open(r"C:/programmieren/wizardrytranslation/extracted/SLPM_653.78",'rb').read()
FILE_BASE = 0xFFF80
# MIPS immediate for these constants appears in ori/addiu/slti etc as low 16 bits.
# Search code region for instructions loading 0xFFD2, 0xFFFE, 0xFFFF, 0x8000 immediates.
import struct
targets = {0xFFD2:'FFD2', 0xFFFE:'FFFE', 0xFFFF:'FFFF', 0xFFD1:'FFD1', 0xFFD3:'FFD3'}
# scan code section roughly 0x100000..0x600000 file offsets
for off in range(0x100000, min(len(data), 0x4FFFFF), 4):
    w = struct.unpack_from('<I', data, off)[0]
    imm = w & 0xFFFF
    op = w >> 26
    if imm in targets and op in (0x08,0x09,0x0C,0x0D,0x0A,0x0B,0x0F):  # addiu/addi/andi/ori/slti/sltiu/lui
        va = off + FILE_BASE
        print(f"off=0x{off:06X} va=0x{va:08X} word=0x{w:08X} op=0x{op:02X} imm=0x{imm:04X}({targets[imm]})")
