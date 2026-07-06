import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
disc=open('C:/programmieren/wizardrytranslation/extracted/SLPM_653.78','rb').read()
def v2f(va): return va-0x100000+0x80
regs=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
def R(i): return '$'+regs[i]
MMI3={0x3C:'psllw',0x3E:'psrlw',0x3F:'psraw'}
def dec(va):
    w=struct.unpack_from('<I', disc, v2f(va))[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31; sh=(w>>6)&31; fn=w&63; imm=w&0xFFFF
    simm=imm-0x10000 if imm>=0x8000 else imm
    t=''
    if op==0:
        if fn==0x21: t=f"addu {R(rd)}, {R(rs)}, {R(rt)}"
        elif fn==0x23: t=f"subu {R(rd)}, {R(rs)}, {R(rt)}"
        elif fn==0x20: t=f"add {R(rd)}, {R(rs)}, {R(rt)}"
        elif fn==0x00 and w!=0: t=f"sll {R(rd)}, {R(rt)}, {sh}"
        elif fn==0x00 and w==0: t="nop"
        elif fn==0x02: t=f"srl {R(rd)}, {R(rt)}, {sh}"
        elif fn==0x03: t=f"sra {R(rd)}, {R(rt)}, {sh}"
        elif fn==0x04: t=f"sllv {R(rd)}, {R(rt)}, {R(rs)}"
        elif fn==0x18: t=f"mult {R(rs)}, {R(rt)}"
        elif fn==0x19: t=f"multu {R(rs)}, {R(rt)}"
        elif fn==0x1A: t=f"div {R(rs)}, {R(rt)}"
        elif fn==0x12: t=f"mflo {R(rd)}"
        elif fn==0x10: t=f"mfhi {R(rd)}"
        elif fn==0x2A: t=f"slt {R(rd)}, {R(rs)}, {R(rt)}"
        elif fn==0x2B: t=f"sltu {R(rd)}, {R(rs)}, {R(rt)}"
        elif fn==0x25: t=f"or {R(rd)}, {R(rs)}, {R(rt)}"
        elif fn==0x24: t=f"and {R(rd)}, {R(rs)}, {R(rt)}"
        elif fn==0x08: t=f"jr {R(rs)}"
        elif fn==0x09: t=f"jalr {R(rd)}, {R(rs)}"
        elif fn in MMI3: t=f"{MMI3[fn]} {R(rd)}, {R(rt)}, {sh}"
        elif fn==0x28: t=f"MMI0/pmthi? rd={R(rd)}"
        else: t=f".op0 fn=0x{fn:02X} rd={R(rd)} rs={R(rs)} rt={R(rt)} sh={sh}"
    elif op==2: t=f"j 0x{((va+4)&0xF0000000)|((w&0x3FFFFFF)<<2):08X}"
    elif op==3: t=f"jal 0x{((va+4)&0xF0000000)|((w&0x3FFFFFF)<<2):08X}"
    elif op==4: t=f"beq {R(rs)}, {R(rt)}, 0x{va+4+(simm<<2):08X}"
    elif op==5: t=f"bne {R(rs)}, {R(rt)}, 0x{va+4+(simm<<2):08X}"
    elif op==6: t=f"blez {R(rs)}, 0x{va+4+(simm<<2):08X}"
    elif op==7: t=f"bgtz {R(rs)}, 0x{va+4+(simm<<2):08X}"
    elif op==1:
        sub={0:'bltz',1:'bgez',16:'bltzal',17:'bgezal'}.get(rt,f'regimm{rt}')
        t=f"{sub} {R(rs)}, 0x{va+4+(simm<<2):08X}"
    elif op==8: t=f"addi {R(rt)}, {R(rs)}, {simm}"
    elif op==9: t=f"addiu {R(rt)}, {R(rs)}, {simm}"
    elif op==0xA: t=f"slti {R(rt)}, {R(rs)}, {simm}"
    elif op==0xB: t=f"sltiu {R(rt)}, {R(rs)}, {simm}"
    elif op==0xC: t=f"andi {R(rt)}, {R(rs)}, 0x{imm:X}"
    elif op==0xD: t=f"ori {R(rt)}, {R(rs)}, 0x{imm:X}"
    elif op==0xE: t=f"xori {R(rt)}, {R(rs)}, 0x{imm:X}"
    elif op==0xF: t=f"lui {R(rt)}, 0x{imm:X}"
    elif op==0x20: t=f"lb {R(rt)}, {simm}({R(rs)})"
    elif op==0x21: t=f"lh {R(rt)}, {simm}({R(rs)})"
    elif op==0x23: t=f"lw {R(rt)}, {simm}({R(rs)})"
    elif op==0x24: t=f"lbu {R(rt)}, {simm}({R(rs)})"
    elif op==0x25: t=f"lhu {R(rt)}, {simm}({R(rs)})"
    elif op==0x28: t=f"sb {R(rt)}, {simm}({R(rs)})"
    elif op==0x29: t=f"sh {R(rt)}, {simm}({R(rs)})"
    elif op==0x2B: t=f"sw {R(rt)}, {simm}({R(rs)})"
    elif op==0x1F and fn==0x3A: t=f"sq {R(rt)}, {simm}({R(rs)})"  # approx
    elif op==0x1E: t=f"lq {R(rt)}, {simm}({R(rs)})"
    elif op==0x37: t=f"ld {R(rt)}, {simm}({R(rs)})"
    elif op==0x3F: t=f"sd {R(rt)}, {simm}({R(rs)})"
    elif op==0x31: t=f"lwc1 $f{rt}, {simm}({R(rs)})"
    elif op==0x39: t=f"swc1 $f{rt}, {simm}({R(rs)})"
    elif op==0x11: t=f"COP1 rs={rs} ft={rt} fs={rd} fd={sh} fn=0x{fn:X}"
    else: t=f".word 0x{w:08X} op=0x{op:X}"
    return w,t
def disasm(va,n):
    for i in range(n):
        a=va+i*4; w,t=dec(a)
        print(f"0x{a:08X}: {t}")
if __name__=="__main__":
    disasm(int(sys.argv[1],16), int(sys.argv[2]) if len(sys.argv)>2 else 120)
