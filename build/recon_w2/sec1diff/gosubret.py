import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.abspath('tools'))
import sec1_disasm as S
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
base=0x11c3d20; sec1=ee[base:base+47136]
ok,instrs=S.walk(sec1)
# 0x12 GOSUB pushes return = pc AFTER the gosub (pc+6) and jumps to target.
# When the sub RETURNS (some opcode pops), execution resumes at pc+6.
# 0x9e5b is op11 (jump). The instr BEFORE it: 0x9e55 op0c, 0x9e51 op44, 0x9e4b opb2...
# Is 0x9e5b reached by gosub? Find gosub whose return (pc+6) lands in this block, OR
# whether the 0x11 at 0x9e5b is itself a gosub target.
# More useful: WHICH gosub targets the request handler. Find 0x12 targets and see the called subs.
# The request menu: master menu has 5 options. Let's find the choice block (0xFFC0 markers in sec1? no, those are sec2).
# The menu opcode is likely 0x1A or a choice op reading sec2 markers.
# Let me find the GOSUB targets that are common (the dialogue helpers 0x1078,0x108a,0x10a4,0x10d6 seen).
from collections import Counter
gt=Counter()
for p in instrs:
    if instrs[p]==0x12: gt[struct.unpack_from(">I",sec1,p+2)[0]]+=1
print("top GOSUB targets:",gt.most_common(8))
# disasm sub at 0x1078 (most common helper)
for tgt in [0x1078,0x108a,0x10a4]:
    print("\n--- sub @0x%x ---"%tgt)
    p=tgt
    for _ in range(8):
        if p not in instrs: 
            op=(sec1[p]<<8)|sec1[p+1]; print("  0x%x op=0x%02x (not in reach)"%(p,op)); break
        op=instrs[p];ln=S.LENB[op]
        print("  0x%x op=0x%02x %s"%(p,op,sec1[p:p+ln].hex()))
        if op in (0x08,0x0b,0x11): break
        p+=ln
