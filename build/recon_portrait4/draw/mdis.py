import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def v2f(va): return va - 0x100000 + 0x80
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
REG=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
     's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
def ee(w):
    # decode EE-specific that capstone misses; return string or None
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31; sa=(w>>6)&31; fn=w&63
    if op==0 and fn==0x2D: # daddu
        if rt==0: return f"move   ${REG[rd]}, ${REG[rs]}"
        return f"daddu  ${REG[rd]}, ${REG[rs]}, ${REG[rt]}"
    if op==0 and fn==0x2C: return f"dadd   ${REG[rd]}, ${REG[rs]}, ${REG[rt]}"
    if op==0 and fn==0x2F: return f"dsubu  ${REG[rd]}, ${REG[rs]}, ${REG[rt]}"
    if op==0 and fn==0x14: return f"dsllv  ${REG[rd]}, ${REG[rt]}, ${REG[rs]}"
    if op==0 and fn==0x16: return f"dsrlv  ${REG[rd]}, ${REG[rt]}, ${REG[rs]}"
    if op==0x1F: return f"(special3 fn=0x{fn:02X})"
    return None
def show(va, n=100):
    off=v2f(va)
    for i in range(n):
        a=va+i*4; chunk=data[off+i*4:off+i*4+4]; w=struct.unpack('<I',chunk)[0]
        g=list(md.disasm(chunk, a))
        if g and g[0].mnemonic not in ('subu.qb','ext','dpa.w.ph','addu.qb','.word'):
            ins=g[0]; print(f"  0x{a:08X}: {chunk.hex()}  {ins.mnemonic:9} {ins.op_str}")
        else:
            d=ee(w)
            print(f"  0x{a:08X}: {chunk.hex()}  {d if d else ('.word 0x%08X'%w)}")
if __name__=='__main__':
    va=int(sys.argv[1],16); n=int(sys.argv[2]) if len(sys.argv)>2 else 100
    print(f"=== VA 0x{va:08X} file 0x{v2f(va):X} ===")
    show(va,n)
