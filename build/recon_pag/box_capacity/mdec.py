import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
f=open('extracted/SLPM_653.78','rb').read()
def off(va): return va-0x100000+0x80
REG=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
def dec(w,va):
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31; sh=(w>>6)&31; fn=w&0x3f; imm=w&0xffff
    s=lambda x: x-0x10000 if x>=0x8000 else x
    if w==0: return 'nop'
    if op==0:
        if fn==0x20: return f'add {REG[rd]},{REG[rs]},{REG[rt]}'
        if fn==0x21: return f'addu {REG[rd]},{REG[rs]},{REG[rt]}'
        if fn==0x22: return f'sub {REG[rd]},{REG[rs]},{REG[rt]}'
        if fn==0x23: return f'subu {REG[rd]},{REG[rs]},{REG[rt]}'
        if fn==0x00: return f'sll {REG[rd]},{REG[rt]},{sh}'
        if fn==0x02: return f'srl {REG[rd]},{REG[rt]},{sh}'
        if fn==0x03: return f'sra {REG[rd]},{REG[rt]},{sh}'
        if fn==0x08: return f'jr {REG[rs]}'
        if fn==0x09: return f'jalr {REG[rd]},{REG[rs]}'
        if fn==0x2a: return f'slt {REG[rd]},{REG[rs]},{REG[rt]}'
        if fn==0x2b: return f'sltu {REG[rd]},{REG[rs]},{REG[rt]}'
        if fn==0x25: return f'or {REG[rd]},{REG[rs]},{REG[rt]}'
        if fn==0x24: return f'and {REG[rd]},{REG[rs]},{REG[rt]}'
        return f'.special fn=0x{fn:02x}'
    if op==1:
        if rt==0: return f'bltz {REG[rs]},0x{va+4+(s(imm)<<2):08x}'
        if rt==1: return f'bgez {REG[rs]},0x{va+4+(s(imm)<<2):08x}'
        return f'.regimm rt={rt}'
    if op==2: return f'j 0x{((va+4)&0xF0000000)|((w&0x3ffffff)<<2):08x}'
    if op==3: return f'jal 0x{((va+4)&0xF0000000)|((w&0x3ffffff)<<2):08x}'
    if op==4: return f'beq {REG[rs]},{REG[rt]},0x{va+4+(s(imm)<<2):08x}'
    if op==5: return f'bne {REG[rs]},{REG[rt]},0x{va+4+(s(imm)<<2):08x}'
    if op==6: return f'blez {REG[rs]},0x{va+4+(s(imm)<<2):08x}'
    if op==7: return f'bgtz {REG[rs]},0x{va+4+(s(imm)<<2):08x}'
    if op==9: return f'addiu {REG[rt]},{REG[rs]},{s(imm)}'
    if op==8: return f'addi {REG[rt]},{REG[rs]},{s(imm)}'
    if op==0x0a: return f'slti {REG[rt]},{REG[rs]},{s(imm)}'
    if op==0x0b: return f'sltiu {REG[rt]},{REG[rs]},{s(imm)}'
    if op==0x0c: return f'andi {REG[rt]},{REG[rs]},0x{imm:x}'
    if op==0x0d: return f'ori {REG[rt]},{REG[rs]},0x{imm:x}'
    if op==0x0f: return f'lui {REG[rt]},0x{imm:x}'
    if op==0x20: return f'lb {REG[rt]},{s(imm)}({REG[rs]})'
    if op==0x21: return f'lh {REG[rt]},{s(imm)}({REG[rs]})'
    if op==0x23: return f'lw {REG[rt]},{s(imm)}({REG[rs]})'
    if op==0x24: return f'lbu {REG[rt]},{s(imm)}({REG[rs]})'
    if op==0x25: return f'lhu {REG[rt]},{s(imm)}({REG[rs]})'
    if op==0x28: return f'sb {REG[rt]},{s(imm)}({REG[rs]})'
    if op==0x29: return f'sh {REG[rt]},{s(imm)}({REG[rs]})'
    if op==0x2b: return f'sw {REG[rt]},{s(imm)}({REG[rs]})'
    if op==0x37: return f'ld {REG[rt]},{s(imm)}({REG[rs]})'
    if op==0x3f: return f'sd {REG[rt]},{s(imm)}({REG[rs]})'
    return f'.op=0x{op:02x}'
va=int(sys.argv[1],16); n=int(sys.argv[2]) if len(sys.argv)>2 else 80
for k in range(n):
    a=va+k*4; w=struct.unpack_from('<I',f,off(a))[0]
    print('%08x  %08x  %s'%(a,w,dec(w,a)))
