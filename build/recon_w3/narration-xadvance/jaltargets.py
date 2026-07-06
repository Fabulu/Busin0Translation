import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE="C:/programmieren/wizardrytranslation/extracted/SLPM_653.78"
D=open(EXE,'rb').read()
def v2f(va): return va-0x100000+0x80
def f2v(o): return o-0x80+0x100000
lo=int(sys.argv[1],16); hi=int(sys.argv[2],16)
for off in range(v2f(lo),v2f(hi),4):
    w=struct.unpack_from('<I',D,off)[0]
    if (w>>26)==3:
        tgt=(w&0x03ffffff)<<2
        print(f"{f2v(off):08x}: jal 0x{tgt:06x}")
