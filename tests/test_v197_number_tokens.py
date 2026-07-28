#!/usr/bin/env python3
"""
test_v197_number_tokens.py -- data-level regression gates for the v197 fix of
GitHub issue #44 (the "0123456789" leak + missing runtime numbers).

Mechanism (proven statically AND runtime-confirmed from the reporter's RAM:
gp=0x504FF0, var[0x1AC]=3360 church gold, the live {off,cnt=11,p2=0x1AC}
record landing byte-exactly on the "0123456789-" digit run): the leading
"0123456789-" in these messages is a per-message DIGIT-GLYPH TABLE the engine
reads to print numbers; it must NOT be present as literal display text in the
english (the engine keeps the preserved pristine table; the display offset
skips past it). Restored numbers ride on authored [FE01]/[FE02] control tokens
(passed through by build_v9.py's CTRL_TOKEN_RE) or on a preserved leading FE01.

These gates pin the DATA layer (Layer 1 strips + Layer 3 token authoring). The
Section-1 island remaps (Layer 2) are pinned by test_section1_integrity /
test_build_outputs_regression_gate / test_line_width against the built ISO.

Anchored on the RESOLVED type-2 merge map (sorted-glob last-file-wins).
"""
import os
import re
import glob
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TYPE2_DIR = os.path.join(ROOT, "data", "type2_translated")

# Literal leading digit-template the fix strips (any of these leading forms).
_LEAK_RE = re.compile(r'^\s*0*123456789')


def _resolve_merge():
    excl = {"batch_r39_equip_a.json", "batch_r39_equip_b.json"}
    out = {}
    for fn in sorted(glob.glob(os.path.join(TYPE2_DIR, "batch_*.json"))):
        if os.path.basename(fn) in excl:
            continue
        for e in json.load(open(fn, encoding="utf-8")):
            r = e.get("resource")
            mi = e.get("msg_index")
            eng = e.get("english", "")
            if r is None or mi is None:
                continue
            out[(r, mi)] = eng
    return out


MERGED = _resolve_merge()


def _eng(r, mi):
    assert (r, mi) in MERGED, "v197: (R%d, m%d) missing from merged map" % (r, mi)
    return MERGED[(r, mi)]


# The 84 template-carrying keys that were stripped (from the fix inventory).
STRIPPED_KEYS = [
    (1200, 105), (1200, 165), (1200, 227), (1200, 240), (1201, 128),
    (1203, 52), (1203, 65), (1203, 198), (1203, 233),
    (1203, 341), (1203, 346), (1203, 351), (1203, 356), (1203, 361), (1203, 366),
    (1204, 410), (1204, 423), (1204, 556), (1204, 832), (1204, 837),
    (1205, 406), (1205, 419), (1205, 552), (1205, 587),
    (1206, 318), (1207, 348), (1207, 361), (1207, 494), (1207, 529),
    (1208, 209), (1208, 222), (1208, 390), (1209, 220), (1209, 233), (1209, 401),
    (1210, 259), (1210, 272), (1210, 405), (1211, 104), (1211, 117), (1211, 250),
    (1211, 356), (1211, 395), (1348, 1),
]


def test_no_leading_digit_template_leak():
    """No live english string still leads with the literal digit template."""
    hits = []
    for (r, mi), eng in MERGED.items():
        first_seg = eng.split(" / ")[0].split(" // ")[0]
        if _LEAK_RE.match(first_seg):
            hits.append((r, mi, eng[:40]))
    assert not hits, "v197: %d string(s) still leak the digit template: %s" % (
        len(hits), hits[:8])


def test_stripped_keys_present_and_clean():
    """Each known template key still exists and no longer leads with the leak."""
    for r, mi in STRIPPED_KEYS:
        eng = _eng(r, mi)
        first = eng.split(" / ")[0].split(" // ")[0]
        assert not _LEAK_RE.match(first), (
            "v197: (R%d, m%d) still leaks: %r" % (r, mi, eng[:40]))


def test_donation_gold_token():
    # R1200 m165: "...donated [FE01]G to..." -- the FE01 prints the gold amount.
    assert "[FE01]G" in _eng(1200, 165), "R1200 m165 lost its [FE01]G gold token"


def test_member_number_tokens():
    # Member-card lines carry [FE01][FE02] where the member number prints.
    for r, mi in [(1203, 52), (1203, 65), (1207, 348)]:
        assert "[FE01][FE02]" in _eng(r, mi), (
            "R%d m%d lost its [FE01][FE02] member-number token" % (r, mi))


def test_gold_rewords():
    assert _eng(1200, 228).startswith("G obtained"), "R1200 m228 gold reword lost"
    assert _eng(1201, 130).startswith("G returned"), "R1201 m130 gold reword lost"
    assert "[g]" not in _eng(1201, 130), "R1201 m130 still has literal [g]"


TESTS = [
    test_no_leading_digit_template_leak,
    test_stripped_keys_present_and_clean,
    test_donation_gold_token,
    test_member_number_tokens,
    test_gold_rewords,
]

if __name__ == "__main__":
    for fn in TESTS:
        fn()
        print("PASS", fn.__name__)
    print("OK")
