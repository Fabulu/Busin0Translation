import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.abspath('tools'))
import sec1_disasm as S
import json
t=json.load(open('build/recon_v85/exe-interpreter/opcode_table_v85.json',encoding='utf-8'))
print("0x1a:",t['opcodes'].get('0x1a') or t['opcodes'].get('0x1A'))
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
base=0x11c3d20; sec1=ee[base:base+47136]
ok,instrs=S.walk(sec1)
# who jumps to 0x9e61?
for p in sorted(instrs):
    op=instrs[p]; t2=None
    if op in (0x08,0x0b,0x11,0x12): t2=struct.unpack_from(">I",sec1,p+2)[0]
    elif op in (0x06,0x07): t2=struct.unpack_from(">I",sec1,p+10)[0]
    if t2 in (0x9e61,0x9e5b): print("  jump to 0x%x from pc=0x%x op=0x%02x"%(t2,p,op))
# fallthrough predecessor of 0x9e61: instr ending at 0x9e61
for p in sorted(instrs):
    if p+S.LENB[instrs[p]]==0x9e61: print("  fallthrough pred @0x%x op=0x%02x (ends at 0x9e61)"%(p,instrs[p]))
# is 0x9e61 in reachable set?
print("0x9e61 reachable:",0x9e61 in instrs)
