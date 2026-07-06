#!/usr/bin/env python3
"""RECON A: systematic dialogue/narration misroute sweep.

Quantify, across all type-02 resources we translated, every group the build
classifies as NARRATION but which wraps >3 lines at 360px and <=3 lines at 480px
(candidate mis-routed boxed dialogue). Reproduce the build's exact wrap.
"""
import os, sys, struct, glob, json
os.chdir('C:/Programmieren/wizardrytranslation')
sys.path.insert(0, 'tools')

from sec1_disasm import walk, extract_records
from patch_section1_offsets import parse_sec2_group_offsets
from dialogue_classifier import build_dialogue_map, build_narration_map
import glyph_metrics

table = json.load(open('data/english_glyph_table.json', encoding='utf-8'))
def enc(ch):
    if ch in table: return table[ch]
    if ch.lower() in table: return table[ch.lower()]
    return 31

# ---- replicate build_v9 wrap helpers ----
def _wrap_line_px(seg, box_px):
    words = seg.split(' ')
    lines, cur = [], ''
    for w in words:
        cand = w if not cur else cur + ' ' + w
        if cur and glyph_metrics.px_width(cand, enc) > box_px:
            lines.append(cur); cur = w
        else:
            cur = cand
    if cur: lines.append(cur)
    return lines or ['']

def wrap_px_collapse(text, box_px):
    flat = ' '.join(s.strip() for s in text.replace(' // ', ' / ').split(' / ') if s.strip())
    return ' / '.join(_wrap_line_px(flat, box_px))

def n_lines(text):
    # number of rendered lines = count of ' / ' segments across pages
    parts = [seg for page in text.split(' // ') for seg in page.split(' / ')]
    return len(parts)

DIALOGUE_BOX_PX = 480
NARRATION_BOX_PX = 360

# ---- load translations exactly as build_v9 does ----
SKIP_STRUCTURAL_GROUPS = {(1197, 1)}
all_trans = {}
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    # MIRROR build_v9 EXACTLY: one try/except around the whole file; a KeyError
    # (e.g. batch_md_import.json has 'message' not 'msg_index') aborts that file
    # so the build silently skips it -> we must too.
    try:
        d = json.load(open(fn, encoding='utf-8'))
        for e in d:
            r = e['resource']
            mi = e['msg_index']
            if (r, mi) in SKIP_STRUCTURAL_GROUPS:
                continue
            en = e.get('english', '')
            if not en:
                continue
            if en.startswith('[DATA]') or en.startswith('[LAYOUT]') or en.startswith('[BINARY]'):
                continue
            if en.startswith('[MAP]') or en.startswith('[SYSTEM]') or en.startswith('[GLYPH'):
                continue
            if en.startswith('[DEBUG]'):
                continue
            if any(ord(c) > 127 for c in en):
                continue
            all_trans.setdefault(r, {})[mi] = en
    except Exception as ex:
        print(f"  Warning: {fn}: {ex}")

manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))
type02 = sorted(r for r in all_trans
                if r < len(manifest) and not manifest[r].get('skipped')
                and manifest[r].get('type_code') == 2 and r != 1193)

# ---- sweep ----
report = []   # (res, gi, en, n360, n480)
per_res = {}
total_narr = 0
total_dialogue = 0
walk_fail = []
for r in type02:
    dmap = build_dialogue_map(r)
    nmap = build_narration_map(r)
    total_dialogue += len(dmap)
    total_narr += len(nmap)
    if not dmap and not nmap:
        walk_fail.append(r)
    for mi, en in all_trans[r].items():
        if mi not in nmap:
            continue
        n360 = n_lines(wrap_px_collapse(en, NARRATION_BOX_PX))
        n480 = n_lines(wrap_px_collapse(en, DIALOGUE_BOX_PX))
        if n360 > 3 and n480 <= 3:
            report.append((r, mi, en, n360, n480))
            per_res[r] = per_res.get(r, 0) + 1

print("=== SWEEP RESULTS ===")
print(f"type02 resources translated: {len(type02)}")
print(f"total dialogue-mapped groups: {total_dialogue}")
print(f"total narration-mapped groups: {total_narr}")
print(f"walk-fail (empty both maps): {len(walk_fail)} -> {walk_fail}")
print(f"\nCANDIDATE MIS-ROUTED (narration-mapped, >3 lines@360 but <=3@480): {len(report)}")
print("\nPer-resource breakdown:")
for r in sorted(per_res, key=lambda k: -per_res[k]):
    print(f"  R{r}: {per_res[r]}")

json.dump([{'res':r,'gi':g,'en':e,'n360':a,'n480':b} for (r,g,e,a,b) in report],
          open('build/recon_sweep/candidates.json','w',encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f"\nwrote build/recon_sweep/candidates.json ({len(report)} entries)")
