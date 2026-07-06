import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.abspath('tools'))
import sec1_disasm as S
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
base=0x11c3d20
sec1=ee[base:base+47136]
ok,instrs=S.walk(sec1)
ps=sorted(instrs)
# find reachable coverage gaps
print("reachable pc range 0x%x..0x%x, count=%d"%(ps[0],ps[-1],len(ps)))
# Build covered byte set
cov=set()
for p in ps: 
    for b in range(p,p+S.LENB[instrs[p]]): cov.add(b)
# find gaps > 8 bytes within [0, max]
gaps=[]
i=0;mx=ps[-1]+S.LENB[instrs[ps[-1]]]
while i<len(sec1):
    if i not in cov and i<mx:
        j=i
        while j<len(sec1) and j not in cov: j+=1
        if j-i>=4: gaps.append((i,j,j-i))
        i=j
    else: i+=1
print("uncovered gaps (>=4B) within reachable range:")
for g in gaps[:40]: print("  0x%04x..0x%04x (%d)"%g)
# Is the parked PC 0xb820 covered?
print("\nPC 0xb820 covered:",0xb820 in cov)
# any jump/gosub/cond target into [0x9e62, 0xb820]?
print("\njumps/targets landing in [0x9e62,0xb840):")
for p in ps:
    op=instrs[p]
    t=None
    if op in (0x08,0x0b,0x11,0x12): t=struct.unpack_from(">I",sec1,p+2)[0]
    elif op in (0x06,0x07): t=struct.unpack_from(">I",sec1,p+10)[0]
    if t is not None and 0x9e62<=t<0xb840:
        print("  pc=0x%x op=0x%02x -> 0x%x"%(p,op,t))
