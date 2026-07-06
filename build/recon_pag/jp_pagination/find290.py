import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN); md.skipdata=True
exe=open('extracted/SLPM_653.78','rb').read()
def f2o(va): return va-0xFFF80
# $s2 is the interpreter ctx (per opcode_table: ctx_struct +0x00 pc...). The 0x04 handler
# uses $s2 as ctx. 0x290 is a flag in ctx. Find sw/lw with imm 0x290 across the
# opcode-handler region 0x2F3300..0x2F4000 and the dispatcher area.
# scan all instructions in interpreter region for 0x290 offset stores
targets=[0x290,0x294,0x298]
for region_lo,region_hi in [(0x2F3200,0x2F4200)]:
    for i in md.disasm(exe[f2o(region_lo):f2o(region_hi)], region_lo):
        if i.mnemonic in ('sw','sh','sb','lw','lh','lhu','lb','ori','andi') and ('0x290(' in i.op_str or '0x294(' in i.op_str or '0x298(' in i.op_str):
            print(f"  {i.address:06X}: {i.mnemonic:8s} {i.op_str}")
print("--- now scan ENTIRE exe for store to +0x290 (sw rt, 0x290(base)) ---")
# Too noisy; instead, the ctx base is loaded in dispatcher. Let's find opcode handlers
# that do 'ori/sw ... 0x290'. Scan whole interpreter handler table region 0x2F3300-0x2F5000
for i in md.disasm(exe[f2o(0x2F3300):f2o(0x2F5000)], 0x2F3300):
    if ('0x290(' in i.op_str) and i.mnemonic in ('sw','sh','sb'):
        print(f"  STORE {i.address:06X}: {i.mnemonic} {i.op_str}")
