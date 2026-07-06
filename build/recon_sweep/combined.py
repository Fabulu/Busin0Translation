#!/usr/bin/env python3
"""RECON A phase 2b: combined discriminator + structural inspection.

Goal: among the 571 narration-mapped candidates (>3@360, <=3@480), separate
TRUE boxed dialogue from TRUE long narration, WITHOUT regressing R1196 narration.

Insight from phase 2:
 - scene-walk marks ALL post-speaker groups dialogue (catches dialogue but
   floods narration interludes) -> high recall, low precision.
 - content (speaker-prefix/quote/\\n) is a precise NARRATION/DIALOGUE content
   signal: 3rd-person descriptive == narration; quoted/prefixed/\\n == dialogue.

Test the structural difference between a DIALOGUE 0x04 block and a NARRATION
interlude 0x04 block in the SAME scene (R1197). Maybe the 0x14/0x0C that precedes
a dialogue line is IMMEDIATELY before its 0x04 (adjacent), while narration
interludes have NO name-set in the few instrs before their 0x04.
"""
import os, sys, struct, glob, json
os.chdir('C:/Programmieren/wizardrytranslation')
sys.path.insert(0, 'tools')
from sec1_disasm import walk, extract_records
from patch_section1_offsets import parse_sec2_group_offsets

def load_res(r):
    raw = open(f'extracted/packdata_raw/{r:04d}_type02.raw','rb').read()
    sec2_off = struct.unpack_from('<I', raw, 0x18)[0]
    sec2_size = struct.unpack_from('<I', raw, 0x14)[0]
    sec1 = raw[0x20:sec2_off]; sec2 = raw[sec2_off:sec2_off+sec2_size]
    groups,_ = parse_sec2_group_offsets(sec2)
    ok,instrs = walk(sec1); recs = extract_records(sec1,instrs)
    return sec1,sec2,groups,ok,instrs,recs

def group_of(groups,off):
    for gi,(gs,ge) in enumerate(groups):
        if gs<=off<=ge: return gi
    return None

# For R1197, print every 0x04 DISPLAY in program order with: covered group,
# and the nearest preceding 0x14/0x0C (instr-distance). Tag with known truth.
TRUTH={4:'D',9:'D',10:'D',925:'D',927:'D',929:'D',3:'N',7:'N',13:'N',926:'N'}
for r in (1197,1196):
    print(f"\n===== R{r} 0x04 blocks in program order =====")
    sec1,sec2,groups,ok,instrs,recs=load_res(r)
    order=sorted(instrs)
    # index pc->position
    pos={pc:i for i,pc in enumerate(order)}
    label_pc=set(L['pc'] for L in recs['label'])
    label_grp={}
    for L in recs['label']:
        g=group_of(groups,L['off'])
        if g is not None: label_grp.setdefault(g,[]).append(L['pc'])
    nameset_pc=set(n['pc'] for n in recs['name_ref'] if n['op']==0x0C)
    nameclr_pc=set(n['pc'] for n in recs['name_ref'] if n['op']==0x0D)
    disp_by_pc={d['pc']:d for d in recs['display']}
    for d in recs['display']:
        if d['cnt']==0: continue
        end=d['off']+d['cnt']
        covered=[gi for gi,(gs,ge) in enumerate(groups) if not (ge<d['off'] or gs>=end)]
        if not covered: continue
        first=covered[0]
        # nearest preceding 0x14 or 0x0C in program order
        ppos=pos[d['pc']]
        prev_kind=None; prev_dist=None
        for j in range(ppos-1,-1,-1):
            ppc=order[j]
            if ppc in label_pc: prev_kind='0x14'; prev_dist=ppos-j; break
            if ppc in nameset_pc: prev_kind='0x0C'; prev_dist=ppos-j; break
            if ppc in nameclr_pc: prev_kind='0x0D'; prev_dist=ppos-j; break
        # does this group have its OWN 0x14 (local name-island)?
        own_label = first in label_grp or (first-1) in label_grp
        truth=TRUTH.get(first,'?')
        if truth!='?' or own_label:
            print(f"  g{first:4d} truth={truth} own_label={int(own_label)} "
                  f"prev={prev_kind}@{prev_dist} cnt={d['cnt']}")
