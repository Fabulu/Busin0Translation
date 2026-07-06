import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def f2v(off): return off - 0x80 + 0x100000
targets=[int(x,16) for x in sys.argv[1:]]
for off in range(0,len(data)-3,4):
    w=struct.unpack('<I',data[off:off+4])[0]
    if w in targets:
        print(f'word @file_off 0x{off:06x} (va 0x{f2v(off):08x}) == 0x{w:08x}')
