import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data = open(r"C:/programmieren/wizardrytranslation/extracted/SLPM_653.78",'rb').read()
FILE_BASE = 0xFFF80
target_va = int(sys.argv[1],16)
# jal encodes target = (instr_index<<2) within 256MB region; addr26 = (target>>2)&0x3FFFFFF
field = (target_va>>2) & 0x03FFFFFF
out=[]
for off in range(0x100000, min(len(data),0x500000),4):
    w = struct.unpack_from('<I',data,off)[0]
    op = w>>26
    if op==3:  # jal
        if (w & 0x03FFFFFF)==field:
            va = off+FILE_BASE
            out.append(f"jal from va=0x{va:08X}")
print(f"callers of 0x{target_va:08X}:")
print("\n".join(out) if out else "  (none found)")
