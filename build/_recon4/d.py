import sys, capstone
sys.stdout.reconfigure(encoding='utf-8')
data=open('extracted/SLPM_653.78','rb').read()
def va2f(va): return va-0x100000+0x80
md=capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN)
md.skipdata=True
a=int(sys.argv[1],16); b=int(sys.argv[2],16)
va=a
while va<b:
    off=va2f(va)
    raw=data[off:off+4]
    got=list(md.disasm(raw, va))
    if got:
        ins=got[0]
        print(f"0x{va:08X} {raw.hex()} {ins.mnemonic:8} {ins.op_str}")
    else:
        print(f"0x{va:08X} {raw.hex()} ???")
    va+=4
