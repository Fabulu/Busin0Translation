import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
from capstone import *
from capstone.mips import *

DATA=open('extracted/SLPM_653.78','rb').read()
BASE_VA=0x100000
BASE_OFF=0x80
SEG_END_VA=0x100000+0x3fdc80

def va2off(va): return va-BASE_VA+BASE_OFF
def off2va(off): return off-BASE_OFF+BASE_VA

md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
md.detail=True

def disasm_func(start_va, max_insn=400):
    """Disassemble until jr $ra + delay slot, or max."""
    off=va2off(start_va)
    code=DATA[off:off+max_insn*4]
    out=[]
    seen_jr=False
    for ins in md.disasm(code, start_va):
        out.append(ins)
        if ins.mnemonic=='jr' and ins.op_str.strip()=='$ra':
            seen_jr=True
            continue
        if seen_jr:
            break
    return out

def show(start_va, max_insn=400):
    for ins in disasm_func(start_va,max_insn):
        print(f"0x{ins.address:08x}: {ins.mnemonic:8s} {ins.op_str}")

# scan whole segment for instructions referencing a target VA (jal/j) 
def find_callers(target_va):
    """Find all jal target_va in segment."""
    callers=[]
    seg=DATA[BASE_OFF:BASE_OFF+0x3fdc80]
    for i in range(0,len(seg)-4,4):
        w=struct.unpack('<I',seg[i:i+4])[0]
        op=w>>26
        if op==3:  # jal
            tgt=((off2va(i+BASE_OFF) & 0xF0000000) | ((w&0x03FFFFFF)<<2))
            if tgt==target_va:
                callers.append(off2va(i+BASE_OFF))
        elif op==2: # j
            tgt=((off2va(i+BASE_OFF) & 0xF0000000) | ((w&0x03FFFFFF)<<2))
            if tgt==target_va:
                callers.append(off2va(i+BASE_OFF))
    return callers

# list all jal/j targets within a function range
def calls_from(start_va, end_va):
    out=[]
    off0=va2off(start_va); off1=va2off(end_va)
    for i in range(off0,off1,4):
        w=struct.unpack('<I',DATA[i:i+4])[0]
        op=w>>26
        if op in (2,3):
            tgt=((off2va(i) & 0xF0000000) | ((w&0x03FFFFFF)<<2))
            out.append((off2va(i), 'jal' if op==3 else 'j', tgt))
    return out

if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd=='show':
        show(int(sys.argv[2],16), int(sys.argv[3]) if len(sys.argv)>3 else 400)
    elif cmd=='callers':
        for c in find_callers(int(sys.argv[2],16)):
            print(hex(c))
    elif cmd=='calls':
        for a,m,t in calls_from(int(sys.argv[2],16),int(sys.argv[3],16)):
            print(f"{hex(a)} {m} {hex(t)}")
