#!/usr/bin/env python3
"""
test_pill_widen.py -- v180 item-name capsule widening (R2139 sub13 rec2 +
R2138 sub27 band re-ink) built-output gates.

The pill fix is data-only: tools/patch_pill_widen.py widens the capsule
geometry record from 192 to 256 and re-inks the sub27 box art so the right
cap sits at the new edge. These tests pin:

  1. Built R2139 differs from pristine ONLY in the w field of sub13 rec2
     (BE u32 @0x1228) and reads 256.
  2. Built R2138's sub27 texture, inside the box band rows [136,200), differs
     from pristine ONLY at x >= 176 (the re-ink), and the relocated right
     border has a solid vertical run at column 248.
  3. The band's pristine left cap (double line at x0..6) is untouched.

SKIP (not FAIL) when the build outputs are absent.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (
    PACKDATA_RES_DIR,
    RAW_DIR,
    Skip,
    main_exit,
    require_file,
)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools"))

R2139_BUILT = os.path.join(PACKDATA_RES_DIR, "2139_type15.raw")
R2139_PRISTINE = os.path.join(RAW_DIR, "2139_type15.raw")
R2138_BUILT = os.path.join(PACKDATA_RES_DIR, "2138_type29.raw")
R2138_PRISTINE = os.path.join(RAW_DIR, "2138_type29.raw")

REC_OFF = 0x1220          # R2139 sub13 rec2 (BE u32 u,v,w,h,page)
SUB27_OFF = 0x16D4F0
SUB27_PIXEL_OFF = 0x740
SUB27_PIXEL_SIZE = 32768
TEX_W = 256
BAND_Y0, BAND_Y1 = 136, 200
DST_X0 = 176


def _deswizzled_sub27(path):
    from psmt4_deswizzle import deswizzle_psmt4
    data = open(path, "rb").read()
    lo = SUB27_OFF + SUB27_PIXEL_OFF
    pix = data[lo:lo + SUB27_PIXEL_SIZE]
    return deswizzle_psmt4(pix, TEX_W, TEX_W, bw_psmt4=256, dbw_ct32=128)


def test_r2139_record_widened():
    require_file(R2139_BUILT, "pill-widen build output")
    require_file(R2139_PRISTINE, "pristine extract")
    built = open(R2139_BUILT, "rb").read()
    pristine = open(R2139_PRISTINE, "rb").read()
    assert len(built) == len(pristine) == 6144, "R2139 size changed"
    u, v, w, h, page = struct.unpack_from(">5I", built, REC_OFF)
    assert (u, v, h, page) == (0, 136, 64, 3), (
        "sub13 rec2 fields moved: u=%d v=%d h=%d page=%d" % (u, v, h, page))
    assert w == 256, "capsule record width is %d, expected 256" % w
    diffs = [i for i, (a, b) in enumerate(zip(pristine, built)) if a != b]
    assert diffs, "built R2139 is byte-identical to pristine (patch missing)"
    assert all(REC_OFF + 8 <= i < REC_OFF + 12 for i in diffs), (
        "R2139 diff containment violated: unexpected bytes at %s"
        % [hex(i) for i in diffs[:8]])


def test_sub27_band_reink_contained():
    require_file(R2138_BUILT, "R2138 build output")
    require_file(R2138_PRISTINE, "pristine extract")
    built = _deswizzled_sub27(R2138_BUILT)
    pristine = _deswizzled_sub27(R2138_PRISTINE)
    outside = 0
    changed = 0
    for y in range(BAND_Y0, BAND_Y1):
        for x in range(TEX_W):
            i = y * TEX_W + x
            if built[i] != pristine[i]:
                changed += 1
                if x < DST_X0:
                    outside += 1
    assert changed > 0, (
        "sub27 band has NO pixel diffs -- the pill re-ink did not land")
    assert outside == 0, (
        "%d changed band pixels at x<%d -- re-ink leaked into the original "
        "capsule art" % (outside, DST_X0))


def test_sub27_right_border_relocated():
    require_file(R2138_BUILT, "R2138 build output")
    built = _deswizzled_sub27(R2138_BUILT)
    ink = sum(1 for y in range(BAND_Y0, BAND_Y1)
              if built[y * TEX_W + 248] != 0)
    assert ink >= 40, (
        "column 248 has only %d ink rows in the band -- relocated right "
        "border missing" % ink)


def test_sub27_left_cap_pristine():
    require_file(R2138_BUILT, "R2138 build output")
    require_file(R2138_PRISTINE, "pristine extract")
    built = _deswizzled_sub27(R2138_BUILT)
    pristine = _deswizzled_sub27(R2138_PRISTINE)
    for y in range(BAND_Y0, BAND_Y1):
        for x in range(0, 16):
            i = y * TEX_W + x
            assert built[i] == pristine[i], (
                "left cap pixel changed at (%d,%d)" % (x, y))


TESTS = [
    test_r2139_record_widened,
    test_sub27_band_reink_contained,
    test_sub27_right_border_relocated,
    test_sub27_left_cap_pristine,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_pill_widen")
