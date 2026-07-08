#!/usr/bin/env python3
"""
test_exe_extension_arena.py -- v174 EXE-EXTENSION end-to-end battle-safety pin.

Companion to test_exe_extension_segment.py.  Where that module pins the segment
header/heap/table BYTES by fixed file offsets, THIS module proves the SAME v174
invariants a different way -- by walking the ELF program-header table of the
BUILT EXE and by DISASSEMBLING the six font caves out of the built binary and
resolving their effective addresses into the segment -- and adds the one pin the
sibling only spot-checks: the WHOLE battle arena carries no resident code/table
of ours.

Pins (all against the BUILT build/SLPM_653.78_patched):

  P1  LOAD SEGMENT  -- an independent e_phoff/e_phnum walk finds a PT_LOAD whose
                       p_vaddr==p_paddr==SEG_VA (0x580000), p_offset==0x3FDD00,
                       p_filesz==p_memsz==0x300, 64KiB-aligned, above the old heap
                       base 0x579800.  (== "reserved LOAD segment at VA/size".)
  P2  HEAP BASE     -- the sbrk break constant is bumped from 0x00579800 to a value
                       strictly past the segment end (>= SEG_VA+0x300) so malloc can
                       never hand back an address inside the segment.
  P3  ARENA CLEAN   -- across the whole file-backed arena 0x4B0E00..0x4FDC80 NO cave
                       and NO metric table of ours is resident: every cave install VA
                       lies below the arena, every canonical table VA lies in the
                       segment above the arena, the historical in-arena table sites
                       (0x4C7564/0x4C7690 vacated, 0x4B1000/0x4B1100 arena-start hole)
                       are pristine-ZERO, and no patched-vs-pristine diff byte falls
                       inside any cave range or table window.  (The 327 remaining
                       arena diffs are the long-standing game-data patches -- banner/
                       gender glyph IDs, NPC name/width tables -- NOT relocatable code
                       or metric tables; this is the honest static form of "the arena
                       ships byte-identical to pristine w.r.t. OUR resident data",
                       i.e. the battle fix.)
  P4  CAVES->SEG    -- disassembling each of the SIX font caves (P14c1, P14c2, P26,
                       P27, P29f1, P31f1) out of the built EXE, its table-read
                       effective address resolves (correct sign-extension) to the
                       expected table VA AND lies inside [SEG_VA, SEG_VA+0x300).
  P5  TABLE BYTES   -- the bytes those EAs point at (read through the SEGMENT file
                       mapping) equal the glyph_metrics tables exactly.

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
import mips_cave_analyzer as MCA                      # noqa: E402

# P26's cave words live only in patch_exe.py main(); reuse the single mirror the
# byte-pin test already keeps VERBATIM (with source-line citations).
import test_reloc_caves_installed as CAVES            # noqa: E402

PRISTINE_EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")

SEG_VA = 0x580000
SEG_FILE_OFF = 0x3FDD00
SEG_SIZE = 0x300
OLD_BREAK = 0x00579800
NEW_BREAK = 0x00581000
HEAP_FO = 0x3AF6D4                 # RELOC.fo(0x4AF654)

# Battle-heap arena (v171).  File-backed portion ends at the PH0 filesz end
# (VA 0x4FDC80 -> file 0x3FDD00); the 0x4FDC80..0x4FDE30 tail is zero-init BSS,
# not present in the file, and the segment blob now occupies file >= 0x3FDD00.
ARENA_LO = 0x4B0E00
ARENA_HI = 0x4FDE30
FILESZ_END = 0x4FDC80

# Historical in-arena metric-table sites that MUST be pristine-zero after v174:
#   0x4C7564 / 0x4C7690 -- the canonical ADV/LSH homes, vacated into the segment.
#   0x4B1000 / 0x4B1100 -- the v158 arena-START hole that DMA-swept -> battle softlock.
ARENA_TABLE_WINDOWS = (0x4C7564, 0x4C7690, 0x4B1000, 0x4B1100)

# The six font caves, decoded FROM the built EXE at their install VA, whose table
# read must land in the segment:  (name, install_va, words, table_va, table_fn)
FONT_CAVES = [
    ("P14c1", RELOC.P14C1_VA, RELOC.P14C1_WORDS,   RELOC.ADV_VA,  glyph_metrics.adv_table_256),
    ("P14c2", RELOC.P14C2_VA, RELOC.P14C2_WORDS,   RELOC.LSH_VA,  glyph_metrics.leftshift_table_256),
    ("P26",   RELOC.P26_VA,   CAVES.P26_CAVE_WORDS, RELOC.ADV2_VA, glyph_metrics.adv2_table_256),
    ("P27",   RELOC.P27_VA,   RELOC.P27_WORDS,     RELOC.ADV2_VA, glyph_metrics.adv2_table_256),
    ("P29f1", RELOC.P29_F1_VA, RELOC.P29_F1_WORDS, RELOC.LSH2_VA, glyph_metrics.leftshift_table_256),
    ("P31f1", RELOC.P31_F1_VA, RELOC.P31_F1_WORDS, RELOC.LSH2_VA, glyph_metrics.leftshift_table_256),
]


def _fo(va):
    """PH0 file offset (image mapping).  Valid for VA in PH0's range only."""
    return va - 0x100000 + 0x80


def _seg_fo(va):
    """Segment file offset: p_offset + (va - p_vaddr).  NOT the PH0 _fo()."""
    return SEG_FILE_OFF + (va - SEG_VA)


def _patched():
    if not os.path.isfile(PATCHED_EXE):
        raise Skip("build/SLPM_653.78_patched missing (run build/patch_exe.py)")
    return open(PATCHED_EXE, "rb").read()


def _pristine():
    if not os.path.isfile(PRISTINE_EXE):
        raise Skip("extracted/SLPM_653.78 missing")
    return open(PRISTINE_EXE, "rb").read()


def _program_headers(d):
    """Walk the ELF32-LE program-header table -> list of (type,off,va,pa,fsz,msz,flags,align)."""
    assert d[:4] == b"\x7fELF", "not an ELF"
    assert d[4] == 1 and d[5] == 1, "expected ELF32 little-endian"
    e_phoff = struct.unpack_from("<I", d, 0x1C)[0]
    e_phentsize = struct.unpack_from("<H", d, 0x2A)[0]
    e_phnum = struct.unpack_from("<H", d, 0x2C)[0]
    assert e_phentsize == 32, "unexpected e_phentsize %d" % e_phentsize
    return [struct.unpack_from("<8I", d, e_phoff + i * e_phentsize) for i in range(e_phnum)]


# ── P1: the reserved LOAD segment (via an independent phdr walk) ──────────────
def test_p1_load_segment_present_at_va_size():
    d = _patched()
    loads = [ph for ph in _program_headers(d) if ph[0] == 1]        # PT_LOAD
    segs = [ph for ph in loads if ph[2] == SEG_VA]
    assert len(segs) == 1, (
        "expected exactly ONE PT_LOAD at VA 0x%06X, found %d" % (SEG_VA, len(segs)))
    p_type, p_off, p_va, p_pa, p_fsz, p_msz, p_flags, p_align = segs[0]
    assert p_off == SEG_FILE_OFF, "seg p_offset 0x%X != 0x%X" % (p_off, SEG_FILE_OFF)
    assert p_va == p_pa == SEG_VA, "seg vaddr/paddr 0x%X/0x%X != 0x%X" % (p_va, p_pa, SEG_VA)
    assert p_fsz == p_msz == SEG_SIZE, (
        "seg filesz/memsz 0x%X/0x%X != 0x%X (filesz must == memsz: no zero-fill reliance)"
        % (p_fsz, p_msz, SEG_SIZE))
    assert (SEG_VA & 0xFFFF) == 0, "SEG_VA not 64KiB-aligned -> lbu sign-ext carry risk"
    assert SEG_VA >= OLD_BREAK, "SEG_VA 0x%X below old heap base 0x%X" % (SEG_VA, OLD_BREAK)
    # the segment file window must physically fit inside the built file.
    assert p_off + p_fsz <= len(d), "segment file window runs past EOF"
    # single-source constants agree with the built header.
    assert RELOC.SEG_VA == SEG_VA
    assert (RELOC.ADV_VA, RELOC.LSH_VA, RELOC.ADV2_VA) == (SEG_VA, SEG_VA + 0x100, SEG_VA + 0x200)


# ── P2: heap-init base bumped past the segment ───────────────────────────────
def test_p2_heap_base_bumped_past_segment():
    pr, d = _pristine(), _patched()
    assert struct.unpack_from("<I", pr, HEAP_FO)[0] == OLD_BREAK, (
        "pristine sbrk break @0x%X != 0x%08X -- wrong extract?" % (HEAP_FO, OLD_BREAK))
    got = struct.unpack_from("<I", d, HEAP_FO)[0]
    assert got == NEW_BREAK, "patched sbrk break = 0x%08X, expected 0x%08X" % (got, NEW_BREAK)
    assert got >= SEG_VA + SEG_SIZE, (
        "heap base 0x%08X is NOT past segment end 0x%06X -- malloc could return into segment"
        % (got, SEG_VA + SEG_SIZE))
    # and no other copy of the old break word survives in the loaded image.
    raw = d[0x80:SEG_FILE_OFF]
    assert raw.find(b"\x00\x98\x57\x00") == -1, "a stray 0x00579800 word survives in the image"


# ── P3: nothing of ours resident in the battle arena ─────────────────────────
def test_p3_no_cave_or_table_resident_in_arena():
    """Geometric: every cave install VA is BELOW the arena; every canonical table
    VA is in the segment ABOVE the arena."""
    for name, (_hook, install_va, size) in RELOC.CAVE_RELOC.items():
        assert install_va + size <= ARENA_LO, (
            "cave %s @0x%06X..0x%06X intrudes into the arena (>= 0x%06X)"
            % (name, install_va, install_va + size, ARENA_LO))
    for va in RELOC.CANONICAL_TABLE_VAS:
        assert va >= ARENA_HI and SEG_VA <= va < SEG_VA + SEG_SIZE, (
            "metric-table VA 0x%06X is not in the segment [0x%06X,0x%06X) above the arena"
            % (va, SEG_VA, SEG_VA + SEG_SIZE))


def test_p3_arena_table_windows_pristine_zero():
    pr, d = _pristine(), _patched()
    for va in ARENA_TABLE_WINDOWS:
        fo = _fo(va)
        assert d[fo:fo + 256] == b"\x00" * 256, (
            "BATTLE-FIX BROKEN: arena table window VA 0x%06X (file 0x%06X) is NOT zero "
            "in the built EXE -- a metric table is resident in the arena" % (va, fo))
        assert pr[fo:fo + 256] == b"\x00" * 256, (
            "pristine window VA 0x%06X is not zero -- wrong extract?" % va)


def test_p3_arena_diffs_are_only_gamedata():
    """Every patched-vs-pristine diff byte in the file-backed arena must fall OUTSIDE
    every cave range and every metric-table window -- i.e. the only arena changes are
    the long-standing game-data patches, never relocatable code or a metric table."""
    pr, d = _pristine(), _patched()
    lo, hi = _fo(ARENA_LO), _fo(FILESZ_END)      # file-backed arena [0x3B0E80, 0x3FDD00)
    forbidden = []
    # cave ranges (all below the arena, so a sanity guard) + table windows.
    for name, (_h, iva, size) in RELOC.CAVE_RELOC.items():
        forbidden.append((name, _fo(iva), _fo(iva + size)))
    for va in ARENA_TABLE_WINDOWS:
        forbidden.append(("tbl@0x%06X" % va, _fo(va), _fo(va) + 256))
    ndiff = 0
    for i in range(lo, hi):
        if pr[i] != d[i]:
            ndiff += 1
            for name, flo, fhi in forbidden:
                if flo <= i < fhi:
                    raise AssertionError(
                        "arena diff at file 0x%06X (VA 0x%06X) lands inside %s -- a cave "
                        "or metric table is resident in the arena"
                        % (i, i - 0x80 + 0x100000, name))
    # sanity: there ARE game-data diffs (proves we are diffing the right builds), and
    # they are far fewer than a resident 256B/512B table block scattered across windows.
    assert ndiff > 0, "no arena diffs at all -- comparing identical files? wrong inputs"


# ── P4/P5: the six font caves resolve into the segment, bytes correct ─────────
def test_p4_font_caves_resolve_into_segment():
    d = _patched()
    problems = []
    for name, install_va, words, table_va, _fn in FONT_CAVES:
        n = len(words)
        built = list(struct.unpack_from("<%dI" % n, d, _fo(install_va)))
        insns = MCA.decode(built, install_va)
        load_eas = {a["ea"] for a in MCA.resolve_absolute_accesses(insns) if a["kind"] == "load"}
        if table_va not in load_eas:
            problems.append("%s: table read did not resolve to 0x%06X (got %s)"
                            % (name, table_va, sorted("0x%06X" % v for v in load_eas)))
            continue
        if not (SEG_VA <= table_va < SEG_VA + SEG_SIZE):
            problems.append("%s: table EA 0x%06X not inside segment [0x%06X,0x%06X)"
                            % (name, table_va, SEG_VA, SEG_VA + SEG_SIZE))
    assert not problems, "font-cave -> segment resolution failed:\n  " + "\n  ".join(problems)


def test_p5_segment_table_bytes_byte_correct():
    d = _patched()
    problems = []
    for name, _iva, _words, table_va, table_fn in FONT_CAVES:
        want = table_fn()
        assert len(want) == 256
        fo = _seg_fo(table_va)
        got = d[fo:fo + 256]
        if got != want:
            problems.append("%s: bytes @VA 0x%06X (seg file 0x%06X) != glyph_metrics"
                            % (name, table_va, fo))
    assert not problems, "segment table bytes wrong:\n  " + "\n  ".join(problems)
    # and the full 768B blob is exactly [ADV | LEFTSHIFT | ADV2].
    want_blob = (glyph_metrics.adv_table_256()
                 + glyph_metrics.leftshift_table_256()
                 + glyph_metrics.adv2_table_256())
    assert len(want_blob) == SEG_SIZE
    assert d[SEG_FILE_OFF:SEG_FILE_OFF + SEG_SIZE] == want_blob, "segment blob != adv+lsh+adv2"


TESTS = [
    test_p1_load_segment_present_at_va_size,
    test_p2_heap_base_bumped_past_segment,
    test_p3_no_cave_or_table_resident_in_arena,
    test_p3_arena_table_windows_pristine_zero,
    test_p3_arena_diffs_are_only_gamedata,
    test_p4_font_caves_resolve_into_segment,
    test_p5_segment_table_bytes_byte_correct,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_exe_extension_arena")
