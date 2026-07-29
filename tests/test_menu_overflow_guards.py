#!/usr/bin/env python3
"""
test_menu_overflow_guards.py -- pins the menu/UI overflow tripwires.

Background: a 2026-07-29 audit found no menu text was overflowing, but ~6 build
sites SILENTLY shrink-to-floor-then-clip (or skip -> ship Japanese) on overflow,
with no assert. That's why the overflow class kept recurring: the build never
failed. This wave added a hard-overflow raise to each site (using the patcher's
own font metrics). These tests prove the tripwires FIRE, so they can't be
silently removed. (The current build passing is the other half: no live string
trips them -- verified output byte-identical to v201.)

The 4 render functions are tested functionally (an absurdly long string in a
tiny cell must raise regardless of exact font metrics). The patch_exe / R39
guards live inside larger build routines, so they're pinned at the source level.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (os.path.join(ROOT, "tools"), os.path.join(ROOT, "build")):
    if p not in sys.path:
        sys.path.insert(0, p)

# An absurd string that cannot fit a tiny cell at any font >= the floor.
LONG = "W" * 40
CELL = 16


def _raises(fn):
    try:
        fn()
    except (ValueError, SystemExit):
        return True
    return False


def test_strip_patcher_render_label_raises_on_overflow():
    import strip_patcher as sp
    font = sp.load_font(13)
    assert _raises(lambda: sp.render_label(LONG, CELL, CELL, font, 0, 15)), (
        "strip_patcher.render_label must raise on overflow, not silently clip")
    # a short label in a generous cell must NOT raise
    sp.render_label("OK", 64, 16, font, 0, 15)


def test_r2138_render_label_raises_on_overflow():
    import patch_r2138 as r
    font = r.load_font(12)
    assert _raises(lambda: r.render_label(LONG, CELL, CELL, font)), (
        "patch_r2138.render_label must raise on overflow")
    r.render_label("OK", 64, 16, font)


def test_facility_render_gray_raises_on_overflow():
    import patch_facility_strips as f
    assert _raises(lambda: f.render_gray(LONG, CELL, CELL, 13, "center")), (
        "patch_facility_strips.render_gray must raise on overflow")
    f.render_gray("OK", 64, 16, 13, "center")


def test_r1365_render_text_gray_raises_on_overflow():
    import patch_r1365 as r
    assert _raises(lambda: r.render_text_gray(LONG, CELL, CELL, 13)), (
        "patch_r1365.render_text_gray must raise on overflow")
    r.render_text_gray("OK", 64, 16, 13)


def test_patch_exe_overflow_is_fatal_not_skip():
    src = open(os.path.join(ROOT, "build", "patch_exe.py"), encoding="utf-8").read()
    assert "FATAL(patch_exe): string too long" in src, (
        "patch_exe.py must ABORT on a too-long string (was: SKIP -> ship JP)")
    # the old silent skip must be gone
    assert "new string too long" not in src, (
        "patch_exe.py still has the old silent 'too long' SKIP path")


def test_patch_r39_truncation_is_fatal():
    src = open(os.path.join(ROOT, "tools", "patch_r39_inline.py"),
               encoding="utf-8").read()
    assert "FATAL(patch_r39_inline)" in src, (
        "patch_r39_inline.py must ABORT on truncation, not warn-and-cut")


TESTS = [
    test_strip_patcher_render_label_raises_on_overflow,
    test_r2138_render_label_raises_on_overflow,
    test_facility_render_gray_raises_on_overflow,
    test_r1365_render_text_gray_raises_on_overflow,
    test_patch_exe_overflow_is_fatal_not_skip,
    test_patch_r39_truncation_is_fatal,
]

if __name__ == "__main__":
    for fn in TESTS:
        fn()
        print("PASS", fn.__name__)
    print("OK")
