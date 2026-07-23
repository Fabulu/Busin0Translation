#!/usr/bin/env python3
"""test_r34_name_budget.py -- item-name display-overflow gate (the long-reported
inventory overflow).

Every R34 item NAME must fit the narrowest inventory slot: <=13 glyph cells,
ASCII only. Names render monospace from a SINGLE R34 source across every
inventory screen (camp bag, alchemy shop, item pill, battle menu, library
mirror), and the slots are runtime-width with NO clipping -- a name >13 cells
overdraws the stat panel (camp list) or the shop quantity column ("...Boo0/40"
garble). Root cause + measurements: scratchpad/inv_findings/FINDINGS.md; the
v190 wave rewrote 228 names to <=13. This gate keeps them capped.

TIER-1: the source data is always present (not build-gated).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, main_exit, require_file

R34 = os.path.join(ROOT, "data", "r34_english_aligned.json")
NAME_SUBS = {0, 2, 4, 6, 8, 10, 12, 14, 15, 16, 17, 18, 19}
MAX_CELLS = 13


def _names():
    require_file(R34, "R34 aligned item DB")
    ents = json.load(open(R34, encoding="utf-8"))["entries"]
    return [
        e for e in ents
        if e.get("sub") in NAME_SUBS
        and isinstance(e.get("english"), str)
        and e["english"]
    ]


def test_name_budget():
    over = [
        (e["sub"], e.get("idx"), e["english"], len(e["english"]))
        for e in _names() if len(e["english"]) > MAX_CELLS
    ]
    assert not over, (
        "%d R34 item name(s) exceed the %d-cell inventory slot budget -- they "
        "overdraw the stat panel / shop quantity column (no clipping). Shorten "
        "them (see the v190 rename wave): %s" % (len(over), MAX_CELLS, over[:8])
    )


def test_name_ascii():
    bad = [(e["sub"], e["english"]) for e in _names() if not e["english"].isascii()]
    assert not bad, (
        "non-ASCII R34 item name(s) will mis-render in the monospace slot: %s"
        % bad[:8]
    )


TESTS = [test_name_budget, test_name_ascii]

if __name__ == "__main__":
    main_exit(TESTS, "test_r34_name_budget")
