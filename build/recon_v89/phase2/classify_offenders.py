#!/usr/bin/env python3
"""For each remaining TIER-2 offender, determine: is the group TRANSLATED
(present in all_trans, so our wrap path should have handled it) or PRISTINE
(untranslated original glyphs that happen to be ASCII -> not our regression)?"""
import sys, os, glob
sys.stdout.reconfigure(encoding='utf-8')
ROOT = 'C:/Programmieren/wizardrytranslation'
os.chdir(ROOT)
sys.path.insert(0, 'tools')
sys.path.insert(0, 'tests')
sys.path.insert(0, 'build/recon_v89/phase2')
from verify_wrap import load_all_trans, type02_set, load_pristine_choice_groups
from test_line_width import _line_offenders, EXEMPT_RESOURCES
from _helpers import parse_type02

all_trans = load_all_trans()
SCRATCH = 'build/recon_v89/phase2/tier2_out'

translated_off = []
pristine_off = []
for path in sorted(glob.glob(os.path.join(SCRATCH, '*.raw'))):
    res = int(os.path.basename(path)[:4])
    if res in EXEMPT_RESOURCES:
        continue
    try:
        p = parse_type02(open(path, 'rb').read())
    except Exception:
        continue
    for (r, gi, w, txt) in _line_offenders(p['words'], res):
        is_trans = gi in all_trans.get(r, {})
        (translated_off if is_trans else pristine_off).append((r, gi, w, txt))

print(f"TRANSLATED offenders (our wrap path SHOULD have fixed): {len(translated_off)}")
for r, gi, w, txt in translated_off[:20]:
    print(f"  R{r} g{gi} w={w}: {txt[:50]!r}  EN={all_trans[r][gi][:60]!r}")
print(f"\nPRISTINE offenders (untranslated original ASCII -- not the v89 regression): {len(pristine_off)}")
for r, gi, w, txt in pristine_off[:10]:
    print(f"  R{r} g{gi} w={w}: {txt[:50]!r}")
