import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'build/recon_pag')
from signals import analyze
res=int(sys.argv[1]); gis=[int(x) for x in sys.argv[2:]]
a=analyze(res)
bygi={}
for r in a['rows']: bygi.setdefault(r['gi'],[]).append(r)
for g in gis:
    rs=bygi.get(g)
    if not rs: print(f"  R{res} g{g}: NO 0x04 targets this group (cnt==0 or untargeted)"); continue
    for r in rs:
        print(f"  R{res} g{g}: 0C(spk)={r['saw_0c']} 60={r['saw_60']} 14={r['saw_14']} JP_FFD2={r['n_ffd2']} JP_FFFE={r['n_fffe']} glyphlen={r['glyphlen']}")
