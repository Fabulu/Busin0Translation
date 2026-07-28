#!/usr/bin/env python3
"""
test_v196_reward_ritual_rcveq.py -- TIER-1 data-level regression gates for
the v196 wave (GitHub issues #42/#43/#44b):

  #42 reward-name divergence (glyph-page mis-decode landing in reward menus):
      the v187 rewardnames batch read R1206's garbled glyph page literally as
      "Ogre Armor" ([044F]棒の間鎧); R34 canon (sub4 idx16 "Spirit Sword" =
      言臆の何祠, same _ _ の _ _ sword structure) + the reporter confirm the
      real item is a Spirit Sword. Fixed in BOTH the "Which will you take?"
      choice (R1206/860) and the "Got it!" received line (R1206/867).
      R1203/R1199/R1196 were verified already-correct and deliberately NOT
      touched.

  #44b ritual options (R1200/169): the resurrection-rite choice was scrambled
      ("Lay/Sit/Lean on the bed", wrong subject). JP order + outcome narration
      (m170 sit->topples, m172 lay->gently, m173 under->on the floor) fix it to
      "Sit leader on the bed / Lay leader on the bed / Put leader under the bed".

  #43 Vigger guild-order label: R39 inline record 466 (回復装備品) is a
      fixed-slot 5-char cap; "RcvEq" relabelled to the more readable "Recov".

Anchored against the RESOLVED type-2 merge map (sorted-glob last-file-wins,
mirroring build_v9.py) so a stale earlier-file entry shadowed by a later file
is still caught. R39 label checked by parsing patch_r39_inline.py's REPLACEMENTS.
"""
import os
import re
import glob
import json
import ast

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TYPE2_DIR = os.path.join(ROOT, "data", "type2_translated")
R39_INLINE = os.path.join(ROOT, "tools", "patch_r39_inline.py")


def _norm(s):
    """Collapse the ' / ' line-break marker so word-wrapped names match."""
    return " ".join(s.replace(" / ", " ").split())


def _live_type2_files():
    excl = {"batch_r39_equip_a.json", "batch_r39_equip_b.json"}
    return sorted(
        f for f in glob.glob(os.path.join(TYPE2_DIR, "batch_*.json"))
        if os.path.basename(f) not in excl
    )


def _resolve_merge():
    out = {}
    for fn in _live_type2_files():
        for e in json.load(open(fn, encoding="utf-8")):
            r = e.get("resource")
            mi = e.get("msg_index")
            eng = e.get("english", "")
            if r is None or mi is None or not eng:
                continue
            out[(r, mi)] = eng
    return out


def _resolved(merged, r, mi):
    assert (r, mi) in merged, (
        "v196 regression: (resource=%d, msg_index=%d) missing from merged "
        "type-2 map -- entry renumbered or dropped" % (r, mi)
    )
    return merged[(r, mi)]


MERGED = _resolve_merge()


# --- #42 reward name: Spirit Sword (not Ogre Armor) -----------------------
def test_issue42_r1206_choice_spirit_sword():
    eng = _norm(_resolved(MERGED, 1206, 860))
    assert "Spirit Sword" in eng, "R1206/860 choice must offer 'Spirit Sword'"
    assert "Ogre Armor" not in eng, "R1206/860 must not still say 'Ogre Armor'"


def test_issue42_r1206_received_spirit_sword():
    eng = _norm(_resolved(MERGED, 1206, 867))
    assert "Spirit Sword" in eng, "R1206/867 'Got it!' must say 'Spirit Sword'"
    assert "Ogre Armor" not in eng, "R1206/867 must not still say 'Ogre Armor'"


def test_issue42_r1203_reward_untouched_canon():
    # R1203 was already correct (matches R34 Magus set); guard against churn.
    eng = _norm(_resolved(MERGED, 1203, 958))
    assert "Magus Greatsword" in eng and "Zakreta Stone" in eng, (
        "R1203/958 canon reward set unexpectedly changed"
    )


# --- #44b ritual options --------------------------------------------------
def test_issue44b_ritual_options():
    eng = _norm(_resolved(MERGED, 1200, 169))
    for opt in ("Sit leader on the bed",
                "Lay leader on the bed",
                "Put leader under the bed"):
        assert opt in eng, "R1200/169 missing ritual option '%s'" % opt
    assert "Lean against" not in eng, "R1200/169 still has wrong 'Lean against'"


# --- #43 R39 RcvEq -> Recov ----------------------------------------------
def _r39_replacements():
    src = open(R39_INLINE, encoding="utf-8").read()
    tree = ast.parse(src)
    merged = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            try:
                d = ast.literal_eval(node)
            except (ValueError, SyntaxError):
                continue
            if all(isinstance(k, int) for k in d) and d:
                merged.update(d)
    return merged


def test_issue43_rcveq_relabelled_recov():
    reps = _r39_replacements()
    assert reps.get(466) == "Recov", (
        "R39 record 466 must be 'Recov' (#43), got %r" % reps.get(466)
    )
    assert len("Recov") <= 5, "record 466 exceeds the 5-slot fixed-slot cap"


TESTS = [
    test_issue42_r1206_choice_spirit_sword,
    test_issue42_r1206_received_spirit_sword,
    test_issue42_r1203_reward_untouched_canon,
    test_issue44b_ritual_options,
    test_issue43_rcveq_relabelled_recov,
]

if __name__ == "__main__":
    for fn in TESTS:
        fn()
        print("PASS", fn.__name__)
    print("OK")
