import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'build/recon_pag')
from spans import load
from collections import Counter
for res in range(1192,1215):
    L=load(res)
    if not L: print('R%d missing'%res); continue
    ok,instrs,sec1,groups,words=L
    c=Counter(instrs.values())
    n04=c.get(0x04,0); n14=c.get(0x14,0); n0c=c.get(0x0C,0); n60=c.get(0x60,0)
    nffd2=sum(1 for w in words if w==0xFFD2)
    print('R%d ok=%s 04=%-4d 14=%-4d 0C=%-4d 60=%-3d grp=%-4d JP_FFD2_words=%d'%(res,ok,n04,n14,n0c,n60,len(groups),nffd2))
