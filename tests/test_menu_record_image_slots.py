#!/usr/bin/env python3
r"""
test_menu_record_image_slots.py -- battle-crash-class regression gate.

ROOT CAUSE this guards against (issues #24/#25/#29/#32; live-debug +
duringdebug.p2s verified): Patch 4's blind "glyph-id 722 -> 0" scan in
build/patch_exe.py walked a whole 56-byte banner menu record and zeroed TWO
IMAGE-SLOT dwords (file 0x3C3444/0x3C344C, pristine 0x02D20000). Stock
label-draw code (fn 0x237130) reads image-slot dwords as file IDs and SKIPS
ONLY on 0xFFFFFFFF (its "absent" sentinel). Our 0x00000000 was treated as a REAL
FileID 0 -> GetLoadAdr(0) -> StoreImg on a zero-size image -> GlmAlloc(size=0)
leaks one allocator node per frame -> pool exhausts -> "racGlmAllocMemory: Empty
Free" freeze.

CATEGORY: a degenerate scalar (0) written into a non-text runtime-parameter
field (ID/size/dimension) that stock code dereferences, where 0 is a
valid-looking-but-illegal value and the engine's real "absent" encoding is
0xFFFFFFFF. A SAME-SIZE, in-place EXE change -> invisible to every structural
gate we have; hence this value-level tripwire.

WHAT IT CHECKS (precise, no false positives): the draw path reads the two image
slots at 0x4C2E84 + i*56 and +8 (VA) -> file 0x3C2F04 + i*56 and +8, per 56-byte
record. Display glyphs (e.g. the banner byte-50 char) may legitimately be 0 (a
space), so we flag ONLY at the true image-slot OFFSETS -- never by value alone.
Rule: a slot whose pristine value is a real image id (0xNNNN0000, nonzero, not
the 0xFFFFFFFF sentinel) must NOT be 0x00000000 in the built EXE.

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

IMG_SLOT1 = 0x3C2F04   # file offset of record-0 image-slot #1 (VA 0x4C2E84); #2 at +8
STRIDE = 56
TABLE_HI = 0x3C5300    # menu struct records end here (CLAUDE.md)


def _load():
    require_file(PRISTINE_EXE, "pristine EXE extract")
    require_file(PATCHED_EXE, "patched EXE build output")
    return open(PRISTINE_EXE, "rb").read(), open(PATCHED_EXE, "rb").read()


# The four records whose image-resource ids Patch 4's scan corrupts (banner scan
# targets). Their three id columns (+0x1C/+0x24/+0x2C) MUST ship byte-identical to
# pristine -- they register the BATTLE scene entities (e.g. B5F spiders). Any change:
#   garbage/0 id  -> GetLoadAdr non-image -> zero-size store -> "Empty Free" freeze;
#   0xFFFFFFFF    -> the setup `beq a0,-1` SKIPS the whole entity -> invisible/un-init
#                    monster -> flee/pass battle-exit softlock.
# So the invariant is EQUALITY to pristine, NOT "pristine-or-sentinel".
BANNER_RECORDS = (0x3C33F0, 0x3C3428, 0x3C3268, 0x3C32A0)
ID_COLUMNS = (0x1C, 0x24, 0x2C)


def test_image_slots_equal_pristine():
    pristine, patched = _load()
    bad = []
    # (1) precise: the four scan-target banner records' three id columns.
    for rec in BANNER_RECORDS:
        for col in ID_COLUMNS:
            off = rec + col
            p = struct.unpack_from("<I", pristine, off)[0]
            v = struct.unpack_from("<I", patched, off)[0]
            if v != p:
                bad.append((off, p, v))
    # (2) broad regression net: every menu-record image-id slot (A/B columns) must
    #     also equal pristine (guards future patches touching other records).
    i = 0
    while IMG_SLOT1 + i * STRIDE + 12 <= TABLE_HI:
        for slot in (0, 8):
            off = IMG_SLOT1 + i * STRIDE + slot
            p = struct.unpack_from("<I", pristine, off)[0]
            v = struct.unpack_from("<I", patched, off)[0]
            hi, lo = (p >> 16) & 0xFFFF, p & 0xFFFF
            if hi != 0 and lo == 0 and p != 0xFFFFFFFF and v != p:
                bad.append((off, p, v))
        i += 1
    bad = sorted(set(bad))
    if bad:
        lines = "; ".join(
            "file 0x%06X (VA 0x%06X) pristine 0x%08X -> 0x%08X"
            % (o, o - 0x80 + 0x100000, p, v)
            for o, p, v in bad
        )
        raise AssertionError(
            "menu-record image-resource id(s) differ from pristine -> a garbage id "
            "crashes (zero-size store leak) and a 0xFFFFFFFF sentinel SKIPS the whole "
            "battle entity (invisible monster + flee/pass exit softlock): %s. These "
            "fields must ship BYTE-IDENTICAL to pristine (build/patch_exe.py Patch 4 "
            "restores them after its glyph scan)." % lines
        )


TESTS = [test_image_slots_equal_pristine]

if __name__ == "__main__":
    main_exit(TESTS, "test_menu_record_image_slots")
