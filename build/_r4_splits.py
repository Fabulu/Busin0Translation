#!/usr/bin/env python3
"""TRACK P3: generate authored ' // ' page-split proposals for the genuine
dialogue groups still >4 lines at the P3 box budget (DIALOGUE_BOX_PX=372).

For each worklist group it COLLAPSES the source english to flat text, then
RECURSIVELY inserts ' // ' at the sentence boundary nearest each over-long page's
midpoint until every resulting page wraps to <=4 lines at BOX=372.  Splits are
NEVER 0xFFD2 — they are authored ' // ' markers in the source english (which the
build encodes as a single 0xFFFE line break per page boundary, see build_v9).

Read-only: prints the proposed source english.  --apply writes the proposals back
into data/type2_translated/batch_*.json 'english' fields (idempotent: re-running
after an apply is a no-op because the split text already wraps <=4).
"""
import sys
import glob
import json
import re

sys.path.insert(0, 'tools')
import glyph_metrics as gm
from dialogue_classifier import build_dialogue_map

# MUST mirror build_v9: same box budget + same exclusion set.
BOX = 372
FALSE_POS = {(1194, 0), (1196, 810), (1200, 64),
             (1212, 1), (1213, 1), (1353, 1)}
MAXPAGE = 4


def enc(c):
    o = ord(c)
    return o - 32 if 32 <= o < 127 else 0


def wrap_line_px(seg, box):
    words = seg.split(' ')
    lines, cur = [], ''
    for w in words:
        cand = w if not cur else cur + ' ' + w
        if cur and gm.px_width(cand, enc) > box:
            lines.append(cur)
            cur = w
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


def page_lines(flat, box):
    return len(wrap_line_px(flat, box))


def maxlines(w, box=BOX):
    return max(page_lines(p, box) for p in w.split(' // '))


def best_boundary(flat):
    """Return the char index of the sentence boundary nearest the midpoint, or a
    near-midpoint space if no sentence boundary exists."""
    ends = [m.end() for m in re.finditer(r'[.!?"]\s+', flat)]
    if not ends:
        ends = [m.end() for m in re.finditer(r'[,;:]\s+', flat)]
    target = len(flat) / 2
    if ends:
        return min(ends, key=lambda e: abs(e - target))
    sp = flat.rfind(' ', 0, int(target))
    return sp if sp > 0 else len(flat) // 2


def split_recursive(flat, box=BOX, depth=0):
    """Recursively split `flat` into ' // '-joined pages each <=MAXPAGE lines."""
    flat = flat.strip()
    if page_lines(flat, box) <= MAXPAGE or depth > 4:
        return flat
    b = best_boundary(flat)
    left, right = flat[:b].strip(), flat[b:].strip()
    if not left or not right:
        return flat  # cannot split further safely
    return (split_recursive(left, box, depth + 1) + ' // '
            + split_recursive(right, box, depth + 1))


def load_all():
    all_trans = {}
    files = {}
    for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
        try:
            d = json.load(open(fn, encoding='utf-8'))
        except Exception:
            continue
        for e in d:
            if 'resource' not in e or 'msg_index' not in e:
                continue
            r, mi, en = e['resource'], e['msg_index'], e.get('english', '')
            if not en or any(ord(c) > 127 for c in en):
                continue
            all_trans.setdefault(r, {})[mi] = en
            files.setdefault((r, mi), fn)
    return all_trans, files


def build_worklist(all_trans):
    wl = []
    for r in sorted(all_trans):
        if r == 1193:
            continue
        try:
            dmap = build_dialogue_map(r)
        except Exception:
            dmap = set()
        for mi, en in all_trans[r].items():
            if mi not in dmap:
                continue
            if (r, mi) in FALSE_POS:
                continue
            if maxlines(wrap_px(en, BOX)) > MAXPAGE:
                wl.append((r, mi, en))
    return wl


def main():
    apply = '--apply' in sys.argv
    all_trans, files = load_all()
    wl = build_worklist(all_trans)
    print(f"{len(wl)} genuine-dialogue page-splits proposed (BOX={BOX})")
    print()
    proposals = []
    ok = 0
    for r, mi, en in wl:
        flat = ' '.join(s.strip() for p in en.split(' // ')
                        for s in p.split(' / ') if s.strip())
        proposed = split_recursive(flat, BOX)
        after = maxlines(wrap_px(proposed, BOX), BOX)
        npages = proposed.count(' // ') + 1
        flag = 'OK' if after <= MAXPAGE else 'STILL>4'
        if after <= MAXPAGE:
            ok += 1
        print(f"R{r} g{mi}: -> {npages} pages, max {after} lines/page  [{flag}]")
        proposals.append((r, mi, proposed, after))
    print()
    print(f"{ok}/{len(wl)} reach <={MAXPAGE} lines/page.")

    if apply:
        # group proposals by file
        by_file = {}
        for r, mi, proposed, after in proposals:
            fn = files[(r, mi)]
            by_file.setdefault(fn, {})[(r, mi)] = proposed
        for fn, edits in by_file.items():
            d = json.load(open(fn, encoding='utf-8'))
            n = 0
            for e in d:
                key = (e.get('resource'), e.get('msg_index'))
                if key in edits:
                    e['english'] = edits[key]
                    n += 1
            json.dump(d, open(fn, 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=2)
            print(f"  applied {n} split(s) to {fn}")


if __name__ == '__main__':
    main()
