import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
from capstone import *
data=open('extracted/SLPM_653.78','rb').read()
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
prev=None
found=[]
for off in range(0, 0x80000, 4):
    va=0x100000+off
    w=data[0x80+off:0x80+off+4]
    ins=list(md.disasm(w,va))
    if not ins:
        prev=None; continue
    ins=ins[0]
    if ins.mnemonic=='lui' and '$gp' in ins.op_str:
        hi=int(ins.op_str.split(',')[-1].strip(),16)
        prev=(va,hi)
    elif prev and ins.mnemonic in ('addiu','ori') and ins.op_str.count('$gp')>=2:
        lop=ins.op_str.split(',')[-1].strip()
        lo=int(lop,16)
        if ins.mnemonic=='addiu' and lo>=0x8000: lo-=0x10000
        gp=(prev[1]<<16)+lo
        print('gp setup at',hex(va),'gp=',hex(gp&0xffffffff))
        found.append(gp&0xffffffff)
        prev=None
        if len(found)>3: break
    else:
        prev=None
print('uniq',[hex(x) for x in set(found)])
