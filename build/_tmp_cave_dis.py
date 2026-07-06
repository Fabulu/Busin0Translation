import struct, sys

REGS=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
      's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']

def dis(word, va):
    op=(word>>26)&0x3f
    rs=(word>>21)&0x1f; rt=(word>>16)&0x1f; rd=(word>>11)&0x1f
    sa=(word>>6)&0x1f; funct=word&0x3f
    imm=word&0xffff
    simm=imm-0x10000 if imm&0x8000 else imm
    tgt=(word&0x3ffffff)
    R=REGS
    if word==0: return 'nop'
    if op==0:
        if funct==0x20: return 'add %s,%s,%s'%(R[rd],R[rs],R[rt])
        if funct==0x21: return 'addu %s,%s,%s'%(R[rd],R[rs],R[rt])
        if funct==0x22: return 'sub %s,%s,%s'%(R[rd],R[rs],R[rt])
        if funct==0x23: return 'subu %s,%s,%s'%(R[rd],R[rs],R[rt])
        if funct==0x24: return 'and %s,%s,%s'%(R[rd],R[rs],R[rt])
        if funct==0x25: return 'or %s,%s,%s'%(R[rd],R[rs],R[rt])
        if funct==0x26: return 'xor %s,%s,%s'%(R[rd],R[rs],R[rt])
        if funct==0x27: return 'nor %s,%s,%s'%(R[rd],R[rs],R[rt])
        if funct==0x2a: return 'slt %s,%s,%s'%(R[rd],R[rs],R[rt])
        if funct==0x2b: return 'sltu %s,%s,%s'%(R[rd],R[rs],R[rt])
        if funct==0x00: return 'sll %s,%s,%d'%(R[rd],R[rt],sa)
        if funct==0x02: return 'srl %s,%s,%d'%(R[rd],R[rt],sa)
        if funct==0x03: return 'sra %s,%s,%d'%(R[rd],R[rt],sa)
        if funct==0x04: return 'sllv %s,%s,%s'%(R[rd],R[rt],R[rs])
        if funct==0x06: return 'srlv %s,%s,%s'%(R[rd],R[rt],R[rs])
        if funct==0x08: return 'jr %s'%R[rs]
        if funct==0x09: return 'jalr %s,%s'%(R[rd],R[rs])
        if funct==0x10: return 'mfhi %s'%R[rd]
        if funct==0x12: return 'mflo %s'%R[rd]
        if funct==0x18: return 'mult %s,%s'%(R[rs],R[rt])
        if funct==0x19: return 'multu %s,%s'%(R[rs],R[rt])
        if funct==0x1a: return 'div %s,%s'%(R[rs],R[rt])
        if funct==0x1b: return 'divu %s,%s'%(R[rs],R[rt])
        return '.word 0x%08x (sp funct=0x%02x)'%(word,funct)
    if op==2: return 'j 0x%08x'%((va&0xf0000000)|(tgt<<2))
    if op==3: return 'jal 0x%08x'%((va&0xf0000000)|(tgt<<2))
    if op==4:
        if rs==0 and rt==0: return 'b 0x%08x'%(va+4+(simm<<2))
        return 'beq %s,%s,0x%08x'%(R[rs],R[rt],va+4+(simm<<2))
    if op==5: return 'bne %s,%s,0x%08x'%(R[rs],R[rt],va+4+(simm<<2))
    if op==6: return 'blez %s,0x%08x'%(R[rs],va+4+(simm<<2))
    if op==7: return 'bgtz %s,0x%08x'%(R[rs],va+4+(simm<<2))
    if op==1:
        if rt==0: return 'bltz %s,0x%08x'%(R[rs],va+4+(simm<<2))
        if rt==1: return 'bgez %s,0x%08x'%(R[rs],va+4+(simm<<2))
        if rt==0x11: return 'bgezal %s,0x%08x'%(R[rs],va+4+(simm<<2))
        return '.word 0x%08x (regimm rt=%d)'%(word,rt)
    if op==8: return 'addi %s,%s,%d'%(R[rt],R[rs],simm)
    if op==9: return 'addiu %s,%s,%d'%(R[rt],R[rs],simm)
    if op==10: return 'slti %s,%s,%d'%(R[rt],R[rs],simm)
    if op==11: return 'sltiu %s,%s,%d'%(R[rt],R[rs],simm)
    if op==12: return 'andi %s,%s,0x%x'%(R[rt],R[rs],imm)
    if op==13: return 'ori %s,%s,0x%x'%(R[rt],R[rs],imm)
    if op==14: return 'xori %s,%s,0x%x'%(R[rt],R[rs],imm)
    if op==15: return 'lui %s,0x%x'%(R[rt],imm)
    if op==0x20: return 'lb %s,%d(%s)'%(R[rt],simm,R[rs])
    if op==0x21: return 'lh %s,%d(%s)'%(R[rt],simm,R[rs])
    if op==0x23: return 'lw %s,%d(%s)'%(R[rt],simm,R[rs])
    if op==0x24: return 'lbu %s,%d(%s)'%(R[rt],simm,R[rs])
    if op==0x25: return 'lhu %s,%d(%s)'%(R[rt],simm,R[rs])
    if op==0x28: return 'sb %s,%d(%s)'%(R[rt],simm,R[rs])
    if op==0x29: return 'sh %s,%d(%s)'%(R[rt],simm,R[rs])
    if op==0x2b: return 'sw %s,%d(%s)'%(R[rt],simm,R[rs])
    if op==0x37: return 'ld %s,%d(%s)'%(R[rt],simm,R[rs])
    if op==0x3f: return 'sd %s,%d(%s)'%(R[rt],simm,R[rs])
    return '.word 0x%08x (op=0x%02x)'%(word,op)

def dump(path, start, end, label):
    f=open(path,'rb');
    print('=== %s : %s  [0x%08x..0x%08x] ==='%(label,path.split('/')[-1],start,end))
    f.seek(start)
    data=f.read(end-start)
    for i in range(0,len(data),4):
        w=struct.unpack('<I',data[i:i+4])[0]
        va=start+i
        print('  0x%08x: %08x  %s'%(va,w,dis(w,va)))
    f.close()

if __name__=='__main__':
    region=sys.argv[1]
    files=sys.argv[2:]
    rmap={'cave':(0x4C7400,0x4C7480),'hook':(0x3A3190,0x3A31D0)}
    s,e=rmap[region]
    for fp in files:
        dump(fp,s,e,region)
        print()
