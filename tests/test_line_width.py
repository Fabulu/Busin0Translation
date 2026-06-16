#!/usr/bin/env python3
"""
test_line_width.py -- on-screen line-width regression gate for type-2 text.

THE BUG THIS CATCHES (v89 overflow regression)
----------------------------------------------
build_v9 Step 4 encodes the English type-2 dialogue/narration by splitting each
translation on its explicit " / " (line break -> 0xFFFE) and " // " (page break
-> 0xFFD2) markers and glyph-encoding the rest.  In the v89 regression the Step-4
encoder did NOT word-wrap: any translated sentence with no explicit " / " was
emitted as ONE line of 100+ glyphs, far wider than the dialogue frame, so ~2604
lines clipped off the right edge on screen.  The fix word-wraps Step-4 text to a
fixed column count (build_v9 word_wrap(max_chars=18)).

This test re-derives, straight from the BUILD OUTPUT, the exact lines the engine
will draw and HARD-FAILs if any injected-English line is wider than the frame.
If word-wrap ever regresses (is removed, broken, or stops being applied to the
type-2 path) this gate fails instantly.

WHAT IS A "LINE"
----------------
For every patched type-02 Section-2 FFFF group, the group's glyph stream is split
on 0xFFFE (line break) and 0xFFD2 (page break) into LINES.  The VISIBLE width of
a line is the count of visible glyphs in it -- glyphs with id < 0xFB00.  Every
control / formatting / marker word (the 0xFBxx..0xFFxx block: choice markers
0xFFCx, page/line breaks, colour/speed opcodes, the 0xFFFF terminator) is id
>= 0xFB00 and is NOT counted.

WHAT IS GATED, WHAT IS EXEMPT
-----------------------------
Only lines whose visible glyphs are ALL ASCII-English (id <= ENGLISH_GLYPH_HI)
are gated -- those are precisely the lines build_v9's encoder produced from an
English translation, the v89 regression surface.  Exempt:

  * CHOICE groups (any 0xFFC0..0xFFCF marker) -- their option layout is a
    different, narrower frame and is governed by test_choice_groups.
  * lines that contain ANY non-ASCII (Japanese) glyph -- untranslated original
    text we never re-flowed; the engine lays the original out correctly and a
    full-width JP line is legitimately wider in glyph-count than 18.  Gating
    those would be ~1761 false positives.
  * KNOWN binary / non-text resources (build_v9's binary_resources list) and
    R1193 (its trailing narration is built by a separate Step-5 path with its
    own <=23-glyph line discipline, NOT the Step-4 word-wrap).
  * the trailing (post-last-FFFF) region -- group_offsets already drops it.
  * the NAME-ISLAND PREFIX of a name-island group's FIRST line.  inject_and_patch
    rebuilds a dialogue group as [name-label glyphs][dialogue] with NO 0xFFFE
    between the label prefix and the dialogue -- the label is drawn by a separate
    0x14 NAME box at runtime, NOT on the dialogue line.  Counting [label]+[first
    dialogue line] as one screen line over-reports the first line's width and
    yields ~280 false positives even on a correctly-wrapped build.  We re-derive
    the exact prefix length the patcher used (the patcher's own 0x14 clean-prefix
    bucketing, run on THIS blob's patched Section 1) and subtract it from the
    first line's visible-glyph count.  Only the first line is adjusted, and only
    for confirmed name-island groups; every later line and every non-name-island
    group is gated at full strength.

TIERS
-----
  TIER-2 : build/patched_type2/*.raw  (Skip if absent -- run a build first).
  TIER-3 : the freshest BUSIN0_EN_v*.iso, with a freshness guard so a stale ISO
           (older than the patched_type2 outputs) Skips instead of false-failing.

NOTE: until the concurrent Step-4 word-wrap fix is built into
build/patched_type2, TIER-2 legitimately FAILS -- it is correctly detecting the
un-wrapped state.  A fresh build with the wrap fix makes it pass.
"""

import glob
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (
    PATCHED_TYPE2_DIR,
    PackData,
    ROOT,
    Skip,
    decode_glyphs,
    default_iso_path,
    get_disasm,
    group_offsets,
    parse_type02,
    require_dir,
)

# The name-island detection re-uses the EXACT primitives the patcher itself uses
# to identify a name prefix: bucket the walked 0x14 records by group, then test
# whether a group's slices form a clean prefix partition.  Importing from the
# patcher keeps the test's notion of "name island" in lockstep with the build.
sys.path.insert(0, os.path.join(ROOT, "tools"))
from patch_section1_offsets import (  # noqa: E402
    _bucket_labels,
    _clean_prefix_len,
    parse_sec2_group_offsets,
)

# ---------------------------------------------------------------------------
# Thresholds / classification constants
# ---------------------------------------------------------------------------
# Hard ceiling on visible glyphs per on-screen line.  build_v9 wraps type-2 text
# at TYPE2_WRAP_WIDTH (20: the boxed-dialogue frame fits ~20 cells; narration is
# authored <=16).  Patch-12 (patch_exe.py) sets the per-glyph dialogue X-advance
# to 18px, so 20 glyphs fit within the boxed frame — width 20 packs dialogue
# tighter to reduce vertical overflow.  A uniform <=20 gate is the hard upper
# bound that catches the gross v89 clips while never tripping on a legitimately
# wrapped line.  Keep this in sync with build/build_v9.py's TYPE2_WRAP_WIDTH.
MAX_GLYPHS = 20

# Visible-glyph boundary: every control/formatting/marker word (0xFBxx..0xFFxx,
# incl. choice 0xFFCx, line break 0xFFFE, page break 0xFFD2, terminator 0xFFFF)
# is id >= 0xFB00.  A "visible" glyph is anything below this.
CONTROL_FLOOR = 0xFB00

# ASCII-English glyph ids run 0..94 (english_glyph_table maps every printable
# ASCII char into this range; build_v9.enc falls back to 31='?').  A line is an
# INJECTED-ENGLISH line iff all its visible glyphs are <= this -- only those are
# gated.  Lines with any higher (Japanese) glyph are untranslated and exempt.
ENGLISH_GLYPH_HI = 94

# Section-2 break / marker words.
LINE_BREAK = 0xFFFE
PAGE_BREAK = 0xFFD2
CHOICE_LO = 0xFFC0
CHOICE_HI = 0xFFCF

# Resources build_v9 treats as binary / non-text (its `binary_resources` list)
# plus R1193 (Step-5 trailing narration, separate line discipline).  Kept in
# sync with build/build_v9.py.  Width-gating these would be meaningless.
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


# ---------------------------------------------------------------------------
# Core: walk a parsed word stream and yield every over-wide injected-English line
# ---------------------------------------------------------------------------
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


def _name_island_prefix_lens(parsed):
    """
    Return {group_index: name_prefix_len} for every NAME-ISLAND group in this
    (already-patched) type-02 blob.

    A name-island group is one inject_and_patch rebuilt as
    [name-label glyphs][dialogue] with NO 0xFFFE between the label prefix and the
    dialogue.  The label glyphs are consumed by a separate 0x14 NAME box at
    runtime, so they are NOT part of the first on-screen dialogue line -- but the
    glyph stream has no break between them, so a naive split counts
    [label]+[first dialogue line] as one over-wide line.

    Detection mirrors the patcher EXACTLY: walk this blob's Section 1, bucket the
    walked 0x14 NAME/LABEL records by their (patched) target group, and keep a
    group iff its slices form a CLEAN PREFIX PARTITION (_clean_prefix_len) whose
    length is strictly inside the group.  That last condition is the same guard
    inject_and_patch uses (`prefix_len >= len(group)` -> label table, left
    verbatim): a prefix that spans the whole group is a label TABLE, not a
    dialogue name-island, so it is NOT exempted here.

    The walk is best-effort: if Section 1 cannot be walked (no opcode table, or a
    non-walkable blob) we return {} and gate the file at full strength.
    """
    try:
        sd = get_disasm()  # raises Skip when the opcode table is absent
    except Skip:
        return {}
    sec1 = parsed["sec1"]
    ok, instrs = sd.walk(sec1)
    if not ok:
        return {}  # un-walkable Section 1 -- no name-island exemption, gate fully
    recs = sd.extract_records(sec1, instrs)
    if not recs["label"]:
        return {}

    # parse_sec2_group_offsets wants the raw Section-2 BYTES; rebuild them from
    # the parsed BE-u16 word tuple so we re-use the patcher's own group splitter.
    sec2_bytes = struct.pack(">%dH" % len(parsed["words"]), *parsed["words"])
    groups, trailing_start = parse_sec2_group_offsets(sec2_bytes)
    per_group, _trailing = _bucket_labels(recs["label"], groups, trailing_start)

    prefixes = {}
    for gi, slices in per_group.items():
        plen = _clean_prefix_len(slices)
        if plen is None:
            continue
        gs, ge = groups[gi]
        # Strictly inside the group => genuine dialogue name-island prefix.
        # plen >= group length => label table (kept verbatim) -- do NOT exempt.
        if 0 < plen < (ge - gs):
            prefixes[gi] = plen
    return prefixes


def _line_offenders(parsed, res):
    """
    Yield (res, group_index, width, decoded_text) for every injected-English
    line in this parsed type-02 blob whose visible width exceeds MAX_GLYPHS.

    group_offsets drops the trailing region for us.  Choice groups are skipped
    whole.  For a name-island group (see _name_island_prefix_lens) the runtime
    name-label prefix is subtracted from the FIRST line's visible count only --
    that prefix is drawn by a separate 0x14 NAME box, not on the dialogue line.
    """
    words = parsed["words"]
    groups, _trailing = group_offsets(words)
    name_prefix = _name_island_prefix_lens(parsed)
    for gi, (gs, ge) in enumerate(groups):
        group = words[gs:ge]
        if _is_choice_group(group):
            continue  # choice option layout is exempt
        prefix_len = name_prefix.get(gi, 0)
        for li, line in enumerate(_split_lines(group)):
            visible = [w for w in line if w < CONTROL_FLOOR]
            # Discount the name-label prefix from the FIRST line of a name-island
            # group: those leading <0xFB00 glyphs render in the 0x14 NAME box, not
            # on this dialogue line.  Only the first line carries the prefix (the
            # label has no 0xFFFE), so li>0 and every other group are untouched.
            width = len(visible)
            if li == 0 and prefix_len:
                width = max(0, width - prefix_len)
            if width == 0:
                continue
            # Gate ONLY injected-English lines (all visible glyphs ASCII).  The
            # name-prefix glyphs are themselves ASCII English labels, so the
            # post-prefix remainder is still all-English -- the all-ASCII test on
            # the full `visible` set is the correct classifier.
            if any(w > ENGLISH_GLYPH_HI for w in visible):
                continue
            if width > MAX_GLYPHS:
                yield (res, gi, width, decode_glyphs(line).strip())


def _format_offenders(offenders, limit=12):
    offenders = sorted(offenders, key=lambda o: o[2], reverse=True)
    head = offenders[:limit]
    return "; ".join(
        "R%d g%d w=%d %r" % (res, gi, w, txt[:48])
        for (res, gi, w, txt) in head
    )


# ---------------------------------------------------------------------------
# TIER-2: build/patched_type2/*.raw
# ---------------------------------------------------------------------------
def test_tier2_patched_type2_line_width():
    """Every injected-English line in build/patched_type2 fits within MAX_GLYPHS
    visible glyphs.  HARD FAIL with the worst offenders on overflow."""
    require_dir(PATCHED_TYPE2_DIR, "run a build first (Step 4 type-02 injection)")
    files = sorted(glob.glob(os.path.join(PATCHED_TYPE2_DIR, "*.raw")))
    if not files:
        raise Skip("no *.raw in build/patched_type2 -- run a build first")

    offenders = []
    checked = 0
    for path in files:
        res = int(os.path.basename(path)[:4])
        if res in EXEMPT_RESOURCES:
            continue
        try:
            p = parse_type02(open(path, "rb").read())
        except Exception:
            continue  # not a parseable type-02 blob -- not our surface
        checked += 1
        offenders.extend(_line_offenders(p, res))

    if checked == 0:
        raise Skip("no parseable type-02 resources in build/patched_type2")
    assert not offenders, (
        "%d injected-English line(s) exceed %d glyphs (v89 word-wrap regression). "
        "Worst: %s"
        % (len(offenders), MAX_GLYPHS, _format_offenders(offenders))
    )


# ---------------------------------------------------------------------------
# TIER-3: freshest ISO, with a freshness guard
# ---------------------------------------------------------------------------
def _newest_iso():
    """Newest BUSIN0_EN_v*.iso (BUSIN_ISO / default first), or '' if none."""
    env = default_iso_path()
    if os.path.isfile(env):
        candidates = [env]
    else:
        candidates = []
    candidates += glob.glob(os.path.join(ROOT, "build", "BUSIN0_EN_v*.iso"))
    candidates = [c for c in candidates if os.path.isfile(c)]
    if not candidates:
        return ""
    return max(candidates, key=os.path.getmtime)


def test_tier3_iso_line_width():
    """Same line-width gate against the type-02 resources as they live in the
    freshest built PACKDATA (the real-PS2 path).  Freshness-guarded: Skip when
    the ISO predates the patched_type2 outputs so a stale ISO never false-fails
    (mirrors test_v86_strips._require_fresh_iso)."""
    iso = _newest_iso()
    if not iso:
        raise Skip("no BUSIN0_EN_v*.iso present (set BUSIN_ISO or build)")

    # Freshness guard: the ISO must be at least as new as the newest patched
    # type-02 output, else no fresh ISO has been built since Step 4 last ran.
    patched = glob.glob(os.path.join(PATCHED_TYPE2_DIR, "*.raw"))
    if patched:
        newest_patched = max(os.path.getmtime(p) for p in patched)
        if os.path.getmtime(iso) < newest_patched:
            raise Skip(
                "ISO %s predates build/patched_type2 -- no fresh ISO built "
                "since Step 4 last ran" % os.path.basename(iso)
            )

    # Which resources to check from the ISO: the type-02 resources that were
    # patched this run (so we exercise exactly the injected surface), minus the
    # exempt set.  Fall back to nothing if patched_type2 is absent.
    patched_resources = sorted(
        int(os.path.basename(p)[:4]) for p in patched
    )
    targets = [r for r in patched_resources if r not in EXEMPT_RESOURCES]
    if not targets:
        raise Skip("no patched type-02 resources to cross-check against the ISO")

    pack = PackData(iso)  # raises Skip itself if the ISO has no PACKDATA
    offenders = []
    checked = 0
    try:
        for res in targets:
            try:
                data, type_code = pack.extract(res)
                if type_code != 2:
                    continue
                p = parse_type02(data)
            except Exception:
                continue
            checked += 1
            offenders.extend(_line_offenders(p, res))
    finally:
        pack.close()

    if checked == 0:
        raise Skip("no type-02 resources resolved from the ISO")
    assert not offenders, (
        "%d injected-English line(s) exceed %d glyphs in the ISO PACKDATA "
        "(v89 word-wrap regression on the real-PS2 path). Worst: %s"
        % (len(offenders), MAX_GLYPHS, _format_offenders(offenders))
    )


TESTS = [
    test_tier2_patched_type2_line_width,
    test_tier3_iso_line_width,
]

if __name__ == "__main__":
    from _helpers import main_exit

    main_exit(TESTS, "test_line_width")
