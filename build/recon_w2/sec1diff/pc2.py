import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.abspath('tools'))
import sec1_disasm as S
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
base=0x11c3d20  # sec1 base in RAM (from prior step)
# But this save is v96-era. Extract that build's actual sec1 from RAM directly.
# sec1 length 47136. Read it from RAM:
sec1_ram=ee[base:base+47136]
ok,instrs=S.walk(sec1_ram)
print("RAM sec1 walk ok=%s instrs=%d"%(ok,len(instrs)))

# Find pointers in EE that point into [base, base+47136)
lo,hi=base,base+47136
ptrs=[]
for i in range(0,len(ee)-3,4):
    v=struct.unpack_from("<I",ee,i)[0]
    if lo<=v<hi:
        ptrs.append((i,v))
print("aligned u32 ptrs into sec1 region:",len(ptrs))
# Show those near EXE data / interpreter state region. Group by value.
# The PC is the most interesting: print unique target offsets (v-base)
from collections import Counter
vals=Counter(v-base for _,v in ptrs)
print("distinct sec1-relative targets pointed at:",len(vals))
for off,c in sorted(vals.items()):
    # is off a valid instr boundary?
    valid = off in instrs
    print("  off=0x%x count=%d instr_boundary=%s opcode=%s"%(off,c, valid, hex(instrs[off]) if valid else '-'))
