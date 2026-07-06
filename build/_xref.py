import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def v2f(va): return va-0xFFF80
target=int(sys.argv[1],16)
# JAL encoding: op=3, target = (instr&0x3FFFFFF)<<2 within 256MB region
# PS2 text seg base 0x100000 area. compute jal target
base_va=0x100000
n=len(data)//4
hits=[]
for i in range(n):
    w=struct.unpack_from('<I',data,i*4)[0]
    op=w>>26
    if op==3 or op==2: # jal / j
        tgt=((w&0x3FFFFFF)<<2) | 0
        # region top bits from current pc
        va=base_va + i*4   # file offset 0x80 maps va 0x100000; v2f= va-0xFFF80 so va= off+0xFFF80
        va=(i*4)+0xFFF80
        full=(va & 0xF0000000) | tgt
        if full==target:
            kind='jal' if op==3 else 'j'
            hits.append((va,kind))
for va,kind in hits:
    print('0x%08X  %s 0x%08X'%(va,kind,target))
print('total',len(hits))
