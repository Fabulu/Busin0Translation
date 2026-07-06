import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='extracted/SLPM_653.78'; BASE=0x100000; FOFF=0x80
data=open(EXE,'rb').read()
def v2f(v): return v-BASE+FOFF
tgt=int(sys.argv[1],16)&0xffff  # gp offset signed
for off in range(FOFF,len(data)-4,4):
    w=struct.unpack_from('<I',data,off)[0]
    op=w>>26; base=(w>>21)&31; imm=w&0xffff
    if base==28 and imm==tgt and op in (0x20,0x21,0x23,0x24,0x25,0x28,0x29,0x2b):
        kind={0x20:'lb',0x21:'lh',0x23:'lw',0x24:'lbu',0x25:'lhu',0x28:'sb',0x29:'sh',0x2b:'sw'}[op]
        rt=(w>>16)&31
        print("0x%08x: %-3s gp[0x%04x] rt=%d"%(off-FOFF+BASE,kind,tgt,rt))
