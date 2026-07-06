import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
DATA=open('extracted/SLPM_653.78','rb').read()
BASE_VA=0x100000; BASE_OFF=0x80
def off2va(off): return off-BASE_OFF+BASE_VA
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
# find lw/sw with gp offset == target signed16
target=int(sys.argv[1],16)  # e.g 0x9dcc -> but it's signed -0x6234
# we scan for instructions whose immediate (lower16) == target and base reg==gp(28)
seg=DATA[BASE_OFF:BASE_OFF+0x3fdc80]
for i in range(0,len(seg)-4,4):
    w=struct.unpack('<I',seg[i:i+4])[0]
    op=w>>26
    rs=(w>>21)&0x1f
    imm=w&0xffff
    # lw=0x23 sw=0x2b lhu=0x25 lh=0x21 lbu=0x24 sb=0x28 sh=0x29 lwc1=0x31 swc1=0x39
    if op in (0x23,0x2b,0x25,0x21,0x24,0x28,0x29,0x31,0x39) and rs==28 and imm==(target&0xffff):
        va=off2va(i+BASE_OFF)
        ins=list(md.disasm(seg[i:i+4],va))
        if ins:
            print(f"0x{va:08x}: {ins[0].mnemonic} {ins[0].op_str}")
