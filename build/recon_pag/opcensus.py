import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'build/recon_pag')
from spans import load
from collections import Counter
for res in [int(x) for x in sys.argv[1:]]:
    L=load(res)
    if not L: continue
    ok,instrs,sec1,groups,words=L
    c=Counter(instrs.values())
    # show counts for opcodes of interest
    interest=[0x04,0x0C,0x0D,0x14,0x21,0x60]
    s=' '.join("0x%02X=%d"%(o,c.get(o,0)) for o in interest)
    print("R%d ok=%s instrs=%d  %s"%(res,ok,len(instrs),s))
