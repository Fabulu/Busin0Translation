#!/usr/bin/env python3
"""
test_narration_pad_map.py -- round-2 gate: the tavern-intro narration left-align
PAD now COVERS the name-island narration bodies the classifier previously dropped.

THE BUG (v132 misalignednarration.p2s / shots/narration.png)
------------------------------------------------------------
The tavern-requests intro narration ("At Gin's tavern counter, requests were
offered to adventurers.") rendered CENTER-ANCHORED / ragged (~4-5 stacked lines)
instead of left-aligned like every other narration.  Root cause: that group
(R1197 g2) is a mode-N narration body that carries a SMALL 0x14 name-island at its
head, so tools/dialogue_classifier._classify dropped it at the line-159 nameplate
skip.  Dropped groups never entered build_narration_map(), so build_v9's
pad_narration_left_align() never padded them -> they fell to the un-padded
wrap_type2_text else-branch and the engine's count-based per-line centering left
them center-anchored.

THE ROUND-2 FIX (W1-NARR)
-------------------------
  * tools/dialogue_classifier.build_narration_pad_map(res_idx) exposes EXACTLY the
    mode-N name-island bodies that _classify drops, gated by a body-span predicate
    (_NARR_PAD_MIN_BODY=20 cells) so genuine speaker nameplates / dense menu-list
    groups (R1203 g1 "Explore / Master? / Storage 1-10 ..." family) are REJECTED.
    The D/N partition (build_dialogue_map / build_narration_map) is UNCHANGED, so
    the classifier's 19/19 ground-truth self-test stays green.
  * build/build_v9.py routes those pad-only groups through the IDENTICAL
    wrap_px(NARRATION_BOX_PX, collapse=True) + pad_narration_left_align path as the
    narration branch, minus NARR_PAD_EXCLUDE menu/list guards.

WHAT THIS GATE ASSERTS (all source/raw-data level -- no built ISO required)
---------------------------------------------------------------------------
  PAD-COVERS    build_narration_pad_map(1197) CONTAINS the tavern-intro group g2 --
                the exact group that escaped the pad in v132.
  PAD-DISJOINT  the pad map is DISJOINT from both build_dialogue_map and
                build_narration_map (it only adds DROPPED groups; it cannot perturb
                the validated D/N partition).
  PAD-REJECTS   the body-span predicate REJECTS the menu/list groups (R1197 g1) --
                padding those risks the R1197-class request-menu softlock the task
                warns about.
  CLASSIFIER-GT the classifier's own 19/19 ground-truth self-test still passes
                AFTER the _collect_narr_nameplate refactor (the partition is intact).
  BUILD-WIRED   build/build_v9.py imports build_narration_pad_map, computes
                narration_pad_groups per-resource, has the NARR_PAD_EXCLUDE guard,
                and the pad-only elif routes through the SAME
                wrap_px(NARRATION_BOX_PX, collapse=True) + pad_narration_left_align
                as the narration branch (no divergent path).
  PAD-EQUALIZES reproducing the build's pad path on R1197 g2's English yields lines
                of EQUAL glyph count -> equal count-based centering -> left edges
                align (the mechanism that fixes the center-anchored render).  This
                mirrors the live-RAM g3=[21,21,21] proof from the narration work.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import BUILD_V9, ROOT, Skip, main_exit, require_file  # noqa: E402

import dialogue_classifier as dc  # noqa: E402  (TOOLS_DIR on sys.path via _helpers)

# The tavern-requests intro narration resource/group (misalignednarration.p2s).
TAVERN_RES = 1197
TAVERN_INTRO_GROUP = 2
# A menu/list sibling group in the same resource that must NOT be padded.
MENU_LIST_GROUP = 1
RAW_R1197 = os.path.join(ROOT, "extracted", "packdata_raw", "%04d_type02.raw" % TAVERN_RES)


def _require_raw():
    """The pad map reads the pristine R1197 raw; SKIP cleanly if absent."""
    if not os.path.isfile(RAW_R1197):
        raise Skip(
            "extracted/packdata_raw/%04d_type02.raw missing -- narration pad map "
            "cannot be measured" % TAVERN_RES
        )


# ---------------------------------------------------------------------------
# PAD-COVERS / PAD-REJECTS / PAD-DISJOINT
# ---------------------------------------------------------------------------
def test_pad_map_covers_tavern_intro_group():
    """PAD-COVERS: build_narration_pad_map(1197) contains the tavern-intro narration
    group g2 -- the group that escaped the left-align pad in v132 and rendered
    center-anchored.  This is THE regression the round-2 fix routes into the pad."""
    _require_raw()
    pad = dc.build_narration_pad_map(TAVERN_RES)
    assert TAVERN_INTRO_GROUP in pad, (
        "build_narration_pad_map(%d) does NOT contain g%d (the tavern-intro "
        "narration) -- the misalignednarration.p2s center-anchored body would "
        "still escape pad_narration_left_align.  Pad map keys: %s"
        % (TAVERN_RES, TAVERN_INTRO_GROUP, sorted(pad)[:20])
    )
    # It must be tagged 'N' (narration) -- it routes through the narration pad path.
    assert pad[TAVERN_INTRO_GROUP] == "N", (
        "tavern-intro g%d is tagged %r in the pad map, expected 'N'"
        % (TAVERN_INTRO_GROUP, pad[TAVERN_INTRO_GROUP])
    )


def test_pad_map_rejects_menu_list_group():
    """PAD-REJECTS: the body-span predicate must REJECT the menu/list group g1 (the
    "Explore / Master? / Storage 1-10 ..." family whose every line is its own 0x14
    label).  Padding a menu/list group risks the R1197-class request-menu softlock
    the task explicitly warns against."""
    _require_raw()
    pad = dc.build_narration_pad_map(TAVERN_RES)
    assert MENU_LIST_GROUP not in pad, (
        "build_narration_pad_map(%d) wrongly INCLUDES the menu/list group g%d -- "
        "padding a per-line-cell menu group risks the request-menu softlock; the "
        "body-span predicate (_NARR_PAD_MIN_BODY) must reject it"
        % (TAVERN_RES, MENU_LIST_GROUP)
    )


def test_pad_map_disjoint_from_dn_partition():
    """PAD-DISJOINT: the pad map only RE-ADDS groups the classifier dropped, so it
    must be DISJOINT from both build_dialogue_map and build_narration_map.  Any
    overlap would mean the pad path double-handles a group already in the validated
    D/N partition (a sign the 19/19-safe contract was broken)."""
    _require_raw()
    pad = set(dc.build_narration_pad_map(TAVERN_RES))
    dmap = dc.build_dialogue_map(TAVERN_RES)
    nmap = dc.build_narration_map(TAVERN_RES)
    assert not (pad & dmap), (
        "narration pad map overlaps build_dialogue_map at %s -- the pad-only map "
        "must NOT contain dialogue groups" % sorted(pad & dmap)[:10]
    )
    assert not (pad & nmap), (
        "narration pad map overlaps build_narration_map at %s -- the pad-only map "
        "must contain ONLY the DROPPED groups, never groups already padded"
        % sorted(pad & nmap)[:10]
    )


def test_pad_min_body_predicate_present():
    """PAD-REJECTS (source): the body-span predicate constant exists and is a sane
    positive threshold -- the guard that keeps dense nameplate/menu groups out of the
    pad.  A missing/zero threshold would let every name-island body pad (regression)."""
    src = open(os.path.join(dc.__file__), encoding="utf-8").read()
    m = re.search(r"_NARR_PAD_MIN_BODY\s*=\s*(\d+)", src)
    assert m, (
        "tools/dialogue_classifier.py: _NARR_PAD_MIN_BODY threshold not found -- the "
        "body-span guard that rejects menu/nameplate groups is missing"
    )
    thr = int(m.group(1))
    assert thr >= 10, (
        "_NARR_PAD_MIN_BODY=%d is too small -- a tiny threshold would pad genuine "
        "speaker nameplates / menu lists (softlock risk)" % thr
    )


# ---------------------------------------------------------------------------
# CLASSIFIER-GT: the 19/19 ground truth survives the _collect_narr_nameplate refactor
# ---------------------------------------------------------------------------
def test_classifier_ground_truth_still_19_of_19():
    """CLASSIFIER-GT: the engine-mode classifier's 19/19 ground truth still holds
    AFTER the _collect_narr_nameplate out-param refactor -- the D/N partition that
    the pad map sits beside is UNCHANGED.  Mirrors dialogue_classifier's own __main__
    self-test (GT_DIALOGUE / GT_NARRATION) without spawning a subprocess."""
    _require_raw()
    # The same ground-truth set the classifier __main__ asserts (on-screen verified).
    GT_DIALOGUE = [(1197, 4), (1197, 9), (1197, 10), (1197, 904), (1197, 922),
                   (1197, 925), (1197, 927), (1197, 929), (1196, 577), (1197, 905)]
    GT_NARRATION = [(1197, 3), (1197, 7), (1197, 13), (1197, 926),
                    (1196, 568), (1196, 569), (1196, 570), (1196, 575),
                    (1196, 615), (1196, 616)]
    # SKIP if either resource raw is absent (cannot establish ground truth).
    for res in (1196, 1197):
        p = os.path.join(ROOT, "extracted", "packdata_raw", "%04d_type02.raw" % res)
        if not os.path.isfile(p):
            raise Skip("extracted/packdata_raw/%04d_type02.raw missing" % res)
    dmaps = {1196: dc.build_dialogue_map(1196), 1197: dc.build_dialogue_map(1197)}
    nmaps = {1196: dc.build_narration_map(1196), 1197: dc.build_narration_map(1197)}
    wrong = []
    for res, gi in GT_DIALOGUE:
        if gi not in dmaps[res]:
            wrong.append("D (%d,%d) not classified DIALOGUE" % (res, gi))
    for res, gi in GT_NARRATION:
        if gi not in nmaps[res]:
            wrong.append("N (%d,%d) not classified NARRATION" % (res, gi))
    assert not wrong, (
        "classifier ground truth regressed after the pad-map refactor (%d/%d wrong): %s"
        % (len(wrong), len(GT_DIALOGUE) + len(GT_NARRATION), wrong[:6])
    )


# ---------------------------------------------------------------------------
# BUILD-WIRED: build_v9 routes the pad groups through the SAME path as narration
# ---------------------------------------------------------------------------
def _build_src():
    return open(BUILD_V9, encoding="utf-8").read()


def test_build_v9_imports_and_calls_pad_map():
    """BUILD-WIRED: build_v9 imports build_narration_pad_map and computes a per-
    resource narration_pad_groups, with the NARR_PAD_EXCLUDE menu/list guard."""
    src = _build_src()
    assert "build_narration_pad_map" in src, (
        "build/build_v9.py does not import/use build_narration_pad_map -- the "
        "dropped name-island narration bodies are not routed into the left-align pad"
    )
    assert re.search(r"narration_pad_groups\s*=\s*build_narration_pad_map\(", src), (
        "build_v9 does not compute narration_pad_groups = build_narration_pad_map(...) "
        "per resource"
    )
    assert "NARR_PAD_EXCLUDE" in src, (
        "build_v9 lost the NARR_PAD_EXCLUDE guard -- the menu/list belt-and-suspenders "
        "exclusion that protects against the request-menu softlock"
    )


def test_build_v9_pad_branch_uses_narration_path():
    """BUILD-WIRED: the pad-only branch routes through the IDENTICAL
    wrap_px(NARRATION_BOX_PX, collapse=True) + pad_narration_left_align as the
    narration branch -- NOT a divergent wrap.  Asserted by locating the elif that
    tests `mi in narration_pad_groups` and confirming both calls appear in its body
    before the next dedented branch."""
    src = _build_src()
    lines = src.splitlines()
    # Find the pad-only elif.
    idx = None
    for i, ln in enumerate(lines):
        if re.search(r"elif\s+mi\s+in\s+narration_pad_groups", ln):
            idx = i
            break
    assert idx is not None, (
        "build_v9 has no `elif mi in narration_pad_groups` branch -- the dropped "
        "narration bodies are not routed into the pad path"
    )
    # Collect the elif body (until the next line at the elif's own indent or less
    # that starts a new clause).
    base_indent = len(lines[idx]) - len(lines[idx].lstrip())
    body = []
    for ln in lines[idx + 1:]:
        if ln.strip() == "":
            body.append(ln)
            continue
        ind = len(ln) - len(ln.lstrip())
        if ind <= base_indent and ln.lstrip().startswith(("else", "elif", "if ")):
            break
        if ind <= base_indent:
            break
        body.append(ln)
    blob = "\n".join(body)
    assert "wrap_px(" in blob and "NARRATION_BOX_PX" in blob and "collapse=True" in blob, (
        "the narration_pad_groups branch does NOT call wrap_px(NARRATION_BOX_PX, "
        "collapse=True) -- it must use the SAME wrap as the narration branch, not a "
        "divergent path.  Branch body:\n%s" % blob
    )
    assert "pad_narration_left_align(" in blob, (
        "the narration_pad_groups branch does NOT call pad_narration_left_align -- "
        "the dropped bodies would not be left-aligned.  Branch body:\n%s" % blob
    )


# ---------------------------------------------------------------------------
# PAD-EQUALIZES: reproduce the build's pad path on g2 -> equal per-line counts
# ---------------------------------------------------------------------------
def _isolate_pad_fn():
    """Import build_v9.pad_narration_left_align WITHOUT running the build pipeline.

    build_v9.py executes its top-level build on import (needs artifacts), so we
    regex-slice ONLY the pad function source and exec it in a clean namespace.
    pad_narration_left_align is pure string ops with NO module-global dependencies
    (verified: it only uses str.split/' / '/' // '/len), so the slice is self-
    contained.  SKIP if the function can't be isolated (signature moved)."""
    src = open(BUILD_V9, encoding="utf-8").read()
    m = re.search(
        r"^def pad_narration_left_align\(.*?(?=^def\s|\Z)", src, re.M | re.S
    )
    if not m:
        raise Skip("could not isolate build_v9.pad_narration_left_align (moved?)")
    ns = {}
    try:
        exec(m.group(0), ns)
    except Exception as e:
        raise Skip("pad_narration_left_align exec failed (%s)" % e)
    fn = ns.get("pad_narration_left_align")
    if not callable(fn):
        raise Skip("pad_narration_left_align not callable after isolation")
    return fn


def test_pad_function_equalizes_line_counts():
    """PAD-EQUALIZES: build_v9.pad_narration_left_align, run on a representative
    pre-wrapped tavern-intro body (4 ragged lines), pads EVERY line to EQUAL glyph
    count -> equal count-based centering -> left edges align.  This is the exact
    mechanism that fixes the center-anchored misalignednarration render, mirroring
    the live g3=[21,21,21] equal-count proof.  Uses the build's OWN function (SoT),
    isolated so no build artifacts are required."""
    pad = _isolate_pad_fn()
    # A ragged 4-line wrap of the tavern-intro narration (the shape the engine
    # center-anchored in v132).  Lines have DIFFERENT lengths before padding.
    wrapped = "At Gin's tavern / counter, requests / were offered to / adventurers."
    pre_counts = [len(l) for l in wrapped.split(" / ")]
    assert len(set(pre_counts)) > 1, (
        "test fixture is already equal-count (%s) -- it would not prove the pad does "
        "anything" % pre_counts
    )
    padded = pad(wrapped)
    counts = [len(l) for l in padded.split(" / ")]
    assert len(set(counts)) == 1, (
        "pad_narration_left_align did NOT equalize the ragged narration line glyph "
        "counts %s -> %s -- without equal counts the engine's count-based centering "
        "leaves the narration center-anchored (the misalignednarration.p2s bug)"
        % (pre_counts, counts)
    )
    # The padded count must be the max of the pre-pad counts (TRAILING pad only --
    # the visible text/ink width is unchanged, per the left-align mechanism).
    assert counts[0] == max(pre_counts), (
        "pad equalized to %d, expected max line len %d (trailing-space pad only)"
        % (counts[0], max(pre_counts))
    )
    # Padding must add ONLY trailing spaces (ink unchanged): rstrip restores originals.
    rstripped = [l.rstrip(" ") for l in padded.split(" / ")]
    assert rstripped == wrapped.split(" / "), (
        "pad_narration_left_align altered visible ink, not just trailing spaces: %r"
        % rstripped
    )


TESTS = [
    test_pad_map_covers_tavern_intro_group,
    test_pad_map_rejects_menu_list_group,
    test_pad_map_disjoint_from_dn_partition,
    test_pad_min_body_predicate_present,
    test_classifier_ground_truth_still_19_of_19,
    test_build_v9_imports_and_calls_pad_map,
    test_build_v9_pad_branch_uses_narration_path,
    test_pad_function_equalizes_line_counts,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_narration_pad_map")
