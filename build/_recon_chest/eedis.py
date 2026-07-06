import sys, struct
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
data=open(r'C:/programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260623-1835-box-request-formatting/subagents/chest/eeMemory.bin','rb').read()
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)

# manual decode for EE 64-bit ops capstone-mips32 misses
def manual(w):
    op=w>>26
    rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31; sa=(w>>6)&31; fn=w&63
    imm=w&0xFFFF; simm=imm-0x10000 if imm&0x8000 else imm
    R=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
    if op==0:
        if fn==0x3c: return 'dsll32 %s,%s,%d'%(R[rd],R[rt],sa)
        if fn==0x3f: return 'dsra32 %s,%s,%d'%(R[rd],R[rt],sa)
        if fn==0x3e: return 'dsrl32 %s,%s,%d'%(R[rd],R[rt],sa)
        if fn==0x38: return 'dsll %s,%s,%d'%(R[rd],R[rt],sa)
        if fn==0x3a: return 'dsrl %s,%s,%d'%(R[rd],R[rt],sa)
        if fn==0x2d: return 'daddu %s,%s,%s'%(R[rd],R[rs],R[rt])
        if fn==0x2f: return 'dsubu %s,%s,%s'%(R[rd],R[rs],R[rt])
    if op==0x3f: return 'sd %s,0x%x(%s)'%(R[rt],imm,R[rs])
    if op==0x37: return 'ld %s,0x%x(%s)'%(R[rt],imm,R[rs])
    if op==0x18: return 'daddi %s,%s,%d'%(R[rt],R[rs],simm)
    if op==0x19: return 'daddiu %s,%s,%d'%(R[rt],R[rs],simm)
    return None

def go(va,n=40):
    a=va
    end=va+n*4
    while a<end:
        w=struct.unpack_from('<I',data,a)[0]
        ins=list(md.disasm(data[a:a+4], a))
        if ins:
            i=ins[0]
            print('0x%08X  %08X  %-10s %s'%(a, w, i.mnemonic, i.op_str))
        else:
            m=manual(w)
            print('0x%08X  %08X  %s'%(a, w, m if m else '???'))
        a+=4
if __name__=='__main__':
    go(int(sys.argv[1],16), int(sys.argv[2]) if len(sys.argv)>2 else 40)
