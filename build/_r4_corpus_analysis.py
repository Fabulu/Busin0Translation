#!/usr/bin/env python3
"""TRACK R4 read-only corpus analysis: with a raised DIALOGUE_BOX_PX, how many
dialogue groups still exceed 3/4 lines per ' // ' page?  Worklist them.

NO build side effects: re-implements wrap_px locally but uses the SAME
glyph_metrics SoT widths and the SAME build_dialogue_map classifier.
"""
import sys, os, glob, json
sys.path.insert(0, 'tools')
import glyph_metrics as gm
from dialogue_classifier import build_dialogue_map

GLYPH = None
def enc(c):
    o = ord(c)
    return o - 32 if 32 <= o < 127 else 0

def wrap_line_px(seg, box):
    words = seg.split(' '); lines = []; cur = ''
    for w in words:
        cand = w if not cur else cur + ' ' + w
        if cur and gm.px_width(cand, enc) > box:
            lines.append(cur); cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines or ['']

def wrap_px(text, box):
    out = []
    for page in text.split(' // '):
        flat = ' '.join(s.strip() for s in page.split(' / ') if s.strip())
        out.append(' / '.join(wrap_line_px(flat, box)))
    return ' // '.join(out)

def max_lines_per_page(wrapped):
    return max(len(p.split(' / ')) for p in wrapped.split(' // '))

# Load all type-2 translations exactly like build_v9.
all_trans = {}
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    try:
        d = json.load(open(fn, encoding='utf-8'))
    except Exception:
        continue
    for e in d:
        if 'resource' not in e or 'msg_index' not in e:
            continue
        r = e['resource']; mi = e['msg_index']; en = e.get('english', '')
        if not en:
            continue
        if en[:6] in ('[DATA]', '[LAYOU', '[BINAR', '[MAP]', '[SYSTE', '[GLYPH', '[DEBUG'):
            continue
        if any(ord(c) > 127 for c in en):
            continue
        all_trans.setdefault(r, {})[mi] = en

BOX = int(sys.argv[1]) if len(sys.argv) > 1 else 376

# Restrict to resources that have a dialogue map.
results = {}  # r -> list of (mi, maxlines, total_src_segs)
total_dialogue_groups = 0
over4 = []
over3 = []
for r in sorted(all_trans):
    try:
        dmap = build_dialogue_map(r)
    except Exception:
        dmap = set()
    if not dmap:
        continue
    for mi, en in all_trans[r].items():
        if mi not in dmap:
            continue
        total_dialogue_groups += 1
        wrapped = wrap_px(en, BOX)
        ml = max_lines_per_page(wrapped)
        if ml >= 5:
            over4.append((r, mi, ml, en))
        if ml == 4:
            over3.append((r, mi, ml, en))

print(f"BOX_PX={BOX}")
print(f"Total dialogue groups (classifier-gated): {total_dialogue_groups}")
print(f"Groups still > 4 lines on some page: {len(over4)}")
print(f"Groups == 4 lines (at the 4-line limit): {len(over3)}")
print()
print("=== WORKLIST: groups > 4 lines (NEED authored ' // ' page splits) ===")
for r, mi, ml, en in sorted(over4):
    print(f"  R{r} g{mi}  maxlines={ml}")
    for ln in wrap_px(en, BOX).split(' // '):
        for sub in ln.split(' / '):
            print(f"       | {gm.px_width(sub,enc):3d}px {sub}")
        print("       ---page---")
