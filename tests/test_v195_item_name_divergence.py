#!/usr/bin/env python3
"""
test_v195_item_name_divergence.py -- TIER-1 data-level regression gates for
the v195 item-name-divergence sweep: 64 dialogue lines across
data/type2_translated/batch_*.json were corrected so item mentions in
pickup/reward/shop dialogue match the pre-existing R34/R39 canon menu names
(neither R34 nor R39 itself changed in this wave -- git status confirms only
type2_translated batch files moved). Anchored by (resource, msg_index)
against the RESOLVED merge map (mirrors build_v9.py's sorted-glob
last-file-wins semantics), not raw per-file loads, so a stale earlier-file
fix silently shadowed by a later file would still be caught.

Renames gated as FIXED (old name must be gone, new name present):
  - Samurai Soul       (R1201/148)                        was "Samurai Gem"
  - Silence Breaker x11 (R1203/272, R1204/630, R1205/626, R1206/538,
    R1208/429, R1210/479, R1211/331, R1212/381, R1353/380, R1351/10,
    R1207/568)                                             was "Break Silence"
  - Recovery Medicine  (R1203/244, R1204/215, R1205/598, R1208/401,
    R1210/451, R1211/296)             was "Dragon Potion"/"Stamina Scroll"/
                                       "Recovery Vial"/"Potion of Recovery"
  - Silver Hair Ornament (R1203/285, R1204/643, R1205/639, R1210/492,
    R1211/344)                        was "Crystal Hair Clip"/"Jade
                                       Accessory"/"Clay Ring"
  - Return Potion      (R1203/19, R1204/197)                was "Return Scroll"
  - Magic Wine (R1209/393), Member Card (R1208/211, R1209/222), Gin's Blade
    (R1196/829,842), Osafune (R1201/162,166), Bishop Cloak (R1200/227,240),
    Flame Mace (R1203/565), Orc Pants (R1203/1536), Repel Bell (R1203/1538),
    Stun Smash (R1205/270), Cross-Gauge Kill (R1210/495), Raiman Letter
    (R1197/245), Heal Potion (R1204/202,243), Dark Medal (R1203/318,1609).

Several of these renders wrap the new name across a " / " line-break inside
the item name itself (e.g. "Got Silence / Breaker!", "Obtained the / Silver
Hair / Ornament."). This codebase's own convention treats " / " as a
line-break marker (see test_issue40_name_reconciliation's Seraph shop test,
which splits on " / "), so anchor checks here normalize by collapsing
" / " to a single space before doing the substring match -- a literal
contiguous "eng contains 'Silver Hair Ornament'" check would false-negative
on correctly-fixed, merely word-wrapped text.

Deliberately NOT gated as fixed (reverted / held for owner decision in this
same wave -- asserting these as renamed would false-positive against the
actual shipped intent): "Recipe List" (was reverted FROM "Decision List"),
"Decor Charm" (reverted to "Decorative Talisman"), "Holy Talisman" at
R1203/623 (reverted to "King's Amulet"), Fiakea (R1197/698,699,706,718,
719,722 -- still "Fearkea" in data), Wagness Stone (R1199/246, R1205/30),
Purify Potion (R1204/208,249), Skedim Horn (R1204/957,958), Magic Shield
(R1208/782), Romi's Amulet (R1211/319).

TIER-1: all source files are plain data checked into the repo (not build- or
ISO-gated), so these gates always run.
"""
import ast
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import DATA_DIR, ROOT, main_exit, require_file

TYPE2_DIR = os.path.join(DATA_DIR, "type2_translated")
CHUNK_DIR = os.path.join(DATA_DIR, "translate_chunks")
BUILD_FULL_V2 = os.path.join(ROOT, "build", "build_full_english_v2.py")

# Old names that must be GONE from every live-loaded dialogue string. This is
# the exact predecessor list from the fix-wave report -- NOT the full set of
# every historical old name ever used for these items (e.g. "Potion of
# Recovery" is a documented predecessor of "Recovery Medicine" too, but is
# deliberately excluded here: it still lives on, untouched, at R1208/407 and
# R1208/414 -- outside this wave's 64-line scope -- and asserting it would
# false-positive against an unrelated pre-existing gap, not a regression of
# THIS wave's fixes. See test report / TASK_LOG for that open item.)
OLD_NAMES = (
    "Samurai Gem",
    "Break Silence",
    "Return Scroll",
    "Dragon Potion",
    "Crystal Hair Clip",
    "Jade Accessory",
)


# ===========================================================================
# Generic helpers (same conventions as test_issue40_name_reconciliation.py /
# test_v192_spell_quest_fixes.py)
# ===========================================================================
def _norm(s):
    """Collapse the " / " line-break marker to a single space so a renamed
    item that happens to word-wrap mid-name (e.g. "Silver Hair / Ornament")
    still substring-matches its canonical name."""
    return " ".join(s.replace(" / ", " ").split())


def _live_type2_files():
    # batch_r39_equip_a/_b carry R39 (type-15) entries the type-2 loader
    # globs but the type_code==2 filter drops -- excluded so this mirrors
    # what actually ships via the type-2 merge (same exclusion as
    # test_issue40_name_reconciliation._live_type2_files).
    excl = {"batch_r39_equip_a.json", "batch_r39_equip_b.json"}
    return sorted(
        f for f in glob.glob(os.path.join(TYPE2_DIR, "batch_*.json"))
        if os.path.basename(f) not in excl
    )


def _live_chunk_files():
    """The exact translate_chunks/ inputs build_full_english_v2.py loads:
    chunk_00..09 + its hardcoded fix_files list, extracted via AST from the
    pipeline source so this test can't drift from what actually ships."""
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
    return [
        os.path.join(CHUNK_DIR, n) for n in names
        if os.path.isfile(os.path.join(CHUNK_DIR, n))
    ]


def _resolve_type2_merge():
    """Replicate build_v9.py's type-2 merge: sorted(glob(...)) order,
    dict[(resource, msg_index)] = english, later files win. Mirrors
    build_v9.py lines ~635-656 (minus the [DATA]/non-ASCII filters,
    irrelevant to plain-English anchors). Anchoring against THIS resolved
    map (rather than a raw per-file load) is what makes these gates respect
    same-file merge order -- if two batch files both touch a given
    (resource, msg_index), the later-sorted file's content is what actually
    ships, and that's what must be checked."""
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


def _resolved(merged, resource, mi):
    key = (resource, mi)
    assert key in merged, (
        "v195 regression: (resource=%d, msg_index=%d) missing from the "
        "merged type-2 map entirely -- entry renumbered or dropped"
        % (resource, mi)
    )
    return merged[key]


def _assert_renamed(merged, resource, mi, new_name, old_names):
    eng = _resolved(merged, resource, mi)
    norm = _norm(eng)
    assert new_name in norm, (
        "v195 regression: R%d/%d = %r (normalized %r), expected to contain "
        "%r" % (resource, mi, eng, norm, new_name)
    )
    for old in old_names:
        assert old not in norm, (
            "v195 regression: R%d/%d = %r still contains old name %r"
            % (resource, mi, eng, old)
        )


# ===========================================================================
# Individual renamed-item anchors
# ===========================================================================
def test_samurai_soul_renamed():
    merged = _resolve_type2_merge()
    _assert_renamed(merged, 1201, 148, "Samurai Soul", ["Samurai Gem"])


def test_silence_breaker_renamed():
    merged = _resolve_type2_merge()
    anchors = [
        (1203, 272), (1204, 630), (1205, 626), (1206, 538), (1208, 429),
        (1210, 479), (1211, 331), (1212, 381), (1353, 380), (1351, 10),
        (1207, 568),
    ]
    for resource, mi in anchors:
        _assert_renamed(merged, resource, mi, "Silence Breaker", ["Break Silence"])


def test_recovery_medicine_renamed():
    merged = _resolve_type2_merge()
    anchors = [(1203, 244), (1204, 215), (1205, 598), (1208, 401), (1210, 451), (1211, 296)]
    old = ["Dragon Potion", "Stamina Scroll", "Recovery Vial", "Potion of Recovery"]
    for resource, mi in anchors:
        _assert_renamed(merged, resource, mi, "Recovery Medicine", old)


def test_silver_hair_ornament_renamed():
    merged = _resolve_type2_merge()
    anchors = [(1203, 285), (1204, 643), (1205, 639), (1210, 492), (1211, 344)]
    old = ["Crystal Hair Clip", "Jade Accessory", "Clay Ring"]
    for resource, mi in anchors:
        _assert_renamed(merged, resource, mi, "Silver Hair Ornament", old)


def test_return_potion_renamed():
    merged = _resolve_type2_merge()
    for resource, mi in [(1203, 19), (1204, 197)]:
        _assert_renamed(merged, resource, mi, "Return Potion", ["Return Scroll"])


def test_misc_single_item_anchors_renamed():
    merged = _resolve_type2_merge()
    anchors = [
        (1209, 393, "Magic Wine"),
        (1208, 211, "Member Card"),
        (1209, 222, "Member Card"),
        (1196, 829, "Gin's Blade"),
        (1196, 842, "Gin's Blade"),
        (1201, 162, "Osafune"),
        (1201, 166, "Osafune"),
        (1200, 227, "Bishop Cloak"),
        (1200, 240, "Bishop Cloak"),
        (1203, 565, "Flame Mace"),
        (1203, 1536, "Orc Pants"),
        (1203, 1538, "Repel Bell"),
        (1205, 270, "Stun Smash"),
        (1210, 495, "Cross-Gauge Kill"),
        (1197, 245, "Raiman Letter"),
        (1204, 202, "Heal Potion"),
        (1204, 243, "Heal Potion"),
        (1203, 318, "Dark Medal"),
        (1203, 1609, "Dark Medal"),
    ]
    for resource, mi, expected in anchors:
        eng = _resolved(merged, resource, mi)
        norm = _norm(eng)
        assert expected in norm, (
            "v195 regression: R%d/%d = %r (normalized %r), expected to "
            "contain %r" % (resource, mi, eng, norm, expected)
        )


# ===========================================================================
# Systemic sweep: no stale predecessor item name anywhere in live-loaded data
# ===========================================================================
def test_no_stale_predecessor_names_in_live_pipeline_data():
    """Systemic gate: sweep every file the v2 build pipeline actually loads
    (type2 batches auto-discovered by glob, minus the dead R39-equip
    batches, + the exact chunk/fix-file list build_full_english_v2.py reads)
    for any leftover WRONG predecessor item name from this wave. Checks both
    the literal string and the " / "-collapsed normalized form, so a
    reintroduced old name that happens to line-wrap mid-name doesn't slip
    past a literal-substring check."""
    hits = []
    for path in _live_type2_files() + _live_chunk_files():
        entries = json.load(open(path, encoding="utf-8"))
        if not isinstance(entries, list):
            continue
        for e in entries:
            eng = e.get("english")
            if not isinstance(eng, str):
                continue
            norm = _norm(eng)
            for old in OLD_NAMES:
                if old in eng or old in norm:
                    hits.append((os.path.basename(path), e.get("resource"),
                                 e.get("msg_index", e.get("message")), old, eng))

    assert not hits, (
        "v195 regression: %d live entr(y/ies) still carry an OLD item name "
        "from the divergence wave: %s" % (len(hits), hits[:8])
    )


TESTS = [
    test_samurai_soul_renamed,
    test_silence_breaker_renamed,
    test_recovery_medicine_renamed,
    test_silver_hair_ornament_renamed,
    test_return_potion_renamed,
    test_misc_single_item_anchors_renamed,
    test_no_stale_predecessor_names_in_live_pipeline_data,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_v195_item_name_divergence")
