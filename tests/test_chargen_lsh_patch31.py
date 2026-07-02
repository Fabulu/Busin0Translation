#!/usr/bin/env python3
"""
test_chargen_lsh_patch31.py -- lock Patch 31 (chargen description-box first-letter
gap LSH fix), NEW in v157.

Patch 26 gave the LIVE chargen body/description renderer func 0x307510 (line-walk
0x307DA0 -> glyph blit 0x307510 -> emit 0x3060B0) a proportional ADVANCE (hook
@0x3079CC, gated mem[0x4FED18]==5) but NOT the companion left-bearing draw-shift.
Patch 31 is the 0x307510 analogue of Patch 29: it subtracts LEFTSHIFT2[gid] (the
R2100 table @0x4B1100 -- v158: this renderer draws the R2100 upright 16px font,
NOT R1188) from the SINGLE draw-X site 0x307974 (`lh t2,0(s2)`, the penX read
feeding `addu t2,t2,t0` @0x307980), mode-gated ==5 so ADV+LSH stay in lockstep and
every other surface is byte-identical (subu 0).  gid = the ACTUAL drawn glyph,
stored `sd v0,0x10(sp)` @0x307960 (recovered `lhu 0x10(sp)`), ASCII-guarded
(sltiu<95 + movz).  Branchless sub split across two verified-zero post-`jr ra`
.text pads below the arena: frag1 @0x4AFA00 (40B) + frag2 @0x4AB5EC (20B).

This module pins:
  D (static, always): the design in build/_reloc_v147_design.py -- the hook is `j`
     frag1; frag1 sources LSH2 from lbu 0x1100(0x4B0000) and recovers gid via
     lhu 0x10(sp); frag2 reads mode via the same absolute path Patch 26 uses
     (lw -0x12E8), folds to ==5, and returns `j 0x30797C` with `subu t2,t2,t9` in
     the delay slot; both fragments live below the arena with no overlap.
  B (TIER-2, SKIP when build/SLPM_653.78_patched absent): the BUILT patched EXE has
     the draw-X site = j cave, the two fragments byte-match the design, and the
     pristine delay slot (lh t1,0(v0)) at 0x307978 is preserved.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, Skip, main_exit  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "build"))
import _reloc_v147_design as RELOC  # noqa: E402

PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")


def _op(w):    return w >> 26
def _rs(w):    return (w >> 21) & 31
def _rt(w):    return (w >> 16) & 31
def _rd(w):    return (w >> 11) & 31
def _fn(w):    return w & 0x3F
def _imm(w):   return w & 0xFFFF


# ── D: design invariants (always run) ────────────────────────────────────────
def test_d1_hook_is_j_to_frag1_at_drawx_site():
    """The single draw-X site 0x307974 hooks to `j frag1` below the arena."""
    assert RELOC.P31_HOOK == 0x307974
    assert RELOC.P31_ORIG_SITE == 0x864A0000  # lh t2,0(s2)
    jw = RELOC.P31_HOOK_JWORD
    assert _op(jw) == 0x02, "Patch 31 hook must be a `j` (op 2)"
    assert ((jw & 0x3FFFFFF) << 2) == RELOC.P31_F1_VA, "j target != frag1 VA"
    assert RELOC.P31_F1_VA == 0x4AFA00 and RELOC.P31_F2_VA == 0x4AB5EC


def test_d2_frag1_sources_lsh_from_r2100_table():
    """v158: frag1 READS LEFTSHIFT from the R2100 LSH2 table @0x4B1100
    (lui t9,0x4B ; ... ; lbu t9,0x1100(t9)) — the 0x307510 chargen path draws
    the R2100 upright 16px font, NOT the oblique R1188 font the canonical
    table @0x4C7690 was measured from (the "Ge nde r" root cause)."""
    f1 = RELOC.P31_F1_WORDS
    assert RELOC.LSH2_VA == 0x4B1100 and RELOC.LSH_VA == 0x4C7690
    assert any(_op(w) == 0x0F and _imm(w) == (RELOC.LSH2_VA >> 16) for w in f1), (
        "frag1 must lui the R2100 LSH2 table base 0x%X0000" % (RELOC.LSH2_VA >> 16)
    )
    assert any(_op(w) == 0x24 and _imm(w) == (RELOC.LSH2_VA & 0xFFFF) for w in f1), (
        "frag1 must lbu LEFTSHIFT2[gid] at 0x%X == RELOC.LSH2_VA" % (RELOC.LSH2_VA & 0xFFFF)
    )
    # TEETH: the R1188 canonical LSH must no longer be read here (wrong font).
    assert not any(_op(w) == 0x24 and _imm(w) == 0x7690 for w in f1), (
        "frag1 still reads the canonical R1188 LSH @0x7690 -- wrong font (v158 regression)"
    )


def test_d3_gid_recovered_and_ascii_guarded():
    """gid is the stored drawn glyph `lhu t8,0x10(sp)`, and the read is ASCII-guarded
    (sltiu <95 + movz -> gid>=95 subtracts nothing; index bounded by andi 0xFF)."""
    f1 = RELOC.P31_F1_WORDS
    # lhu t8, 0x10(sp)  (op 0x25, rt=t8=24, rs=sp=29, off=0x10)
    assert any(_op(w) == 0x25 and _rt(w) == 24 and _rs(w) == 29 and _imm(w) == 0x10
               for w in f1), "frag1 must recover gid via lhu 0x10(sp)"
    assert any(_op(w) == 0x0B and _imm(w) == 95 for w in f1), (
        "frag1 must ASCII-guard via sltiu <95"
    )
    assert any(_op(w) == 0x0C and _imm(w) == 0xFF for w in f1), (
        "frag1 must bound the table index via andi 0xFF"
    )
    # movz t9,zero,at (fn 0x0A) zeroes the shift when gid>=95
    assert any(_op(w) == 0x00 and _fn(w) == 0x0A for w in f1), "frag1 must movz (guard)"


def test_d4_mode_gate_matches_patch26_read_and_folds_to_5():
    """The mode gate reads 0x4FED18 via the absolute path (lui 0x50 ; lw -0x12E8) and
    folds to ==5 (addiu -5 + movn -> non-5 subtracts nothing)."""
    f1 = RELOC.P31_F1_WORDS
    f2 = RELOC.P31_F2_WORDS
    allw = list(f1) + list(f2)
    assert any(_op(w) == 0x0F and _imm(w) == 0x0050 for w in allw), "mode read: lui 0x50"
    assert any(_op(w) == 0x23 and _imm(w) == (0x10000 - 0x12E8) for w in allw), (
        "mode read: lw -0x12E8 (RAM 0x4FED18) -- same as Patch 26"
    )
    assert any(_op(w) == 0x09 and _imm(w) == (0x10000 - 5) for w in allw), (
        "gate must subtract 5 (mode-5, chargen only)"
    )
    # movn t9,zero,at (fn 0x0B) zeroes the shift when mode!=5
    assert any(_op(w) == 0x00 and _fn(w) == 0x0B for w in f2), "frag2 must movn (mode gate)"


def test_d5_frag2_returns_and_subtracts_drawx():
    """frag2 ends with `j 0x30797C` (return to the draw block) and its delay slot
    `subu t2,t2,t9` (draw-X penX -= LSH)."""
    f2 = RELOC.P31_F2_WORDS
    assert any(_op(w) == 0x02 and ((w & 0x3FFFFFF) << 2) == 0x30797C for w in f2), (
        "frag2 must return via j 0x30797C"
    )
    # subu t2,t2,t9 : rd=t2=10, rs=t2=10, rt=t9=25, fn 0x23
    assert any(_op(w) == 0x00 and _fn(w) == 0x23 and _rd(w) == 10 and _rt(w) == 25
               for w in f2), "frag2 must subu t2,t2,t9 (draw-X -= LSH)"


def test_d6_fragments_below_arena_no_overlap():
    """Both fragments are dead .text padding below the arena, clear of the libgraph
    block, registered in CAVE_RELOC, and do not overlap any existing cave."""
    for va, words, label in (
        (RELOC.P31_F1_VA, RELOC.P31_F1_WORDS, "P31 frag1"),
        (RELOC.P31_F2_VA, RELOC.P31_F2_WORDS, "P31 frag2"),
    ):
        RELOC.assert_install_safe(va, len(words) * 4, label)  # raises on violation
    assert "P31f1" in RELOC.CAVE_RELOC and "P31f2" in RELOC.CAVE_RELOC, (
        "fragments must be registered in CAVE_RELOC for the overlap self-check"
    )
    spans = [(nv, nv + sz, lb) for lb, (ov, nv, sz) in RELOC.CAVE_RELOC.items()]
    spans.append((RELOC.P27_VA, RELOC.P27_VA + len(RELOC.P27_WORDS) * 4, "P27"))
    spans.sort()
    for i in range(1, len(spans)):
        assert spans[i][0] >= spans[i - 1][1], (
            "cave overlap: %s [0x%06X,0x%06X) vs %s [0x%06X,0x%06X)"
            % (spans[i - 1][2], spans[i - 1][0], spans[i - 1][1],
               spans[i][2], spans[i][0], spans[i][1])
        )


# ── B: built-EXE invariants (SKIP when patched EXE absent) ────────────────────
def _load_patched():
    if not os.path.isfile(PATCHED_EXE):
        raise Skip("build/SLPM_653.78_patched missing (run the build)")
    with open(PATCHED_EXE, "rb") as fh:
        return fh.read()


def test_b1_built_hook_installed():
    """Built EXE: the draw-X site 0x307974 is `j frag1`, and the pristine delay slot
    at 0x307978 (`lh t1,0(v0)`) is preserved (the cave reloads penX)."""
    data = _load_patched()
    jw = RELOC.P31_HOOK_JWORD
    w = struct.unpack_from("<I", data, RELOC.fo(RELOC.P31_HOOK))[0]
    assert w == jw, "site 0x307974 = 0x%08X, expected j cave 0x%08X" % (w, jw)
    ds = struct.unpack_from("<I", data, RELOC.fo(RELOC.P31_HOOK + 4))[0]
    assert ds == 0x84490000, (
        "delay slot 0x307978 = 0x%08X, expected pristine lh t1,0(v0) 0x84490000" % ds
    )


def test_b2_built_fragments_match_design():
    """Built EXE: both fragments byte-match _reloc_v147_design build_p31()."""
    data = _load_patched()
    for va, words, label in (
        (RELOC.P31_F1_VA, RELOC.P31_F1_WORDS, "frag1"),
        (RELOC.P31_F2_VA, RELOC.P31_F2_WORDS, "frag2"),
    ):
        f = RELOC.fo(va)
        got = [struct.unpack_from("<I", data, f + i * 4)[0] for i in range(len(words))]
        assert got == list(words), (
            "Patch 31 %s @0x%06X does not match design module" % (label, va)
        )


def test_b3_built_cave_reads_lsh_and_gates():
    """Built EXE: the shipped cave contains both the LSH2 read (v158: lbu
    0x1100(0x4B0000)) and the mode read (lw -0x12E8)."""
    data = _load_patched()
    allw = []
    for va, words in ((RELOC.P31_F1_VA, RELOC.P31_F1_WORDS),
                      (RELOC.P31_F2_VA, RELOC.P31_F2_WORDS)):
        f = RELOC.fo(va)
        allw += [struct.unpack_from("<I", data, f + i * 4)[0] for i in range(len(words))]
    assert any(_op(w) == 0x24 and _imm(w) == (RELOC.LSH2_VA & 0xFFFF) for w in allw), (
        "shipped cave must read LSH2 @0x%X" % (RELOC.LSH2_VA & 0xFFFF)
    )
    assert any(_op(w) == 0x23 and _imm(w) == (0x10000 - 0x12E8) for w in allw), (
        "shipped cave must read mode @-0x12E8 (the ==5 gate)"
    )


TESTS = [
    test_d1_hook_is_j_to_frag1_at_drawx_site,
    test_d2_frag1_sources_lsh_from_r2100_table,
    test_d3_gid_recovered_and_ascii_guarded,
    test_d4_mode_gate_matches_patch26_read_and_folds_to_5,
    test_d5_frag2_returns_and_subtracts_drawx,
    test_d6_fragments_below_arena_no_overlap,
    test_b1_built_hook_installed,
    test_b2_built_fragments_match_design,
    test_b3_built_cave_reads_lsh_and_gates,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_chargen_lsh_patch31")
