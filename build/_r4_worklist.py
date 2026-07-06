#!/usr/bin/env python3
"""TRACK R4 final worklist: categorize the >4-line groups into
  (A) GENUINE dialogue -> need authored ' // ' page splits
  (B) FALSE-POSITIVE (menu/list/narration) -> classifier/skip guard, NOT page-split
and propose a ' // ' split for category A.
"""
import sys, os, glob, json
sys.path.insert(0, 'tools')
import glyph_metrics as gm
from dialogue_classifier import build_dialogue_map

def enc(c):
    o = ord(c); return o - 32 if 32 <= o < 127 else 0

def wrap_line_px(seg, box):
    words = seg.split(' '); lines = []; cur = ''
    for w in words:
        cand = w if not cur else cur + ' ' + w
        if cur and gm.px_width(cand, enc) > box:
            lines.append(cur); cur = w
        else:
            cur = cand
    if cur: lines.append(cur)
    return lines or ['']

def wrap_px(text, box):
    out = []
    for page in text.split(' // '):
        flat = ' '.join(s.strip() for s in page.split(' / ') if s.strip())
        out.append(' / '.join(wrap_line_px(flat, box)))
    return ' // '.join(out)

def maxlines(w):
    return max(len(p.split(' / ')) for p in w.split(' // '))

BOX = 376
all_trans = {}
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    try: d = json.load(open(fn, encoding='utf-8'))
    except Exception: continue
    for e in d:
        if 'resource' not in e or 'msg_index' not in e: continue
        r, mi, en = e['resource'], e['msg_index'], e.get('english', '')
        if not en or en[:6] in ('[DATA]','[LAYOU','[BINAR','[MAP]','[SYSTE','[GLYPH','[DEBUG'): continue
        if any(ord(c) > 127 for c in en): continue
        all_trans.setdefault(r, {})[mi] = en

cat_A = []  # genuine dialogue
cat_B = []  # false positives
for r in sorted(all_trans):
    if r == 1193:   # built separately (narration), never wrap_px'd
        continue
    try: dmap = build_dialogue_map(r)
    except Exception: dmap = set()
    for mi, en in all_trans[r].items():
        if mi not in dmap: continue
        w = wrap_px(en, BOX)
        if maxlines(w) < 5: continue
        # classify false-positive: literal newline, or many short ' / ' segments
        # that look like a command/menu list, or the long ending crawl (R1194)
        has_nl = '\n' in en
        segs = [s for s in en.replace(' // ',' / ').split(' / ') if s.strip()]
        avg_seg = sum(len(s) for s in segs)/max(1,len(segs))
        is_list = len(segs) >= 5 and avg_seg < 18 and not has_nl
        is_crawl = r == 1194
        if has_nl or is_crawl or (is_list and r in (1196,1200,1212,1213,1347,1353,1355,1196)):
            cat_B.append((r, mi, en, 'newline' if has_nl else ('crawl' if is_crawl else 'list')))
        else:
            cat_A.append((r, mi, en, w))

print(f"=== CATEGORY A: GENUINE dialogue >4 lines (need ' // ' page split): {len(cat_A)} ===")
for r, mi, en, w in cat_A:
    pages = w.split(' // ')
    print(f"R{r} g{mi}  maxlines={maxlines(w)}  pages_now={len(pages)}")
print()
print(f"=== CATEGORY B: FALSE-POSITIVE (menu/list/crawl) -> guard, NOT split: {len(cat_B)} ===")
for r, mi, en, why in cat_B:
    print(f"R{r} g{mi}  reason={why}  src={en[:60]!r}")
