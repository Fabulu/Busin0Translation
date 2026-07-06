import struct
PATH=r'C:\programmieren\wizardrytranslation\extracted\SLPM_653.78'
f=open(PATH,'rb').read()
def fo(va): return va-0x100000+0x80
def w(va): return struct.unpack('<I', f[fo(va):fo(va)+4])[0]

REG=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
     's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
def s16(x):
    return x-0x10000 if x&0x8000 else x

def dis(va):
    i=w(va)
    op=i>>26; rs=(i>>21)&31; rt=(i>>16)&31; rd=(i>>11)&31; sh=(i>>6)&31; fn=i&63
    imm=i&0xffff; tgt=(i&0x3ffffff)
    def b(): return '%08X'%i
    if i==0: return 'nop'
    if op==0:
        if fn==0x21: return 'addu %s,%s,%s'%(REG[rd],REG[rs],REG[rt])
        if fn==0x20: return 'add %s,%s,%s'%(REG[rd],REG[rs],REG[rt])
        if fn==0x23: return 'subu %s,%s,%s'%(REG[rd],REG[rs],REG[rt])
        if fn==0x22: return 'sub %s,%s,%s'%(REG[rd],REG[rs],REG[rt])
        if fn==0x24: return 'and %s,%s,%s'%(REG[rd],REG[rs],REG[rt])
        if fn==0x25: return 'or %s,%s,%s'%(REG[rd],REG[rs],REG[rt])
        if fn==0x2a: return 'slt %s,%s,%s'%(REG[rd],REG[rs],REG[rt])
        if fn==0x2b: return 'sltu %s,%s,%s'%(REG[rd],REG[rs],REG[rt])
        if fn==0x00: return 'sll %s,%s,%d'%(REG[rd],REG[rt],sh)
        if fn==0x02: return 'srl %s,%s,%d'%(REG[rd],REG[rt],sh)
        if fn==0x03: return 'sra %s,%s,%d'%(REG[rd],REG[rt],sh)
        if fn==0x04: return 'sllv %s,%s,%s'%(REG[rd],REG[rt],REG[rs])
        if fn==0x08: return 'jr %s'%REG[rs]
        if fn==0x09: return 'jalr %s'%REG[rs]
        return 'special fn=0x%x [%s]'%(fn,b())
    if op==2: return 'j 0x%X'%((va&0xf0000000)|(tgt<<2))
    if op==3: return 'jal 0x%X'%((va&0xf0000000)|(tgt<<2))
    if op==4: return 'beq %s,%s,0x%X'%(REG[rs],REG[rt],va+4+(s16(imm)<<2))
    if op==5: return 'bne %s,%s,0x%X'%(REG[rs],REG[rt],va+4+(s16(imm)<<2))
    if op==6: return 'blez %s,0x%X'%(REG[rs],va+4+(s16(imm)<<2))
    if op==7: return 'bgtz %s,0x%X'%(REG[rs],va+4+(s16(imm)<<2))
    if op==1:
        if rt==0: return 'bltz %s,0x%X'%(REG[rs],va+4+(s16(imm)<<2))
        if rt==1: return 'bgez %s,0x%X'%(REG[rs],va+4+(s16(imm)<<2))
        return 'regimm rt=%d [%s]'%(rt,b())
    if op==8: return 'addi %s,%s,0x%X'%(REG[rt],REG[rs],imm)
    if op==9: return 'addiu %s,%s,%d (0x%X)'%(REG[rt],REG[rs],s16(imm),imm)
    if op==0xa: return 'slti %s,%s,%d'%(REG[rt],REG[rs],s16(imm))
    if op==0xb: return 'sltiu %s,%s,0x%X'%(REG[rt],REG[rs],imm)
    if op==0xc: return 'andi %s,%s,0x%X'%(REG[rt],REG[rs],imm)
    if op==0xd: return 'ori %s,%s,0x%X'%(REG[rt],REG[rs],imm)
    if op==0xe: return 'xori %s,%s,0x%X'%(REG[rt],REG[rs],imm)
    if op==0xf: return 'lui %s,0x%X'%(REG[rt],imm)
    if op==0x20: return 'lb %s,0x%X(%s)'%(REG[rt],imm,REG[rs])
    if op==0x21: return 'lh %s,0x%X(%s)'%(REG[rt],imm,REG[rs])
    if op==0x23: return 'lw %s,%d(%s) (0x%X)'%(REG[rt],s16(imm),REG[rs],imm)
    if op==0x24: return 'lbu %s,0x%X(%s)'%(REG[rt],imm,REG[rs])
    if op==0x25: return 'lhu %s,0x%X(%s)'%(REG[rt],imm,REG[rs])
    if op==0x28: return 'sb %s,0x%X(%s)'%(REG[rt],imm,REG[rs])
    if op==0x29: return 'sh %s,0x%X(%s)'%(REG[rt],imm,REG[rs])
    if op==0x2b: return 'sw %s,%d(%s) (0x%X)'%(REG[rt],s16(imm),REG[rs],imm)
    return 'op=0x%x [%s]'%(op,b())

def dump(start,end):
    va=start
    while va<end:
        print('%08X: %08X  %s'%(va,w(va),dis(va)))
        va+=4

if __name__=='__main__':
    import sys
    a=int(sys.argv[1],16); b=int(sys.argv[2],16)
    dump(a,b)
