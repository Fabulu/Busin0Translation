#!/usr/bin/env python3
"""RECON A phase 2: find the real DIALOGUE-vs-NARRATION discriminator.

Tests three hypotheses against KNOWN truth, with code, on real resources:
 (a) SCENE-WALK speaker inheritance: the FIRST 0x14 name-island OR 0x0C
     SET_NAME_REF in program order sets dialogue-box mode for all following bare
     0x04 DISPLAY blocks until a 'scene boundary' (define structurally).
 (b) Section-1 render-MODE opcode (does any opcode toggle box mode?).
 (c) CONTENT signal in english (speaker prefix / quotes / \\n).
"""
import os, sys, struct, glob, json
os.chdir('C:/Programmieren/wizardrytranslation')
sys.path.insert(0, 'tools')
from sec1_disasm import walk, extract_records, LENB
from patch_section1_offsets import parse_sec2_group_offsets

def load_res(r):
    path = f'extracted/packdata_raw/{r:04d}_type02.raw'
    raw = open(path, 'rb').read()
    sec2_off = struct.unpack_from('<I', raw, 0x18)[0]
    sec2_size = struct.unpack_from('<I', raw, 0x14)[0]
    sec1 = raw[0x20:sec2_off]
    sec2 = raw[sec2_off:sec2_off+sec2_size]
    groups, trailing = parse_sec2_group_offsets(sec2)
    ok, instrs = walk(sec1)
    recs = extract_records(sec1, instrs)
    return sec1, sec2, groups, ok, instrs, recs

def group_of(groups, off):
    for gi,(gs,ge) in enumerate(groups):
        if gs <= off <= ge:
            return gi
    return None

# ============ Hypothesis (a): scene-walk speaker inheritance ============
# Walk instructions in PROGRAM ORDER (sorted pc). Maintain active_speaker flag:
#   - 0x14 name-island sets active_speaker = True (and tags its OWN group dialogue)
#   - 0x0C SET_NAME_REF sets active_speaker = True
#   - 0x0D CLEAR_NAME_REF clears active_speaker = False
# A bare 0x04 DISPLAY block while active_speaker -> DIALOGUE; else NARRATION.
# 'scene boundary' candidates to test as mode-clearers: 0x0D, jump-back, choice
# opcodes. We compute dialogue set under this rule.

# opcode classes
CHOICE_OPS = set()  # discover empirically below

def scene_walk_classify(r, clear_on_0D=True):
    sec1, sec2, groups, ok, instrs, recs = load_res(r)
    if not ok:
        return None
    # build pc -> record lookups
    disp = {d['pc']: d for d in recs['display']}
    label = {}
    for L in recs['label']:
        label.setdefault(L['pc'], L)
    nameref = {n['pc']: n for n in recs['name_ref']}
    dialogue = set()
    narration = set()
    active = False
    for pc in sorted(instrs):
        op = instrs[pc]
        if op == 0x14:
            active = True
            gi = group_of(groups, label[pc]['off'])
            if gi is not None:
                dialogue.add(gi)
        elif op == 0x0C:
            active = True
        elif op == 0x0D:
            if clear_on_0D:
                active = False
        elif op == 0x04:
            d = disp[pc]
            if d['cnt'] == 0:
                continue
            end = d['off'] + d['cnt']
            covered = [gi for gi,(gs,ge) in enumerate(groups)
                       if not (ge < d['off'] or gs >= end)]
            for gi in covered:
                if active:
                    dialogue.add(gi)
                else:
                    narration.add(gi)
    # dialogue wins ties
    narration -= dialogue
    return dialogue, narration

# ============ Hypothesis (c): content signal ============
import re
SPEAKER_PREFIX = re.compile(r'^[A-Z][A-Za-z .]{0,18}:')
def content_is_dialogue(en):
    s = en.strip()
    if '\n' in en: return True          # multi-speaker exchange
    if SPEAKER_PREFIX.match(s): return True
    if s.startswith('"') or s.startswith('“'): return True
    return False

# ============ evaluate against known truth ============
TRUTH = {
    # (res, gi): 'D' dialogue (480) or 'N' narration (360)
    (1197,4):'D',(1197,9):'D',(1197,10):'D',(1197,925):'D',(1197,927):'D',(1197,929):'D',
    (1196,569):'N',(1196,575):'N',(1196,616):'N',
    (1197,3):'N',(1197,7):'N',(1197,13):'N',(1197,926):'N',
    (1196,577):'D',  # Shady Man boxed dialogue
}

print("=== Hypothesis (a): scene-walk speaker inheritance (clear on 0x0D) ===")
cache = {}
for clear in (True, False):
    print(f"\n-- clear_on_0D={clear} --")
    res_d = {}
    for r in sorted(set(k[0] for k in TRUTH)):
        out = scene_walk_classify(r, clear)
        if out is None:
            print(f"  R{r} walk-fail"); continue
        res_d[r] = out
    correct = wrong = 0
    for (r,gi),lab in TRUTH.items():
        if r not in res_d: continue
        dlg, narr = res_d[r]
        pred = 'D' if gi in dlg else ('N' if gi in narr else '?')
        mark = 'OK' if pred==lab else 'XX'
        if pred==lab: correct+=1
        else: wrong+=1
        print(f"  R{r} g{gi}: truth={lab} pred={pred} [{mark}]")
    print(f"  => {correct} correct / {wrong} wrong")
    cache[clear]=res_d

print("\n=== Hypothesis (c): content signal ===")
# load english for truth groups
all_trans={}
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    try:
        d=json.load(open(fn,encoding='utf-8'))
        for e in d:
            all_trans[(e['resource'],e['msg_index'])]=e.get('english','')
    except Exception: pass
for (r,gi),lab in TRUTH.items():
    en=all_trans.get((r,gi),'')
    pred='D' if content_is_dialogue(en) else 'N'
    mark='OK' if pred==lab else 'XX'
    print(f"  R{r} g{gi}: truth={lab} pred={pred} [{mark}]  {en[:60]!r}")
