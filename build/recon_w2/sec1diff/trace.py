import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.abspath('tools'))
import sec1_disasm as S
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
base=0x11c3d20
sec1=ee[base:base+47136]
# The gosub context stack at 0x1137980 (state+0x008). Dump it.
stk=0x1137980
print("ctx stack region @0x%x:"%stk)
for k in range(0,16):
    v=struct.unpack_from("<I",ee,stk+k*4)[0]
    rel = v-base if base<=v<base+0xb840 else None
    print("  [%d] 0x%08x  sec1rel=%s"%(k,v, hex(rel) if rel is not None else '-'))
