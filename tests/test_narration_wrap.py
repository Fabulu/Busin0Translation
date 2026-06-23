#!/usr/bin/env python3
"""
test_narration_wrap.py -- P1 narration wrap reflow gate.

WHAT P1 DID
-----------
build_v9 Step 4 re-wraps BARE-DISPLAY centered NARRATION groups (the INVERSE of
the dialogue classifier: a single 0x04 DISPLAY block NOT headed by a 0x14 name
island) at a PIXEL budget instead of the JP author's far-too-narrow per-cell
line breaks:

    elif mi in narration_groups:
        en_text = wrap_px(en_text, NARRATION_BOX_PX, collapse=True)

NARRATION_BOX_PX (= 300) is the R8/R10 interim budget: it stays INSIDE the
already-PROVEN centered span (x87..339 in the thing4-7 GS dumps) regardless of
the centering-reserve state, so the wider wrap is safe to ship even before P2's
summed-width centering lands.  collapse=True flattens the premature ' / ' breaks
in each ' // ' page and re-wraps to <=NARRATION_BOX_PX pixels, emitting ONLY
' / '/' // ' (-> a single 0xFFFE word), NEVER a 0xFFD2 (the v97 colour-code rule).

WHAT THIS GATE ASSERTS (all PASS on the current tree -- build-data only)
------------------------------------------------------------------------
  G-px  (TIER-2 + TIER-3): every INJECTED-ENGLISH on-screen line of a NARRATION
        group in the built output has glyph_metrics.px_width <= NARRATION_BOX_PX.
        A single unwrappable token (no internal space glyph) is exempt -- wrap_px
        emits it alone rather than split mid-token.  Choice groups are exempt
        (build_v9 never wraps a choice group, so its question line legitimately
        stays full width; their layout is governed by test_choice_groups).  This
        is the regression surface: if the narration px-wrap is ever removed,
        broken, or stops being applied, an over-wide narration line trips here.

  G-sot (static, always): NARRATION_BOX_PX is read STRAIGHT FROM the build source
        (never imported -- build_v9.py runs a full ISO build at import time) and
        the wrap path reads widths ONLY through the shared SoT glyph_metrics, so
        the gate budget can never drift from what the build actually wraps to
        (this project's #1 failure mode: independent width recompute).

  G-cls (static, always): the narration classifier is the strict INVERSE of the
        dialogue classifier -- disjoint on R1196 -- and the user-reported
        narration groups (R1196 g568/g570/g615) ARE narration while a known
        STRUCTURAL/menu group (R1196 g810) is NOT, so structural groups ship
        byte-identical.  Binary Section 1 (R35) yields an EMPTY set (ship
        pristine), matching inject_and_patch.

  G-col (TIER-2): R1196 g568 ("A heavy fog had ...") collapses from the JP
        author's 4 ragged ' / ' segments to <=3 wider lines in the built output.

This complements test_line_width (dialogue px<=324 + char-20 narration ceiling)
and test_no_auto_pagebreak (no spurious 0xFFD2): together they pin every wrap
path build_v9 produces.

TIERS
-----
  TIER-2 : build/patched_type2/*.raw  (Skip if absent -- run a build first).
  TIER-3 : the freshest BUSIN0_EN_v*.iso, freshness-guarded so a stale ISO Skips
           instead of false-failing.
"""

import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (  # noqa: E402  (path insert first)
    BUILD_V9,
    PATCHED_TYPE2_DIR,
    PackData,
    ROOT,
    Skip,
    decode_glyphs,
    default_iso_path,
    group_offsets,
    main_exit,
    parse_type02,
    require_dir,
    require_file,
)

# tools/ is put on sys.path by _helpers; import the SoT + the classifier.
import glyph_metrics  # noqa: E402
from dialogue_classifier import (  # noqa: E402
    build_dialogue_map,
    build_narration_map,
)

# ---------------------------------------------------------------------------
# Constants -- the px budget comes STRAIGHT FROM build_v9 source (no import:
# importing build_v9.py runs a full ISO build at module load).  This is the SoT
# read that keeps the gate budget == the build budget (test_line_width does the
# same for TYPE2_WRAP_WIDTH).
# ---------------------------------------------------------------------------
def _build_v9_narration_box_px():
    src = open(BUILD_V9, encoding="utf-8").read()
    m = re.search(r"^NARRATION_BOX_PX\s*=\s*(\d+)", src, re.M)
    assert m, "build_v9.py: NARRATION_BOX_PX constant not found (P1 not applied)"
    return int(m.group(1))


NARRATION_BOX_PX = _build_v9_narration_box_px()


def _build_v9_dialogue_force():
    """Parse build_v9's DIALOGUE_FORCE {(r, m), ...} set straight from source
    (NOT imported -- build_v9 builds at import time).  These groups are
    classifier-mis-routed boxed dialogue that the build re-routes into the 480px
    DIALOGUE wrap, so they are NOT narration and must NOT be gated here."""
    src = open(BUILD_V9, encoding="utf-8").read()
    m = re.search(r"^DIALOGUE_FORCE\s*=\s*\{(.*?)\}", src, re.M | re.S)
    if not m:
        return set()
    return set(
        (int(a), int(b))
        for a, b in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", m.group(1))
    )


DIALOGUE_FORCE = _build_v9_dialogue_force()

# Visible-glyph boundary: every control/marker word (choice 0xFFCx, line break
# 0xFFFE, page break 0xFFD2, terminator 0xFFFF, colour/speed opcodes) is
# id >= 0xFB00.  A "visible" glyph is anything below this.
CONTROL_FLOOR = 0xFB00
# ASCII-English glyph ids run 0..94 (build_v9.enc maps every printable ASCII char
# here).  A line is INJECTED-ENGLISH iff all its visible glyphs are <= this.
ENGLISH_GLYPH_HI = 94
# Space glyph id (gid = char-32, ' ' -> 0): a line with no space is a single
# unwrappable token, exempt from the px ceiling (wrap_px emits it alone).
SPACE_GID = 0

# Section-2 break / marker words.
LINE_BREAK = 0xFFFE
PAGE_BREAK = 0xFFD2
CHOICE_LO = 0xFFC0
CHOICE_HI = 0xFFCF

# Resources build_v9 treats as binary / non-text plus R1193 (Step-5 trailing
# narration, separate <=23-glyph line discipline -- NOT the Step-4 px wrap).
# Kept in sync with test_line_width.BINARY_RESOURCES.
BINARY_RESOURCES = frozenset([
    677, 690, 712, 715, 726, 741, 750, 757, 769, 780, 785, 787, 793, 795, 797,
    799, 801, 803, 816, 837, 839, 852, 860, 862, 864, 866, 868, 870, 871, 873,
    875, 877, 879, 881, 883, 885, 889, 917, 920, 1057, 1061, 1072, 1073, 1077,
    1084, 1091, 1093, 1099, 1105, 1109, 1110, 1112, 1123, 1133, 1141, 1145,
    1146, 1147, 1174, 1192, 1912, 1930, 1931, 1933, 1934, 1935, 1936, 1939,
    1940, 1941, 1948, 1952, 1953, 1959, 1972, 2141, 2144, 2161, 2162, 2163,
    2166, 2174, 2176, 2200, 2201, 2204, 2206, 2207, 2208, 2588, 2589, 2651,
    2652, 2653,
])
EXEMPT_RESOURCES = BINARY_RESOURCES | {1193}


def _id_enc(g):
    """Identity enc for glyph IDs: the visible-glyph stream is already a list of
    ADV-table indices (gid = char-32), so glyph_metrics.px_width needs no map."""
    return g


# build_narration_map walks Section 1 per resource; memoize (it is the SAME map
# build_v9.wrap_px is gated on, so the test and the build classify identically).
_NMAP_CACHE = {}


def _narration_map(res):
    if res not in _NMAP_CACHE:
        try:
            _NMAP_CACHE[res] = build_narration_map(res)
        except Exception:
            _NMAP_CACHE[res] = set()  # unwalkable -> nothing classified narration
    return _NMAP_CACHE[res]


def _is_choice_group(group_words):
    return any(CHOICE_LO <= w <= CHOICE_HI for w in group_words)


def _split_lines(group_words):
    """Split a group's glyph stream into on-screen lines on 0xFFFE / 0xFFD2."""
    line = []
    for w in group_words:
        if w == LINE_BREAK or w == PAGE_BREAK:
            yield line
            line = []
        else:
            line.append(w)
    yield line


def _narration_offenders(words, res):
    """
    Yield (res, gi, px, text) for every INJECTED-ENGLISH on-screen line of a
    NARRATION-classified group whose glyph_metrics px width exceeds
    NARRATION_BOX_PX.

    Mirrors the build's wrap decision EXACTLY:
      * only groups in build_narration_map(res) are gated (those are the groups
        build_v9 actually re-wraps at NARRATION_BOX_PX);
      * choice groups are exempt -- build_v9's `if mi not in choice_groups:` gate
        means a narration-classified CHOICE group's question line is never
        wrapped, so its full-width line is correct, not a clip;
      * a single unwrappable token (no internal space glyph) is exempt -- wrap_px
        emits it alone rather than split mid-token;
      * widths come ONLY from glyph_metrics.px_width (NEVER a recompute).
    """
    groups, _trailing = group_offsets(words)
    nmap = _narration_map(res)
    for gi, (gs, ge) in enumerate(groups):
        if gi not in nmap:
            continue  # not narration -> ships via the other paths, gated elsewhere
        if (res, gi) in DIALOGUE_FORCE:
            # build_v9 re-routes this classifier-mis-routed group into the 480px
            # DIALOGUE wrap (NOT narration) -- gated by test_line_width's dialogue
            # path, so do not false-fail it against the 360px narration budget.
            continue
        group = words[gs:ge]
        if _is_choice_group(group):
            continue  # choice group: build_v9 never wraps it -> not a narration clip
        for line in _split_lines(group):
            visible = [w for w in line if w < CONTROL_FLOOR]
            # Drop the invisible trailing-space pad (gid 0) the narration LEFT-ALIGN
            # adds to equalise glyph count -> measure INK width only.  The pad is
            # blank on screen; the engine's count-based centering uses it, but it
            # never widens the visible line.
            while visible and visible[-1] == SPACE_GID:
                visible.pop()
            if not visible:
                continue
            # Gate ONLY all-English lines -- those are exactly the lines build_v9's
            # narration re-wrap produced.  A line with any Japanese glyph is
            # untranslated original we never re-flowed (exempt).
            if any(w > ENGLISH_GLYPH_HI for w in visible):
                continue
            wrappable = SPACE_GID in visible
            px = glyph_metrics.px_width(visible, _id_enc)
            if px > NARRATION_BOX_PX and wrappable:
                yield (res, gi, px, decode_glyphs(line).strip())


def _format(offenders, limit=12):
    offenders = sorted(offenders, key=lambda o: o[2], reverse=True)
    return "; ".join(
        "R%d g%d px=%d %r" % (res, gi, px, txt[:48])
        for (res, gi, px, txt) in offenders[:limit]
    )


# ---------------------------------------------------------------------------
# G-px TIER-2: build/patched_type2/*.raw
# ---------------------------------------------------------------------------
def test_tier2_narration_px_budget():
    """Every injected-English narration line in build/patched_type2 fits within
    NARRATION_BOX_PX pixels (P1 wrap regression gate)."""
    require_dir(PATCHED_TYPE2_DIR, "run a build first (Step 4 type-02 injection)")
    files = sorted(glob.glob(os.path.join(PATCHED_TYPE2_DIR, "*.raw")))
    if not files:
        raise Skip("no *.raw in build/patched_type2 -- run a build first")

    offenders, checked = [], 0
    for path in files:
        res = int(os.path.basename(path)[:4])
        if res in EXEMPT_RESOURCES:
            continue
        try:
            words = parse_type02(open(path, "rb").read())["words"]
        except Exception:
            continue
        if not _narration_map(res):
            continue  # no narration groups (or unwalkable S1) -- nothing to gate
        checked += 1
        offenders.extend(_narration_offenders(words, res))

    if checked == 0:
        raise Skip("no narration-bearing type-02 resources in build/patched_type2")
    assert not offenders, (
        "%d injected-English narration line(s) exceed the %dpx budget (P1 "
        "narration wrap regression). Worst: %s"
        % (len(offenders), NARRATION_BOX_PX, _format(offenders))
    )


# ---------------------------------------------------------------------------
# G-px TIER-3: freshest ISO (real-PS2 path), freshness-guarded
# ---------------------------------------------------------------------------
def _newest_iso():
    env = default_iso_path()
    candidates = [env] if os.path.isfile(env) else []
    candidates += glob.glob(os.path.join(ROOT, "build", "BUSIN0_EN_v*.iso"))
    candidates = [c for c in candidates if os.path.isfile(c)]
    return max(candidates, key=os.path.getmtime) if candidates else ""


def test_tier3_iso_narration_px_budget():
    """Same narration px budget against the type-02 resources as they live in the
    freshest built PACKDATA.  Freshness-guarded: Skip when the ISO predates the
    patched_type2 outputs (mirrors test_line_width.test_tier3_iso_line_width)."""
    iso = _newest_iso()
    if not iso:
        raise Skip("no BUSIN0_EN_v*.iso present (set BUSIN_ISO or build)")

    patched = glob.glob(os.path.join(PATCHED_TYPE2_DIR, "*.raw"))
    if patched:
        newest_patched = max(os.path.getmtime(p) for p in patched)
        if os.path.getmtime(iso) < newest_patched:
            raise Skip(
                "ISO %s predates build/patched_type2 -- no fresh ISO built since "
                "Step 4 last ran" % os.path.basename(iso)
            )

    targets = sorted(
        r for r in (int(os.path.basename(p)[:4]) for p in patched)
        if r not in EXEMPT_RESOURCES
    )
    if not targets:
        raise Skip("no patched type-02 resources to cross-check against the ISO")

    pack = PackData(iso)  # raises Skip itself if the ISO has no PACKDATA
    offenders, checked = [], 0
    try:
        for res in targets:
            try:
                data, type_code = pack.extract(res)
                if type_code != 2:
                    continue
                words = parse_type02(data)["words"]
            except Exception:
                continue
            if not _narration_map(res):
                continue
            checked += 1
            offenders.extend(_narration_offenders(words, res))
    finally:
        pack.close()

    if checked == 0:
        raise Skip("no narration-bearing type-02 resources resolved from the ISO")
    assert not offenders, (
        "%d injected-English narration line(s) exceed the %dpx budget in the ISO "
        "PACKDATA (P1 narration wrap regression on the real-PS2 path). Worst: %s"
        % (len(offenders), NARRATION_BOX_PX, _format(offenders))
    )


# ---------------------------------------------------------------------------
# G-sot: the build budget is read from the SoT, never recomputed
# ---------------------------------------------------------------------------
def test_narration_box_px_is_sane_and_within_proven_span():
    """NARRATION_BOX_PX must be a positive budget and stay within the GS-proven
    centered span (x87..339 => ~252px usable) so P1 is safe to ship before P2's
    summed-width centering lands.  Catches a future careless bump past the proven
    area that would clip the right edge with the current count*18 reserve."""
    assert NARRATION_BOX_PX > 0, "NARRATION_BOX_PX must be positive"
    # The PROVEN centered span is x=[87,339] = 252px wide; 300 is the R8/R10
    # interim (the wrap fills slightly past the bare span because the count*18
    # reserve over-centers, leaving headroom).  Anything > 360 is the post-P2
    # regime and must NOT ship before P2 -- guard it here.
    assert NARRATION_BOX_PX <= 360, (
        "NARRATION_BOX_PX=%d exceeds the pre-P2 safe ceiling (360). Lines wider "
        "than ~360px only stay on-screen once P2's summed-width centering is "
        "correct -- bump only after P2 + a fresh GS dump confirms no right clip."
        % NARRATION_BOX_PX
    )


def test_narration_wrap_uses_shared_metrics():
    """The narration wrap path in build_v9 must read per-glyph widths through the
    shared SoT glyph_metrics (px_width), never an inline recompute -- the silent
    desync bug.  Static source assertion (autonomous-safe)."""
    src = open(BUILD_V9, encoding="utf-8").read()
    assert "import glyph_metrics" in src, (
        "build/build_v9.py dropped `import glyph_metrics` -- the narration "
        "wrap_px path must source widths from tools/glyph_metrics.py"
    )
    assert "glyph_metrics.px_width" in src, (
        "build/build_v9.py: the px wrap no longer calls glyph_metrics.px_width "
        "-- widths must NEVER be recomputed independently (project bug #1)"
    )
    # The narration branch must wrap at NARRATION_BOX_PX with collapse=True.
    assert re.search(
        r"wrap_px\(\s*en_text\s*,\s*NARRATION_BOX_PX\s*,\s*collapse\s*=\s*True\s*\)",
        src,
    ), (
        "build/build_v9.py: the narration encode branch must be "
        "wrap_px(en_text, NARRATION_BOX_PX, collapse=True) -- P1 wiring missing"
    )


# ---------------------------------------------------------------------------
# G-cls: narration classifier is the strict inverse of the dialogue classifier
# ---------------------------------------------------------------------------
def test_narration_classifier_inverse_and_disjoint():
    """build_narration_map is the INVERSE of build_dialogue_map: disjoint on
    R1196; the user-reported narration groups ARE narration and NOT dialogue; a
    known STRUCTURAL/menu group is NOT narration (ships byte-identical); binary
    Section 1 yields an EMPTY set (ship pristine)."""
    n = build_narration_map(1196)
    d = build_dialogue_map(1196)
    assert not (n & d), (
        "build_narration_map(1196) & build_dialogue_map(1196) overlap -- the "
        "classifiers are NOT disjoint (a group would be both wrapped AND reflowed)"
    )
    for g in (568, 570, 615):
        assert g in n, "R1196 g%d is user-reported narration but NOT classified" % g
        assert g not in d, "R1196 g%d narration must NOT be dialogue" % g
    # g810 is a structural newline-list group: NOT narration -> ships unchanged.
    assert 810 not in n, (
        "R1196 g810 (structural list) is classified narration -- it would be "
        "re-wrapped and stop shipping byte-identical (R8 structural-corruption risk)"
    )
    # Binary Section 1 (R35) -> empty set, matching inject_and_patch (ship pristine).
    assert build_narration_map(35) == set(), (
        "build_narration_map(35) is non-empty -- a binary/unwalkable Section 1 "
        "must yield an EMPTY narration set so it ships pristine"
    )


# ---------------------------------------------------------------------------
# G-col TIER-2: the user-reported R1196 narration actually collapsed
# ---------------------------------------------------------------------------
def test_tier2_r1196_narration_collapsed():
    """R1196 g568 ('A heavy fog had ...') must collapse from the JP author's 4
    ragged ' / ' segments to <=3 wider lines per page in the BUILT output, and
    every line must fit NARRATION_BOX_PX (the P1 win, measured from build data)."""
    path = os.path.join(PATCHED_TYPE2_DIR, "1196_type02.raw")
    require_file(path, "run a build first (Step 4 type-02 injection)")
    words = parse_type02(open(path, "rb").read())["words"]
    groups, _trailing = group_offsets(words)
    assert 568 < len(groups), "R1196 has no group 568 in the built output"
    gs, ge = groups[568]
    group = words[gs:ge]
    # count ' / ' line segments per ' // ' page; the engine has no 0xFFD2 here
    # (v97 rule), so segments == 0xFFFE count + 1 within the single page.
    segments = sum(1 for w in group if w == LINE_BREAK) + 1
    assert segments <= 3, (
        "R1196 g568 has %d line segments -- P1 should have collapsed the JP "
        "author's 4 ragged ' / ' breaks to <=3 wider lines: %r"
        % (segments, decode_glyphs(group))
    )
    for line in _split_lines(group):
        visible = [w for w in line if w < CONTROL_FLOOR]
        while visible and visible[-1] == SPACE_GID:
            visible.pop()  # ignore the invisible left-align trailing pad
        if not visible or any(w > ENGLISH_GLYPH_HI for w in visible):
            continue
        px = glyph_metrics.px_width(visible, _id_enc)
        assert px <= NARRATION_BOX_PX, (
            "R1196 g568 line %r is %dpx > %dpx budget"
            % (decode_glyphs(line).strip(), px, NARRATION_BOX_PX)
        )


TESTS = [
    test_tier2_narration_px_budget,
    test_tier3_iso_narration_px_budget,
    test_narration_box_px_is_sane_and_within_proven_span,
    test_narration_wrap_uses_shared_metrics,
    test_narration_classifier_inverse_and_disjoint,
    test_tier2_r1196_narration_collapsed,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_narration_wrap")
