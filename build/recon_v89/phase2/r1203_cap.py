#!/usr/bin/env python3
"""Empirically derive the R1203 Section-2 word cap under the NEW wrapped encoding
by actually running inject_and_patch and reading the real output word count.

The estimate in verify_wrap.py undercounts because inject_and_patch rebuilds
name-island groups as English labels (longer than pristine).  The authoritative
number is the injected output's Section-2 size, so binary-search on the real
inject."""
import sys, os, struct, glob, json
sys.stdout.reconfigure(encoding='utf-8')
ROOT = 'C:/Programmieren/wizardrytranslation'
os.chdir(ROOT)
sys.path.insert(0, 'tools')
sys.path.insert(0, 'build/recon_v89/phase2')

from patch_section1_offsets import inject_and_patch
from verify_wrap import (load_all_trans, wrap_type2_text, encode_msg,
                         load_pristine_choice_groups)

R = 1203
LIMIT = 65535
OUT = 'build/recon_v89/phase2/cap_out'
os.makedirs(OUT, exist_ok=True)

all_trans = load_all_trans()
choice = load_pristine_choice_groups(R)


def full_encoded():
    enc = {}
    for mi, en in all_trans[R].items():
        txt = en if mi in choice else wrap_type2_text(en)
        enc[mi] = encode_msg(txt)
    return enc


full = full_encoded()
keys = sorted(full)


def words_at(cap):
    capped = {mi: g for mi, g in full.items() if mi <= cap}
    res = inject_and_patch(R, capped, 'extracted/packdata_raw', OUT)
    if res[0] is None:
        return None
    out = open(os.path.join(OUT, res[0]), 'rb').read()
    s2sz = struct.unpack_from('<I', out, 0x14)[0]
    return s2sz // 2


# binary search highest cap whose real injected word count <= LIMIT
lo, hi = 0, max(keys)
best = None
best_words = None
# candidate caps = the actual group keys (caps between keys give same result)
cands = keys
import bisect
lo_i, hi_i = 0, len(cands) - 1
while lo_i <= hi_i:
    mid = (lo_i + hi_i) // 2
    cap = cands[mid]
    w = words_at(cap)
    tag = 'OK' if (w is not None and w <= LIMIT) else 'OVER'
    print(f"  cap={cap}: words={w} [{tag}]")
    if w is not None and w <= LIMIT:
        best, best_words = cap, w
        lo_i = mid + 1
    else:
        hi_i = mid - 1

print(f"\nHIGHEST SAFE CAP under wrapping: {best}  (Section-2 words={best_words}, limit={LIMIT})")
# confirm next group over the cap overflows
nxt = cands[bisect.bisect_right(cands, best)] if bisect.bisect_right(cands, best) < len(cands) else None
if nxt is not None:
    wn = words_at(nxt)
    print(f"Next group {nxt}: words={wn} [{'OK' if wn<=LIMIT else 'OVER'}] (confirms cap boundary)")
print(f"\nOLD CAP 1069: words={words_at(1069)}")
