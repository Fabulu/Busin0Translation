import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE="C:/programmieren/wizardrytranslation/extracted/SLPM_653.78"
D=open(EXE,'rb').read()
def v2f(va): return va-0x100000+0x80
def f2v(o): return o-0x80+0x100000
target=int(sys.argv[1],16)
tw=(0x0c000000)|((target>>2)&0x03ffffff)  # jal encoding (assumes same 256MB region)
# search whole text
TEXT_LO,TEXT_HI=0x100000,0x400000
for off in range(v2f(TEXT_LO),v2f(TEXT_HI),4):
    w=struct.unpack_from('<I',D,off)[0]
    if (w>>26)==3:  # jal
        tgt=((w&0x03ffffff)<<2)|0x10000000  # jal uses upper bits of delay slot PC; region 0x1xxxxxx
        # actual: target = (PC & 0xF0000000) | (idx<<2). PC ~0x3xxxxx within 0x000xxxxx region
        idx=(w&0x03ffffff)<<2
        full=0x00000000|idx
        if full==target:
            print(f"{f2v(off):08x}: jal 0x{target:06x}")
