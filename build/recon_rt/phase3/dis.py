"""Generic MIPS disassembler for SLPM_653.78 EXE."""
import struct, sys
import rabbitizer
sys.stdout.reconfigure(encoding='utf-8')

exe = open('extracted/SLPM_653.78','rb').read()
P_OFFSET=0x80
P_VADDR=0x00100000
def v2f(va): return va - P_VADDR + P_OFFSET

REGS=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']

def disrange(start,end,label=""):
    if label: print(f"\n==== {label} ====")
    for va in range(start,end,4):
        f=v2f(va)
        if f<0 or f+4>len(exe): break
        raw=struct.unpack_from('<I',exe,f)[0]
        ins=rabbitizer.Instruction(raw); ins.vram=va
        asm=ins.disassemble()
        op=raw>>26
        # PS2 sq/lq
        if op==0x1F:
            rt=(raw>>16)&0x1F; base=(raw>>21)&0x1F; off=raw&0xFFFF
            if off>=0x8000: off-=0x10000
            asm=f"sq    ${REGS[rt]}, {off:#x}(${REGS[base]})"
        elif op==0x1E:
            rt=(raw>>16)&0x1F; base=(raw>>21)&0x1F; off=raw&0xFFFF
            if off>=0x8000: off-=0x10000
            asm=f"lq    ${REGS[rt]}, {off:#x}(${REGS[base]})"
        mark=""
        if op==0x03:  # jal
            tgt=((raw&0x03FFFFFF)<<2)|(va&0xF0000000)
            mark=f"  -> jal {tgt:#010x}"
        elif op==0x02: # j
            tgt=((raw&0x03FFFFFF)<<2)|(va&0xF0000000)
            mark=f"  -> j {tgt:#010x}"
        print(f"  {va:08X}:  {raw:08X}  {asm:48s}{mark}")

if __name__=='__main__':
    a=int(sys.argv[1],16); b=int(sys.argv[2],16)
    lbl=sys.argv[3] if len(sys.argv)>3 else ""
    disrange(a,b,lbl)
