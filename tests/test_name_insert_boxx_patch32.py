#!/usr/bin/env python3
"""
test_name_insert_boxx_patch32.py -- lock Patch 32 (narration NAME-INSERT
boxX=+96), NEW in v206 (GitHub issue #46).

The name/variable-insert draw loop (renderer 0x307da0, loop 0x308ac8..0x308ce4)
reads the descriptor boxX raw, while Patch 24 gives every normal narration
glyph boxX=96 when the descriptor's boxX is 0.  So the player's name drew 96px
to the left of its pen, on top of the preceding words ("winKeelvin").  Patch 32
rewrites the once-per-insert prologue 0x308a80..0x308ac4 (18 words, in place)
so that 0x120(sp) = line*12 + (boxX==0 ? 96 : 0).

This module pins:
  TIER-1 (static, always): the replacement words in build/patch_exe.py
     disassemble to a straight-line block (no branch/jump) that still stores
     0x110(sp) and 0x120(sp), sets the float-branch advance to 0.18f, and
     carries the movn boxX gate with the 96 immediate.
  TIER-2 (built EXE, SKIP when build/SLPM_653.78_patched absent): the 18 words
     at file 0x208B00 equal Patch 32's replacement.
"""

import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, Skip, require_file, main_exit  # noqa: E402

PATCH_EXE = os.path.join(ROOT, "build", "patch_exe.py")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")
P32_VA = 0x308A80
P32_FO = P32_VA - 0x100000 + 0x80     # 0x208B00


def _words(name):
    """The u32 list literal assigned to `name` inside the Patch 32 block."""
    require_file(PATCH_EXE, "Patch 32 gate")
    src = open(PATCH_EXE, encoding="utf-8").read()
    i = src.find("PATCH 32")
    assert i != -1, "build/patch_exe.py has no PATCH 32 block"
    m = re.search(r"%s = \[(.*?)\]" % name, src[i:], re.S)
    assert m, "Patch 32 block has no %s list" % name
    body = "\n".join(ln.split("#", 1)[0] for ln in m.group(1).splitlines())
    return [int(x, 16) for x in re.findall(r"0x[0-9A-Fa-f]{8}", body)]


def test_t1_replacement_shape():
    """Same length as the original prologue; straight-line; stores both
    stack slots; keeps 0.24f; has the movn boxX gate and the +96."""
    new, orig = _words("P32_NEW"), _words("P32_ORIG")
    assert len(new) == len(orig) == 18, "Patch 32 must rewrite exactly 18 words"
    for w in new:
        op = w >> 26
        assert op not in (1, 2, 3, 4, 5, 6, 7, 20, 21, 22, 23), (
            "Patch 32 word 0x%08X is a branch/jump -- prologue must stay straight-line" % w)
    assert 0xAFA30120 in new, "must store the corrected line offset to 0x120(sp)"
    assert 0xAFA20110 in new, "must still store sext16(scale) to 0x110(sp)"
    assert 0x3C033E38 in new and 0x346351EC in new, (
        "float-branch name advance must be 0.18f (0x3E3851EC), matching the 18px text")
    assert 0x8604003C in new, "must read boxX (lh a0,0x3c(s0))"
    assert 0x24020060 in new, "must use the Patch-24 narration boxX of 96"
    assert 0x0004100B in new, "must gate with movn v0,zero,a0 (boxX!=0 -> +0)"


def test_t2_built_exe_has_patch32():
    if not os.path.isfile(PATCHED_EXE):
        raise Skip("build/SLPM_653.78_patched missing (run the build)")
    data = open(PATCHED_EXE, "rb").read()
    new = _words("P32_NEW")
    got = list(struct.unpack_from("<%dI" % len(new), data, P32_FO))
    assert got == new, "built EXE prologue @0x%06X is not Patch 32" % P32_FO


TESTS = [test_t1_replacement_shape, test_t2_built_exe_has_patch32]

if __name__ == "__main__":
    main_exit(TESTS, "test_name_insert_boxx_patch32")
