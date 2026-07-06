import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
exe=open('extracted/SLPM_653.78','rb').read()
def f2o(va): return va-0xFFF80
def disasm(va,n):
    code=exe[f2o(va):f2o(va)+n]
    for i in md.disasm(code, va):
        yield i
# Disassemble the shared text engine entry 0x305A60 through 0x305D00
print("=== 0x305A60 (shared text engine, called by 0x04 handler) ===")
for i in disasm(0x305A60, 0x305D00-0x305A60):
    # annotate calls and branch targets
    print(f"  0x{i.address:06X}: {i.mnemonic:8s} {i.op_str}")
