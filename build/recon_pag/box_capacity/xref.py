import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
f=open('extracted/SLPM_653.78','rb').read()
target=int(sys.argv[1],16)
seg=f[0x80:0x80+0x3fdc80]
# jal target = (instr & 0x03ffffff)<<2 within 256MB region; pc-region from 0x100000
hits=[]
for i in range(0,len(seg)-4,4):
    w=struct.unpack_from('<I',seg,i)[0]
    op=w>>26
    if op==3: # jal
        tgt=((0x100000+i)&0xf0000000)|((w&0x03ffffff)<<2)
        if tgt==target:
            hits.append(0x100000+i)
print('xrefs to',hex(target),':',len(hits))
for h in hits: print(hex(h))
