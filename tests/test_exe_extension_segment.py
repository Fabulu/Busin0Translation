#!/usr/bin/env python3
"""
test_exe_extension_segment.py -- v174 EXE-EXTENSION static gate.

The v174 build moves the three load-bearing font-metric tables OUT of the battle
arena into a NEW file-backed PT_LOAD (the repurposed spare PH1) at VA 0x580000, and
bumps the sbrk break so malloc can never hand back an address inside the segment.
This module pins every file-static invariant of that change against the BUILT EXE:

  GATE-a SEGMENT : ELF magic; e_phnum==2; PH1@0x54 is a PT_LOAD at vaddr==paddr==
                   0x580000, offset 0x3FDD00, filesz==memsz==0x300; SEG_VA is
                   64KiB-aligned (>= old heap base 0x579800); and the 768B blob is
                   EXACTLY adv_table_256()+leftshift_table_256()+adv2_table_256().
  GATE-b HEAP    : pristine sbrk word @0x3AF6D4 == 0x00579800; patched == 0x00581000
                   (> segment end); and NO other 00 98 57 00 word survives in the
                   loaded image [0x80, 0x3FDD00).
  GATE-c ARENA   : the vacated in-arena table windows (0x4C7564 / 0x4C7690) and the
                   old arena-start hole (0x4B1000 / 0x4B1100) are pristine-ZERO -- no
                   metric table of ours is resident in the arena (the battle fix).
  GATE-d DATA    : the byte each cave reads at fo(ADV_VA)/fo(LSH_VA)/fo(ADV2_VA)
                   equals the corresponding glyph_metrics table (segment mapping,
                   NOT the PH0 fo()).

TIER-2: SKIPs when build/SLPM_653.78_patched is absent.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, Skip, main_exit          # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "build"))
import _reloc_v147_design as RELOC                   # noqa: E402  (single source)

sys.path.insert(0, os.path.join(ROOT, "tools"))
import glyph_metrics                                 # noqa: E402

PRISTINE_EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")

SEG_VA = 0x580000
SEG_FILE_OFF = 0x3FDD00
SEG_SIZE = 0x300
PRISTINE_SIZE = 4_185_776
OUTPUT_SIZE = 4_186_112
HEAP_FO = 0x3AF6D4
OLD_BREAK = 0x00579800
NEW_BREAK = 0x00581000


def _seg_fo(va):
    """Segment file offset: p_offset + (va - p_vaddr).  NOT the PH0 fo()."""
    return SEG_FILE_OFF + (va - SEG_VA)


def _patched():
    if not os.path.isfile(PATCHED_EXE):
        raise Skip("build/SLPM_653.78_patched missing (run build/patch_exe.py)")
    return open(PATCHED_EXE, "rb").read()


def _pristine():
    if not os.path.isfile(PRISTINE_EXE):
        raise Skip("extracted/SLPM_653.78 missing")
    return open(PRISTINE_EXE, "rb").read()


# ── GATE-a: segment ──────────────────────────────────────────────────────────
def test_a_segment_header_and_blob():
    d = _patched()
    assert d[:4] == b"\x7fELF", "not an ELF"
    assert len(d) == OUTPUT_SIZE, "patched EXE is %d bytes, expected %d" % (len(d), OUTPUT_SIZE)
    e_phnum = struct.unpack_from("<H", d, 0x2C)[0]
    assert e_phnum == 2, "e_phnum = %d, expected 2 (PHT must NOT grow)" % e_phnum
    p_type, p_off, p_va, p_pa, p_fsz, p_msz, p_flags, p_align = struct.unpack_from("<8I", d, 0x54)
    assert p_type == 1, "PH1 type = %d, expected PT_LOAD (1)" % p_type
    assert p_off == SEG_FILE_OFF, "PH1 p_offset = 0x%X, expected 0x%X" % (p_off, SEG_FILE_OFF)
    assert p_va == p_pa == SEG_VA, "PH1 vaddr/paddr = 0x%X/0x%X, expected 0x%X" % (p_va, p_pa, SEG_VA)
    assert p_fsz == p_msz == SEG_SIZE, (
        "PH1 filesz/memsz = 0x%X/0x%X, expected 0x%X==0x%X (no zero-fill reliance)"
        % (p_fsz, p_msz, SEG_SIZE, SEG_SIZE))
    assert (SEG_VA & 0xFFFF) == 0, "SEG_VA 0x%X not 64KiB-aligned -> lbu sign-ext risk" % SEG_VA
    assert SEG_VA >= OLD_BREAK, "SEG_VA 0x%X below old heap base 0x%X" % (SEG_VA, OLD_BREAK)
    # blob == the three metric tables, exactly.
    want = (glyph_metrics.adv_table_256()
            + glyph_metrics.leftshift_table_256()
            + glyph_metrics.adv2_table_256())
    assert len(want) == SEG_SIZE
    got = d[SEG_FILE_OFF:SEG_FILE_OFF + SEG_SIZE]
    assert got == want, "segment blob != adv+leftshift+adv2 tables"


def test_a_reloc_constants_match_segment():
    assert RELOC.SEG_VA == SEG_VA
    assert RELOC.ADV_VA == SEG_VA + 0x000
    assert RELOC.LSH_VA == SEG_VA + 0x100
    assert RELOC.ADV2_VA == SEG_VA + 0x200
    assert RELOC.LSH2_VA == RELOC.LSH_VA  # R2100 leftshift 4th-table deferred


# ── GATE-b: heap reservation ─────────────────────────────────────────────────
def test_b_heap_base_bumped():
    pr, d = _pristine(), _patched()
    assert struct.unpack_from("<I", pr, HEAP_FO)[0] == OLD_BREAK, (
        "pristine sbrk break word @0x%X != 0x%08X" % (HEAP_FO, OLD_BREAK))
    got = struct.unpack_from("<I", d, HEAP_FO)[0]
    assert got == NEW_BREAK, "patched sbrk break word = 0x%08X, expected 0x%08X" % (got, NEW_BREAK)
    assert NEW_BREAK >= SEG_VA + SEG_SIZE, "new heap base is not above the segment end"


def test_b_no_surviving_old_break_word():
    """No other 00 98 57 00 word survives in the loaded image [0x80, 0x3FDD00)."""
    d = _patched()
    raw = d[0x80:SEG_FILE_OFF]
    patt = b"\x00\x98\x57\x00"
    i = raw.find(patt)
    hits = []
    while i != -1:
        hits.append(hex(0x80 + i))
        i = raw.find(patt, i + 1)
    assert not hits, "surviving 0x00579800 word(s) in loaded image: %s" % hits


# ── GATE-c: arena (battle fix) ───────────────────────────────────────────────
def test_c_vacated_windows_and_hole_zero():
    pr, d = _pristine(), _patched()
    for va, fo in ((0x4C7564, 0x3C75E4), (0x4C7690, 0x3C7710),
                   (0x4B1000, RELOC.fo(0x4B1000)), (0x4B1100, RELOC.fo(0x4B1100))):
        assert d[fo:fo + 256] == b"\x00" * 256, (
            "arena window VA 0x%06X (file 0x%06X) is NOT zero -- a metric table is "
            "resident in the arena" % (va, fo))
        assert pr[fo:fo + 256] == b"\x00" * 256, (
            "pristine window VA 0x%06X is not zero -- wrong extract?" % va)


# ── GATE-d: the bytes the caves read ─────────────────────────────────────────
def test_d_cave_read_bytes_match_metrics():
    d = _patched()
    adv = glyph_metrics.adv_table_256()
    lsh = glyph_metrics.leftshift_table_256()
    adv2 = glyph_metrics.adv2_table_256()
    for va, table, name in ((RELOC.ADV_VA, adv, "ADV"),
                            (RELOC.LSH_VA, lsh, "LSH"),
                            (RELOC.ADV2_VA, adv2, "ADV2")):
        fo = _seg_fo(va)
        got = d[fo:fo + 256]
        assert got == table, (
            "%s table the caves read @VA 0x%06X (file 0x%06X) != glyph_metrics"
            % (name, va, fo))


TESTS = [
    test_a_segment_header_and_blob,
    test_a_reloc_constants_match_segment,
    test_b_heap_base_bumped,
    test_b_no_surviving_old_break_word,
    test_c_vacated_windows_and_hole_zero,
    test_d_cave_read_bytes_match_metrics,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_exe_extension_segment")
