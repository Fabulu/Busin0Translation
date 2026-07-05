#!/usr/bin/env python3
"""
test_reloc_caves_installed.py -- byte-pin EVERY relocated EXE cave + its hook.

July-2 audit gap: test_glyph_metrics_sync g1b verified P27/P14 hooks and the
arena-safety geometry, but the CAVE WORDS of P6/P24/P26/P19 (and the hook words
of P6/P19/P24/P26/P29/P31) were never byte-checked in the built EXE.  A build
that silently skipped one install (e.g. a WARN branch in patch_exe.py after an
unexpected hook byte) would ship with a dead or half-dead patch and no test
would notice.

For EVERY entry in build/_reloc_v147_design.CAVE_RELOC (P6, P14c1/c2, P26, P24,
P19c1/c2, P29f1/f2, P31f1/f2) -- plus P27 for completeness -- this module
asserts against build/SLPM_653.78_patched:

  1. DESIGN-SIZE : the design word list is exactly CAVE_RELOC's declared size.
  2. CAVE WORDS  : the built EXE carries the design words at the NEW VA.
  3. PAD ZERO    : the same region is all-zero in the PRISTINE EXE (the
                   "verified-zero dead .text pad" claim each install rests on).
  4. HOOK WORD   : the hook site carries the right j/jal word, and the delay
                   slots patch_exe.py nops are nop'd.
  5. GATE MARKER : file 0x209820 == RELOC.NEW_GATE_MARKER (patches 19/24/25/26/
                   27/29/31 all gate on it -- wrong marker == mass silent skip).

Word lists for P14c1/c2, P27, P29f1/f2, P31f1/f2 come STRAIGHT from the design
module (single source).  P6/P26/P24/P19c1/P19c2 word lists live only inside
patch_exe.py main() and are MIRRORED here verbatim (comments cite the source
lines' VAs); the PAD-ZERO + pristine-hook guards catch drift.
TIER-2: SKIPs when the built/pristine EXE is absent.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, Skip, main_exit

sys.path.insert(0, os.path.join(ROOT, "build"))
import _reloc_v147_design as RELOC  # noqa: E402  (relocation single source)

PRISTINE_EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")


def _w(words):
    return b"".join(struct.pack("<I", wd) for wd in words)


# ── Mirrored from build/patch_exe.py (installed only inside main()) ─────────
# Patch 6 trampoline TRAMP @RELOC.P6_VA (mode==5 skips RenderAllTiles):
P6_TRAMP = bytes.fromhex(
    "289d8293" "05000124" "03004110" "00000000"
    "102e0c08" "00000000" "0800e003" "00000000")

# Patch 26 cave words (chargen body-text proportional, R2100 ADV2 read):
P26_CAVE_WORDS = [
    0x3C010050, 0x8C21ED18, 0x24040005, 0x14240014, 0x00000000,
    0x96E20000, 0x00021040, 0x02221021, 0x90430000, 0x90440001,
    0x00031A00, 0x00641025, 0x3042FFFF, 0x2C41005F, 0x10200009,
    0x00000000, 0x86430000, 0x3C01004B, 0x00220821, 0x90211000,
    0x00611821, 0xA6430000, 0x080C1E80, 0x00000000, 0x080C1E74,
    0x8FA200E0,
]

# Patch 24 cave words (narration boxX=+96, gated boxX==0):
P24_CAVE_WORDS = [
    0x860A003C, 0x15400002, 0x00000000, 0x240A0060, 0x080C25D1, 0x00000000,
]

# Patch 19 cave1 (chargen Path-1 advance LUT, mode==5 gate, srl-8 gid):
P19_CAVE1_WORDS = [
    0x8F819D28, 0x86230040, 0x24080005, 0x14280008, 0x00031A02,
    0x3C08004C, 0x01034021, 0x91087564, 0x87A201CC, 0x00481021,
    0x10000003, 0x00000000, 0x87A201CC, 0x24420018, 0xA7A201CC,
    0x080C2012, 0x00000000,
]

# Patch 19 cave2 (chargen Path-1 draw-shift, LEFTSHIFT @0x7690):
P19_CAVE2_WORDS = [
    0x8F999D28, 0x87A301CC, 0x24180005, 0x17380006, 0x86390040,
    0x0019CA02, 0x3C01004C, 0x00390821, 0x90217690, 0x00611823,
    0x080C2007, 0x00000000,
]

# label -> expected on-disc cave bytes at CAVE_RELOC[label]'s NEW VA.
CAVE_BYTES = {
    "P6":    P6_TRAMP,
    "P14c1": _w(RELOC.P14C1_WORDS),
    "P14c2": _w(RELOC.P14C2_WORDS),
    "P26":   _w(P26_CAVE_WORDS),
    "P24":   _w(P24_CAVE_WORDS),
    "P19c1": _w(P19_CAVE1_WORDS),
    "P19c2": _w(P19_CAVE2_WORDS),
    "P29f1": _w(RELOC.P29_F1_WORDS),
    "P29f2": _w(RELOC.P29_F2_WORDS),
    "P31f1": _w(RELOC.P31_F1_WORDS),
    "P31f2": _w(RELOC.P31_F2_WORDS),
}

# Hook sites: (name, file_off, expected_built_word, expected_pristine_word).
# File offsets / pristine words mirrored from patch_exe.py's install blocks.
HOOKS = [
    ("P6 JAL site VA 0x2F2568",       0x1F25E8,
     0x0C000000 | (RELOC.P6_VA >> 2),         0x0C0C2E10),  # jal RenderAllTiles
    ("P14 hook1/gate VA 0x3097A0",    0x209820,
     RELOC.P14_HOOK1_JWORD,                   0x87A201CE),
    ("P14 hook2 VA 0x309750",         0x2097D0,
     RELOC.P14_HOOK2_JWORD,                   0x00EC6021),
    ("P19 stage1 hook VA 0x308040",   0x2080C0,
     RELOC.P19C1_HOOK_JWORD,                  0x24420018),
    ("P19 stage2 hook VA 0x308018",   0x208098,
     RELOC.P19C2_HOOK_JWORD,                  0x87A301CC),
    ("P26 hook VA 0x3079CC",          0x207A4C,
     RELOC.P26_HOOK_JWORD,                    0x8FA200E0),
    ("P24 hook VA 0x30973C",          0x2097BC,
     RELOC.P24_HOOK_JWORD,                    0x860A003C),
    ("P27 hook VA 0x3A31A0",          0x2A3220,
     RELOC.P27_HOOK_JWORD,                    0x8FA300D0),
    ("P29 site A VA 0x3A30F4",        RELOC.fo(RELOC.P29_HOOK1),
     RELOC.P29_HOOK_JWORD,                    RELOC.P29_ORIG_SITE),
    ("P29 site B VA 0x3A3170",        RELOC.fo(RELOC.P29_HOOK2),
     RELOC.P29_HOOK_JWORD,                    RELOC.P29_ORIG_SITE),
    ("P31 site VA 0x307974",          RELOC.fo(RELOC.P31_HOOK),
     RELOC.P31_HOOK_JWORD,                    RELOC.P31_ORIG_SITE),
]

# Delay slots patch_exe.py explicitly nops when installing the hook.
DELAY_NOPS = [
    ("P14 hook1 delay VA 0x3097A4 (was addiu v0,v0,0x18/0x12)", 0x209824),
    ("P19 stage1 delay VA 0x308044 (was sh v0,0x1cc(sp))",      0x2080C4),
    ("P27 delay VA 0x3A31A4 (was dsll32)",                      0x2A3224),
]

_CACHE = {}


def _exe(path, tag):
    if tag not in _CACHE:
        if not os.path.isfile(path):
            raise Skip("%s missing (%s)" % (os.path.relpath(path, ROOT), tag))
        _CACHE[tag] = open(path, "rb").read()
    return _CACHE[tag]


def _pristine():
    return _exe(PRISTINE_EXE, "pristine EXE")


def _patched():
    return _exe(PATCHED_EXE, "built EXE (run build/patch_exe.py)")


# ===========================================================================
# Design self-consistency
# ===========================================================================
def test_design_sizes_match_cave_reloc():
    """Every design/mirrored word list is exactly CAVE_RELOC's declared size --
    a size drift means the relocation map and the installer desynced."""
    for label, (old_va, new_va, size) in sorted(RELOC.CAVE_RELOC.items()):
        blob = CAVE_BYTES.get(label)
        assert blob is not None, (
            "CAVE_RELOC entry %r has NO design/mirrored word list in this test "
            "-- a new cave was added; extend CAVE_BYTES" % label
        )
        assert len(blob) == size, (
            "%s: design words are %d bytes but CAVE_RELOC declares %d "
            "(new VA 0x%06X)" % (label, len(blob), size, new_va)
        )
    assert set(CAVE_BYTES) == set(RELOC.CAVE_RELOC), (
        "CAVE_BYTES labels %s != CAVE_RELOC labels %s"
        % (sorted(CAVE_BYTES), sorted(RELOC.CAVE_RELOC))
    )
    # P27 is deliberately NOT in CAVE_RELOC (it has its own GAP_P27 slot).
    assert len(RELOC.P27_WORDS) * 4 == 84, (
        "P27 design cave is %d bytes, expected 84 (21 words)"
        % (len(RELOC.P27_WORDS) * 4)
    )
    # Fragment chains: frag1 must j into frag2, P31 frag2 must rejoin 0x30797C.
    assert RELOC.P29_F1_WORDS[8] == RELOC.j(RELOC.P29_F2_VA), \
        "P29 frag1[8] does not j P29_F2_VA -- fragment chain broken"
    assert RELOC.P31_F1_WORDS[8] == RELOC.j(RELOC.P31_F2_VA), \
        "P31 frag1[8] does not j P31_F2_VA -- fragment chain broken"
    assert RELOC.P31_F2_WORDS[3] == RELOC.j(0x30797C), \
        "P31 frag2[3] does not rejoin 0x30797C"


# ===========================================================================
# Per-cave: built words match design, pristine pad is zero.
# ===========================================================================
def _check_cave(label, new_va, blob):
    fo = RELOC.fo(new_va)
    pr = _pristine()
    assert pr[fo:fo + len(blob)] == b"\x00" * len(blob), (
        "%s: pristine EXE @VA 0x%06X (file 0x%06X) is NOT all-zero -- the "
        "'verified-zero dead .text pad' claim is broken; the install would "
        "have been WARN-skipped or clobbered live code" % (label, new_va, fo)
    )
    bd = _patched()
    got = bd[fo:fo + len(blob)]
    if got == b"\x00" * len(blob):
        raise AssertionError(
            "%s: built EXE cave @VA 0x%06X is still all-zero -- patch_exe.py "
            "SKIPPED this install (check its WARN output)" % (label, new_va)
        )
    assert got == blob, (
        "%s: built EXE cave @VA 0x%06X != design words (first diff at word %d: "
        "got 0x%08X want 0x%08X)" % (
            label, new_va,
            next(i for i in range(0, len(blob), 4) if got[i:i+4] != blob[i:i+4]) // 4,
            struct.unpack_from("<I", got, next(
                i for i in range(0, len(blob), 4) if got[i:i+4] != blob[i:i+4]))[0],
            struct.unpack_from("<I", blob, next(
                i for i in range(0, len(blob), 4) if got[i:i+4] != blob[i:i+4]))[0],
        )
    )


def _make_cave_test(label):
    new_va = RELOC.CAVE_RELOC[label][1]

    def fn():
        _check_cave(label, new_va, CAVE_BYTES[label])

    fn.__name__ = "test_cave_%s_words" % label
    fn.__doc__ = "%s cave words @VA 0x%06X match design" % (label, new_va)
    return fn


def test_cave_P27_words():
    """P27 (completeness: covered in g1b too) -- design words @RELOC.P27_VA."""
    _check_cave("P27", RELOC.P27_VA, _w(RELOC.P27_WORDS))


# ===========================================================================
# Hooks
# ===========================================================================
def test_hook_words_installed():
    pr, bd = _pristine(), _patched()
    problems = []
    for name, fo, want, pris_want in HOOKS:
        p = struct.unpack_from("<I", pr, fo)[0]
        if p != pris_want:
            problems.append(
                "%s: PRISTINE word 0x%08X != documented 0x%08X (mirror drift "
                "-- hook site moved?)" % (name, p, pris_want))
            continue
        b = struct.unpack_from("<I", bd, fo)[0]
        if b == pris_want:
            problems.append(
                "%s: built EXE still carries the PRISTINE word 0x%08X -- the "
                "hook was never installed (patch WARN-skipped)" % (name, b))
        elif b != want:
            problems.append(
                "%s: built word 0x%08X != expected j/jal 0x%08X" % (name, b, want))
    assert not problems, "; ".join(problems)


def test_hook_delay_slots_nopped():
    bd = _patched()
    problems = []
    for name, fo in DELAY_NOPS:
        b = struct.unpack_from("<I", bd, fo)[0]
        if b != 0:
            problems.append("%s @file 0x%06X = 0x%08X, expected nop" % (name, fo, b))
    assert not problems, "; ".join(problems)


def test_gate_marker_is_relocated_p14_hook():
    """Patches 19/24(gate)/25/26/27/29/31 all gate on the marker @0x209820; a
    wrong marker means EVERY dependent patch silently WARN-skips."""
    bd = _patched()
    got = struct.unpack_from("<I", bd, 0x209820)[0]
    assert got == RELOC.NEW_GATE_MARKER == RELOC.P14_HOOK1_JWORD, (
        "gate marker @0x209820 = 0x%08X, expected j relocated P14 cave1 "
        "(0x%08X) -- dependent patches would all skip"
        % (got, RELOC.NEW_GATE_MARKER)
    )


# ===========================================================================
# Assemble
# ===========================================================================
TESTS = [test_design_sizes_match_cave_reloc]
for _label in sorted(RELOC.CAVE_RELOC):
    TESTS.append(_make_cave_test(_label))
TESTS += [
    test_cave_P27_words,
    test_hook_words_installed,
    test_hook_delay_slots_nopped,
    test_gate_marker_is_relocated_p14_hook,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_reloc_caves_installed")
