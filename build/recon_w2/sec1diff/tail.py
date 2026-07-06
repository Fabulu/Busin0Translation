import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.abspath('tools'))
import sec1_disasm as S
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
base=0x11c3d20
sec1=ee[base:base+47136]
ok,instrs=S.walk(sec1)
mx=max(instrs)
print("max reachable instr pc=0x%x op=0x%02x"%(mx,instrs[mx]))
# Show last 30 reachable instrs
last=sorted(instrs)[-30:]
for p in last:
    op=instrs[p];ln=S.LENB[op]
    print("  0x%04x op=0x%02x %s"%(p,op,sec1[p:p+ln].hex()))
# Now: where does the gap start? scan from mx forward for first nonzero
print("\nbytes after max instr:")
o=mx+S.LENB[instrs[mx]]
print("post-instr offset 0x%x"%o)
# find first nonzero after o
nz=o
while nz<len(sec1) and sec1[nz]==0: nz+=1
print("first nonzero after gap: 0x%x (gap %d bytes)"%(nz,nz-o))
print("region 0x%x..0x%x:"%(o,min(o+0x40,len(sec1)),), sec1[o:o+0x40].hex())
