#!/usr/bin/env python3
"""
test_r2100_metrics_source.py -- lock the R2100 metrics JSON to its GROUND TRUTH.

v158 fixed the game-wide "Ge nde r" per-letter unevenness by discovering that
the chargen/request renderers (0x307510 / 0x3A2EF0, Patches 26/27/29/31) draw
the R2100 sub0 UPRIGHT 16px font, NOT the oblique 24px R1188 font -- and by
replacing the wrong R1188 tables with new ones (ADV2/LSH2, v170 relocated to the
dead libgraph pad @0x4AF338 / 0x4AF398, 95B each) derived from
data/r2100_ascii_metrics.json.

The existing gates (test_glyph_metrics_sync, test_chargen_lsh_patch29/31) pin
the EXE bytes against tools/glyph_metrics.py, but NOTHING pinned the metrics
JSON itself against its physical source: the pristine R2100 sub0 atlas pixels
in extracted/PACKDATA.DIG.  A silent re-measure from the WRONG atlas or the
wrong deswizzle geometry (the exact mistake that caused the defect) would flow
straight through every downstream gate.  This module closes that hole:

  T1 (TIER-2, SKIP when extracted/PACKDATA.DIG absent): re-measure all 95 ASCII
     glyph ink boxes from the pristine atlas (R2100 sub0 pixel data at
     17*2048 + 64 + 0x4C0, 32768 bytes, deswizzled 256x256 dbw_ct32=128;
     16x16-px cells, 16 columns, gid = char-0x20 = cell index) and require
     byte-exact equality with data/r2100_ascii_metrics.json.
  T2 (static): glyph_metrics.ADV2/LEFTSHIFT2 match the documented derivation
     from the JSON (clamp(ink_width+GAP2, 4, 15) / max(0, ink_left)).
  T3 (static): the 256-byte EXE table layouts (ADV2 tail 0x12, LSH2 tail 0).
  T4 (static): the known-symptom glyphs 'e'/'f' carry the measured values that
     actually fixed the defect -- a silent re-measure fails LOUDLY here.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (  # noqa: E402  (path insert first)
    DATA_DIR,
    ROOT,
    main_exit,
    require_file,
)

import glyph_metrics  # noqa: E402  (TOOLS_DIR put on sys.path by _helpers)

# ── R2100 sub0 ground-truth geometry (verified against PACKDATA Jun/Jul 2026) ─
PACKDATA = os.path.join(ROOT, "extracted", "PACKDATA.DIG")
METRICS_JSON = os.path.join(DATA_DIR, "r2100_ascii_metrics.json")
# R2100 lives in the PACKDATA header gap (sectors 17-84); sub0's PSMT4 pixel
# block starts 64 + 0x4C0 bytes into sector 17 and is 256*256/2 = 32768 bytes.
SUB0_PIXEL_OFF = 17 * 2048 + 64 + 0x4C0
SUB0_PIXEL_LEN = 32768
ATLAS_W = ATLAS_H = 256   # nibbles after deswizzle; value 15 = background
DBW_CT32 = 128            # R2100 deswizzles cleanly at 256x256 dbw_ct32=128
CELL = 16                 # 16x16-pixel cells, 16 columns; gid = row*16 + col
BG = 15                   # background nibble; anything != 15 is ink


def _load_metrics_json():
    path = require_file(METRICS_JSON, "R2100 metrics ground-truth copy")
    m = json.load(open(path, encoding="utf-8"))
    assert isinstance(m, list) and len(m) == 95, (
        "r2100_ascii_metrics.json must be a 95-element list (gid 0..94), got %s/%s"
        % (type(m).__name__, len(m) if hasattr(m, "__len__") else "?")
    )
    return m


def _measure_ink_box(pixels, gid):
    """Ink box of the 16x16 cell for gid: (ink_left, ink_right, ink_width).

    Empty cell (space gid0, '@' gid32, '`' gid64) -> (-1, -1, 0).
    """
    row, col = gid // CELL, gid % CELL
    y0, x0 = row * CELL, col * CELL
    ink_cols = [
        x for x in range(CELL)
        if any(pixels[(y0 + y) * ATLAS_W + x0 + x] != BG for y in range(CELL))
    ]
    if not ink_cols:
        return (-1, -1, 0)
    return (min(ink_cols), max(ink_cols), max(ink_cols) - min(ink_cols) + 1)


def test_t1_json_matches_pristine_atlas():
    """TIER-2: re-measure all 95 glyphs from the pristine R2100 sub0 atlas and
    require byte-exact equality with data/r2100_ascii_metrics.json.  This is
    the wrong-font/wrong-geometry regression tripwire."""
    require_file(PACKDATA, "pristine R2100 atlas ground truth")
    m = _load_metrics_json()

    from psmt4_deswizzle import deswizzle_psmt4  # TOOLS_DIR on sys.path

    with open(PACKDATA, "rb") as fh:
        fh.seek(SUB0_PIXEL_OFF)
        data = fh.read(SUB0_PIXEL_LEN)
    assert len(data) == SUB0_PIXEL_LEN, (
        "short read of R2100 sub0 pixels: %d/%d bytes @0x%X -- PACKDATA truncated?"
        % (len(data), SUB0_PIXEL_LEN, SUB0_PIXEL_OFF)
    )
    pixels = deswizzle_psmt4(data, ATLAS_W, ATLAS_H, dbw_ct32=DBW_CT32)

    mismatches = []
    for gid in range(95):
        got = _measure_ink_box(pixels, gid)
        e = m[gid]
        want = (e["ink_left"], e["ink_right"], e["ink_width"])
        if got != want:
            mismatches.append(
                "gid %d (%r): atlas (l,r,w)=%s but JSON says %s"
                % (gid, e.get("char", chr(0x20 + gid)), got, want)
            )
    assert not mismatches, (
        "r2100_ascii_metrics.json DESYNCED from the pristine R2100 sub0 atlas "
        "(%d/95 glyphs) -- someone re-measured from the wrong atlas/geometry or "
        "hand-edited the JSON. First: %s" % (len(mismatches), mismatches[0])
    )


def test_t2_adv2_lsh2_derivation():
    """Static: ADV2/LEFTSHIFT2 match the documented formula from the JSON:
    ADV2[g] = SPACE_ADV2 if g==0 or ink_width==0 else clamp(iw+GAP2, 4, 15);
    LEFTSHIFT2[g] = max(0, ink_left)."""
    m = _load_metrics_json()
    gap2 = glyph_metrics.GAP2
    space_adv2 = glyph_metrics.SPACE_ADV2
    for g in range(95):
        iw = m[g]["ink_width"]
        il = m[g]["ink_left"]
        want_adv = space_adv2 if (g == 0 or iw == 0) else max(4, min(15, iw + gap2))
        want_lsh = max(0, il)
        assert glyph_metrics.ADV2[g] == want_adv, (
            "ADV2[%d] = %d but the formula from r2100_ascii_metrics.json "
            "(iw=%d, GAP2=%d, SPACE_ADV2=%d) gives %d -- glyph_metrics desynced "
            "from its source JSON" % (g, glyph_metrics.ADV2[g], iw, gap2,
                                      space_adv2, want_adv)
        )
        assert glyph_metrics.LEFTSHIFT2[g] == want_lsh, (
            "LEFTSHIFT2[%d] = %d but max(0, ink_left=%d) = %d"
            % (g, glyph_metrics.LEFTSHIFT2[g], il, want_lsh)
        )


def test_t3_exe_table_layouts():
    """Static: adv2_table_256() = ADV2 @0..94 + 0x12 tail; leftshift2_table_256()
    = LEFTSHIFT2 @0..94 + zero tail; both exactly 256 bytes (the shapes the
    Patch 26/27/29/31 caves index)."""
    adv_t = glyph_metrics.adv2_table_256()
    lsh_t = glyph_metrics.leftshift2_table_256()
    assert len(adv_t) == 256, "adv2_table_256() must be 256 bytes, got %d" % len(adv_t)
    assert len(lsh_t) == 256, (
        "leftshift2_table_256() must be 256 bytes, got %d" % len(lsh_t)
    )
    for g in range(95):
        assert adv_t[g] == glyph_metrics.ADV2[g], (
            "adv2_table_256()[%d] = %d != ADV2[%d] = %d"
            % (g, adv_t[g], g, glyph_metrics.ADV2[g])
        )
        assert lsh_t[g] == glyph_metrics.LEFTSHIFT2[g], (
            "leftshift2_table_256()[%d] = %d != LEFTSHIFT2[%d] = %d"
            % (g, lsh_t[g], g, glyph_metrics.LEFTSHIFT2[g])
        )
    for i in range(95, 256):
        assert adv_t[i] == 0x12, (
            "adv2_table_256()[%d] = 0x%02X, tail must stay 0x12 (kanji low-byte "
            "reads through P27's unguarded lbu keep pre-v158 advance)"
            % (i, adv_t[i])
        )
        assert lsh_t[i] == 0, (
            "leftshift2_table_256()[%d] = %d, tail must stay 0 (non-ASCII "
            "subtracts nothing)" % (i, lsh_t[i])
        )


def test_t4_known_symptom_glyphs():
    """Static: pin the glyphs that DIAGNOSED the "Ge nde r" defect.  From the
    pristine atlas: 'e' (gid 69) ink box (4,10,7) -> ADV2 = 7+GAP2 = 9,
    LSH2 = 4; 'f' (gid 70) ink box (5,10,6) -> ADV2 = 8, LSH2 = 5.  Under the
    old (wrong) R1188 tables these glyphs got 24px-font metrics, producing the
    gappy "Ge nde r" spacing; the values below are the measured R2100 numbers
    that fixed it.  If a re-measure silently changes them, fail loudly."""
    checks = [
        ("ADV2[69] ('e')", glyph_metrics.ADV2[69], 9),
        ("LEFTSHIFT2[69] ('e')", glyph_metrics.LEFTSHIFT2[69], 4),
        ("ADV2[70] ('f')", glyph_metrics.ADV2[70], 8),
        ("LEFTSHIFT2[70] ('f')", glyph_metrics.LEFTSHIFT2[70], 5),
    ]
    for name, got, want in checks:
        assert got == want, (
            "%s = %d, expected %d -- these are the v158 measured values that "
            "fixed the 'Ge nde r' chargen spacing defect; a changed value means "
            "the metrics were silently re-measured (wrong atlas/geometry?) and "
            "the on-screen spacing WILL regress" % (name, got, want)
        )


TESTS = [
    test_t1_json_matches_pristine_atlas,
    test_t2_adv2_lsh2_derivation,
    test_t3_exe_table_layouts,
    test_t4_known_symptom_glyphs,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_r2100_metrics_source")
