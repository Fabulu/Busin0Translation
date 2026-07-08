#!/usr/bin/env python3
"""
test_banner_widget_pristine.py -- chargen white-banner regression gate (v179).

The v175-v178 white-banner regression was caused by a blind EXE patch that
rewrote the immediate at VA 0x13F688 (addiu a1,zero,185) believing it was a
pill WIDTH.  It is the MIDDLE-SEGMENT TILE ID of the 3-part stretchable box
widget: the function at ~0x13F5F0 issues three `jal 0x14DF30` draws with
a1 = 0xB8/0xB9/0xBA (left cap / middle / right cap); the real width is the
caller-computed s0 on the stack, and the middle draw is skipped via `blez`
when s0 <= 0.  Patching the id made the middle strip reference a wrong tile
-> banner middle vanished while both caps kept drawing.
Post-mortem: build/BANNER_PROBLEM_HANDOFF.md ("SOLVED" section).

These tests pin, in the BUILT EXE (build/SLPM_653.78_patched):

  1. The three tile-id immediates (0xB8/0xB9/0xBA) ship pristine.
  2. The three widget draw calls still target 0x14DF30.
  3. The entire widget caller span 0x13F5F0..0x13F73C is byte-identical to
     pristine (no future patch may land inside this function).
  4. The shop-module tile-variant selector at 0x170EB4..0x170EC8 (the OTHER
     place immediates 185-188 appear as tile ids -- a natural false target
     for any future "grep for an immediate" patch) ships pristine.

Every expectation is also asserted against the PRISTINE EXE first, so the
test screams if the addresses ever drift rather than silently passing.

SKIP (not FAIL) when build outputs are absent.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import main_exit, require_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRISTINE_EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")


def _fo(va):
    return va - 0x100000 + 0x80


def _word(data, va):
    return struct.unpack_from("<I", data, _fo(va))[0]


def _addiu(rt, imm):
    # addiu $rt, $zero, imm
    return 0x24000000 | (rt << 16) | (imm & 0xFFFF)


def _jal(target):
    return 0x0C000000 | (target >> 2)


# (va, expected word, meaning)
BANNER_TILE_IMMS = [
    (0x13F620, _addiu(5, 0xB8), "left-cap tile id 184 (addiu a1,zero,0xB8)"),
    (0x13F688, _addiu(5, 0xB9), "MIDDLE tile id 185 (the v175-v178 regression site)"),
    (0x13F700, _addiu(5, 0xBA), "right-cap tile id 186 (addiu a1,zero,0xBA)"),
]

WIDGET_DRAW_CALLS = [0x13F63C, 0x13F6A4, 0x13F708]
WIDGET_DRAW_TARGET = 0x14DF30

WIDGET_SPAN = (0x13F5F0, 0x13F73C)

SHOP_SELECTOR_IMMS = [
    (0x170EB4, _addiu(14, 0xBC), "shop variant tile id 188 (addiu t6,zero,0xBC)"),
    (0x170EBC, _addiu(6, 0xBB), "shop variant tile id 187 (addiu a2,zero,0xBB)"),
    (0x170EC0, _addiu(14, 0xBA), "shop variant tile id 186 (addiu t6,zero,0xBA)"),
    (0x170EC4, _addiu(6, 0xB9), "shop variant tile id 185 (addiu a2,zero,0xB9)"),
]


def _load():
    require_file(PRISTINE_EXE, "pristine EXE extract")
    require_file(PATCHED_EXE, "patched EXE build output")
    pristine = open(PRISTINE_EXE, "rb").read()
    patched = open(PATCHED_EXE, "rb").read()
    return pristine, patched


def _check_words(pristine, patched, sites, what):
    for va, expect, meaning in sites:
        pw = _word(pristine, va)
        assert pw == expect, (
            "%s: PRISTINE word @VA 0x%06X is 0x%08X, expected 0x%08X (%s) -- "
            "address drift? fix the test's site list before trusting it"
            % (what, va, pw, expect, meaning)
        )
        bw = _word(patched, va)
        assert bw == expect, (
            "%s: BUILT EXE word @VA 0x%06X is 0x%08X, expected pristine "
            "0x%08X (%s) -- a patch re-landed on a banner/shop tile id; "
            "this is the exact v175-v178 white-banner regression class"
            % (what, va, bw, expect, meaning)
        )


def test_banner_tile_immediates_pristine():
    pristine, patched = _load()
    _check_words(pristine, patched, BANNER_TILE_IMMS, "banner tile ids")


def test_banner_widget_draw_calls_intact():
    pristine, patched = _load()
    expect = _jal(WIDGET_DRAW_TARGET)
    sites = [(va, expect, "jal 0x14DF30 (3-part box segment draw)")
             for va in WIDGET_DRAW_CALLS]
    _check_words(pristine, patched, sites, "banner widget draw calls")


def test_banner_widget_span_byte_identical():
    pristine, patched = _load()
    lo, hi = WIDGET_SPAN
    a = pristine[_fo(lo):_fo(hi)]
    b = patched[_fo(lo):_fo(hi)]
    if a != b:
        first = next(i for i in range(len(a)) if a[i] != b[i])
        raise AssertionError(
            "banner widget span VA 0x%06X..0x%06X differs from pristine, "
            "first diff @VA 0x%06X (pristine %02X != built %02X) -- no patch "
            "may land inside the 3-part banner widget caller"
            % (lo, hi, lo + first, a[first], b[first])
        )


def test_shop_variant_selector_pristine():
    pristine, patched = _load()
    _check_words(pristine, patched, SHOP_SELECTOR_IMMS, "shop tile selector")


TESTS = [
    test_banner_tile_immediates_pristine,
    test_banner_widget_draw_calls_intact,
    test_banner_widget_span_byte_identical,
    test_shop_variant_selector_pristine,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_banner_widget_pristine")
