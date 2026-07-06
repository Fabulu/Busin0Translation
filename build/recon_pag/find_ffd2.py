import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='extracted/SLPM_653.78'; BASE=0x100000; FOFF=0x80
data=open(EXE,'rb').read()
for tgt in (0xFFD2,0xFFFE,0xFFFF,0xFFD0,0xFFD1,0xFFD3):
    hits=[]
    for off in range(FOFF,len(data)-4,4):
        w=struct.unpack_from('<I',data,off)[0]
        op=w>>26
        # addiu/ori/andi with imm == tgt, or lui
        if op in (9,0xd,0xc) and (w&0xffff)==tgt:
            hits.append(off-FOFF+BASE)
    print("imm 0x%04X: %d hits: %s"%(tgt,len(hits),['0x%08x'%h for h in hits[:12]]))
