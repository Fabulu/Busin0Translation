import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build/recon_pag')
from spans import load, groups_in_span
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]
# Simulate scene fields along PC order (linear approximation):
#   [0x290]&1  set by opcode 0x21 (handler 0x2F4700) -> MODE1
#   cleared by ?  -> need to find. For now track set events.
# We'll print, per 0x04, the most recent 0x21 and 0x0C and 0x60 since last 0x04.
res=int(sys.argv[1])
gis_filter=set(int(x) for x in sys.argv[2:]) if len(sys.argv)>2 else None
ok,instrs,sec1,groups,words=load(res)
pcs=sorted(instrs); op_seq=[(pc,instrs[pc]) for pc in pcs]
for i,(pc,op) in enumerate(op_seq):
    if op!=0x04: continue
    off=beu32(sec1,pc+2);cnt=beu32(sec1,pc+6)
    if cnt==0: continue
    sg=groups_in_span(groups,off,cnt)
    if gis_filter and not (gis_filter & set(sg)): continue
    j=i-1; seen=[]
    while j>=0 and op_seq[j][1]!=0x04:
        o2=op_seq[j][1]
        if o2 in (0x21,0x0C,0x0D,0x60,0x14): seen.append(o2)
        j-=1
    seen=seen[::-1]
    has21=0x21 in seen
    # JP page break?
    ffd2=any(0xFFD2 in words[groups[g][0]:groups[g][1]] for g in sg)
    seenstr=','.join('0x%02X'%o for o in seen)
    print("g%s..%s mode1(0x21)=%-5s JP_FFD2=%-5s preceding=[%s]"%(sg[0],sg[-1],has21,ffd2,seenstr))
