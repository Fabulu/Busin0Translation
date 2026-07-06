import sys, struct, re
from capstone import *
sys.stdout.reconfigure(encoding='utf-8')
EXE=r'C:\programmieren\wizardrytranslation\extracted\SLPM_653.78'
def v2f(va): return va - 0x100000 + 0x80
data=open(EXE,'rb').read()
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64 | CS_MODE_LITTLE_ENDIAN)
# scan broad: every 'lw reg,0x290(base)' that is a READ (followed by andi within 6 insns), print window
start=0x130000; end=0x3B0000
for va in range(start,end,4):
    ins=list(md.disasm(data[v2f(va):v2f(va)+4],va))
    if not ins: continue
    i=ins[0]
    if i.mnemonic=='lw' and '0x290(' in i.op_str:
        dst=i.op_str.split(',')[0]
        # look ahead up to 6 insns for andi/and on dst with imm bit
        win=[]
        gate=None
        for k in range(1,7):
            va2=va+4*k
            j=list(md.disasm(data[v2f(va2):v2f(va2)+4],va2))
            if not j: break
            jj=j[0]; win.append(jj.mnemonic+' '+jj.op_str)
            if jj.mnemonic in ('andi','and') and dst in jj.op_str:
                gate=jj.op_str
            if jj.mnemonic in ('beqz','bnez','bne','beq') : 
                win.append('<branch>'); 
        if gate and ('4' in gate.split(',')[-1] or '0x4' in gate):
            print(f"{va:08X}: lw {i.op_str} ; "+' | '.join(win))
