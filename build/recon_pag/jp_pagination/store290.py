import struct,sys,json
sys.stdout.reconfigure(encoding='utf-8')
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN); md.skipdata=True
exe=open('extracted/SLPM_653.78','rb').read()
def f2o(va): return va-0xFFF80
def dump(va,end,tag=''):
    print(f"--- {tag} 0x{va:X}..0x{end:X} ---")
    for i in md.disasm(exe[f2o(va):f2o(end)], va):
        print(f"  {i.address:06X}: {i.mnemonic:8s} {i.op_str}")
dump(0x2F47C0,0x2F4860,'store@2F4810 context')
dump(0x2F49E0,0x2F4A80,'store@2F4A38 context')
# Map these to opcode handlers via the handler table at 0x4C9360 (file 0x3C93E0)
ht_va=0x4C9360; ht_off=ht_va-0xFFF80
print("--- handler table opcodes pointing into these regions ---")
for k in range(193):
    h=struct.unpack_from('<I',exe,ht_off+k*4)[0]
    if 0x2F4700<=h<=0x2F4B00:
        print(f"  opcode 0x{k:02X} -> handler 0x{h:X}")
