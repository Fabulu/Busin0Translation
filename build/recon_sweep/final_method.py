#!/usr/bin/env python3
"""RECON A final: classify the 571 narration-mapped overflow candidates into
PROVABLE boxed-dialogue (safe to reroute to 480px) vs ambiguous/narration.

Decisive signal set per candidate group gi:
  - covering 0x04 block: first/last group, block size (n groups)
  - block_headed: block's first group (or first-1) has a 0x14 name-island
  - block_multigroup: block spans >1 group (a back-and-forth conversation island)
  - content_dialogue: english has speaker-prefix / leading quote / literal \\n
  - content_narration: 3rd-person descriptive (no dialogue markers)

A candidate is SAFE-DIALOGUE iff (block_headed OR content_dialogue) -- i.e. it is
either structurally inside a name-island block OR its english is unambiguously
spoken. Pure bare-block 3rd-person prose stays NARRATION (no regression).
"""
import os, sys, struct, glob, json, re
os.chdir('C:/Programmieren/wizardrytranslation')
sys.path.insert(0,'tools')
from sec1_disasm import walk, extract_records
from patch_section1_offsets import parse_sec2_group_offsets

SPEAKER = re.compile(r'^[A-Z][A-Za-z .]{0,18}:')
def content_dialogue(en):
    s=en.strip()
    return ('\n' in en) or bool(SPEAKER.match(s)) or s[:1] in ('"','“')

def load_res(r):
    raw=open(f'extracted/packdata_raw/{r:04d}_type02.raw','rb').read()
    so=struct.unpack_from('<I',raw,0x18)[0]; ss=struct.unpack_from('<I',raw,0x14)[0]
    sec1=raw[0x20:so]; sec2=raw[so:so+ss]
    groups,_=parse_sec2_group_offsets(sec2)
    ok,instrs=walk(sec1); recs=extract_records(sec1,instrs)
    return groups,ok,instrs,recs

def analyze(r):
    """Return per-group dict: gi -> (block_first, block_size, block_headed)."""
    groups,ok,instrs,recs=load_res(r)
    if not ok: return None
    lg=set()
    for L in recs['label']:
        off=L['off']
        for gi,(gs,ge) in enumerate(groups):
            if gs<=off<=ge: lg.add(gi); break
    info={}
    for d in recs['display']:
        if d['cnt']==0: continue
        end=d['off']+d['cnt']
        cov=[gi for gi,(gs,ge) in enumerate(groups) if not (ge<d['off'] or gs>=end)]
        if not cov: continue
        first=cov[0]
        headed=(first in lg) or (first-1 in lg)
        for gi in cov:
            # if multiple blocks cover gi keep the headed-est (dialogue-most) one
            prev=info.get(gi)
            cur=(first,len(cov),headed)
            if prev is None or (headed and not prev[2]):
                info[gi]=cur
    return info

cand=json.load(open('build/recon_sweep/candidates.json',encoding='utf-8'))
by_res={}
for e in cand: by_res.setdefault(e['res'],[]).append(e)

reroute=[]; stay=[]
for r,entries in by_res.items():
    info=analyze(r)
    for e in entries:
        gi=e['gi']; en=e['en']
        binfo=info.get(gi) if info else None
        headed = bool(binfo and binfo[2])
        multi = bool(binfo and binfo[1]>1)
        cdlg = content_dialogue(en)
        safe = headed or cdlg
        rec={'res':r,'gi':gi,'headed':headed,'multi':multi,'content_dlg':cdlg,
             'n360':e['n360'],'n480':e['n480'],'en':en[:80]}
        (reroute if safe else stay).append(rec)

print(f"candidates: {len(cand)}")
print(f"SAFE-DIALOGUE reroute (headed OR content): {len(reroute)}")
print(f"STAY narration (bare 3rd-person prose): {len(stay)}")

# regression guard: no KNOWN narration may appear in reroute
KNOWN_NARR={(1196,569),(1196,575),(1196,616),(1197,3),(1197,7),(1197,13),(1197,926)}
bad=[(x['res'],x['gi']) for x in reroute if (x['res'],x['gi']) in KNOWN_NARR]
print(f"REGRESSION CHECK -- known narration wrongly in reroute: {bad}")

# how many reroute are headed vs content-only
h=sum(1 for x in reroute if x['headed'])
co=sum(1 for x in reroute if not x['headed'] and x['content_dlg'])
print(f"  reroute by headed-block: {h} | by content-only: {co}")

# breakdown per resource
from collections import Counter
print("reroute per resource:", dict(Counter(x['res'] for x in reroute)))

json.dump(reroute, open('build/recon_sweep/reroute_480.json','w',encoding='utf-8'),
          ensure_ascii=False, indent=1)
json.dump(stay, open('build/recon_sweep/stay_narration.json','w',encoding='utf-8'),
          ensure_ascii=False, indent=1)
print("wrote reroute_480.json + stay_narration.json")

# also emit the DIALOGUE_FORCE-style tuple list
pairs=sorted((x['res'],x['gi']) for x in reroute)
print("FORCE-480 pairs:")
print(pairs)
