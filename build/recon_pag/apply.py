import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build/recon_pag')
from spans import load, groups_in_span
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]

NARRATION_RES={1193,1194,1196}  # intro, ending, prologue (priors)

def group_classes(res):
    """Return {gi: 'DIALOGUE'|'NARRATION'} for a type-02 resource.
    Rule (narration-safe):
      A group is DIALOGUE iff:
        (D1) the JP block covering it contains 0xFFD2 (author paginated), OR
        (D2) it is part of a 0x04 body bound to a SPEAKER NAME caption
             (a 0x60 param>0 + small name-0x04 immediately precedes the
             0x60 param=0 that precedes the body) -- the dialogue speaker header.
      Resources in NARRATION_RES are ALL narration (override to NARRATION).
    """
    L=load(res)
    if not L: return None
    ok,instrs,sec1,groups,words=L
    if not ok: return ('walkfail',)
    pcs=sorted(instrs); seq=[(pc,instrs[pc]) for pc in pcs]
    cls={}
    for i,(pc,op) in enumerate(seq):
        if op!=0x04: continue
        off=beu32(sec1,pc+2);cnt=beu32(sec1,pc+6)
        if cnt==0: continue
        sg=groups_in_span(groups,off,cnt)
        jp_ffd2=any(0xFFD2 in words[groups[g][0]:groups[g][1]] for g in sg)
        # speaker-caption detect: a 0x60 p>0 within 8 ops back (not crossing a big body)
        seen60pos=False; k=i-1; steps=0
        while k>=0 and steps<8:
            o2=seq[k][1]; p2=seq[k][0]
            if o2==0x04:
                if beu32(sec1,p2+6)>20: break
            if o2==0x60 and beu16(sec1,p2+2)>0: seen60pos=True
            k-=1; steps+=1
        is_dialogue = jp_ffd2 or seen60pos
        if res in NARRATION_RES: is_dialogue=False
        for g in sg:
            # JP_FFD2 / caption wins; once DIALOGUE keep it
            if cls.get(g)=='DIALOGUE': continue
            cls[g]='DIALOGUE' if is_dialogue else 'NARRATION'
    return ('ok',cls)

if __name__=='__main__':
    overflow=json.load(open('build/recon_pag/overflow_worklist.json',encoding='utf-8'))
    # group by resource
    byres={}
    for o in overflow: byres.setdefault(o['resource'],[]).append(o)
    safe=[]; unsafe_narr=[]; unwalkable=[]; type01=[]
    cache={}
    import os
    for res,items in sorted(byres.items()):
        path=f'extracted/packdata_raw/{res:04d}_type02.raw'
        if not os.path.isfile(path):
            type01+=items; continue
        gc=group_classes(res)
        if gc is None or gc[0]!='ok':
            unwalkable+=items; continue
        cls=gc[1]
        for it in items:
            c=cls.get(it['message'],'UNTARGETED')
            if c=='DIALOGUE': safe.append(it)
            else: unsafe_narr.append((it,c))
    print("Overflow items total:", len(overflow))
    print("  -> type-01 resource (R39 etc, separate path):", len(type01))
    print("  -> type-02 unwalkable Section1 (ship pristine, skip):", len(unwalkable))
    print("  -> type-02 DIALOGUE (SAFE to auto-paginate):", len(safe))
    print("  -> type-02 NARRATION/UNTARGETED (DO NOT paginate):", len(unsafe_narr))
    from collections import Counter
    print("  SAFE by resource:", Counter(s['resource'] for s in safe).most_common(12))
    print("  NARRATION-held by resource:", Counter(u[0]['resource'] for u in unsafe_narr).most_common(12))
    json.dump(safe, open('build/recon_pag/safe_dialogue_worklist.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
