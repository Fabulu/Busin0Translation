import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def f2v(off): return off - 0x80 + 0x100000
def v2f(va): return va - 0x100000 + 0x80
targets=[int(x,16) for x in sys.argv[1:]]
for off in range(0,len(data)-3,4):
    w=struct.unpack('<I',data[off:off+4])[0]
    op=w>>26
    if op==3: # jal
        tgt=((f2v(off)+4)&0xf0000000)|((w&0x3ffffff)<<2)
        if tgt in targets:
            print(f'0x{f2v(off):08x}: jal 0x{tgt:08x}')
