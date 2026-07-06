import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open("extracted/SLPM_653.78",'rb').read()
def va2off(va): return va-0x100000+0x80
REG=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
     's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','s8','ra']
SPECIAL={0x00:'sll',0x02:'srl',0x03:'sra',0x04:'sllv',0x06:'srlv',0x07:'srav',
 0x08:'jr',0x09:'jalr',0x0c:'syscall',0x10:'mfhi',0x12:'mflo',0x18:'mult',0x19:'multu',
 0x1a:'div',0x1b:'divu',0x20:'add',0x21:'addu',0x22:'sub',0x23:'subu',0x24:'and',
 0x25:'or',0x26:'xor',0x27:'nor',0x2a:'slt',0x2b:'sltu',0x2c:'dadd',0x2d:'daddu',
 0x2e:'dsub',0x2f:'dsubu',0x14:'dsllv',0x16:'dsrlv',0x17:'dsrav',
 0x38:'dsll',0x3a:'dsrl',0x3b:'dsra',0x3c:'dsll32',0x3e:'dsrl32',0x3f:'dsra32',
 0x3d:'movz'}
OPS={0x08:'addi',0x09:'addiu',0x0a:'slti',0x0b:'sltiu',0x0c:'andi',0x0d:'ori',0x0e:'xori',
 0x0f:'lui',0x18:'daddi',0x19:'daddiu',0x20:'lb',0x21:'lh',0x23:'lw',0x24:'lbu',0x25:'lhu',
 0x28:'sb',0x29:'sh',0x2b:'sw',0x37:'ld',0x3f:'sd',0x04:'beq',0x05:'bne',0x06:'blez',0x07:'bgtz'}
MMI={ }  # op 0x1c special2 (mult-acc etc); pmthi/plo handled crudely
def r(i): return '$'+REG[i]
def dec(va,w):
    op=w>>26
    if op==0:
        fn=w&0x3f; rs=(w>>21)&0x1f; rt=(w>>16)&0x1f; rd=(w>>11)&0x1f; sa=(w>>6)&0x1f
        nm=SPECIAL.get(fn)
        if nm is None: return f".word {w:#010x}"
        if fn in (0x00,0x02,0x03,0x38,0x3a,0x3b,0x3c,0x3e,0x3f): return f"{nm} {r(rd)},{r(rt)},{sa}"
        if fn in (0x08,): return f"jr {r(rs)}"
        if fn in (0x18,0x19,0x1a,0x1b): return f"{nm} {r(rs)},{r(rt)}"
        if fn in (0x10,0x12): return f"{nm} {r(rd)}"
        return f"{nm} {r(rd)},{r(rs)},{r(rt)}"
    if op==0x1c: # MMI
        fn=w&0x3f; rs=(w>>21)&0x1f; rt=(w>>16)&0x1f; rd=(w>>11)&0x1f
        return f"mmi.{fn:#x} {r(rd)},{r(rs)},{r(rt)}"
    nm=OPS.get(op)
    if nm is None: return f".word {w:#010x}"
    rs=(w>>21)&0x1f; rt=(w>>16)&0x1f; imm=w&0xffff
    if imm>=0x8000 and op not in (0x0c,0x0d,0x0e,0x0f): imm-=0x10000
    if op==0x0f: return f"lui {r(rt)},{imm:#x}"
    if op in (0x04,0x05): tgt=va+4+imm*4; return f"{nm} {r(rs)},{r(rt)},{tgt:#x}"
    if op in (0x20,0x21,0x23,0x24,0x25,0x28,0x29,0x2b,0x37,0x3f):
        return f"{nm} {r(rt)},{imm:#x}({r(rs)})"
    return f"{nm} {r(rt)},{r(rs)},{imm:#x}"
lo,hi=int(sys.argv[1],16),int(sys.argv[2],16)
for va in range(lo,hi,4):
    o=va2off(va); w=struct.unpack('<I',data[o:o+4])[0]
    print(f"0x{va:08x}: {w:08x}  {dec(va,w)}")
