import sys
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
sys.stdout.reconfigure(encoding='utf-8')
exe=open('extracted/SLPM_653.78','rb').read()
def va2off(va): return va-0x100000+0x80
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN); md.skipdata=True
# Find references to 0xFFD2 constant in the EXE (the glyph renderer compares words to FFD2).
# Search for 'ori reg,reg,0xffd2' or 'addiu reg,zero,0xffd2'(=signed -0x2e) or li.
# 0xFFD2 as immediate: addiu uses sign so it'd be -0x2e. Search bytes for the renderer comparing.
# Simpler: disasm 0x305A60 (DISPLAY worker) and look for ffd2/ff** comparisons.
def dis(va,n,filt=None):
    for ins in md.disasm(exe[va2off(va):va2off(va)+n*4],va):
        s="0x%08x: %-10s %s"%(ins.address,ins.mnemonic,ins.op_str)
        if filt is None or filt in ins.op_str.lower(): print(s)
print("=== scan 0x305A60..+0x600 for 0xff comparisons ===")
dis(0x305A60,0x180, 'ff')
