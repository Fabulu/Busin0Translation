#!/usr/bin/env python3
"""
test_regress_harness.py -- unit-test the L1/L2 differential regression harness
(tools/p2s_extract.py + tools/regress_diff.py) against REAL ramdumps.

These are the two v171-regression nets:
  * png_tripwire  -> the post-chargen BLACK screen (Screenshot.png byte size).
  * pixel_diff    -> the garbled-chargen class (framebuffer divergence).
plus the guardrails (build_match / ee VA-direct) that make a diff trustworthy.

TIER: uses ramdumps/*.p2s as fixtures.  Every test SKIPs cleanly when its
fixture is absent, so a checkout without the (large, un-tracked) ramdumps still
runs green.  Fast: only the ~2909 B black frame and a couple of ee reads; the
heavy full-frame pixel scan is NOT run here (that lives in the self-test).
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, Skip, main_exit

sys.path.insert(0, os.path.join(ROOT, "tools"))
import p2s_extract  # noqa: E402
import regress_diff  # noqa: E402

RAM = os.path.join(ROOT, "ramdumps")
BLACK = os.path.join(RAM, "chargenblackscreen.p2s")
GOOD = os.path.join(RAM, "RaceSelect.p2s")
GOOD2 = os.path.join(RAM, "selectgender.p2s")
PRISTINE_EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")


def _need(path, why):
    if not os.path.isfile(path):
        raise Skip("%s missing (%s)" % (os.path.relpath(path, ROOT), why))
    return path


# ---------------------------------------------------------------------------
# png_tripwire -- the black-screen net
# ---------------------------------------------------------------------------
def test_png_tripwire_flags_black_screen():
    """The ~2909 B black frame must FAIL the absolute-floor tripwire."""
    _need(BLACK, "black-screen fixture")
    r = regress_diff.png_tripwire(BLACK)
    assert r["ok"] is False, "black screen must FAIL: %s" % r["reason"]
    assert r["cand_bytes"] < 10000, "black frame should be tiny, got %d" % r["cand_bytes"]


def test_png_tripwire_passes_good_frame():
    """A real 200-460 KB rendered frame must PASS."""
    _need(GOOD, "good-frame fixture")
    r = regress_diff.png_tripwire(GOOD)
    assert r["ok"] is True, "good frame must PASS: %s" % r["reason"]
    assert r["cand_bytes"] > 100000, "good frame should be large, got %d" % r["cand_bytes"]


def test_png_tripwire_relative_floor():
    """A good frame vs a good baseline PASSES; the black frame vs the same
    baseline FAILS on the 25%-of-baseline relative rule too."""
    _need(GOOD, "good-frame fixture")
    _need(BLACK, "black-screen fixture")
    good = regress_diff.png_tripwire(GOOD, baseline_p2s=GOOD)
    assert good["ok"] is True, good["reason"]
    black = regress_diff.png_tripwire(BLACK, baseline_p2s=GOOD)
    assert black["ok"] is False, black["reason"]


# ---------------------------------------------------------------------------
# ee_ram VA-direct sanity
# ---------------------------------------------------------------------------
def test_ee_ram_is_va_direct():
    """ee is a 32 MB VA-direct image: the mode sentinel 0x4FED18 is a small
    int and 0x3A31A0 decodes as a MIPS j/jal word (opcode field 2 or 3)."""
    _need(GOOD, "good-frame fixture")
    ee = p2s_extract.ee_ram(GOOD)
    assert len(ee) == 33554432, "EE RAM must be 32 MB, got %d" % len(ee)
    mode = struct.unpack_from("<I", ee, 0x4FED18)[0]
    assert 0 <= mode < 16, "mode sentinel 0x4FED18 not a small int: %d" % mode
    word = struct.unpack_from("<I", ee, 0x3A31A0)[0]
    assert (word >> 26) in (2, 3), \
        "0x3A31A0 should be a j/jal word, got 0x%08X" % word


# ---------------------------------------------------------------------------
# build_match -- the stale-save guardrail
# ---------------------------------------------------------------------------
def test_build_match_detects_stale_save():
    """A save captured from a PATCHED build must MISMATCH the pristine EXE at
    the P27 hook VA (proving the stale-save abort gate actually fires)."""
    _need(GOOD, "good-frame fixture")
    _need(PRISTINE_EXE, "pristine EXE")
    r = regress_diff.build_match(GOOD, PRISTINE_EXE, probe_vas=(0x3A31A0,))
    assert r["ok"] is False, \
        "a patched-build save vs pristine EXE must be flagged STALE: %s" % r["reason"]
    assert r["mismatches"], "expected a probe mismatch record"


def test_build_match_passes_self_consistent():
    """A save matches an EXE image reconstructed FROM that save at the probe
    VAs -- the fresh-build happy path (no mismatch)."""
    _need(GOOD, "good-frame fixture")
    ee = p2s_extract.ee_ram(GOOD)
    va = 0x3A31A0
    # Build a synthetic EXE buffer whose fo(va) word equals the save's RAM word.
    fo = regress_diff.exe_fo(va)
    exe = bytearray(fo + 4)
    struct.pack_into("<I", exe, fo, struct.unpack_from("<I", ee, va)[0])
    r = regress_diff.build_match(GOOD, bytes(exe), probe_vas=(va,))
    assert r["ok"] is True, "self-consistent probe must PASS: %s" % r["reason"]


# ---------------------------------------------------------------------------
# pixel_diff -- cheap self-vs-self (fast); full-frame divergence in self-test
# ---------------------------------------------------------------------------
def test_pixel_diff_self_is_zero():
    """A frame compared against itself reports 0% changed (Pillow required;
    SKIP if Pillow is absent)."""
    _need(GOOD, "good-frame fixture")
    png = p2s_extract.screenshot(GOOD)
    try:
        r = regress_diff.pixel_diff(png, png)
    except RuntimeError as e:
        raise Skip(str(e))  # Pillow missing
    assert r["ok"] is True and r["pct_changed"] == 0.0, \
        "self-diff must be 0%%, got %s" % r["reason"]


TESTS = [
    test_png_tripwire_flags_black_screen,
    test_png_tripwire_passes_good_frame,
    test_png_tripwire_relative_floor,
    test_ee_ram_is_va_direct,
    test_build_match_detects_stale_save,
    test_build_match_passes_self_consistent,
    test_pixel_diff_self_is_zero,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_regress_harness")
