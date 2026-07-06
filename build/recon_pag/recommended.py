import sys,struct,json,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build/recon_pag')
import patch_section1_offsets as P
from sec1_disasm import extract_records
from spans import load, groups_in_span
P._load_tables()
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]
PURE_NARR={1193,1194}

def dialogue_groups(res):
    """RECOMMENDED narration-safe classifier.
    A group is DIALOGUE (safe to auto-paginate) iff res not pure-narration AND
      (A) the JP 0x04 block covering it already contains a 0xFFD2 page break, OR
      (B) the 0x04 body span begins at a group whose 0x14 prefix decodes to a
          KNOWN speaker name (data/name_labels.json).
    Returns (dialogue_groups, all_targeted_groups, ok)."""
    L=load(res)
    if not L: return None
    ok,instrs,sec1,groups,words=L
    if not ok: return None
    if res in PURE_NARR: return (set(), set(), ok)
    recs=extract_records(sec1,instrs)
    named=set()
    for r in recs['label']:
        gi=P._find_group(groups,r['off'])
        if gi is None: continue
        if r['off']!=groups[gi][0]: continue
        nm=P._decode_jp(words[r['off']:r['off']+r['cnt']])
        if nm and nm in P._NAME_LABELS: named.add(gi)
    dlg=set(); targeted=set()
    for r in recs['display']:
        if r['cnt']==0: continue
        sg=groups_in_span(groups,r['off'],r['cnt'])
        targeted.update(sg)
        jp_ffd2=any(0xFFD2 in words[groups[g][0]:groups[g][1]] for g in sg)
        if jp_ffd2 or (sg and sg[0] in named):
            dlg.update(sg)
    return (dlg, targeted, ok)

if __name__=='__main__':
    # validate FP
    NARR=[(1196,569),(1196,575),(1196,577),(1196,616),(1193,0),(1194,0),(1196,564),(1196,567),(1196,568)]
    DIAL=[(1197,904),(1197,905),(1197,906),(1196,556),(1196,562),(1196,577)]
    c={}
    def get(res):
        if res not in c: c[res]=dialogue_groups(res)
        return c[res]
    fp=0
    print("=== NARRATION labels (must NOT be dialogue) ===")
    for res,gi in NARR:
        r=get(res); 
        cl='DIALOGUE' if (r and gi in r[0]) else 'narration/skip'
        bad= r and gi in r[0]
        fp+=bool(bad)
        print("  R%d g%d -> %s%s"%(res,gi,cl,'  FALSE POSITIVE' if bad else ''))
    print("=== DIALOGUE labels (want dialogue) ===")
    fn=0
    for res,gi in DIAL:
        r=get(res); hit= r and gi in r[0]
        if not hit: fn+=1
        print("  R%d g%d -> %s"%(res,gi,'DIALOGUE' if hit else 'MISSED(false neg)'))
    print("\nNarration FALSE POSITIVES:",fp," | Dialogue false negatives:",fn)

    # apply to overflow worklist
    overflow=json.load(open('build/recon_pag/overflow_worklist.json',encoding='utf-8'))
    byres={}
    for o in overflow: byres.setdefault(o['resource'],[]).append(o)
    safe=[]; held=[]; t1=0; unw=0
    for res,items in sorted(byres.items()):
        if not os.path.isfile(f'extracted/packdata_raw/{res:04d}_type02.raw'):
            t1+=len(items); continue
        r=get(res)
        if not r: unw+=len(items); continue
        dlg=r[0]
        for it in items:
            (safe if it['message'] in dlg else held).append(it)
    print("\n=== OVERFLOW WORKLIST (>4 English lines, no authored //) ===")
    print("total:",len(overflow)," type01(R39 etc):",t1," t2-unwalkable:",unw)
    print("SAFE dialogue (auto-paginate):",len(safe))
    print("HELD (no proof of dialogue, ship as-is):",len(held))
    from collections import Counter
    print("SAFE by res:",Counter(s['resource'] for s in safe).most_common(15))
    json.dump(safe,open('build/recon_pag/RECOMMENDED_safe_worklist.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
