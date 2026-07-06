import sys, capstone
sys.stdout.reconfigure(encoding='utf-8')
data=open('extracted/SLPM_653.78','rb').read()
def va2f(va): return va-0x100000+0x80
md=capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN)
def find_store(off_field, lo, hi, ops=(0x29,0x2B)):  # sh=0x29, sw=0x2B
    res=[]
    for off in range(va2f(lo), va2f(hi), 4):
        w=int.from_bytes(data[off:off+4],'little')
        op=w>>26; imm=w&0xFFFF
        if op in ops and imm==off_field:
            va=off-0x80+0x100000
            for ins in md.disasm(data[off:off+4], va):
                res.append((va, ins.mnemonic, ins.op_str))
    return res
def find_load(off_field, lo, hi, ops=(0x21,0x23,0x25,0x27)):  # lh=0x21,lw=0x23,lhu=0x25,lwu=0x27
    res=[]
    for off in range(va2f(lo), va2f(hi), 4):
        w=int.from_bytes(data[off:off+4],'little')
        op=w>>26; imm=w&0xFFFF
        if op in ops and imm==off_field:
            va=off-0x80+0x100000
            for ins in md.disasm(data[off:off+4], va):
                res.append((va, ins.mnemonic, ins.op_str))
    return res
if __name__=='__main__':
    cmd=sys.argv[1]
    fld=int(sys.argv[2],16); lo=int(sys.argv[3],16); hi=int(sys.argv[4],16)
    fn=find_store if cmd=='st' else find_load
    for va,m,o in fn(fld,lo,hi):
        print(f'0x{va:08X} {m} {o}')

