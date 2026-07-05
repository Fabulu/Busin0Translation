#!/usr/bin/env python3
"""
test_chargen_lsh_patch29.py -- lock Patch 29 (box-text first-letter-gap LSH fix).

Patch 27 gave the shared chargen/request renderer func 0x3A2EF0 proportional
ADVANCE but omitted the companion left-bearing draw-shift (LSH), so box ink lands
at baseX + pen + ink_left(gid) and a huge gap opens after a low-bearing leading
capital ("A....llocate").  Patch 29 mirrors Patch 14 cave2 for BOTH glyph draw-X
sites in 0x3A2EF0 (0x3A30F4 / 0x3A3170), hooking each with a `jal` into ONE shared
subroutine that subtracts LEFTSHIFT2[gid] from the R2100 table @0x4B1100 (v158:
this renderer draws the R2100 upright 16px font in modes 5/7, NOT R1188),
mode-gated on 0x4FED18 in {5,7} (battle mode 8 stays byte-identical).

This module pins:
  D (static, always): the design in build/_reloc_v147_design.py -- both hooks are
     `jal` the frag1 cave; frag1 sources LSH2 from lbu 0x1100(0x4B0000) and reads
     the mode via the SAME absolute path as Patch 27 (lui 0x50 / lw -0x12E8);
     frag2 gates via movn and returns with jr ra + subu; both fragments live
     below the arena with no overlap.
  B (TIER-2, SKIP when build/SLPM_653.78_patched absent): the BUILT patched EXE
     has both sites = jal cave, the two fragments byte-match the design, and the
     pristine jal delay slots (lbu v0,off(sp)) are preserved.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, Skip  # noqa: E402
from _helpers import main_exit   # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "build"))
import _reloc_v147_design as RELOC  # noqa: E402

PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")

# Opcode helpers for word inspection
def _op(w):    return w >> 26
def _rs(w):    return (w >> 21) & 31
def _rt(w):    return (w >> 16) & 31
def _rd(w):    return (w >> 11) & 31
def _fn(w):    return w & 0x3F
def _imm(w):   return w & 0xFFFF


# ── D: design invariants (always run) ────────────────────────────────────────
def test_d1_hooks_are_jal_to_frag1():
    """Both draw-X sites hook to `jal frag1`, and the hooked word is a jal into the
    fragment 1 cave below the arena."""
    assert RELOC.P29_HOOK1 == 0x3A30F4 and RELOC.P29_HOOK2 == 0x3A3170
    jw = RELOC.P29_HOOK_JWORD
    assert _op(jw) == 0x03, "Patch 29 hook must be a jal (op 3)"
    assert ((jw & 0x3FFFFFF) << 2) == RELOC.P29_F1_VA, "jal target != frag1 VA"
    assert RELOC.P29_F1_VA == 0x4B0C48 and RELOC.P29_F2_VA == 0x4B0BC8


def test_d2_frag1_sources_lsh_from_r2100_table():
    """v158: frag1 must READ LEFTSHIFT from the R2100 LSH2 table @0x4B1100
    (lui t9,0x4B ; ... ; lbu t9,0x1100(t9)) — the 0x3A2EF0 renderer draws the
    R2100 upright 16px font in modes 5/7, NOT the oblique R1188 font the
    canonical table @0x4C7690 was measured from (the "Ge nde r" root cause)."""
    f1 = RELOC.P29_F1_WORDS
    # v170: LSH2 relocated to the FREE200 dead libgraph pad (0x4AF338..0x4AF400), 95B.
    assert (RELOC.ADV2_VA + 95 <= RELOC.LSH2_VA and RELOC.LSH2_VA + 95 <= 0x4AF400
            and RELOC.LSH_VA == 0x4C7690)
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


def test_d3_gid_recovered_via_lbu_minus1_s2_into_k1():
    """gid recovery is `lbu k1,-1(s2)` -- s2 already points past the current BE-u16
    glyph, and v170 carries gid in SCRATCH k1 (R1) so the gid>=95 guard can fold into
    frag2's 8 free bytes."""
    f1 = RELOC.P29_F1_WORDS
    assert any(
        _op(w) == 0x24 and _rs(w) == 18 and _rt(w) == 27 and _imm(w) == 0xFFFF  # k1,-1(s2)
        for w in f1
    ), "frag1 must recover gid into k1 via lbu k1,-1(s2)"


def test_d3b_gid_ascii_guard_in_frag2():
    """v170: because LSH2 is now a 95-byte table (relocated out of the arena), frag2
    ADDS a gid>=95 ASCII guard that reproduces the old 256-byte zero tail: sltiu at,k1,95
    then movz t9,zero,at -> a non-ASCII gid subtracts 0 (never over-indexes the 95B table)."""
    f2 = RELOC.P29_F2_WORDS
    # sltiu at,k1,95  (op 0x0b, rs=k1=27, rt=at=1, imm=95)
    assert any(_op(w) == 0x0B and _rs(w) == 27 and _imm(w) == 95 for w in f2), (
        "frag2 must ASCII-guard the gid via sltiu at,k1,95"
    )
    # a movz (fn 0x0A) that zeroes the shift when the guard fails
    assert any(_op(w) == 0x00 and _fn(w) == 0x0A for w in f2), (
        "frag2 must movz (zero the LSH when gid>=95)"
    )
    # frag2 now fills its 24B pad exactly (6 words).
    assert len(f2) == 6, "P29 frag2 must be 6 words (24B), got %d" % len(f2)


def test_d4_mode_gate_present_matches_patch27_read():
    """The mode gate reads 0x4FED18 via the SAME absolute path Patch 27 uses
    (lui 0x50 ; lw -0x12E8), and the fold to {5,7} + movn is present so a non-gated
    mode subtracts nothing (byte-identical stock draw-X)."""
    f1 = RELOC.P29_F1_WORDS
    f2 = RELOC.P29_F2_WORDS
    assert any(_op(w) == 0x0F and _imm(w) == 0x0050 for w in f1), "mode read: lui 0x50"
    assert any(_op(w) == 0x23 and _imm(w) == (0x10000 - 0x12E8) for w in f1), (
        "mode read: lw -0x12E8 (RAM 0x4FED18) -- same as Patch 27"
    )
    # gate fold: addiu at,at,-5 then andi at,at,0xFFFD (true iff mode in {5,7})
    all_words = list(f1) + list(f2)
    assert any(_op(w) == 0x09 and _imm(w) == (0x10000 - 5) for w in all_words), (
        "gate must subtract 5 (mode-5)"
    )
    assert any(_op(w) == 0x0C and _imm(w) == 0xFFFD for w in all_words), (
        "gate must andi 0xFFFD (clear bit1 -> 0 iff mode in {5,7})"
    )
    # movn t9,zero,at : zero the shift when not gated
    assert any(_op(w) == 0x00 and _fn(w) == 0x0B for w in f2), (
        "frag2 must movn (zero the LSH when not gated)"
    )


def test_d5_frag2_returns_jr_ra_and_subtracts():
    """frag2 ends with `jr ra` and its delay slot `subu v1,v1,t9` (draw-X -= LSH)."""
    f2 = RELOC.P29_F2_WORDS
    assert any(_op(w) == 0x00 and _fn(w) == 0x08 and _rs(w) == 31 for w in f2), (
        "frag2 must jr ra"
    )
    assert any(_op(w) == 0x00 and _fn(w) == 0x23 and _rd(w) == 3 for w in f2), (
        "frag2 must subu v1,v1,t9 (draw-X -= LSH)"
    )


def test_d6_fragments_below_arena_no_overlap():
    """Both fragments are in dead .text padding below the arena, clear of the PsII
    libgraph block, and do not overlap any existing cave (guardrail + CAVE_RELOC)."""
    for va, words, label in (
        (RELOC.P29_F1_VA, RELOC.P29_F1_WORDS, "P29 frag1"),
        (RELOC.P29_F2_VA, RELOC.P29_F2_WORDS, "P29 frag2"),
    ):
        RELOC.assert_install_safe(va, len(words) * 4, label)  # raises on violation
    assert "P29f1" in RELOC.CAVE_RELOC and "P29f2" in RELOC.CAVE_RELOC, (
        "fragments must be registered in CAVE_RELOC so the overlap self-check covers them"
    )
    # explicit pairwise overlap check against every registered cave + P27
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


def test_b1_built_hooks_installed():
    """Built EXE: both draw-X sites are `jal frag1`, and the pristine delay-slot
    lbu v0,off(sp) at each site+4 is preserved (the cave reloads baseX)."""
    data = _load_patched()
    jw = RELOC.P29_HOOK_JWORD
    for va in (RELOC.P29_HOOK1, RELOC.P29_HOOK2):
        w = struct.unpack_from("<I", data, RELOC.fo(va))[0]
        assert w == jw, "site 0x%06X = 0x%08X, expected jal cave 0x%08X" % (va, w, jw)
        ds = struct.unpack_from("<I", data, RELOC.fo(va + 4))[0]
        # delay slot must be a preserved `lbu v0,imm(sp)` (op 0x24, rt=v0, rs=sp)
        assert _op(ds) == 0x24 and _rt(ds) == 2 and _rs(ds) == 29, (
            "site 0x%06X delay slot 0x%08X is not the pristine lbu v0,off(sp)" % (va, ds)
        )


def test_b2_built_fragments_match_design():
    """Built EXE: both fragments byte-match _reloc_v147_design build_p29()."""
    data = _load_patched()
    for va, words, label in (
        (RELOC.P29_F1_VA, RELOC.P29_F1_WORDS, "frag1"),
        (RELOC.P29_F2_VA, RELOC.P29_F2_WORDS, "frag2"),
    ):
        f = RELOC.fo(va)
        got = [struct.unpack_from("<I", data, f + i * 4)[0] for i in range(len(words))]
        assert got == list(words), (
            "Patch 29 %s @0x%06X does not match design module" % (label, va)
        )


def test_b3_built_cave_reads_lsh_and_gates():
    """Built EXE frag1 contains the lbu LSH2 read (v158: 0x1100(0x4B0000)) and the
    lw -0x12E8 (mode read) -- proves the shipped cave both sources LSH2 and
    mode-gates."""
    data = _load_patched()
    f = RELOC.fo(RELOC.P29_F1_VA)
    words = [struct.unpack_from("<I", data, f + i * 4)[0] for i in range(len(RELOC.P29_F1_WORDS))]
    assert any(_op(w) == 0x24 and _imm(w) == (RELOC.LSH2_VA & 0xFFFF) for w in words), (
        "shipped frag1 must read LSH2 @0x%X" % (RELOC.LSH2_VA & 0xFFFF)
    )
    assert any(_op(w) == 0x23 and _imm(w) == (0x10000 - 0x12E8) for w in words), (
        "shipped frag1 must read mode @-0x12E8 (the {5,7} gate)"
    )


TESTS = [
    test_d1_hooks_are_jal_to_frag1,
    test_d2_frag1_sources_lsh_from_r2100_table,
    test_d3_gid_recovered_via_lbu_minus1_s2_into_k1,
    test_d3b_gid_ascii_guard_in_frag2,
    test_d4_mode_gate_present_matches_patch27_read,
    test_d5_frag2_returns_jr_ra_and_subtracts,
    test_d6_fragments_below_arena_no_overlap,
    test_b1_built_hooks_installed,
    test_b2_built_fragments_match_design,
    test_b3_built_cave_reads_lsh_and_gates,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_chargen_lsh_patch29")
