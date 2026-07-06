import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
import capstone as _cs

EXE = r"C:/programmieren/wizardrytranslation/extracted/SLPM_653.78"
data = open(EXE,'rb').read()
FILE_BASE = 0xFFF80

md = _cs.Cs(_cs.CS_ARCH_MIPS, _cs.CS_MODE_MIPS32 | _cs.CS_MODE_LITTLE_ENDIAN)
md.detail = False
md.skipdata = True

def va2off(va): return va - FILE_BASE

def disone(va, n):
    off = va2off(va)
    code = data[off:off+n*4]
    addr = va
    for ins in md.disasm(code, va):
        print(f"0x{ins.address:08X}: {ins.bytes.hex()}  {ins.mnemonic:8s} {ins.op_str}")
        addr = ins.address + ins.size

if __name__ == "__main__":
    va = int(sys.argv[1],16)
    n = int(sys.argv[2]) if len(sys.argv)>2 else 60
    disone(va, n)
