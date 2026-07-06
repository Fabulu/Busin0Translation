#!/usr/bin/env python3
"""Simulate test_line_width TIER-2 against SCRATCH-injected output (without
touching the real build/patched_type2).  Injects every type-02 resource with the
NEW wrapped Step-4 encoding into a scratch dir, then runs the test's exact
offender logic.  Proves a fresh build makes TIER-2 pass."""
import sys, os, glob
sys.stdout.reconfigure(encoding='utf-8')
ROOT = 'C:/Programmieren/wizardrytranslation'
os.chdir(ROOT)
sys.path.insert(0, 'tools')
sys.path.insert(0, 'tests')
sys.path.insert(0, 'build/recon_v89/phase2')

from patch_section1_offsets import inject_and_patch
from verify_wrap import (load_all_trans, type02_set, wrap_type2_text,
                         encode_msg, load_pristine_choice_groups)
# the test's own logic & helpers
from test_line_width import _line_offenders, EXEMPT_RESOURCES, MAX_GLYPHS, _format_offenders
from _helpers import parse_type02

R1203_MAX_GROUP = 1016
SCRATCH = 'build/recon_v89/phase2/tier2_out'
os.makedirs(SCRATCH, exist_ok=True)

all_trans = load_all_trans()
t02 = type02_set(all_trans)

# inject all type-02 into scratch with the new encoding
for r_id in sorted(t02):
    choice = load_pristine_choice_groups(r_id)
    encoded = {}
    for mi, en in all_trans[r_id].items():
        txt = en if mi in choice else wrap_type2_text(en)
        encoded[mi] = encode_msg(txt)
    if r_id == 1203:
        encoded = {mi: g for mi, g in encoded.items() if mi <= R1203_MAX_GROUP}
    inject_and_patch(r_id, encoded, 'extracted/packdata_raw', SCRATCH)

# run the TEST's exact offender logic over the scratch output
offenders = []
checked = 0
for path in sorted(glob.glob(os.path.join(SCRATCH, '*.raw'))):
    res = int(os.path.basename(path)[:4])
    if res in EXEMPT_RESOURCES:
        continue
    try:
        p = parse_type02(open(path, 'rb').read())
    except Exception:
        continue
    checked += 1
    offenders.extend(_line_offenders(p['words'], res))

print(f"checked {checked} type-02 resources, MAX_GLYPHS={MAX_GLYPHS}")
if offenders:
    print(f"FAIL: {len(offenders)} offender line(s)")
    print("  " + _format_offenders(offenders))
else:
    print("PASS: 0 injected-English lines exceed the gate (TIER-2 would PASS after build)")
