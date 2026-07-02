#!/usr/bin/env python3
"""
test_chargen_sidebar_patch30.py -- lock Patch 30 (chargen sidebar value-column
left-shift), NEW in v157.

The chargen SIDEBAR VALUE fields (Sex / Race:Human / Align:Good / Class:Fight)
overflowed their boxes on the RIGHT on every chargen screen.  They share ONE
base-X immediate, traced end-to-end to the renderer baseX:
  VA 0x14C0A0 (file 0x4C120)  addiu t3,zero,72  (word 0x240B0048)
the t3 arg to `jal 0x144A90` @0x14C09C in the chargen list module 0x14BED0 (the
value graph 0x144A90/0x142A60 has ONLY chargen-module callers -> chargen-only).
Patch 30 rewrites 72 -> 44 (word 0x240B002C, ~28px left) in place.  It must NOT
touch 0x14C070 (the Sex info-banner v0=-104, word 0x2402FF98) which is right
above it.

This module pins:
  TIER-1 (static, always): build/patch_exe.py Patch 30 block references file
     0x4C120, gates on the pristine word 0x240B0048, writes 0x240B002C, and does
     NOT touch 0x14C070 / 0x4C0F0 in code.
  TIER-2 (built EXE, SKIP when build/SLPM_653.78_patched absent): 0x4C120 ==
     0x240B002C (44); the Sex banner 0x4C0F0 stays pristine 0x2402FF98.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, Skip, require_file, main_exit  # noqa: E402

PATCH_EXE = os.path.join(ROOT, "build", "patch_exe.py")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")

P30_OFF = 0x4C120           # file off of VA 0x14C0A0
P30_PRISTINE = 0x240B0048   # addiu t3,zero,72
P30_NEW = 0x240B002C        # addiu t3,zero,44
SEX_BANNER_FO = 0x4C0F0     # VA 0x14C070 -- Sex banner, must stay pristine
SEX_BANNER_PRISTINE = 0x2402FF98


def _block():
    require_file(PATCH_EXE, "Patch 30 gate")
    src = open(PATCH_EXE, encoding="utf-8").read()
    i = src.find("PATCH 30")
    assert i != -1, "build/patch_exe.py has no PATCH 30 block"
    j = src.find("PATCH 20", i)
    return "\n".join(
        ln.split("#", 1)[0] for ln in src[i : j if j != -1 else len(src)].splitlines()
    )


def test_t1_enabled_and_writes():
    """Patch 30 references file 0x4C120, gates on pristine 0x240B0048, writes
    0x240B002C, and performs pack_into."""
    code = _block()
    assert "0x4C120" in code, "Patch 30 must reference the value-column file off 0x4C120"
    assert "0x240B0048" in code, "Patch 30 must gate on pristine word 0x240B0048"
    assert "0x240B002C" in code, "Patch 30 must write 0x240B002C (72 -> 44)"
    assert "pack_into" in code, "Patch 30 must pack_into the new word"


def test_t1_no_falsified_sites_in_code():
    """Patch 30 must NOT touch the Sex info-banner site 0x4C0F0 in code."""
    code = _block()
    assert "0x4C0F0" not in code, "Patch 30 code must not touch the Sex banner 0x4C0F0"


def _load_patched():
    if not os.path.isfile(PATCHED_EXE):
        raise Skip("build/SLPM_653.78_patched missing (run the build)")
    with open(PATCHED_EXE, "rb") as fh:
        return fh.read()


def _u32(data, off):
    return struct.unpack_from("<I", data, off)[0]


def test_t2_value_column_shifted():
    """Built EXE: 0x4C120 == 0x240B002C (44). TEETH: must not still be pristine 72."""
    data = _load_patched()
    w = _u32(data, P30_OFF)
    assert w != P30_PRISTINE, (
        "value column 0x4C120 still pristine 72 (0x%08X) -- Patch 30 did not fire" % w
    )
    assert w == P30_NEW, "value column 0x4C120 = 0x%08X, expected 0x%08X (44)" % (w, P30_NEW)


def test_t2_sex_banner_pristine():
    """The Sex info-banner origin 0x4C0F0 stays pristine 0x2402FF98 (must NOT move)."""
    data = _load_patched()
    w = _u32(data, SEX_BANNER_FO)
    assert w == SEX_BANNER_PRISTINE, (
        "Sex banner 0x4C0F0 = 0x%08X, expected pristine 0x%08X (neighbour touched!)"
        % (w, SEX_BANNER_PRISTINE)
    )


TESTS = [
    test_t1_enabled_and_writes,
    test_t1_no_falsified_sites_in_code,
    test_t2_value_column_shifted,
    test_t2_sex_banner_pristine,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_chargen_sidebar_patch30")
