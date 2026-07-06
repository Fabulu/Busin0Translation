#!/usr/bin/env python3
"""RECON A: COMBINED rule = scene-walk dialogue-context AND content not-narration.

scene-walk: active=True after any 0x14/0x0C, active=False after 0x0D; a bare 0x04
under active is dialogue-CONTEXT. This over-includes narration interludes.
Combine with a CONTENT veto: a dialogue-context group is only routed to 480 if its
english is NOT clearly 3rd-person descriptive narration.

narration-content heuristic (must be precise, since a false 'narration' veto on a
real dialogue line just leaves it at 360 = status quo, but a false 'dialogue' on a
narration line is the v90 regression we must avoid):
  narration if NO dialogue marker (speaker prefix / quote / \\n) AND begins with a
  narrative lead (past-tense 3rd-person 'As/He/She/They/No one/A man' ...). We use
  the safe inverse: route to 480 ONLY when (scene-active) AND content_dialogue-ish.
"""
import os, sys, struct, glob, json, re
os.chdir('C:/Programmieren/wizardrytranslation')
sys.path.insert(0,'tools')
from sec1_disasm import walk, extract_records
from patch_section1_offsets import parse_sec2_group_offsets

SPEAKER=re.compile(r'^[A-Z][A-Za-z .]{0,18}:')
# third-person narrative leads (past-tense scene description)
NARR_LEAD=re.compile(r'^(As |After |Before |When |No one |A man|A woman|A figure|'
    r'The |He |She |They |You |Suddenly|Then |Soon |Gin |Vera |Meanwhile)')
def content_dialogue(en):
    s=en.strip()
    if '\n' in en or SPEAKER.match(s) or s[:1] in ('"','“'): return True
    return False
def content_narration(en):
    s=en.strip()
    if content_dialogue(en): return False
    return bool(NARR_LEAD.match(s))

def load_res(r):
    raw=open(f'extracted/packdata_raw/{r:04d}_type02.raw','rb').read()
    so=struct.unpack_from('<I',raw,0x18)[0]; ss=struct.unpack_from('<I',raw,0x14)[0]
    sec1=raw[0x20:so]; sec2=raw[so:so+ss]
    groups,_=parse_sec2_group_offsets(sec2)
    ok,instrs=walk(sec1); recs=extract_records(sec1,instrs)
    return groups,ok,instrs,recs

def scene_active_map(r):
    """gi -> True if a bare 0x04 covering gi runs under an active speaker."""
    groups,ok,instrs,recs=load_res(r)
    if not ok: return None,None
    lg=set()
    for L in recs['label']:
        for gi,(gs,ge) in enumerate(groups):
            if gs<=L['off']<=ge: lg.add(gi); break
    disp={d['pc']:d for d in recs['display']}
    nameref={n['pc']:n for n in recs['name_ref']}
    active=False; amap={}; headed_block=set()
    for pc in sorted(instrs):
        op=instrs[pc]
        if op==0x14: active=True
        elif op==0x0C: active=True
        elif op==0x0D: active=False
        elif op==0x04:
            d=disp[pc]
            if d['cnt']==0: continue
            end=d['off']+d['cnt']
            cov=[gi for gi,(gs,ge) in enumerate(groups) if not (ge<d['off'] or gs>=end)]
            if not cov: continue
            first=cov[0]
            headed=(first in lg) or (first-1 in lg)
            for gi in cov:
                amap[gi]=active
                if headed: headed_block.add(gi)
    return amap,headed_block

TRUTH={(1197,4):'D',(1197,9):'D',(1197,10):'D',(1197,925):'D',(1197,927):'D',(1197,929):'D',
       (1196,569):'N',(1196,575):'N',(1196,616):'N',
       (1197,3):'N',(1197,7):'N',(1197,13):'N',(1197,926):'N',(1196,577):'D'}

def predict(r,gi,en,amap,headed):
    # rule: 480px if (headed-block) OR (scene-active AND content_dialogue)
    if gi in headed: return 'D'
    if amap.get(gi) and content_dialogue(en): return 'D'
    return 'N'

# load english
tr={}
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    try:
        for e in json.load(open(fn,encoding='utf-8')):
            tr[(e['resource'],e['msg_index'])]=e.get('english','')
    except Exception: pass

print("=== combined rule vs TRUTH ===")
cache={}
for r in sorted(set(k[0] for k in TRUTH)):
    cache[r]=scene_active_map(r)
c=w=0
for (r,gi),lab in TRUTH.items():
    amap,headed=cache[r]
    if amap is None: print(f"  R{r} walk-fail"); continue
    p=predict(r,gi,tr.get((r,gi),''),amap,headed)
    mark='OK' if p==lab else 'XX'
    if p==lab: c+=1
    else: w+=1
    print(f"  R{r} g{gi}: truth={lab} pred={p} [{mark}]")
print(f"  => {c} correct / {w} wrong")
