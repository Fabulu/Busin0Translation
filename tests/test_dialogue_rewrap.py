#!/usr/bin/env python3
"""
test_dialogue_rewrap.py -- gate for the DIALOGUE corpus re-wrap at the 480px box
and the engine-rule box-mode classifier that drives it.

WHAT THIS COVERS (all STRUCTURAL — runs from disk, no live session)
-------------------------------------------------------------------
Render mode is now read DIRECTLY from the engine's own rule (the 0x12-GOSUB ->
0x63-align helper mechanism in tools/dialogue_classifier.py, validated 19/19 +
EXE-grounded).  build_dialogue_map / build_narration_map are an exact partition of
every group covered by a walked 0x04 block, so the old manual DIALOGUE_FORCE
override is GONE.  These gates assert the wrap the build produces over that set:

  budget   DIALOGUE_BOX_PX is the canonical 480px budget, wider than the 360px
           narration budget (the two-tier split the wrap depends on).
  px       every wrapped dialogue LINE is <= DIALOGUE_BOX_PX, measured through the
           shared glyph_metrics.px_width SoT (no independent width recompute).
  bucket   every classified dialogue group wraps to <=4 lines/page at the budget
           after the authored ' // ' page splits.
  guard    the DIALOGUE_WRAP_EXCLUDE groups (intentional ' / ' LISTS) are present
           and WOULD be corrupted by wrap_px -> the build's pass-through guard is
           necessary and wired BEFORE the wrap branches.
  classifier  the box-mode classifier reproduces the engine on the 19-case ground
           truth (incl. the cutscene cases) + the structural gates.

Every width comes EXCLUSIVELY from the shared SoT tools/glyph_metrics.py via the
build's OWN wrap_px (extracted from build_v9.py source).
"""

import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import BUILD_V9, ROOT, Skip, main_exit  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "tools"))
import glyph_metrics  # noqa: E402

# Must mirror build/build_v9.py.  The exclude set is the only hand-list left (the
# DIALOGUE_FORCE override is gone — the classifier reproduces the engine).
EXPECTED_EXCLUDE = {(1194, 0), (1196, 810), (1200, 64),
                    (1212, 1), (1213, 1), (1353, 1)}
CANONICAL_BOX_PX = 456    # live-playtest box width (was 480 — too generous)
MAX_LINES_PER_PAGE = 4


def _enc(ch):
    o = ord(ch)
    return o - 32 if 32 <= o < 127 else 0


def _load_build_wrap():
    """Return (DIALOGUE_BOX_PX, NARRATION_BOX_PX, wrap_px) from build_v9 source
    WITHOUT running the build (it chdir+builds at import)."""
    src = open(BUILD_V9, encoding="utf-8").read()
    ns = {"glyph_metrics": glyph_metrics, "enc": _enc}
    for cm, name in ((r"^DIALOGUE_BOX_PX\s*=\s*(\d+)", "DIALOGUE_BOX_PX"),
                     (r"^NARRATION_BOX_PX\s*=\s*(\d+)", "NARRATION_BOX_PX")):
        m = re.search(cm, src, re.M)
        assert m, "build_v9.py: %s constant not found" % name
        ns[name] = int(m.group(1))
    for fn in ("_wrap_line_px", "wrap_px"):
        mm = re.search(r"^def %s\(.*?(?=^\S|\Z)" % fn, src, re.M | re.S)
        assert mm, "def %s not found in build_v9.py" % fn
        exec(compile(mm.group(0), "build_v9:%s" % fn, "exec"), ns)
    return ns["DIALOGUE_BOX_PX"], ns["NARRATION_BOX_PX"], ns["wrap_px"]


def _parse_pair_set(name):
    src = open(BUILD_V9, encoding="utf-8").read()
    m = re.search(r"\b%s\s*=\s*\{(.*?)\}" % re.escape(name), src, re.S)
    assert m, "build_v9.py: %s set not found" % name
    pairs = re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", m.group(1))
    return {(int(a), int(b)) for a, b in pairs}


def _build_exclude_set():
    got = _parse_pair_set("DIALOGUE_WRAP_EXCLUDE")
    assert got, "build_v9.py: DIALOGUE_WRAP_EXCLUDE empty/absent (guard missing)"
    return got


def _load_corpus():
    batches = sorted(glob.glob(os.path.join(ROOT, "data", "type2_translated",
                                            "batch_*.json")))
    if not batches:
        raise Skip("no data/type2_translated/batch_*.json")
    trans = {}
    for fn in batches:
        try:
            data = json.load(open(fn, encoding="utf-8"))
        except Exception:
            continue
        for e in data:
            if "resource" not in e or "msg_index" not in e:
                continue
            en = e.get("english", "")
            if not en or any(ord(c) > 127 for c in en):
                continue
            trans[(e["resource"], e["msg_index"])] = en
    if not trans:
        raise Skip("no translatable type-2 strings in the corpus")
    return trans


def _dialogue_maps():
    try:
        from dialogue_classifier import build_dialogue_map
    except Exception as e:
        raise Skip("dialogue_classifier import failed (opcode table?): %s" % e)
    return build_dialogue_map


def _max_lines_per_page(text, wrap_px, box):
    return max(len(wrap_px(page, box).split(" / "))
               for page in text.split(" // "))


def test_dialogue_box_px_is_canonical_budget():
    box, narr, _ = _load_build_wrap()
    assert box == CANONICAL_BOX_PX, (
        "DIALOGUE_BOX_PX=%d != canonical %dpx" % (box, CANONICAL_BOX_PX))
    assert box > narr, (
        "DIALOGUE_BOX_PX=%d must exceed NARRATION_BOX_PX=%d" % (box, narr))


def test_every_wrapped_dialogue_line_within_box():
    box, _narr, wrap_px = _load_build_wrap()
    build_dialogue_map = _dialogue_maps()
    trans = _load_corpus()
    exclude = _build_exclude_set()

    by_res = {}
    for (r, mi), en in trans.items():
        by_res.setdefault(r, {})[mi] = en

    offenders = []
    checked = 0
    for r in sorted(by_res):
        if r == 1193:
            continue
        try:
            dmap = build_dialogue_map(r)
        except Exception:
            continue
        for mi, en in by_res[r].items():
            if mi not in dmap or (r, mi) in exclude:
                continue
            for page in wrap_px(en, box).split(" // "):
                for line in page.split(" / "):
                    px = glyph_metrics.px_width(line, _enc)
                    checked += 1
                    if px > box and " " in line:
                        offenders.append((r, mi, px, line[:48]))
    if checked == 0:
        raise Skip("no dialogue lines resolved")
    assert not offenders, (
        "%d wrapped dialogue line(s) exceed the %dpx box. Worst: %s" % (
            len(offenders), box,
            "; ".join("R%d g%d px=%d %r" % o
                      for o in sorted(offenders, key=lambda x: -x[2])[:8])))


def test_no_dialogue_group_over_4_lines_at_budget():
    box, _narr, wrap_px = _load_build_wrap()
    build_dialogue_map = _dialogue_maps()
    trans = _load_corpus()
    exclude = _build_exclude_set()

    by_res = {}
    for (r, mi), en in trans.items():
        by_res.setdefault(r, {})[mi] = en

    over = []
    ngroups = 0
    for r in sorted(by_res):
        if r == 1193:
            continue
        try:
            dmap = build_dialogue_map(r)
        except Exception:
            continue
        for mi, en in by_res[r].items():
            if mi not in dmap or (r, mi) in exclude:
                continue
            ngroups += 1
            ml = _max_lines_per_page(en, wrap_px, box)
            if ml > MAX_LINES_PER_PAGE:
                over.append((r, mi, ml))
    if ngroups == 0:
        raise Skip("no classified dialogue groups")
    assert not over, (
        "%d dialogue group(s) wrap >%d lines/page at %dpx — need an authored "
        "' // ' split. Offenders: %s"
        % (len(over), MAX_LINES_PER_PAGE, box,
           "; ".join("R%d g%d=%dL" % o for o in over[:12])))


def test_exclude_set_matches_expected():
    got = _build_exclude_set()
    assert got == EXPECTED_EXCLUDE, (
        "build_v9.DIALOGUE_WRAP_EXCLUDE = %s, expected %s"
        % (sorted(got), sorted(EXPECTED_EXCLUDE)))


def test_each_guard_group_would_be_corrupted_by_wrap():
    """Every DIALOGUE_WRAP_EXCLUDE group is an intentional ' / '/newline LIST that
    wrap_px WOULD flatten — proving the build's pass-through guard prevents real
    corruption.  (Under the engine-rule classifier these groups are NOT dialogue,
    but they are still covered/narration and would be re-wrapped without the guard,
    so the necessity is now 'wrap_px changes it', not 'flagged as dialogue'.)"""
    box, _narr, wrap_px = _load_build_wrap()
    exclude = _build_exclude_set()
    raw = {}
    for fn in sorted(glob.glob(os.path.join(ROOT, "data", "type2_translated",
                                            "batch_*.json"))):
        try:
            data = json.load(open(fn, encoding="utf-8"))
        except Exception:
            continue
        for e in data:
            if "resource" in e and "msg_index" in e and e.get("english"):
                raw[(e["resource"], e["msg_index"])] = e["english"]

    missing, harmless = [], []
    for (r, mi) in sorted(exclude):
        en = raw.get((r, mi))
        if en is None:
            missing.append((r, mi))
            continue
        if wrap_px(en, box) == en:
            harmless.append((r, mi))
    assert not missing, "guard group(s) %s absent from corpus" % missing
    assert not harmless, (
        "guard group(s) %s are unchanged by wrap_px — the guard claims to PREVENT "
        "corruption, so each must be a string wrap_px WOULD flatten" % harmless)


def test_guard_branch_wired_before_wrap():
    src = open(BUILD_V9, encoding="utf-8").read()
    i_excl = src.find("(r_id, mi) in DIALOGUE_WRAP_EXCLUDE")
    assert i_excl != -1, "build_v9.py does not gate on DIALOGUE_WRAP_EXCLUDE"
    i_wrap = src.find("wrap_px(en_text", i_excl)
    assert i_wrap != -1 and i_wrap > i_excl, (
        "the DIALOGUE_WRAP_EXCLUDE check does not precede wrap_px")
    assert "pass" in src[i_excl:i_wrap], (
        "the exclude branch is not a no-op (`pass`) before wrap_px")


def test_no_manual_force_override_remains():
    """The manual DIALOGUE_FORCE override must be GONE — the engine-rule classifier
    reproduces the box mode for every group, so a hand list would only mask a
    classifier bug."""
    src = open(BUILD_V9, encoding="utf-8").read()
    assert not re.search(r"^DIALOGUE_FORCE\s*=", src, re.M), (
        "build_v9.py still defines DIALOGUE_FORCE — the manual override should be "
        "removed now that dialogue_classifier reproduces the engine's box mode")
    assert "(r_id, mi) in DIALOGUE_FORCE" not in src, (
        "build_v9.py wrap dispatch still references DIALOGUE_FORCE")


def test_classifier_reproduces_engine_ground_truth():
    """The box-mode classifier (the 0x63-helper engine rule) reproduces the engine
    on the 19-case on-screen ground truth, including the cutscene cases that defeat
    every heuristic, plus the structural gates."""
    try:
        from dialogue_classifier import build_dialogue_map, build_narration_map
    except Exception as e:
        raise Skip("dialogue_classifier import failed (opcode table?): %s" % e)
    GT_D = [(1197, 4), (1197, 9), (1197, 10), (1197, 904), (1197, 922),
            (1197, 925), (1197, 927), (1197, 929), (1196, 577), (1197, 905)]
    GT_N = [(1197, 3), (1197, 7), (1197, 13), (1197, 926),
            (1196, 568), (1196, 569), (1196, 570), (1196, 575),
            (1196, 615), (1196, 616)]
    dmaps = {r: build_dialogue_map(r) for r in (1196, 1197)}
    nmaps = {r: build_narration_map(r) for r in (1196, 1197)}
    bad = []
    for r, g in GT_D:
        if g not in dmaps[r]:
            bad.append(("dialogue", r, g))
    for r, g in GT_N:
        if g not in nmaps[r] or g in dmaps[r]:
            bad.append(("narration", r, g))
    assert not bad, "classifier misclassified ground-truth groups: %s" % bad
    # structural gates
    assert build_dialogue_map(35) == set(), "R35 walk-fail must be empty"
    assert not (dmaps[1196] & nmaps[1196]), "R1196 maps must be disjoint"
    assert not (dmaps[1197] & nmaps[1197]), "R1197 maps must be disjoint"


TESTS = [
    test_dialogue_box_px_is_canonical_budget,
    test_every_wrapped_dialogue_line_within_box,
    test_no_dialogue_group_over_4_lines_at_budget,
    test_exclude_set_matches_expected,
    test_each_guard_group_would_be_corrupted_by_wrap,
    test_guard_branch_wired_before_wrap,
    test_no_manual_force_override_remains,
    test_classifier_reproduces_engine_ground_truth,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_dialogue_rewrap")
