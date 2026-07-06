#!/usr/bin/env python3
"""Verify the 280 remaining TIER-2 offenders are name-island prefix artifacts,
NOT real screen-line overflow: for each offender group, the over-wide 'line' is
[name-label prefix consumed by the 0x14 NAME box] + [first dialogue line].  The
DISPLAY_TEXT for the dialogue starts at new_prefix_len, so the on-screen line 1
is only the portion AFTER the prefix -- which our wrap keeps <=16.

We re-run inject_and_patch's group-build for the offending groups and confirm:
 (1) the group has a name_plan entry (it's a name island), and
 (2) splitting the group's stream AFTER new_prefix_len yields all lines <=18.
"""
import sys, os, glob, struct
sys.stdout.reconfigure(encoding='utf-8')
ROOT = 'C:/Programmieren/wizardrytranslation'
os.chdir(ROOT)
sys.path.insert(0, 'tools')
sys.path.insert(0, 'tests')
sys.path.insert(0, 'build/recon_v89/phase2')
from verify_wrap import (load_all_trans, wrap_type2_text, encode_msg,
                         load_pristine_choice_groups)
from test_line_width import _line_offenders, EXEMPT_RESOURCES, CONTROL_FLOOR, ENGLISH_GLYPH_HI, LINE_BREAK, PAGE_BREAK
from _helpers import parse_type02
import patch_section1_offsets as ps

all_trans = load_all_trans()
SCRATCH = 'build/recon_v89/phase2/tier2_out'

# We need, per resource, the name_plan new_prefix_len for offending groups.
# Re-derive by calling the same internal build inject_and_patch does, but the
# simplest robust check: re-run inject_and_patch capturing name_plan via a tap.

orig_patch_section1 = ps.patch_section1
captured = {}

def tap(orig_bytes, injected, name_plan=None, res_name=None):
    captured[res_name] = dict(name_plan or {})
    return orig_patch_section1(orig_bytes, injected, name_plan=name_plan, res_name=res_name)

ps.patch_section1 = tap

def build_inject(r):
    choice = load_pristine_choice_groups(r)
    enc = {}
    for mi, en in all_trans[r].items():
        txt = en if mi in choice else wrap_type2_text(en)
        enc[mi] = encode_msg(txt)
    if r == 1203:
        enc = {mi: g for mi, g in enc.items() if mi <= 1016}
    ps.inject_and_patch(r, enc, 'extracted/packdata_raw', SCRATCH)


def split_widths(words):
    line = []
    out = []
    for w in words:
        if w in (LINE_BREAK, PAGE_BREAK):
            out.append(len([x for x in line if x < CONTROL_FLOOR]))
            line = []
        else:
            line.append(w)
    out.append(len([x for x in line if x < CONTROL_FLOOR]))
    return out


# collect offenders per resource
off_by_res = {}
for path in sorted(glob.glob(os.path.join(SCRATCH, '*.raw'))):
    res = int(os.path.basename(path)[:4])
    if res in EXEMPT_RESOURCES:
        continue
    try:
        p = parse_type02(open(path, 'rb').read())
    except Exception:
        continue
    for (r, gi, w, txt) in _line_offenders(p['words'], res):
        off_by_res.setdefault(r, []).append(gi)

name_island = 0
real_overflow = 0
no_plan = 0
examples = []
for r, gis in off_by_res.items():
    build_inject(r)  # populates captured[str(r)]
    np = captured.get(str(r), {})
    # reparse the freshly written output to get each group's words
    p = parse_type02(open(os.path.join(SCRATCH, f'{r:04d}_type02.raw'), 'rb').read())
    from _helpers import group_offsets
    groups, _ = group_offsets(p['words'])
    for gi in set(gis):
        plan = np.get(gi)
        gs, ge = groups[gi]
        gw = p['words'][gs:ge]
        if plan is None:
            no_plan += 1
            if len(examples) < 10:
                examples.append(('NO_PLAN', r, gi, split_widths(gw)))
            continue
        prefix = plan['new_prefix_len']
        body = gw[prefix:]
        widths = split_widths(body)
        # ignore the body's own line-1 leading break artifacts
        bad = [x for x in widths if x > 18]
        if bad:
            real_overflow += 1
            if len(examples) < 10:
                examples.append(('REAL', r, gi, widths))
        else:
            name_island += 1

print(f"offending groups total: {sum(len(set(g)) for g in off_by_res.values())}")
print(f"  name-island prefix artifact (body after prefix all <=18): {name_island}")
print(f"  REAL overflow in dialogue body: {real_overflow}")
print(f"  no name_plan entry (not a name island): {no_plan}")
print("\nexamples:")
for kind, r, gi, widths in examples:
    print(f"  [{kind}] R{r} g{gi} body line widths={widths}")
