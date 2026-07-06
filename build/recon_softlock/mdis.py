import sys, capstone, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def off(va): return va-0x100000+0x80
md=capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN)
md.skipdata=True
def disasm(va, n):
    o=off(va); code=data[o:o+n*4]
    for ins in md.disasm(code, va):
        w=struct.unpack('<I',data[off(ins.address):off(ins.address)+4])[0]
        print(f"0x{ins.address:08X}: {w:08X}  {ins.mnemonic:9s} {ins.op_str}")
if __name__=='__main__':
    va=int(sys.argv[1],16); n=int(sys.argv[2]) if len(sys.argv)>2 else 40
    disasm(va,n)
