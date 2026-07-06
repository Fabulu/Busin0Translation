#!/usr/bin/env python3
"""RECON A phase 2c: window-opcode discriminator.

Hypothesis (b)/(a) refined: each 0x04 DISPLAY block's render box is set by the
MOST-RECENT window-setup opcode preceding it in PROGRAM ORDER along the walked
control flow. Candidates observed in the barkeep scene:
  0x48 (3 operands, stores a byte global @gp-0x6930)  precedes DIALOGUE g4
  0x47 (2 operands, calls 0x2FF590 with a3=1)         precedes NARRATION g7/g13

We classify by scanning backwards in program order from each 0x04 to the nearest
0x47/0x48 and tagging dialogue (0x48) vs narration (0x47). 0x14-name-island
groups stay dialogue (the existing proven rule).

Evaluate precision/recall vs known truth and report disagreement with the
existing build_narration_map / build_dialogue_map (the 571 candidates).
"""
import os, sys, struct, glob, json
os.chdir('C:/Programmieren/wizardrytranslation')
sys.path.insert(0,'tools')
from sec1_disasm import walk, extract_records
from patch_section1_offsets import parse_sec2_group_offsets
from dialogue_classifier import build_dialogue_map, build_narration_map

WIN_DIALOGUE = {0x48}
WIN_NARRATION = {0x47}

def load_res(r):
    raw=open(f'extracted/packdata_raw/{r:04d}_type02.raw','rb').read()
    sec2_off=struct.unpack_from('<I',raw,0x18)[0]
    sec2_size=struct.unpack_from('<I',raw,0x14)[0]
    sec1=raw[0x20:sec2_off]; sec2=raw[sec2_off:sec2_off+sec2_size]
    groups,_=parse_sec2_group_offsets(sec2)
    ok,instrs=walk(sec1); recs=extract_records(sec1,instrs)
    return groups,ok,instrs,recs

def group_of(groups,off):
    for gi,(gs,ge) in enumerate(groups):
        if gs<=off<=ge: return gi
    return None

def classify_window(r):
    """Return (dialogue_set, narration_set) by nearest preceding 0x47/0x48."""
    groups,ok,instrs,recs=load_res(r)
    if not ok: return None
    label_groups=set()
    for L in recs['label']:
        g=group_of(groups,L['off'])
        if g is not None: label_groups.add(g)
    order=sorted(instrs)
    pos={pc:i for i,pc in enumerate(order)}
    disp={d['pc']:d for d in recs['display']}
    dialogue=set(); narration=set()
    for d in recs['display']:
        if d['cnt']==0: continue
        end=d['off']+d['cnt']
        cov=[gi for gi,(gs,ge) in enumerate(groups) if not (ge<d['off'] or gs>=end)]
        if not cov: continue
        first=cov[0]
        # scan back in program order for nearest 0x47/0x48
        i=pos[d['pc']]; win=None
        for j in range(i-1,-1,-1):
            op=instrs[order[j]]
            if op in WIN_DIALOGUE: win='D'; break
            if op in WIN_NARRATION: win='N'; break
        # name-island group is always dialogue
        if first in label_groups or (first-1) in label_groups:
            for gi in cov: dialogue.add(gi)
        elif win=='D':
            for gi in cov: dialogue.add(gi)
        elif win=='N':
            for gi in cov: narration.add(gi)
        else:
            # no window opcode seen -> fall back to narration (conservative)
            for gi in cov: narration.add(gi)
    narration-=dialogue
    return dialogue,narration

TRUTH={(1197,4):'D',(1197,9):'D',(1197,10):'D',(1197,925):'D',(1197,927):'D',(1197,929):'D',
       (1196,569):'N',(1196,575):'N',(1196,616):'N',
       (1197,3):'N',(1197,7):'N',(1197,13):'N',(1197,926):'N',(1196,577):'D'}

print("=== window-opcode classifier vs TRUTH ===")
cache={}
correct=wrong=0
for r in sorted(set(k[0] for k in TRUTH)):
    cache[r]=classify_window(r)
for (r,gi),lab in TRUTH.items():
    out=cache[r]
    if out is None: print(f"  R{r} g{gi}: walk-fail"); continue
    dlg,narr=out
    pred='D' if gi in dlg else ('N' if gi in narr else '?')
    mark='OK' if pred==lab else 'XX'
    if pred==lab: correct+=1
    else: wrong+=1
    print(f"  R{r} g{gi}: truth={lab} pred={pred} [{mark}]")
print(f"  => {correct} correct / {wrong} wrong")
