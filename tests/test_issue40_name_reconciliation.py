#!/usr/bin/env python3
"""
test_issue40_name_reconciliation.py -- TIER-1 data-level regression gates for
the issue-#40 fix wave (item-name reconciliation + two small dialogue/trap
fixes), all fixed in translation JSON (no build/EXE changes). Anchored by
(resource, msg_index/message) or (sub, idx) rather than full-string match so
unrelated rewording doesn't false-positive the gate.

Issue map:
  Name reconciliation -- three R34 consumable items had drifted names that no
  longer matched the shop-list / pickup-message copy quoting them, and a
  Seraph shop-list line still spelled out the OLD long names:
    - R34 sub6/idx1  (msg703) Wound Salve  -> Medicine
    - R34 sub6/idx4  (msg706) Detox Potion -> Antidote
    - R34 sub6/idx7  (msg709) Vigor Potion -> Tonic
    - Seraph shop menu (batch_03 R1203 msg452/453/455/461/468/477) updated to
      match: "Healing Potion"/"Rest Potion" -> "Medicine"/"Tonic".
    - girl's stall (batch_zzz_rewardnames R1196 msg41) + pouches (batch_02
      R1199 msg230, batch_zzz_rewardnames R1199 msg231) updated the same way,
      plus "Town Return Potion" -> "Return Potion" for consistency.
  "? Sword" -- R34 sub19/idx3 (msg1152) was mis-named "? Shuriken" (a
  duplicate of the real Shuriken weapon); renamed to "? Sword". Mirrored in
  R39 (batch_r39_equip_b msg585, injected directly by inject_r39_quest.py --
  NOT part of the type-2 pipeline). The REAL Shuriken weapon (R34 sub4/idx93,
  sub16/idx10) must be untouched.
  "No one able" -- chunk_03_translated R39 msg28 read "No one heal" (garbled
  fragment); fixed to "No one able" (to act).
  Trap two-line render -- chunk_r37_r48_r49_translated R49 msg38 ("Trap is
  set.") is displayed directly after a trap-name string that itself ends in
  " / " (e.g. "Crossbow / "); msg38 previously had no leading break, so the
  trap name and "Trap is set." ran together on one line ("CrossbowTrap is
  set."). A leading " / " was added so the trap name and message always
  render as two separate lines.
  Seraph shop menu labels -- batch_03 R1203 msg448's trailing three
  " / "-separated segments were "Read / Stop" (only two, mismatched to the
  three-option menu); fixed to the three real options "Buy / Help / Exit".

TIER-1: all source files are plain data checked into the repo (not build- or
ISO-gated), so these gates always run.
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import DATA_DIR, ROOT, main_exit, require_file

TYPE2_DIR = os.path.join(DATA_DIR, "type2_translated")
CHUNK_DIR = os.path.join(DATA_DIR, "translate_chunks")

R34 = os.path.join(DATA_DIR, "r34_english_aligned.json")
BATCH_02 = os.path.join(TYPE2_DIR, "batch_02.json")
BATCH_03 = os.path.join(TYPE2_DIR, "batch_03.json")
BATCH_ZZZ_REWARDNAMES = os.path.join(TYPE2_DIR, "batch_zzz_rewardnames.json")
BATCH_R39_EQUIP_B = os.path.join(TYPE2_DIR, "batch_r39_equip_b.json")
CHUNK_03 = os.path.join(CHUNK_DIR, "chunk_03_translated.json")
CHUNK_R37_R48_R49 = os.path.join(CHUNK_DIR, "chunk_r37_r48_r49_translated.json")
BUILD_FULL_V2 = os.path.join(ROOT, "build", "build_full_english_v2.py")

# Old names that must be GONE everywhere they were reconciled.
OLD_POTION_NAMES = (
    "Detox Potion",
    "Vigor Potion",
    "Wound Salve",
    "Healing Potion",
    "Rest Potion",
)


# ===========================================================================
# Generic helpers (same conventions as test_v192_spell_quest_fixes.py)
# ===========================================================================
def _load_list(path):
    require_file(path, "issue-40 fix wave data")
    return json.load(open(path, encoding="utf-8"))


def _find(entries, resource, idx):
    """Find a type-2-style entry by (resource, msg_index|message). Hard-fails
    (not Skip) when absent -- an anchor going missing is itself a regression
    signal (the entry got dropped/renumbered), not an absent tier."""
    for e in entries:
        if e.get("resource") != resource:
            continue
        mi = e.get("msg_index", e.get("message"))
        if mi == idx:
            return e
    raise AssertionError(
        "anchor (resource=%s, msg_index=%s) not found in data -- entry "
        "renumbered or dropped" % (resource, idx)
    )


def _eng(entries, resource, idx):
    return _find(entries, resource, idx)["english"]


def _r34_entries():
    require_file(R34, "R34 aligned item DB")
    return json.load(open(R34, encoding="utf-8"))["entries"]


def _r34_eng(sub, idx):
    for e in _r34_entries():
        if e.get("sub") == sub and e.get("idx") == idx:
            return e["english"]
    raise AssertionError("R34 anchor (sub=%d, idx=%d) not found" % (sub, idx))


def _live_type2_files():
    # batch_r39_equip_a/_b carry R39 (type-15) entries: the type-2 loader globs
    # them but the type_code==2 filter drops every entry, so nothing here ships
    # via the type-2 path (_b is injected directly by inject_r39_quest.py;
    # _a is a dead source superseded by r39_quest_text_aligned.json). Exclude
    # them so this sweep matches what actually ships as type-2 dialogue --
    # batch_r39_equip_b is checked separately (test_r39_equip_b_sword_mirror).
    _excl = {"batch_r39_equip_a.json", "batch_r39_equip_b.json"}
    return sorted(
        f for f in glob.glob(os.path.join(TYPE2_DIR, "batch_*.json"))
        if os.path.basename(f) not in _excl
    )


def _live_chunk_files():
    """The exact translate_chunks/ inputs build_full_english_v2.py loads:
    chunk_00..09 + its hardcoded fix_files list. Extracted via AST from the
    pipeline source itself so this test can't drift from what actually ships
    (rather than re-hardcoding a second copy of the list here)."""
    import ast

    require_file(BUILD_FULL_V2, "v2 build pipeline")
    src = open(BUILD_FULL_V2, encoding="utf-8").read()
    tree = ast.parse(src)
    fix_files = None
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "fix_files"
        ):
            fix_files = ast.literal_eval(node.value)
            break
    assert fix_files is not None, (
        "could not locate 'fix_files = [...]' in build_full_english_v2.py "
        "-- pipeline input list changed shape, update this test"
    )
    names = ["chunk_%02d_translated.json" % i for i in range(10)] + list(fix_files)
    return [os.path.join(CHUNK_DIR, n) for n in names if os.path.isfile(os.path.join(CHUNK_DIR, n))]


def _resolve_type2_merge():
    """Replicate build_v9.py's type-2 merge exactly enough to know what a
    given (resource, msg_index) FINALLY resolves to: sorted(glob(...)) order,
    dict[r][mi] = english, later files win. Mirrors build_v9.py lines ~635-656
    (minus the [DATA]/non-ASCII filters, irrelevant to plain-English anchors)."""
    out = {}
    for fn in _live_type2_files():
        entries = json.load(open(fn, encoding="utf-8"))
        for e in entries:
            r = e.get("resource")
            mi = e.get("msg_index")
            eng = e.get("english", "")
            if r is None or mi is None or not eng:
                continue
            out[(r, mi)] = eng
    return out


# ===========================================================================
# R34 item-name reconciliation
# ===========================================================================
def test_r34_potion_names_reconciled():
    cases = [
        (6, 1, "Medicine", "Wound Salve"),
        (6, 4, "Antidote", "Detox Potion"),
        (6, 7, "Tonic", "Vigor Potion"),
    ]
    for sub, idx, expected, old in cases:
        eng = _r34_eng(sub, idx)
        assert eng == expected, (
            "issue #40 regression: R34 sub=%d idx=%d = %r, expected %r"
            % (sub, idx, eng, expected)
        )
        assert eng != old, (
            "issue #40 regression: R34 sub=%d idx=%d reverted to old name %r"
            % (sub, idx, old)
        )
        assert len(eng) <= 13, (
            "issue #40 regression: R34 sub=%d idx=%d renamed to %r (%d cells) "
            "-- exceeds the 13-cell inventory slot budget" % (sub, idx, eng, len(eng))
        )


def test_r34_sword_not_shuriken_mixup():
    eng = _r34_eng(19, 3)
    assert eng == "? Sword", (
        "issue #40 regression: R34 sub19/idx3 (msg1152) = %r, expected "
        "'? Sword'" % eng
    )
    # The REAL Shuriken weapon entries must be untouched by the rename.
    real1 = _r34_eng(4, 93)
    assert real1 == "Shuriken", (
        "issue #40 regression: R34 sub4/idx93 (real Shuriken weapon) = %r, "
        "expected 'Shuriken' -- must not be collateral damage from the "
        "'? Shuriken' -> '? Sword' rename" % real1
    )
    real2 = _r34_eng(16, 10)
    assert real2 == "Shuriken", (
        "issue #40 regression: R34 sub16/idx10 (real Shuriken weapon) = %r, "
        "expected 'Shuriken' -- must not be collateral damage from the "
        "'? Shuriken' -> '? Sword' rename" % real2
    )


def test_r39_equip_b_sword_mirror():
    entries = _load_list(BATCH_R39_EQUIP_B)
    eng = _eng(entries, 39, 585)
    assert eng == "? Sword", (
        "issue #40 regression: batch_r39_equip_b R39 msg585 (mirrors R34 "
        "sub19/idx3) = %r, expected '? Sword'" % eng
    )


# ===========================================================================
# Seraph shop menu -- Buy / Help / Exit labels (msg448)
# ===========================================================================
def test_seraph_shop_menu_buy_help_exit():
    entries = _load_list(BATCH_03)
    eng = _eng(entries, 1203, 448)
    segs = [s.strip() for s in eng.split(" / ")]
    last3 = segs[-3:]
    assert last3 == ["Buy", "Help", "Exit"], (
        "issue #40 regression: batch_03 R1203 msg448 last 3 segments = %r, "
        "expected ['Buy', 'Help', 'Exit'] -- %r" % (last3, eng)
    )


# ===========================================================================
# Seraph shop-list + Obtained/Purchased messages -- Medicine / Tonic
# ===========================================================================
def test_seraph_shop_list_reconciled_names():
    entries = _load_list(BATCH_03)
    for idx in (452, 453):
        eng = _eng(entries, 1203, idx)
        assert "Medicine" in eng, (
            "issue #40 regression: batch_03 R1203 msg%d lost 'Medicine' -- %r"
            % (idx, eng)
        )
        assert "Tonic" in eng, (
            "issue #40 regression: batch_03 R1203 msg%d lost 'Tonic' -- %r"
            % (idx, eng)
        )
        for old in ("Healing Potion", "Rest Potion"):
            assert old not in eng, (
                "issue #40 regression: batch_03 R1203 msg%d still says %r "
                "-- %r" % (idx, old, eng)
            )

    checks = [
        (455, "Medicine", "Healing Potion"),
        (461, "Tonic", "Rest Potion"),
        (468, "Medicine", "Healing Potion"),
        (477, "Tonic", "Rest Potion"),
    ]
    for idx, new, old in checks:
        eng = _eng(entries, 1203, idx)
        assert new in eng, (
            "issue #40 regression: batch_03 R1203 msg%d lost %r -- %r"
            % (idx, new, eng)
        )
        assert old not in eng, (
            "issue #40 regression: batch_03 R1203 msg%d still says %r -- %r"
            % (idx, old, eng)
        )


# ===========================================================================
# Girl's stall + pouch item names
# ===========================================================================
def test_girls_stall_and_pouch_names():
    entries = _load_list(BATCH_ZZZ_REWARDNAMES)

    eng41 = _eng(entries, 1196, 41)
    assert "Medicine" in eng41, (
        "issue #40 regression: batch_zzz_rewardnames R1196 msg41 lost "
        "'Medicine' -- %r" % eng41
    )
    for old in OLD_POTION_NAMES:
        assert old not in eng41, (
            "issue #40 regression: batch_zzz_rewardnames R1196 msg41 still "
            "says %r -- %r" % (old, eng41)
        )
    assert "Town Return Potion" not in eng41, (
        "issue #40 regression: batch_zzz_rewardnames R1196 msg41 still says "
        "'Town Return Potion' (should be 'Return Potion') -- %r" % eng41
    )

    eng231 = _eng(entries, 1199, 231)
    assert eng231 == "Inside was a / Return Potion.", (
        "issue #40 regression: batch_zzz_rewardnames R1199 msg231 = %r, "
        "expected 'Inside was a / Return Potion.'" % eng231
    )

    e02 = _load_list(BATCH_02)
    eng230 = _eng(e02, 1199, 230)
    assert "Antidote" in eng230, (
        "issue #40 regression: batch_02 R1199 msg230 lost 'Antidote' -- %r"
        % eng230
    )
    assert "antidote herb" not in eng230, (
        "issue #40 regression: batch_02 R1199 msg230 still says "
        "'antidote herb' -- %r" % eng230
    )


def test_type2_merge_resolved_potion_names():
    """Systemic check on the ACTUAL merged (resource, msg_index) -> english
    map, replicating build_v9.py's sorted-glob/last-file-wins semantics --
    catches a future batch file silently re-shadowing these fixes even if the
    individual source files above stay correct."""
    merged = _resolve_type2_merge()

    def _get(resource, mi):
        key = (resource, mi)
        assert key in merged, (
            "issue #40 regression: (resource=%d, msg_index=%d) missing from "
            "the merged type-2 map entirely" % (resource, mi)
        )
        return merged[key]

    assert "Medicine" in _get(1196, 41), (
        "issue #40 regression: merged R1196 msg41 lost 'Medicine' -- %r"
        % _get(1196, 41)
    )
    assert _get(1199, 231) == "Inside was a / Return Potion.", (
        "issue #40 regression: merged R1199 msg231 = %r, expected 'Inside "
        "was a / Return Potion.'" % _get(1199, 231)
    )
    assert "Antidote" in _get(1199, 230), (
        "issue #40 regression: merged R1199 msg230 lost 'Antidote' -- %r"
        % _get(1199, 230)
    )
    for idx in (452, 453, 455, 461, 468, 477):
        eng = _get(1203, idx)
        for old in ("Healing Potion", "Rest Potion"):
            assert old not in eng, (
                "issue #40 regression: merged R1203 msg%d still says %r "
                "-- %r" % (idx, old, eng)
            )


# ===========================================================================
# Systemic sweep: no stale old-potion-name anywhere in live-loaded data
# ===========================================================================
def test_no_stale_potion_names_in_live_pipeline_data():
    """Systemic gate: sweep every file the v2 build pipeline actually loads
    (type2 batches auto-discovered by glob, minus the dead R39-equip
    batches, + the exact chunk/fix-file list build_full_english_v2.py reads)
    plus the R34 item DB, for any leftover OLD potion/medicine name. Catches
    recurrences beyond the specific lines fixed above. Deliberately excludes
    data/translate_chunks/chunk_md_import.json (a raw import artifact not
    loaded by the live pipeline -- see test_v192_spell_quest_fixes.py for the
    same exclusion rationale) and batch_r39_equip_b.json (checked directly,
    since its content ships via inject_r39_quest.py, not the type-2 merge)."""
    hits = []
    for path in _live_type2_files() + _live_chunk_files():
        entries = json.load(open(path, encoding="utf-8"))
        if not isinstance(entries, list):
            continue
        for e in entries:
            eng = e.get("english")
            if not isinstance(eng, str):
                continue
            for old in OLD_POTION_NAMES:
                if old in eng:
                    hits.append((os.path.basename(path), e.get("resource"),
                                 e.get("msg_index", e.get("message")), old, eng))

    for e in _r34_entries():
        eng = e.get("english")
        if not isinstance(eng, str):
            continue
        for old in OLD_POTION_NAMES:
            if old in eng:
                hits.append(("r34_english_aligned.json", e.get("sub"),
                             e.get("idx"), old, eng))

    assert not hits, (
        "issue #40 regression: %d live entr(y/ies) still carry an OLD "
        "potion/medicine name: %s" % (len(hits), hits[:8])
    )


# ===========================================================================
# "No one able" (R39 msg28)
# ===========================================================================
def test_r39_no_one_able():
    entries = _load_list(CHUNK_03)
    eng = _eng(entries, 39, 28)
    assert eng == "No one able", (
        "issue #40 regression: chunk_03 R39 msg28 = %r, expected "
        "'No one able'" % eng
    )
    assert eng != "No one heal", (
        "issue #40 regression: chunk_03 R39 msg28 reverted to 'No one heal'"
    )


# ===========================================================================
# Trap two-line render (R49 msg38 leading line-break)
# ===========================================================================
def test_r49_trap_leading_linebreak():
    entries = _load_list(CHUNK_R37_R48_R49)
    eng = _eng(entries, 49, 38)
    assert eng.startswith(" / "), (
        "issue #40 regression: chunk_r37_r48_r49 R49 msg38 = %r, expected a "
        "leading ' / ' line-break so the preceding trap name and 'Trap is "
        "set.' render on separate lines (previously ran together, e.g. "
        "'CrossbowTrap is set.')" % eng
    )
    assert "Trap is set." in eng, (
        "issue #40 regression: chunk_r37_r48_r49 R49 msg38 lost 'Trap is "
        "set.' -- %r" % eng
    )


TESTS = [
    test_r34_potion_names_reconciled,
    test_r34_sword_not_shuriken_mixup,
    test_r39_equip_b_sword_mirror,
    test_seraph_shop_menu_buy_help_exit,
    test_seraph_shop_list_reconciled_names,
    test_girls_stall_and_pouch_names,
    test_type2_merge_resolved_potion_names,
    test_no_stale_potion_names_in_live_pipeline_data,
    test_r39_no_one_able,
    test_r49_trap_leading_linebreak,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_issue40_name_reconciliation")
