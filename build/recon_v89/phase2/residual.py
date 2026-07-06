#!/usr/bin/env python3
"""Categorize the residual >16-glyph lines after wrapping: choice groups
(intentionally unwrapped) vs single oversize tokens (force-broken at width)
vs genuine leaks."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
ROOT = 'C:/Programmieren/wizardrytranslation'
os.chdir(ROOT)
sys.path.insert(0, 'tools')
sys.path.insert(0, 'build/recon_v89/phase2')
from verify_wrap import (load_all_trans, type02_set, wrap_type2_text,
                         load_pristine_choice_groups, measure_lines)

all_trans = load_all_trans()
t02 = type02_set(all_trans)

choice_lines = 0     # in choice groups (not wrapped on purpose)
token_lines = 0      # single token longer than 16 (no space to break)
other_lines = 0
samples = []
for r in sorted(t02):
    choice = load_pristine_choice_groups(r)
    for mi, en in all_trans[r].items():
        is_choice = mi in choice
        txt = en if is_choice else wrap_type2_text(en)
        for seg in [s for page in txt.split(' // ') for s in page.split(' / ')]:
            if len(seg) > 16:
                if is_choice:
                    choice_lines += 1
                elif ' ' not in seg.strip():
                    token_lines += 1
                    if len(samples) < 12:
                        samples.append((r, mi, 'TOKEN', seg))
                else:
                    other_lines += 1
                    if len(samples) < 12:
                        samples.append((r, mi, 'OTHER', seg))

print(f"residual >16 lines: choice(unwrapped)={choice_lines}  "
      f"single-token={token_lines}  other={other_lines}")
print("\nsamples:")
for r, mi, kind, seg in samples:
    print(f"  R{r} g{mi} [{kind}] ({len(seg)}): {seg!r}")
