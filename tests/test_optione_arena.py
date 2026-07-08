#!/usr/bin/env python3
"""
test_optione_arena.py -- THE battle-softlock gate for the shipping Option-E design.

History: the empty-battle/harpy softlock was caused by our font-metric tables
resident in the battle-heap arena (VA 0x4B0E00..0x4FDE30) stalling the ~6MB
monster-asset DMA. The shipping fix ("Option-E", v175+, boot-confirmed v180)
relocates the tables into the freed span of the shrunk strncpy @0x121568 and
leaves the arena's pristine-zero heap-padding untouched. The old gates for the
FALSIFIED v174 ELF-segment design (test_exe_extension_segment/arena.py) were
deleted -- they pinned a build that never shipped (the PS2 BIOS refused it) and
their absence from run_all left the arena invariant unguarded (master-audit
finding #1, 2026-07-08). This module is the replacement, pinned to Option-E.

Invariants, against build/SLPM_653.78_patched vs extracted/SLPM_653.78:
  1. EXE size unchanged (no ELF growth -- Option-E needs none).
  2. ELF header: e_phnum == 2 and PH1 stays the pristine degenerate
     (filesz == 0) -- no header surgery of the kind the BIOS rejected.
  3. The sbrk heap-break word (file 0x3AF6D4 / VA 0x4AF654) is PRISTINE
     (0x579800) -- Option-E reserves nothing.
  4. The four metric tables live in the freed strncpy span (0x1215B4 /
     0x121610 / 0x12166C / 0x1216C8, 92B each, substantially nonzero) and the
     strncpy head was actually rewritten.
  5. THE ARENA LAW: within VA 0x4B0E00..0x4FDE30, no patched byte may differ
     from pristine where the pristine byte is 0x00 (heap padding must never be
     filled -- that is the exact softlock mechanism), and the total diff stays
     within a small budget for the documented .rodata edits (translated
     strings, metric bytes). v180 ground truth: 327 diff bytes in 50 runs,
     zero on pristine-zero. Budgets below give modest headroom; if this trips,
     account for the delta before bumping (never bump to silence it).

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

ARENA_LO_VA, ARENA_HI_VA = 0x4B0E00, 0x4FDE30
SBRK_FILE_OFF = 0x3AF6D4
SBRK_PRISTINE = 0x00579800
TABLE_VAS = (0x1215B4, 0x121610, 0x12166C, 0x1216C8)  # ADV / LSH / ADV2 / LSH2
TABLE_LEN = 92
STRNCPY_VA = 0x121568

ARENA_DIFF_BYTE_BUDGET = 400   # v180 ground truth: 327
ARENA_DIFF_RUN_BUDGET = 60     # v180 ground truth: 50


def _fo(va):
    return va - 0x100000 + 0x80


def _load():
    require_file(PRISTINE_EXE, "pristine EXE extract")
    require_file(PATCHED_EXE, "patched EXE build output")
    return open(PRISTINE_EXE, "rb").read(), open(PATCHED_EXE, "rb").read()


def test_exe_size_unchanged():
    pristine, patched = _load()
    assert len(patched) == len(pristine), (
        "EXE size changed (%d -> %d): Option-E requires no ELF growth; any "
        "growth means header surgery the PS2 BIOS may reject (the v174 lesson)"
        % (len(pristine), len(patched)))


def test_elf_header_pristine_shape():
    pristine, patched = _load()
    e_phoff = struct.unpack_from("<I", patched, 0x1C)[0]
    e_phnum = struct.unpack_from("<H", patched, 0x2C)[0]
    assert e_phnum == 2, "e_phnum changed (%d != 2)" % e_phnum
    ph1 = e_phoff + 32
    filesz = struct.unpack_from("<I", patched, ph1 + 16)[0]
    assert filesz == 0, (
        "PH1 filesz = 0x%X != 0: the spare program header was repurposed -- "
        "that is the v174 design the PS2 BIOS refused to boot" % filesz)
    assert patched[:0x34] == pristine[:0x34], "ELF header bytes differ from pristine"


def test_sbrk_break_pristine():
    pristine, patched = _load()
    for name, exe in (("pristine", pristine), ("patched", patched)):
        w = struct.unpack_from("<I", exe, SBRK_FILE_OFF)[0]
        assert w == SBRK_PRISTINE, (
            "%s sbrk break word @file 0x%06X is 0x%08X, expected 0x%08X"
            % (name, SBRK_FILE_OFF, w, SBRK_PRISTINE))


def test_tables_in_strncpy_span():
    pristine, patched = _load()
    # strncpy head must actually be rewritten (the shrink happened)
    assert patched[_fo(STRNCPY_VA):_fo(STRNCPY_VA) + 16] != \
        pristine[_fo(STRNCPY_VA):_fo(STRNCPY_VA) + 16], (
        "strncpy @0x121568 is pristine -- the Option-E shrink is missing, so "
        "the tables have nowhere safe to live")
    for va in TABLE_VAS:
        span = patched[_fo(va):_fo(va) + TABLE_LEN]
        nonzero = sum(1 for b in span if b)
        assert nonzero >= TABLE_LEN // 2, (
            "metric table @VA 0x%06X looks empty (%d/%d nonzero) -- the "
            "Option-E table relocation did not land" % (va, nonzero, TABLE_LEN))


def test_arena_law():
    pristine, patched = _load()
    lo, hi = _fo(ARENA_LO_VA), _fo(ARENA_HI_VA)
    a, b = pristine[lo:hi], patched[lo:hi]
    diff_bytes = 0
    runs = 0
    in_run = False
    violations = []
    for i in range(len(a)):
        if a[i] != b[i]:
            diff_bytes += 1
            if not in_run:
                runs += 1
                in_run = True
            if a[i] == 0x00:
                violations.append(ARENA_LO_VA + i)
        else:
            in_run = False
    assert not violations, (
        "ARENA LAW VIOLATED: %d patched byte(s) fill pristine-zero heap padding "
        "in the battle arena (first at VA 0x%06X). This is the exact "
        "empty-battle/harpy softlock mechanism. NEVER ship this."
        % (len(violations), violations[0]))
    assert diff_bytes <= ARENA_DIFF_BYTE_BUDGET and runs <= ARENA_DIFF_RUN_BUDGET, (
        "arena diff grew past the documented .rodata edits: %d bytes in %d runs "
        "(budget %d/%d; v180 ground truth 327/50). Account for the delta before "
        "bumping the budget." % (diff_bytes, runs,
                                 ARENA_DIFF_BYTE_BUDGET, ARENA_DIFF_RUN_BUDGET))


TESTS = [
    test_exe_size_unchanged,
    test_elf_header_pristine_shape,
    test_sbrk_break_pristine,
    test_tables_in_strncpy_span,
    test_arena_law,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_optione_arena")
