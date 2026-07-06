import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build/recon_pag')
from sec1_disasm import extract_records
from spans import load
res=int(sys.argv[1])
ok,instrs,sec1,groups,words=load(res)
recs=extract_records(sec1,instrs)
from collections import Counter
c=Counter((r['op'],r['param'],r['idx']) for r in recs['name_ref'])
for (op,param,idx),n in sorted(c.items()):
    print("op=0x%02X param=%d idx=%d  x%d"%(op,param,idx,n))
