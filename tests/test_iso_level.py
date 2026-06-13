#!/usr/bin/env python3
"""
test_iso_level.py -- TIER 3: byte-level checks on the built ISO.

ISO path: $BUSIN_ISO, default build/BUSIN0_EN_v85.iso.  All tests SKIP when
the ISO is absent.  Resources are extracted via the PACKDATA.DIG TOC (located
through the ISO9660 root directory, never a hardcoded LBA).

Gates:
  * BUG-3: R1188 (the live dialogue/narration font) must ship BYTE-IDENTICAL
    to the pristine extract -- any patcher writing into it regresses the
    r/y/V glyph artifacts.
  * R1196 (intro scene script) must walk cleanly and satisfy the FFFF-end
    invariant on every walked DISPLAY_TEXT.
  * R2100/R2138 must NOT be pristine -- chargen English must still ship
    (regression guard for the R1188 revert accidentally widening).
  * R989/R990/R1034 (binary VIF data) must ship byte-identical to pristine
    (the v83 VIF-crash class).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (
    PackData,
    RAW_DIR,
    Skip,
    default_iso_path,
    display_invariant_issues,
    get_disasm,
    main_exit,
    require_file,
)

_PACK = None


def _pack():
    global _PACK
    if _PACK is None:
        iso = default_iso_path()
        if not os.path.isfile(iso):
            raise Skip("ISO not found: %s (set BUSIN_ISO or build v85)" % iso)
        _PACK = PackData(iso)
    return _PACK


def _pristine_bytes(name):
    return open(
        require_file(os.path.join(RAW_DIR, name), "pristine extract"), "rb"
    ).read()


def _compare(idx, name):
    data, _tc = _pack().extract(idx)
    pris = _pristine_bytes(name)
    if len(data) != len(pris):
        return False, "size %d != pristine %d" % (len(data), len(pris))
    return data == pris, "content differs" if data != pris else ""


def test_r1188_font_pristine():
    """BUG-3 gate: the dialogue font must be untouched on disc."""
    same, why = _compare(1188, "1188_type01.raw")
    assert same, (
        "R1188 in the ISO is NOT byte-identical to pristine (%s) -- a patcher "
        "is writing into the live dialogue font again (BUG-3: r/y/V artifacts)"
        % why
    )


def test_r1196_walks_with_invariant():
    get_disasm()
    data, tc = _pack().extract(1196)
    assert tc == 2, "TOC says R1196 is type %d, expected 2" % tc
    issues, checked = display_invariant_issues(data, strict=False)
    assert not issues, "R1196 from ISO: %s" % "; ".join(issues[:5])
    assert checked >= 100, (
        "R1196 from ISO: only %d DISPLAY_TEXT spans walked -- script "
        "structure regressed" % checked
    )


def test_chargen_resources_shipped_patched():
    """R2100/R2138 carry the chargen English -- they must differ from pristine."""
    for idx, name in ((2100, "2100_type04.raw"), (2138, "2138_type29.raw")):
        same, _why = _compare(idx, name)
        assert not same, (
            "R%d in the ISO is byte-identical to pristine -- the chargen "
            "English patch (%s) is no longer shipping" % (idx, name)
        )


def test_binary_resources_pristine():
    """R989/R990/R1034 are binary VIF data: any modification crashes (v83)."""
    for idx, name in (
        (989, "0989_type02.raw"),
        (990, "0990_type02.raw"),
        (1034, "1034_type02.raw"),
    ):
        same, why = _compare(idx, name)
        assert same, (
            "R%d in the ISO is NOT pristine (%s) -- binary VIF data was "
            "modified, expect a VIF FIFO crash on real hardware" % (idx, why)
        )


TESTS = [
    test_r1188_font_pristine,
    test_r1196_walks_with_invariant,
    test_chargen_resources_shipped_patched,
    test_binary_resources_pristine,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_iso_level")
