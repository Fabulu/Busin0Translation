import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
D=open('extracted/SLPM_653.78','rb').read()
def v2f(va): return va-0x100000+0x80
def f2v(off): return off-0x80+0x100000
def word_at(off): return struct.unpack('<I',D[off:off+4])[0]
TEXT0=v2f(0x100000); TEXT1=v2f(0x100000+0x3fdc80)
targets=[int(x,16) for x in sys.argv[1:]]
# find all lui rt,hi then somewhere addiu/ori rt,rt,lo producing target.
# simpler: scan all instructions, track per-reg lui value, detect addiu forming target
for tgt in targets:
    print('=== building %08x ==='%tgt)
    regs={}
    off=TEXT0
    while off<TEXT1:
        w=word_at(off); va=f2v(off)
        op=w>>26
        if op==0x0f: # lui
            rt=(w>>16)&0x1f; imm=w&0xffff
            regs[rt]=imm<<16
        elif op==0x09: # addiu
            rs=(w>>21)&0x1f; rt=(w>>16)&0x1f; imm=w&0xffff
            if rs in regs:
                base=regs[rs]
                val=(base+(imm if imm<0x8000 else imm-0x10000))&0xffffffff
                if val==tgt:
                    print('  addiu at %08x  (lui base %08x)'%(va,base))
                regs[rt]=val
        elif op==0x0d: # ori
            rs=(w>>21)&0x1f; rt=(w>>16)&0x1f; imm=w&0xffff
            if rs in regs:
                val=(regs[rs]|imm)&0xffffffff
                if val==tgt: print('  ori at %08x'%va)
                regs[rt]=val
        off+=4
