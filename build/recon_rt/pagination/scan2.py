import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data = open(r"C:/programmieren/wizardrytranslation/extracted/SLPM_653.78",'rb').read()
FILE_BASE = 0xFFF80
targets = {0xFFD2:'FFD2', 0xFFFE:'FFFE', 0xFFD0:'FFD0', 0xFFD3:'FFD3', 0xFFD1:'FFD1'}
# Search dialogue render region VA 0x2E0000..0x310000
lo = 0x2E0000 - FILE_BASE
hi = 0x312000 - FILE_BASE
out=[]
for off in range(lo, hi, 4):
    w = struct.unpack_from('<I', data, off)[0]
    imm = w & 0xFFFF
    op = w >> 26
    if imm in targets and op in (0x08,0x09,0x0C,0x0D,0x0A,0x0B,0x0F):
        va = off + FILE_BASE
        out.append(f"va=0x{va:08X} word=0x{w:08X} op=0x{op:02X} imm=0x{imm:04X}({targets[imm]})")
print("\n".join(out) if out else "NO FFD2/FFFE/FFD0/FFD1/FFD3 immediates in 0x2E0000-0x312000")
