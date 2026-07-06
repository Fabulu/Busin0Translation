import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='extracted/SLPM_653.78'; BASE=0x100000; FOFF=0x80
data=open(EXE,'rb').read()
# find sw/sh/sb to offset 0x290 / 0x298 (these are immediate fields). store: op 0x28(sb)0x29(sh)0x2b(sw)
# We look for store with imm==0x290 or 0x298 (and also lw/lh reads)
targets={0x290:'290',0x298:'298',0x29e:'29e',0x2a0:'2a0',0x2a6:'2a6',0x2a7:'2a7'}
for off in range(FOFF,len(data)-4,4):
    w=struct.unpack_from('<I',data,off)[0]
    op=w>>26
    imm=w&0xffff
    if imm in targets and op in (0x28,0x29,0x2b,0x20,0x21,0x23,0x24,0x25):
        kind={0x28:'sb',0x29:'sh',0x2b:'sw',0x20:'lb',0x21:'lh',0x23:'lw',0x24:'lbu',0x25:'lhu'}[op]
        rs=(w>>21)&31; rt=(w>>16)&31
        va=off-FOFF+BASE
        print("0x%08x: %-3s rt=%d base=%d off=0x%x"%(va,kind,rt,rs,imm))
