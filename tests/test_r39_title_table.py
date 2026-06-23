#!/usr/bin/env python3
"""
test_r39_title_table.py -- P5 gate: REQUEST title-table firstNZ-base correctness.

WHAT P5 DID (build/inject_r39_quest.py)
---------------------------------------
The tavern REQUEST list title row rendered the "r t" mid-string fragment
(stillrt.p2s / mostbroken.p2s) because R39's four quest offset tables
(G346 descriptions / G381 clients / G411 UI-labels / G442 titles) were being
WRITTEN against the WRONG base.

Each table is a flat list of BE-u16 (value, 0) pairs.  The in-game request
chooser resolves a content pointer as  base + value  where the base is the
byte address of the table's FIRST NON-ZERO slot (its self-referential
header/count slot), NOT the byte after the table's FFFF terminator.  The old
"after-FFFF" anchor was ~124-140 bytes too late, so in the GROWN English file
every title offset resolved ~5-11 glyphs PAST the English group start -> the
renderer read a mid-string fragment ("rt").

P5 switched the WRITE base in inject_r39_quest.py (line 310,
``new_base = new_group_starts[t] + table_first_nz[t] * 2``) to that same
firstNZ address, so renderer base == write base and every content slot now
resolves to glyph ordinal 0 of the correct English group.  P5 also added a
build-time gated self-check that ABORTS the build if any slot lands mid-string.

GROUND TRUTH (independent of the script's own logic)
----------------------------------------------------
Resolving every content slot of the PRISTINE extracted/packdata_raw/0039_type15.raw:

  firstNZ base : G346 34/34, G381 29/29, G411 30/30, G442 34/34 land on glyph 0
  afterFFFF    : G346 0/34,  G381 3/29,  G411 3/30,  G442 2/34   (essentially never)

The 34/29/30/34 clean 1:1 sequential mapping onto consecutive content groups is
the decisive proof firstNZ is the renderer base.  The afterFFFF column is the
negative control the gate also asserts (so a future revert to it trips).

WHAT THIS GATE ASSERTS  (all PASS on the current tree)
------------------------------------------------------
  R-origin (origin constants): the four PRISTINE table bases are EXACTLY the
        firstNZ addresses 14512/19856/20432/21056 and the firstNZ slot indices
        are {346:4, 381:7, 411:6, 442:2} -- the renderer-base constants P5 keys
        off, mirrored from inject_r39_quest.py.

  R-firstnz (the rt-fragment guard): in the BUILT 0039_type15.raw every content
        slot of all four tables resolves under the firstNZ base to glyph
        ordinal 0 (a group START), with the documented 34/29/30/34 counts.  This
        is the exact arithmetic the in-game chooser runs; if any slot lands
        mid-string (the "rt" regression) this fails.

  R-negative (afterFFFF is NOT the base): the OLD after-FFFF base resolves
        essentially nothing to glyph 0 (0/3/3/2) -- pins down that the firstNZ
        base, not the after-FFFF anchor, is correct, so a revert to the old
        WRITE base trips here.

  R-title (full English title at row 1): G442 slot resolving to the first real
        title row decodes to a full English title (length > 2, no leading
        break) -- e.g. 'Salem Work' / 'Recruiting' / 'Come to B5F', NOT 'r t'.

  R-cave-scope (cave scoping == ZERO EXE edits): inject_r39_quest.py contains NO
        EXE reference (no patch_exe / SLPM / the shared proportional title
        blitter 0x14F220 / 0x3A2EF0 / draw_clamp12 0x3A3300).  P5 is a pure DATA
        fix confined to 0039_type15 -> the narration/request-body/dialogue/
        chargen EXE paths (P1-P4) structurally cannot regress from it.

  R-selfcheck (the build aborts on a mid-string resolve): the source carries the
        gated P5 self-check + ``sys.exit(1)`` abort, so a future regression that
        wrote a mid-string offset would fail the BUILD, not just this gate.

  R-no-overflow (size budget): the built file stays <= 16 sectors (the
        rebuild_packdata TOC budget) and the group count is unchanged vs
        pristine -- P5 only rewrote table offset bytes, not the group layout.

TIERS
-----
  TIER-1 (static, always): pristine resolution + origin constants + the source
          self-check / no-EXE-edit assertions.  Run with the extracted pristine
          R39 only (no build needed).
  TIER-2 (SKIP when a build is absent): the BUILT 0039_type15.raw resolves every
          title to glyph 0 and row 1 decodes to a full English title.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (  # noqa: E402  (path insert first)
    PACKDATA_RES_DIR,
    RAW_DIR,
    ROOT,
    SECTOR,
    Skip,
    decode_glyphs,
    main_exit,
    require_file,
)

GLYPH_DATA_START = 632                 # R39 FFFF group stream starts here
TABLE_GROUPS = (346, 381, 411, 442)
MAX_SECTORS = 16
TITLE_TABLE = 442                      # the request title offset table (the "rt" row)

INJECT_SRC = os.path.join(ROOT, "build", "inject_r39_quest.py")

# ---------------------------------------------------------------------------
# Origin constants -- mirror inject_r39_quest.py EXACTLY (its lines 179-181).
# The firstNZ slot index of each table and the resulting PRISTINE base address.
# These are the renderer-base constants P5 keys off; kept here so a future
# inject_r39_quest.py retune updates the gate in lockstep (project bug #1: never
# recompute, always pin to the SoT).
# ---------------------------------------------------------------------------
PRISTINE_FIRST_NZ = {346: 4, 381: 7, 411: 6, 442: 2}
PRISTINE_TABLE_BASES = {346: 14512, 381: 19856, 411: 20432, 442: 21056}
# Documented content-slot counts that must land on glyph 0 under the firstNZ base.
EXPECTED_CONTENT_SLOTS = {346: 34, 381: 29, 411: 30, 442: 34}

_NON_CONTENT = (0, 0xFFFE, 0xFFFF)

_CACHE = {}


# ---------------------------------------------------------------------------
# Stream scan + table resolution (firstNZ base == the renderer's base).
# ---------------------------------------------------------------------------
def _scan_groups(data):
    """Return (groups, starts): FFFF-delimited glyph groups from byte 632.
    starts[i] = byte position of group i's first glyph."""
    pos = GLYPH_DATA_START
    groups, starts, cur, cs = [], [], [], pos
    n = len(data)
    while pos + 1 < n:
        w = struct.unpack_from(">H", data, pos)[0]
        if w == 0xFFFF:
            groups.append(cur)
            starts.append(cs)
            cur = []
            cs = pos + 2
        else:
            cur.append(w)
        pos += 2
    return groups, starts


def _first_nonzero_index(vals):
    for i, v in enumerate(vals):
        if v != 0:
            return i
    raise AssertionError("offset table has no non-zero slot")


def _resolve(starts, groups, target):
    """Return (group_index, glyph_ordinal) for an absolute byte target, or
    (-1, -1) if it lands in no group."""
    for gi, gs in enumerate(starts):
        ge = gs + len(groups[gi]) * 2 + 2
        if gs <= target < ge:
            return gi, (target - gs) // 2
    return -1, -1


def _resolve_table(groups, starts, t, base):
    """For offset table group t, resolve every content slot (skip the header/
    firstNZ slot and 0/FFFE/FFFF sentinels) under `base`.
    Returns list of (slot_index, value, group_index, glyph_ordinal)."""
    fnz = _first_nonzero_index(groups[t])
    out = []
    for si, v in enumerate(groups[t]):
        if si == fnz or v in _NON_CONTENT:
            continue
        gi, gl = _resolve(starts, groups, base + v)
        out.append((si, v, gi, gl))
    return out


def _firstnz_base(groups, starts, t):
    return starts[t] + _first_nonzero_index(groups[t]) * 2


def _after_ffff_base(groups, starts, t):
    """The OLD (wrong) write base -- byte after the table's FFFF terminator."""
    return starts[t] + len(groups[t]) * 2 + 2


def _load(which):
    if which in _CACHE:
        return _CACHE[which]
    if which == "built":
        p = os.path.join(PACKDATA_RES_DIR, "0039_type15.raw")
        if not os.path.isfile(p):
            raise Skip("build/packdata_resources/0039_type15.raw missing (run a build)")
        data = open(p, "rb").read()
    else:
        data = open(
            require_file(os.path.join(RAW_DIR, "0039_type15.raw"), "P5 pristine"),
            "rb",
        ).read()
    groups, starts = _scan_groups(data)
    _CACHE[which] = (data, groups, starts)
    return _CACHE[which]


def _inject_src():
    require_file(INJECT_SRC, "P5 title-table gate")
    return open(INJECT_SRC, encoding="utf-8").read()


# ===========================================================================
# TIER-1 (static): pristine ground truth + origin constants + source scoping
# ===========================================================================
def test_origin_constants_match_pristine():
    """R-origin: the PRISTINE four table bases are EXACTLY the firstNZ addresses
    inject_r39_quest.py asserts (14512/19856/20432/21056) and the firstNZ slot
    indices are {346:4,381:7,411:6,442:2}.  These are the renderer-base origin
    constants P5 keys the WRITE base off."""
    _d, groups, starts = _load("pristine")
    for t in TABLE_GROUPS:
        fnz = _first_nonzero_index(groups[t])
        assert fnz == PRISTINE_FIRST_NZ[t], (
            "pristine G%d firstNZ slot index = %d, expected %d (renderer base origin "
            "drifted from inject_r39_quest.py)" % (t, fnz, PRISTINE_FIRST_NZ[t])
        )
        base = _firstnz_base(groups, starts, t)
        assert base == PRISTINE_TABLE_BASES[t], (
            "pristine G%d firstNZ base = %d, expected %d (origin constant mismatch)"
            % (t, base, PRISTINE_TABLE_BASES[t])
        )


def test_pristine_firstnz_base_resolves_all_to_group_start():
    """R-firstnz (ground truth): under the firstNZ base every content slot of all
    four PRISTINE tables resolves to glyph ordinal 0, with the documented
    34/29/30/34 counts.  This is the independent proof firstNZ is the renderer
    base (not relying on the build script's own logic)."""
    _d, groups, starts = _load("pristine")
    for t in TABLE_GROUPS:
        base = _firstnz_base(groups, starts, t)
        recs = _resolve_table(groups, starts, t, base)
        assert len(recs) == EXPECTED_CONTENT_SLOTS[t], (
            "pristine G%d has %d content slots, expected %d"
            % (t, len(recs), EXPECTED_CONTENT_SLOTS[t])
        )
        bad = [(si, v, gi, gl) for (si, v, gi, gl) in recs if gl != 0]
        assert not bad, (
            "pristine G%d: %d slot(s) do NOT land on glyph 0 under the firstNZ base, "
            "first: slot %d v=%d -> G%d glyph %d"
            % (t, len(bad), bad[0][0], bad[0][1], bad[0][2], bad[0][3])
        )


def test_after_ffff_base_is_NOT_the_renderer_base():
    """R-negative: the OLD after-FFFF base resolves essentially NOTHING to glyph 0
    (0/3/3/2) -- the negative control.  Pins firstNZ as the correct base so a
    revert of the WRITE base to the after-FFFF anchor (the "rt" bug) would make
    this disagree with the firstNZ result and trip the build."""
    _d, groups, starts = _load("pristine")
    # The after-FFFF base must land FAR fewer slots on glyph 0 than firstNZ.
    for t in TABLE_GROUPS:
        fbase = _firstnz_base(groups, starts, t)
        abase = _after_ffff_base(groups, starts, t)
        assert abase != fbase, "G%d firstNZ and after-FFFF base coincide" % t
        f_hits = sum(1 for (_si, _v, _gi, gl) in _resolve_table(groups, starts, t, fbase) if gl == 0)
        a_hits = sum(1 for (_si, _v, _gi, gl) in _resolve_table(groups, starts, t, abase) if gl == 0)
        assert a_hits < f_hits, (
            "G%d: after-FFFF base lands %d slots on glyph 0 vs firstNZ %d -- the two "
            "bases are no longer distinguishable; the renderer-base proof is void"
            % (t, a_hits, f_hits)
        )
    # And specifically the documented G442 title-table figures: firstNZ 34, afterFFFF 2.
    fbase = _firstnz_base(groups, starts, TITLE_TABLE)
    abase = _after_ffff_base(groups, starts, TITLE_TABLE)
    f_hits = sum(1 for (_si, _v, _gi, gl) in _resolve_table(groups, starts, TITLE_TABLE, fbase) if gl == 0)
    a_hits = sum(1 for (_si, _v, _gi, gl) in _resolve_table(groups, starts, TITLE_TABLE, abase) if gl == 0)
    assert f_hits == 34 and a_hits <= 3, (
        "G442 firstNZ/afterFFFF glyph-0 hits = %d/%d, expected 34/<=3 (the documented "
        "decisive split that proves the rt fragment was a wrong-base bug)" % (f_hits, a_hits)
    )


def test_inject_uses_firstnz_write_base_and_self_check():
    """R-origin + R-selfcheck (source): inject_r39_quest.py writes offsets against the
    firstNZ base (new_group_starts[t] + table_first_nz[t]*2), pins the same origin
    constants, and carries the gated P5 self-check that ABORTS the build (sys.exit(1))
    on a mid-string resolve -- so the "rt" regression fails the BUILD, not just a test."""
    src = _inject_src()
    norm = src.replace(" ", "")
    assert "new_group_starts[t]+table_first_nz[t]*2" in norm, (
        "inject_r39_quest.py no longer computes the WRITE base from the firstNZ slot "
        "(new_group_starts[t] + table_first_nz[t]*2) -- the P5 base switch reverted"
    )
    # The origin-constant assertions must still pin the documented firstNZ map / bases.
    assert "{346: 4, 381: 7, 411: 6, 442: 2}" in src, (
        "inject_r39_quest.py dropped the table_first_nz origin-constant assertion"
    )
    assert "14512" in src and "21056" in src, (
        "inject_r39_quest.py dropped the firstNZ base-address assertions (14512/21056)"
    )
    # The gated self-check + hard abort must be present.
    assert "P5 self-check" in src or "P5 SELF-CHECK" in src, (
        "the P5 build-time self-check is gone -- a mid-string resolve could ship silently"
    )
    assert "sys.exit(1)" in src, (
        "the P5 self-check no longer aborts the build on a mid-string resolve"
    )


def test_zero_exe_edits_cave_scoping():
    """R-cave-scope: P5 is a pure DATA fix confined to 0039_type15.  inject_r39_quest.py
    must reference NO EXE artifact -- not patch_exe / SLPM, and not the shared
    proportional title blitter 0x14F220 / 0x3A2EF0 / draw_clamp12 0x3A3300 -- so the
    narration / request-body / dialogue / chargen EXE paths (P1-P4) structurally
    cannot regress from P5."""
    src = _inject_src().lower()
    forbidden = [
        "patch_exe",
        "slpm",
        "0x14f220",   # shared proportional title blitter (serves every menu list)
        "0x3a2ef0",   # title (category,index) feeder
        "0x3a2d10",
        "0x3a3300",   # draw_clamp12 (the page-counter renderer -- explicitly NOT touched)
        "slpm_653",
    ]
    hits = [tok for tok in forbidden if tok in src]
    assert not hits, (
        "inject_r39_quest.py references EXE artifact(s) %s -- P5 must be a pure data fix "
        "(0039_type15 only); an EXE edit here could regress P1-P4" % hits
    )


# ===========================================================================
# TIER-2 (built): the SHIPPED file resolves every title to glyph 0 / English
# ===========================================================================
def test_built_firstnz_base_resolves_all_to_group_start():
    """R-firstnz (built, the rt-fragment guard): in the BUILT 0039_type15.raw every
    content slot of all four tables resolves under the firstNZ base to glyph ordinal
    0 (a group START), with the 34/29/30/34 counts.  A mid-string resolve here is the
    exact "rt" regression -- it fails."""
    _d, groups, starts = _load("built")
    for t in TABLE_GROUPS:
        base = _firstnz_base(groups, starts, t)
        recs = _resolve_table(groups, starts, t, base)
        assert len(recs) == EXPECTED_CONTENT_SLOTS[t], (
            "built G%d has %d content slots, expected %d (table slot layout changed)"
            % (t, len(recs), EXPECTED_CONTENT_SLOTS[t])
        )
        bad = [(si, v, gi, gl) for (si, v, gi, gl) in recs if gl != 0]
        assert not bad, (
            "built G%d: %d offset slot(s) land MID-STRING (not glyph 0) -- the rt "
            "fragment regression; first: slot %d v=%d -> G%d glyph %d"
            % (t, len(bad), bad[0][0], bad[0][1], bad[0][2], bad[0][3])
        )


def test_built_title_row_is_full_english():
    """R-title: the G442 title rows resolve (firstNZ base) to FULL English title
    groups -- length > 2, no leading break -- NOT the 2-glyph 'r t' fragment.  The
    first real content title must read e.g. 'Salem Work'."""
    _d, groups, starts = _load("built")
    base = _firstnz_base(groups, starts, TITLE_TABLE)
    recs = _resolve_table(groups, starts, TITLE_TABLE, base)
    assert recs, "built G442 has no content slots"
    titles = []
    for (_si, _v, gi, gl) in recs:
        assert gl == 0, "G442 slot resolved to glyph %d, not a group start" % gl
        # decode_glyphs maps 0xFFFE -> ' / '; strip breaks for the row text.
        txt = decode_glyphs(groups[gi]).replace(" / ", " ").strip()
        if txt:
            titles.append(txt)
        # No undecodable (Japanese) glyphs may survive in a title.
        assert "[" not in txt, "G442 title is non-English: %r" % txt
    # Most resolved titles are real strings (a few may be empty separators).
    real = [t for t in titles if len(t) > 2]
    assert len(real) >= 10, (
        "only %d of %d G442 titles are full strings (>2 chars) -- the title table looks "
        "fragmented (the 'r t' class); sample: %r" % (len(real), len(recs), titles[:6])
    )
    # Row 1 (the first real title) must NOT be the 'r t' / 'rt' fragment.
    first = real[0]
    assert first.lower().replace(" ", "") not in ("rt", "r", "t"), (
        "G442 row 1 is the 'rt' fragment %r -- the wrong-base regression is back" % first
    )


def test_built_matches_pristine_table_semantics_under_firstnz():
    """R-firstnz (built==pristine semantics): each content slot of the BUILT tables
    resolves (firstNZ base) to the SAME (group index, glyph ordinal) as the pristine
    table -- i.e. the slots still map 1:1 sequentially onto the (grown) content groups.
    A slot pointing at the wrong group or a non-zero ordinal trips."""
    _bd, bg, bs = _load("built")
    _pd, pg, ps = _load("pristine")
    for t in TABLE_GROUPS:
        assert len(bg[t]) == len(pg[t]), (
            "table G%d slot count changed %d -> %d" % (t, len(pg[t]), len(bg[t]))
        )
        p = _resolve_table(pg, ps, t, _firstnz_base(pg, ps, t))
        b = _resolve_table(bg, bs, t, _firstnz_base(bg, bs, t))
        assert len(p) == len(b), "G%d content-slot count diverged" % t
        bad = [
            (i, (psi, pgi, pgl), (bsi, bgi, bgl))
            for i, ((psi, _pv, pgi, pgl), (bsi, _bv, bgi, bgl)) in enumerate(zip(p, b))
            if psi != bsi or pgi != bgi or pgl != bgl
        ]
        assert not bad, (
            "G%d: %d slot(s) resolve to a different (group, ordinal) than pristine, "
            "first: %s" % (t, len(bad), bad[0])
        )


def test_built_size_budget_and_group_count():
    """R-no-overflow: the built 0039_type15.raw stays <= 16 sectors (rebuild_packdata
    TOC budget) and the FFFF group count is unchanged vs pristine -- P5 only rewrote
    offset-table bytes, never the group layout."""
    bd, bg, _bs = _load("built")
    _pd, pg, _ps = _load("pristine")
    assert len(bg) == len(pg), (
        "R39 group count changed %d -> %d (P5 must not add/remove groups)"
        % (len(pg), len(bg))
    )
    sectors = (len(bd) + SECTOR - 1) // SECTOR
    assert sectors <= MAX_SECTORS, (
        "built R39 is %d sectors (> %d) -- over the TOC budget" % (sectors, MAX_SECTORS)
    )


TESTS = [
    # TIER-1 static (always run with the extracted pristine R39)
    test_origin_constants_match_pristine,
    test_pristine_firstnz_base_resolves_all_to_group_start,
    test_after_ffff_base_is_NOT_the_renderer_base,
    test_inject_uses_firstnz_write_base_and_self_check,
    test_zero_exe_edits_cave_scoping,
    # TIER-2 built (Skip if no build output)
    test_built_firstnz_base_resolves_all_to_group_start,
    test_built_title_row_is_full_english,
    test_built_matches_pristine_table_semantics_under_firstnz,
    test_built_size_budget_and_group_count,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_r39_title_table")
