import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def f2v(off): return off - 0x80 + 0x100000
OPN={0x20:'lb',0x24:'lbu',0x28:'sb',0x21:'lh',0x25:'lhu',0x29:'sh',0x23:'lw',0x2b:'sw'}
target=int(sys.argv[1]) # signed gp offset
for off in range(0,len(data)-3,4):
    w=struct.unpack('<I',data[off:off+4])[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; imm=w&0xffff
    simm=imm-0x10000 if imm&0x8000 else imm
    if op in OPN and rs==28 and simm==target:
        print(f'0x{f2v(off):08x}: {OPN[op]} r{rt},{simm}(gp)')
