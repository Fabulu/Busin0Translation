import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN); md.skipdata=True
exe=open('extracted/SLPM_653.78','rb').read()
def f2o(va): return va-0xFFF80
def jt(va): return (0x0C000000|((va>>2)&0x03FFFFFF))
# find callers of 0x305A60
jalw=jt(0x305A60)
callers=[]
for o in range(0,len(exe)-4,4):
    w=struct.unpack_from('<I',exe,o)[0]
    if w==jalw:
        callers.append(o+0xFFF80)
print("callers of 0x305A60:",[hex(c) for c in callers])
def dump(va,end,tag=''):
    print(f"--- {tag} 0x{va:X}..0x{end:X} ---")
    for i in md.disasm(exe[f2o(va):f2o(end)], va):
        print(f"  {i.address:06X}: {i.mnemonic:8s} {i.op_str}")
# the 0x04 handler
dump(0x2F3700, 0x2F3760, 'op04 handler')
# context around each caller (show 0x40 before to see how $a3 is set)
for c in callers[:3]:
    dump(c-0x40, c+0x10, f'caller {hex(c)}')
