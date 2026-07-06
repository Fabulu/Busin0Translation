import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def f2v(off): return off - 0x80 + 0x100000
target=int(sys.argv[1],16)
# track lui per-register then addiu to form target, scanning linearly
luis={}
for off in range(0,len(data)-3,4):
    w=struct.unpack('<I',data[off:off+4])[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; imm=w&0xffff
    if op==0x0f:
        luis[rt]=(imm,off)
    elif op==9: # addiu rt,rs,imm
        if rs in luis:
            hi,lo_off=luis[rs]
            base=hi<<16
            simm=imm-0x10000 if imm&0x8000 else imm
            if (base+simm)&0xffffffff==target:
                print(f'0x{f2v(off):08x}: addiu r{rt},r{rs},{simm}  (lui@0x{f2v(lo_off):08x}) -> 0x{target:08x}')
        if rt!=rs and rt in luis:
            del luis[rt]
