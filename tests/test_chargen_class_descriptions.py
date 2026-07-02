#!/usr/bin/env python3
"""
test_chargen_class_descriptions.py -- FIX-D data-presence gate: the chargen
Class&Parameter bottom-textbox description strings exist and are translated.

FIX-D investigated the EMPTY bottom textbox on the Class&Parameter stat-allocation
screen (textboxweirdness.png) and confirmed it is ORIGINAL-GAME behaviour, NOT a
render bug: that box is contextual to the highlighted item and is correctly blank
on the non-describable Bonus-Point pool, while it DOES render a description when
the cursor sits on a class row (class-select) or a stat row (stat-allocation).

So FIX-D shipped NO code change -- its correctness rests entirely on the claim
that the description DATA exists and is fully English.  This module locks that
data in so a future translation edit cannot silently empty the bottom textbox and
re-create the "missing description" appearance for real:

  * R38 messages 126-141 = the 16 class descriptions (e.g. msg 126 "Combat
    expert. / Cannot learn any / magic spells.").
  * R38 messages 142-147 = the 6 stat descriptions (weapon damage, Sorcery,
    Holy Magic, max-HP/revival, turn order, breath/crit).

Every one must be PRESENT and non-empty English in the committed translation
chunks (chunk_02 / chunk_03).  Pure data assertion -- no EXE, no build artifact;
SKIPs only if the chunk files are absent.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, main_exit, require_file  # noqa: E402

CHUNKS = [
    os.path.join(ROOT, "data", "translate_chunks", "chunk_02_translated.json"),
    os.path.join(ROOT, "data", "translate_chunks", "chunk_03_translated.json"),
]
R38 = 38
CLASS_DESC_IDS = range(126, 142)   # 16 class descriptions
STAT_DESC_IDS = range(142, 148)    # 6 stat descriptions


def _r38_english():
    """Map {message_id: english} for resource 38 across the committed chunks."""
    for c in CHUNKS:
        require_file(c, "FIX-D class/stat description data")
    by = {}
    for c in CHUNKS:
        for it in json.load(open(c, encoding="utf-8")):
            if it.get("resource") == R38:
                by[it["message"]] = it.get("english", "")
    return by


def _check(ids, label):
    by = _r38_english()
    missing = [m for m in ids if m not in by]
    empty = [m for m in ids if m in by and not by[m].strip()]
    assert not missing, (
        "R38 %s description message(s) %s are MISSING from the translation chunks -- "
        "the chargen bottom textbox would render blank for those (FIX-D's non-bug "
        "claim relies on this data existing)" % (label, missing)
    )
    assert not empty, (
        "R38 %s description message(s) %s are present but EMPTY -- the chargen "
        "bottom textbox would show nothing, re-creating the textboxweirdness 'empty "
        "box' appearance for real" % (label, empty)
    )


def test_class_descriptions_present_and_english():
    """R38 msgs 126-141 (the 16 class descriptions shown in the Class&Parameter
    bottom textbox) exist and are non-empty English."""
    _check(CLASS_DESC_IDS, "class")


def test_stat_descriptions_present_and_english():
    """R38 msgs 142-147 (the 6 stat descriptions shown when the cursor is on a stat
    row during allocation) exist and are non-empty English."""
    _check(STAT_DESC_IDS, "stat")


TESTS = [
    test_class_descriptions_present_and_english,
    test_stat_descriptions_present_and_english,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_chargen_class_descriptions")
