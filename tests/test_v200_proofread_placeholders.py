#!/usr/bin/env python3
"""
test_v200_proofread_placeholders.py -- data-level regression gates for the v200
wave: the "Id Bracelet" name unification, four engine-value placeholder
restorations, and three small text corrections.

- Bracelet: JP 識別ブレスレット was rendered six ways (Identification / Identify /
  Appraisal / ID / Id Bracelet). Owner chose "Id Bracelet"; every live dialogue
  occurrence normalized to it (singular "Id Bracelet" / plural "Id Bracelets").
- Placeholders (literal text where the engine inserts a value -> restored the
  pristine control token, verified present in the built groups):
    R1200 m108 [g] -> [FE02]G (gold slot 2); R1200 m198/m207 [name] -> [FFF0]
    (party-name insert); R1202 m152 [class] -> [FE09] (class insert).
- Text: R1196 m800 Valley->Vallee; R1207 m911 "Can not"->"Cannot";
  R34 sub12 idx17 "Magic Stone"->"Old Magestone".

Anchored on the RESOLVED type-2 merge map (sorted-glob last-file-wins).
"""
import os
import re
import glob
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TYPE2_DIR = os.path.join(ROOT, "data", "type2_translated")
R34 = os.path.join(ROOT, "data", "r34_english_aligned.json")


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


def _eng(r, mi):
    assert (r, mi) in MERGED, "v200: (R%d, m%d) missing" % (r, mi)
    return MERGED[(r, mi)]


_BAD_BRACELET = re.compile(
    r'\b(identification|identify|appraisal|ID)\b\s*(?:/\s*)?bracelet', re.I)


def test_bracelet_unified_id_bracelet():
    """No live dialogue keeps a non-'Id Bracelet' spelling of 識別ブレスレット."""
    hits = []
    for (r, mi), en in MERGED.items():
        for m in _BAD_BRACELET.finditer(en):
            # allow the canonical "Id Bracelet"/"Id Bracelets" exactly
            if m.group(0).replace(" / ", " ") not in ("Id Bracelet", "Id Bracelets"):
                hits.append((r, mi, m.group(0)))
    assert not hits, "v200: %d non-'Id Bracelet' variants remain: %s" % (
        len(hits), hits[:8])


def test_placeholder_tokens_restored():
    assert "[FE02]G" in _eng(1200, 108), "R1200 m108 lost [FE02]G gold token"
    assert "[FFF0]" in _eng(1200, 198), "R1200 m198 lost [FFF0] name token"
    assert "[FFF0]" in _eng(1200, 207), "R1200 m207 lost [FFF0] name token"
    assert "[FE09]" in _eng(1202, 152), "R1202 m152 lost [FE09] class token"
    # and no literal placeholders survive
    for r, mi, lit in [(1200, 108, "[g]"), (1200, 198, "[name]"),
                       (1200, 207, "[name]"), (1202, 152, "[class]")]:
        assert lit not in _eng(r, mi), "R%d m%d still has literal %s" % (r, mi, lit)


def test_text_corrections():
    assert "Vallee" in _eng(1196, 800) and "Valley" not in _eng(1196, 800)
    assert _eng(1207, 911).startswith("Cannot") and "Can not" not in _eng(1207, 911)


def test_r34_old_magestone():
    d = json.load(open(R34, encoding="utf-8"))
    hit = [e for e in d["entries"] if e.get("sub") == 12 and e.get("idx") == 17]
    assert hit and hit[0].get("english") == "Old Magestone", (
        "R34 sub12 idx17 should be 'Old Magestone'")
    assert len("Old Magestone") <= 13, "Old Magestone exceeds 13-cell budget"


TESTS = [
    test_bracelet_unified_id_bracelet,
    test_placeholder_tokens_restored,
    test_text_corrections,
    test_r34_old_magestone,
]

if __name__ == "__main__":
    for fn in TESTS:
        fn()
        print("PASS", fn.__name__)
    print("OK")
