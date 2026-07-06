import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
N=len(data)//4
# gp-relative: find lb/lbu/sb with imm == target & rs==gp(28)
# also find lhu/lh/lw/sw/sh
targets={
 -0x6960:'FLAG_0x4FE690',
 -0x6938:'FLAG_0x4FE6B8',
 -0x68CC:'FLAG_0x4FE724',
 -0x6930:'YIELD_0x4FE6C0',
}
def f2v(off): return off - 0x80 + 0x100000
OPN={0x20:'lb',0x24:'lbu',0x28:'sb',0x21:'lh',0x25:'lhu',0x29:'sh',0x23:'lw',0x2b:'sw'}
for off in range(0,len(data)-3,4):
    w=struct.unpack('<I',data[off:off+4])[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; imm=w&0xffff
    simm=imm-0x10000 if imm&0x8000 else imm
    if op in OPN and rs==28 and simm in targets:
        print(f'0x{f2v(off):08x}: {OPN[op]} r{rt},{simm}(gp)  [{targets[simm]}]')
