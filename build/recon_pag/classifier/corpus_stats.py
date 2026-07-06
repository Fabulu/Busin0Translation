import sys, os, struct, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
import sec1_disasm as S
import patch_section1_offsets as P
sys.path.insert(0,'build/recon_pag/classifier')
import window as W

paths = sorted(glob.glob('extracted/packdata_raw/*_type02.raw'))
tot_res=ok_res=fail_walk=0
tot_blocks=0
dia_blocks=0
# distribution of 'since' for all blocks
from collections import Counter
since_hist=Counter()
# per-resource: count blocks with since==0 (name block) and since==1 (immediate body)
res_with_names=0
for p in paths:
    data=open(p,'rb').read()
    try:
        ok,instrs,sec1,s2=S.walk_resource(data)
    except Exception:
        fail_walk+=1; continue
    tot_res+=1
    if ok: ok_res+=1
    out=W.classify(data,1)
    has_name=False
    for b in out:
        tot_blocks+=1
        since_hist[min(b['since'],9)]+=1
        if b['dialogue']: dia_blocks+=1
        if b['since']==0: has_name=True
    if has_name: res_with_names+=1
print(f"resources: {tot_res} (walk ok={ok_res}, walk fail={fail_walk})")
print(f"resources containing >=1 NAMELBL: {res_with_names}")
print(f"total DISPLAY blocks: {tot_blocks}")
print(f"classified DIALOGUE (K=1): {dia_blocks} ({100*dia_blocks/tot_blocks:.1f}%)")
print(f"classified NARRATION:       {tot_blocks-dia_blocks} ({100*(tot_blocks-dia_blocks)/tot_blocks:.1f}%)")
print("\n'blocks since last NAMELBL' histogram (0=name block,1=immediate body,...):")
for k in range(10):
    lbl=f"{k}" if k<9 else "9+"
    print(f"  since={lbl}: {since_hist[k]}")
