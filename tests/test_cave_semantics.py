#!/usr/bin/env python3
"""
test_cave_semantics.py -- L0 STATIC PRE-BUILD SEMANTIC GATE for EXE caves.

The existing cave tests (test_reloc_caves_installed.py, test_glyph_metrics_sync)
are BYTE-EQUALITY: they confirm the design words were installed correctly.  They
are STRUCTURALLY BLIND to the two regressions that actually shipped:

  BUG#1  sign-extension -- a table meant at VA 0x4AF338 read via `lui at,0x4A` +
         `lbu ...,0xF338(at)`; 0xF338>=0x8000 sign-extends to -0xCC8 so the
         EFFECTIVE address is 0x49F338 (garbage) -> garbled chargen.  Every
         byte/immediate test (lui==VA>>16) passes on that broken cave.
  BUG#2  register clobber -- a cave used k1 (reg 27).  k0/k1 are KERNEL-live
         (async interrupts trash them) -> post-chargen black screen.  The hazard
         is prose at build/patch_exe.py:1040-1045 but was UNENFORCED.

This module decodes every cave with tools/mips_cave_analyzer.py and enforces:
  * RULE K            -- no k0/k1 in any cave word (catches BUG#2).
  * EFFECTIVE-ADDRESS -- every absolute table/mode read resolves (with correct
                         sign-extension) to a VA in the address book derived
                         from the relocation single-source (catches BUG#1).
And, crucially, test_regression_catches_v171_bugs FEEDS THE GATE the two known
BAD v171 caves and asserts it goes RED -- a gate that cannot catch the last two
bugs is not done.

TIER-2 (SKIP if build/SLPM_653.78_patched absent): the same checks are run on
the caves decoded straight out of the BUILT EXE at their install VAs, catching
install drift the design-word checks cannot see.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, Skip, main_exit          # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "build"))
import _reloc_v147_design as RELOC                   # noqa: E402  (single source)

sys.path.insert(0, os.path.join(ROOT, "tools"))
import mips_cave_analyzer as MCA                      # noqa: E402

# The P26/P24/P19 cave words live only inside patch_exe.py main(); the sibling
# byte-pin test already mirrors them VERBATIM (with source-line citations), so
# reuse that single mirror rather than making a third copy.
import test_reloc_caves_installed as CAVES           # noqa: E402

PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")

BOOK = MCA.address_book(RELOC)

# ---------------------------------------------------------------------------
# The full cave registry: (name, design_words, install_VA, expected_read_EAs)
# expected_read_EAs pins the EXACT absolute LOADs each cave should perform
# (None = don't pin the set, only require every access be in the book).
# ---------------------------------------------------------------------------
CAVES_REGISTRY = [
    ("P27",   RELOC.P27_WORDS,       RELOC.P27_VA,   {MCA.MODE_SENTINEL_VA, RELOC.ADV2_VA}),
    ("P14c1", RELOC.P14C1_WORDS,     RELOC.P14C1_VA, {RELOC.ADV_VA}),
    ("P14c2", RELOC.P14C2_WORDS,     RELOC.P14C2_VA, {RELOC.LSH_VA}),
    ("P26",   CAVES.P26_CAVE_WORDS,  RELOC.P26_VA,   {MCA.MODE_SENTINEL_VA, RELOC.ADV2_VA}),
    ("P24",   CAVES.P24_CAVE_WORDS,  RELOC.P24_VA,   set()),
    ("P19c1", CAVES.P19_CAVE1_WORDS, RELOC.P19C1_VA, {RELOC.ADV_VA}),
    ("P19c2", CAVES.P19_CAVE2_WORDS, RELOC.P19C2_VA, {RELOC.LSH_VA}),
    ("P29f1", RELOC.P29_F1_WORDS,    RELOC.P29_F1_VA, {RELOC.LSH2_VA, MCA.MODE_SENTINEL_VA}),
    ("P29f2", RELOC.P29_F2_WORDS,    RELOC.P29_F2_VA, set()),
    ("P31f1", RELOC.P31_F1_WORDS,    RELOC.P31_F1_VA, {RELOC.LSH2_VA}),
    # P31f2's mode read spans the frag1->frag2 boundary (lui in frag1, lw in
    # frag2), so decoded ALONE it exposes no lui-const base -> no recorded abs
    # access.  That is correct: no false positive, and the mode read IS pinned
    # in P27/P26/P29f1 where it is self-contained.
    ("P31f2", RELOC.P31_F2_WORDS,    RELOC.P31_F2_VA, set()),
]

# Caves that MUST prove they read the mode sentinel 0x4FED18 (self-contained).
MODE_READERS = {"P27", "P26", "P29f1"}


# ===========================================================================
# K1 -- RULE K on every DESIGN cave
# ===========================================================================
def test_rule_k_all_caves():
    """No cave word may reference k0/k1 (KERNEL-live).  Would have caught the
    v171 k1 clobber (BUG#2)."""
    problems = []
    for name, words, va, _ in CAVES_REGISTRY:
        insns = MCA.decode(words, va)
        fails, warns = MCA.check_no_kernel_regs(insns)
        for f in fails:
            problems.append("%s: %s" % (name, f['msg']))
        for w in warns:
            # t9/gp are legitimate here (P29/P31 use t9 as the LSH scratch, P19
            # uses gp for .cpload); surface them but do NOT fail.
            print("  [rule-k warn] %s: %s" % (name, w['msg']))
    assert not problems, "RULE K violations:\n  " + "\n  ".join(problems)


# ===========================================================================
# K2 -- EFFECTIVE-ADDRESS verify on every DESIGN cave
# ===========================================================================
def test_effective_addresses_all_caves():
    """Every absolute (lui-const-based) table/mode read must resolve -- with
    correct sign-extension -- to a VA in the address book, and match the exact
    expected read set.  Would have caught the v171 lui-0x4A garble (BUG#1)."""
    problems = []
    for name, words, va, expected in CAVES_REGISTRY:
        insns = MCA.decode(words, va)
        fails = MCA.check_effective_addresses(insns, BOOK, expected=expected)
        for f in fails:
            problems.append("%s: %s" % (name, f['msg']))
    assert not problems, "effective-address violations:\n  " + "\n  ".join(problems)


def test_mode_read_resolves_to_sentinel():
    """The mode read (lui 0x50; lw -0x12E8 -> 0x500000 + sext16(0xED18) =
    0x4FED18) must resolve to the sentinel in every self-contained mode-gated
    cave -- proves the sign-extension math AND that the gate is on the mode."""
    problems = []
    for name, words, va, _ in CAVES_REGISTRY:
        if name not in MODE_READERS:
            continue
        insns = MCA.decode(words, va)
        eas = {a['ea'] for a in MCA.resolve_absolute_accesses(insns)
               if a['kind'] == 'load'}
        if MCA.MODE_SENTINEL_VA not in eas:
            problems.append(
                "%s: mode read did NOT resolve to 0x%06X (got %s)"
                % (name, MCA.MODE_SENTINEL_VA, sorted('0x%06X' % v for v in eas)))
    assert not problems, "; ".join(problems)


# ===========================================================================
# THE CRUCIAL REGRESSION PROOF -- the gate must go RED on the real v171 bugs
# ===========================================================================
def test_regression_catches_v171_bugs():
    """Feed the gate hand-built fixtures of the KNOWN-BAD v171 caves and assert
    it FLAGS them.  If either fixture is not flagged, the gate is worthless and
    THIS TEST FAILS LOUDLY."""

    # (a) BUG#1 -- lui at,0x4A + addu at,at,gid + lbu v1,0xF338(at).
    #     0xF338 sign-extends to -0xCC8 => EA 0x4A0000-0xCC8 = 0x49F338 (garbage,
    #     NOT the intended 0x4AF338).  check_effective_addresses MUST flag it.
    bug1 = [
        RELOC.lui('at', 0x4A),
        RELOC.addu('at', 'at', 'v1'),
        RELOC.lbu('v1', 0xF338, 'at'),
    ]
    insns1 = MCA.decode(bug1, 0x4AB554)
    # sanity: the analyser must actually compute the garbage EA
    accesses = MCA.resolve_absolute_accesses(insns1)
    eas = [a['ea'] for a in accesses]
    assert 0x49F338 in eas, (
        "regression harness broken: analyser did not compute the sign-extended "
        "EA 0x49F338 for the BUG#1 fixture (got %s)" % [hex(e) for e in eas])
    fails1 = MCA.check_effective_addresses(insns1, BOOK)
    assert fails1, (
        "GATE FAILED TO CATCH BUG#1: the sign-extension garble (EA 0x49F338) "
        "was NOT flagged by check_effective_addresses -- the address gate is "
        "not protecting anything")
    assert any(f['ea'] == 0x49F338 for f in fails1), \
        "BUG#1 flagged but not on the expected EA 0x49F338"

    # (b) BUG#2 -- a cave word using k1 (reg 27).  check_no_kernel_regs MUST flag.
    bug2 = [RELOC.sltiu('k1', 'v1', 95)]
    insns2 = MCA.decode(bug2, 0x4AB554)
    fails2, _ = MCA.check_no_kernel_regs(insns2)
    assert fails2, (
        "GATE FAILED TO CATCH BUG#2: a k1 (reg 27) cave word was NOT flagged by "
        "check_no_kernel_regs -- RULE K is not protecting anything")
    assert any(f['reg'] == MCA.K1 for f in fails2), \
        "BUG#2 flagged but not on k1 (reg 27)"

    # (c) also prove k0 is banned and t9/gp only WARN (so the gate is not so
    #     trigger-happy it would forbid the legitimate P29/P31/P19 warnings).
    fails_k0, _ = MCA.check_no_kernel_regs(MCA.decode([RELOC.addu('k0', 'v0', 'v1')], 0))
    assert any(f['reg'] == MCA.K0 for f in fails_k0), "k0 not banned"
    fails_t9, warns_t9 = MCA.check_no_kernel_regs(MCA.decode([RELOC.lui('t9', 0x4B)], 0))
    assert not fails_t9 and any(w['reg'] == MCA.T9 for w in warns_t9), \
        "t9 should WARN, not FAIL"


# ===========================================================================
# TIER-2 -- decode the caves out of the BUILT EXE (catches install drift)
# ===========================================================================
def _read_built_cave(exe, va, nwords):
    fo = RELOC.fo(va)
    if fo < 0 or fo + nwords * 4 > len(exe):
        raise AssertionError("cave VA 0x%06X out of EXE range" % va)
    return list(struct.unpack_from("<%dI" % nwords, exe, fo))


def test_built_exe_caves_semantics():
    """TIER-2: run RULE K + effective-address on the caves DECODED FROM the
    built EXE at their install VAs.  A mis-typed cave that drifted from the
    design (or an install that landed the wrong words) is caught here even if
    the design-word checks pass."""
    if not os.path.isfile(PATCHED_EXE):
        raise Skip("build/SLPM_653.78_patched missing (run build/patch_exe.py)")
    exe = open(PATCHED_EXE, "rb").read()
    problems = []
    for name, words, va, expected in CAVES_REGISTRY:
        built = _read_built_cave(exe, va, len(words))
        insns = MCA.decode(built, va)
        kfails, _ = MCA.check_no_kernel_regs(insns)
        for f in kfails:
            problems.append("%s(built): %s" % (name, f['msg']))
        efails = MCA.check_effective_addresses(insns, BOOK, expected=expected)
        for f in efails:
            problems.append("%s(built): %s" % (name, f['msg']))
    assert not problems, "built-EXE cave violations:\n  " + "\n  ".join(problems)


TESTS = [
    test_rule_k_all_caves,
    test_effective_addresses_all_caves,
    test_mode_read_resolves_to_sentinel,
    test_regression_catches_v171_bugs,
    test_built_exe_caves_semantics,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_cave_semantics")
