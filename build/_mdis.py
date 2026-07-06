import sys, struct
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
sys.stdout.reconfigure(encoding='utf-8')
EXE='extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def v2f(va): return va-0xFFF80
REG=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
     's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
def decode_one(w, va):
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31; sa=(w>>6)&31; fn=w&63
    imm=w&0xFFFF; simm=imm-0x10000 if imm&0x8000 else imm
    # R5900 special opcodes capstone misses: daddu(move), sw, sd, sq, lq, lw, etc handled by capstone normally
    # We handle the ones capstone marks .byte: daddu(0x2D) special, sd(0x3F), sq(0x1F? actually 0x1F), lq(0x1E)
    if op==0: # SPECIAL
        if fn==0x2D: # daddu
            if rt==0: return 'move      $%s,$%s'%(REG[rd],REG[rs])
            return 'daddu     $%s,$%s,$%s'%(REG[rd],REG[rs],REG[rt])
        if fn==0x2C: return 'dadd      $%s,$%s,$%s'%(REG[rd],REG[rs],REG[rt])
    if op==0x3F: return 'sd        $%s,%d($%s)'%(REG[rt],simm,REG[rs])
    if op==0x37: return 'ld        $%s,%d($%s)'%(REG[rt],simm,REG[rs])
    if op==0x1E: return 'lq        $%s,%d($%s)'%(REG[rt],simm,REG[rs])
    if op==0x1F: return 'sq        $%s,%d($%s)'%(REG[rt],simm,REG[rs])
    return None
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
md.skipdata=True
def disas(va, n=80):
    off=v2f(va)
    code=data[off:off+n*4]
    for ins in md.disasm(code, va):
        if ins.mnemonic=='.byte':
            w=struct.unpack_from('<I',data,v2f(ins.address))[0]
            dec=decode_one(w, ins.address)
            if dec:
                print('0x%08X  %s'%(ins.address,dec)); continue
        print('0x%08X  %-9s %s' % (ins.address, ins.mnemonic, ins.op_str))
if __name__=='__main__':
    va=int(sys.argv[1],16)
    n=int(sys.argv[2]) if len(sys.argv)>2 else 80
    disas(va,n)
