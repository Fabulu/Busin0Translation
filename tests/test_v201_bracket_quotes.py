#!/usr/bin/env python3
"""
test_v201_bracket_quotes.py -- regression gate for the v201 bracket normalization.

Statically PROVEN (matched save-state RAM @0x01854680 + issue-44 screenshot): the
ASCII '['/']' in these md_import interjection lines encode to glyph ids 59/61 =
0x3B/0x3D, which the dialogue font draws as Japanese white corner-quotes 『 』 --
faithful to the JP but Japanese-style punctuation around English text. Owner chose
to normalize these 11 lines to English double quotes to match the 8 sibling
shouted-interjection lines. Size-neutral (1 glyph word <-> 1 glyph word); the m634
"Jill" nameplate is a separate 0x14 label island and is untouched.
"""
import os
import glob
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TYPE2_DIR = os.path.join(ROOT, "data", "type2_translated")

KEYS = [(1196, 857), (1196, 507), (1202, 251), (1203, 393), (1203, 398),
        (1203, 406), (1203, 634), (1203, 658), (1203, 809), (1203, 881),
        (1203, 1197)]


def _merge():
    excl = {"batch_r39_equip_a.json", "batch_r39_equip_b.json"}
    out = {}
    for fn in sorted(glob.glob(os.path.join(TYPE2_DIR, "batch_*.json"))):
        if os.path.basename(fn) in excl:
            continue
        for e in json.load(open(fn, encoding="utf-8")):
            r, mi = e.get("resource"), e.get("msg_index")
            if r is not None and mi is not None:
                out[(r, mi)] = e.get("english", "")
    return out


MERGED = _merge()


def test_interjections_use_quotes_not_brackets():
    for r, mi in KEYS:
        en = MERGED.get((r, mi))
        assert en is not None, "v201: (R%d, m%d) missing" % (r, mi)
        assert "[" not in en and "]" not in en, (
            "R%d m%d still has a corner-quote bracket: %r" % (r, mi, en))
        assert en.startswith('"') and en.endswith('"'), (
            "R%d m%d should be wrapped in English quotes: %r" % (r, mi, en))


TESTS = [test_interjections_use_quotes_not_brackets]

if __name__ == "__main__":
    for fn in TESTS:
        fn()
        print("PASS", fn.__name__)
    print("OK")
