#!/usr/bin/env python3
"""
test_library_no_copied_text.py -- no two library (R2654) entries with
DIFFERENT Japanese may carry the SAME long English text.

RUN-20261109-1725 (v205), player report "Weak Smash description in the
Library shows an excerpt from Oda's book": since the v163 library wave,
chunk_r2654_library_fix.json msg 39 (AA description 'Weak Smash') held a
verbatim copy of msg 122 (Oda's diary page). A copy/paste slip like that
passes every width and token gate, so this pins the class directly.
TIER-1: pure data check.
"""

import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, main_exit

LIB = os.path.join(ROOT, "data", "translate_chunks", "chunk_r2654_library_fix.json")
MIN_LEN = 40        # short stock phrases may legitimately repeat


def _norm_jp(s):
    return "".join((s or "").split()).replace("/", "")


def test_no_english_copied_across_library_entries():
    entries = json.load(open(LIB, encoding="utf-8"))
    by_en = collections.defaultdict(list)
    for e in entries:
        en = (e.get("english") or "").strip()
        if len(en) >= MIN_LEN:
            by_en[en].append(e)
    bad = []
    for en, group in by_en.items():
        if len({_norm_jp(e.get("japanese")) for e in group}) > 1:
            bad.append("msgs %s share '%s...'" % (
                sorted(e["message"] for e in group), en[:50]))
    assert not bad, "; ".join(bad)


def test_weak_smash_description():
    e = [x for x in json.load(open(LIB, encoding="utf-8")) if x["message"] == 39][0]
    assert "Hold Attack" in e["english"] and "Oda" not in e["english"], e["english"]


TESTS = [test_no_english_copied_across_library_entries, test_weak_smash_description]

if __name__ == "__main__":
    main_exit(TESTS, "test_library_no_copied_text")
