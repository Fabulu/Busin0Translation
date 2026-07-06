import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def v2f(va): return va - 0x100000 + 0x80
REGS=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
def disasm(va):
    off=v2f(va)
    w=struct.unpack('<I',data[off:off+4])[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31; sh=(w>>6)&31; fn=w&63
    imm=w&0xffff; simm=imm-0x10000 if imm&0x8000 else imm; tgt=(w&0x3ffffff)
    R=lambda x:REGS[x]; s='??'
    if w==0: s='nop'
    elif op==0:
        m={0x20:'add',0x21:'addu',0x22:'sub',0x23:'subu',0x24:'and',0x25:'or',0x27:'nor',0x2a:'slt',0x2b:'sltu'}
        if fn in m: s=f'{m[fn]} {R(rd)},{R(rs)},{R(rt)}'
        elif fn==0x00: s=f'sll {R(rd)},{R(rt)},{sh}'
        elif fn==0x02: s=f'srl {R(rd)},{R(rt)},{sh}'
        elif fn==0x03: s=f'sra {R(rd)},{R(rt)},{sh}'
        elif fn==0x04: s=f'sllv {R(rd)},{R(rt)},{R(rs)}'
        elif fn==0x06: s=f'srlv {R(rd)},{R(rt)},{R(rs)}'
        elif fn==0x08: s=f'jr {R(rs)}'
        elif fn==0x09: s=f'jalr {R(rd)},{R(rs)}'
        elif fn==0x10: s=f'mfhi {R(rd)}'
        elif fn==0x12: s=f'mflo {R(rd)}'
        elif fn==0x18: s=f'mult {R(rs)},{R(rt)}'
        elif fn==0x1a: s=f'div {R(rs)},{R(rt)}'
        elif fn==0x1b: s=f'divu {R(rs)},{R(rt)}'
        else: s=f'.special fn=0x{fn:02x}'
    elif op==1:
        if rt==0: s=f'bltz {R(rs)},0x{va+4+(simm<<2):08x}'
        elif rt==1: s=f'bgez {R(rs)},0x{va+4+(simm<<2):08x}'
        else: s=f'.regimm rt={rt}'
    elif op==2: s=f'j 0x{((va+4)&0xf0000000)|(tgt<<2):08x}'
    elif op==3: s=f'jal 0x{((va+4)&0xf0000000)|(tgt<<2):08x}'
    elif op==4:
        if rs==0 and rt==0: s=f'b 0x{va+4+(simm<<2):08x}'
        else: s=f'beq {R(rs)},{R(rt)},0x{va+4+(simm<<2):08x}'
    elif op==5: s=f'bne {R(rs)},{R(rt)},0x{va+4+(simm<<2):08x}'
    elif op==6: s=f'blez {R(rs)},0x{va+4+(simm<<2):08x}'
    elif op==7: s=f'bgtz {R(rs)},0x{va+4+(simm<<2):08x}'
    elif op==8: s=f'addi {R(rt)},{R(rs)},{simm}'
    elif op==9: s=f'addiu {R(rt)},{R(rs)},{simm}'
    elif op==0x0a: s=f'slti {R(rt)},{R(rs)},{simm}'
    elif op==0x0b: s=f'sltiu {R(rt)},{R(rs)},{simm}'
    elif op==0x0c: s=f'andi {R(rt)},{R(rs)},0x{imm:04x}'
    elif op==0x0d: s=f'ori {R(rt)},{R(rs)},0x{imm:04x}'
    elif op==0x0f: s=f'lui {R(rt)},0x{imm:04x}'
    elif op==0x20: s=f'lb {R(rt)},{simm}({R(rs)})'
    elif op==0x21: s=f'lh {R(rt)},{simm}({R(rs)})'
    elif op==0x23: s=f'lw {R(rt)},{simm}({R(rs)})'
    elif op==0x24: s=f'lbu {R(rt)},{simm}({R(rs)})'
    elif op==0x25: s=f'lhu {R(rt)},{simm}({R(rs)})'
    elif op==0x28: s=f'sb {R(rt)},{simm}({R(rs)})'
    elif op==0x29: s=f'sh {R(rt)},{simm}({R(rs)})'
    elif op==0x2b: s=f'sw {R(rt)},{simm}({R(rs)})'
    else: s=f'.op=0x{op:02x}'
    return w,s
def dump(va,n):
    for i in range(n):
        a=va+i*4; w,s=disasm(a)
        print(f'  0x{a:08x}: {w:08x}  {s}')
if __name__=='__main__':
    va=int(sys.argv[1],16); n=int(sys.argv[2]) if len(sys.argv)>2 else 20
    dump(va,n)
