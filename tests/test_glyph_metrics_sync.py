#!/usr/bin/env python3
"""
test_glyph_metrics_sync.py -- lock Stage 0 proportional spacing against regression.

Stage 0 (proportional narration/dialogue spacing) is ALREADY shipped: build/
patch_exe.py Patch 14 bakes the per-glyph advance LUT cave (VA 0x4C7540 / table
file-off 0x3C75E4) and the draw-shift cave (VA 0x4C7670 / table file-off
0x3C7710) straight from tools/glyph_metrics.adv_table_256() /
leftshift_table_256().  This module DOES NOT change any EXE/ISO bytes -- it only
guards the invariant that EVERY consumer reads the ONE shared metrics module, so
the in-EXE caves, the build wrap/centering and the tests can never silently
desync (this project's #1 failure mode).

  G1 (TIER-2, SKIP when build/SLPM_653.78_patched absent): the BUILT patched EXE
     tables/hooks are byte-identical to glyph_metrics + Patch 14 wiring.
  G2 (static, always): no pipeline source recomputes glyph widths inline unless
     it imports glyph_metrics.
  G3 (static, always): glyph_metrics itself is internally self-consistent.
"""

import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (  # noqa: E402  (path insert first)
    ROOT,
    TOOLS_DIR,
    Skip,
    main_exit,
    require_file,
)

import glyph_metrics  # noqa: E402  (TOOLS_DIR put on sys.path by _helpers)

sys.path.insert(0, os.path.join(ROOT, "build"))
import _reloc_v147_design as RELOC  # noqa: E402  (relocation single-source)

# ── Patch 14 wiring constants ────────────────────────────────────────────────
# v147 BATTLE-FIX (SIMPLIFIED): ONLY Patch-27's box-text cave is battle-stompable
# (proven: word0 0x3C030050 -> 0x3C010050 in battlebreak/fightsoftlock dumps), so it
# alone is RELOCATED out of the EE battle-heap arena to verified-safe code-segment
# padding (RELOC.P27_VA).  Patch-14's caves are PROVEN never-stomped (intact across all
# battle dumps) and ship at their PRODUCTION in-arena addresses 0x4C7540 / 0x4C7670;
# the gate marker @0x209820 stays the production value 0x08131D50.  The canonical 256B
# ADV/LSH tables stay at 0x4C7564 / 0x4C7690 and are read by the in-arena caves AND the
# chargen/request readers (P19/P25/P26).  NO table is relocated into the PsII libgraph
# SDK data block at 0x4AF2E0..0x4AF400 (the prior v147 did, smearing the final GS-write
# descriptor word -> the title-screen hang -- guarded below).
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")
P14_TBL1 = 0x3C75E4   # canonical advance LUT, 256B  (VA 0x4C7564)
P14_TBL2 = 0x3C7710   # canonical left-shift,  256B  (VA 0x4C7690)
# v158 R2100 tables (chargen/request UI font — consumed by Patches 26/27/29/31)
# v170: relocated to the dead libgraph trailing pad, 95B each.
ADV2_FO = RELOC.fo(RELOC.ADV2_VA)   # file off VA 0x4AF338
LSH2_FO = RELOC.fo(RELOC.LSH2_VA)   # file off VA 0x4AF398
P14_HOOK1 = 0x209820  # VA 0x3097A0  -> j 0x4C7540 (production gate marker 0x08131D50)
P14_HOOK2 = 0x2097D0  # VA 0x309750  -> j 0x4C7670 (production 0x08131D9C)
P14_HOOK1_WORD = RELOC.P14_HOOK1_JWORD
P14_HOOK2_WORD = RELOC.P14_HOOK2_JWORD
ARENA_LO, ARENA_HI = RELOC.ARENA_LO, RELOC.ARENA_HI
# The PsII libgraph SDK data block that the prior (over-engineered) v147 corrupted.
# v170 narrowed HI 0x4AF400 -> 0x4AF338 (proven descriptor end); 0x4AF338..0x4AF400
# now holds the relocated R2100 tables, so only 0x4AF2E0..0x4AF338 must stay pristine.
LIBGRAPH_LO, LIBGRAPH_HI = 0x4AF2E0, 0x4AF338


def test_g1_built_exe_tables_match_metrics():
    """TIER-2: the built patched EXE's caves are byte-identical to glyph_metrics."""
    if not os.path.isfile(PATCHED_EXE):
        raise Skip(
            "build/SLPM_653.78_patched missing (run build/patch_exe.py first)"
        )
    with open(PATCHED_EXE, "rb") as fh:
        data = fh.read()

    # canonical 256B tables (in-arena caves AND chargen/request readers index these)
    want_adv = glyph_metrics.adv_table_256()
    want_lsh = glyph_metrics.leftshift_table_256()
    got_adv = data[P14_TBL1:P14_TBL1 + 256]
    got_lsh = data[P14_TBL2:P14_TBL2 + 256]
    assert got_adv == want_adv, (
        "patched EXE canonical advance LUT @file 0x%X != glyph_metrics.adv_table_256() "
        "(Patch 14 desynced from the metrics module)" % P14_TBL1
    )
    assert got_lsh == want_lsh, (
        "patched EXE canonical left-shift table @file 0x%X != "
        "glyph_metrics.leftshift_table_256()" % P14_TBL2
    )
    # The relocated ADV/LSH constants point AT the canonical tables (NO separate copy).
    assert RELOC.ADV_VA == 0x4C7564 and RELOC.LSH_VA == 0x4C7690, (
        "RELOC.ADV_VA/LSH_VA must be the canonical in-arena tables (0x4C7564/0x4C7690); "
        "got 0x%06X/0x%06X -- a relocated table copy is the title-hang bug" % (RELOC.ADV_VA, RELOC.LSH_VA)
    )

    # v170: the R2100 tables (chargen/request UI font) are 95B each, byte-identical to
    # glyph_metrics.adv2_table_95()/leftshift2_table_95(), in the FREE200 dead libgraph
    # pad (0x4AF338..0x4AF400): ADV2+95<=LSH2 and LSH2+95<=0x4AF400.
    assert (RELOC.ADV2_VA + 95 <= RELOC.LSH2_VA
            and RELOC.LSH2_VA + 95 <= 0x4AF400), (
        "RELOC.ADV2_VA/LSH2_VA moved (0x%06X/0x%06X) -- they must stay in the "
        "dump-verified FREE200 pad 0x4AF338..0x4AF400 (ADV2+95<=LSH2, LSH2+95<=0x4AF400)"
        % (RELOC.ADV2_VA, RELOC.LSH2_VA)
    )
    got_adv2 = data[ADV2_FO:ADV2_FO + 95]
    got_lsh2 = data[LSH2_FO:LSH2_FO + 95]
    assert got_adv2 == glyph_metrics.adv2_table_95(), (
        "patched EXE R2100 ADV2 table @file 0x%X != glyph_metrics.adv2_table_95() "
        "(the chargen/request caves would desync)" % ADV2_FO
    )
    assert got_lsh2 == glyph_metrics.leftshift2_table_95(), (
        "patched EXE R2100 LSH2 table @file 0x%X != glyph_metrics.leftshift2_table_95()"
        % LSH2_FO
    )

    h1 = struct.unpack_from("<I", data, P14_HOOK1)[0]
    h2 = struct.unpack_from("<I", data, P14_HOOK2)[0]
    assert h1 == P14_HOOK1_WORD, (
        "patched EXE hook1 @file 0x%X = 0x%08X, expected j in-arena cave1 (0x%08X) -- "
        "Stage 1 advance-LUT trampoline not installed"
        % (P14_HOOK1, h1, P14_HOOK1_WORD)
    )
    assert h2 == P14_HOOK2_WORD, (
        "patched EXE hook2 @file 0x%X = 0x%08X, expected j in-arena cave2 (0x%08X) -- "
        "Stage 2 draw-shift trampoline not installed"
        % (P14_HOOK2, h2, P14_HOOK2_WORD)
    )


def test_g1b_relocated_caves_below_arena():
    """BATTLE-ARENA EVACUATION GATE (v148): EVERY EXE cave -- P27 AND the rest -- lies
    BELOW the EE battle-heap arena (VA < 0x4B0DCF) and its hook j's there.  A cave-safety
    audit found several caves in/abutting the arena (the false-safe trap that broke battle
    once), so v148 relocates them ALL into dead .text padding.  The canonical ADV/LSH tables
    stay at 0x4C7564/0x4C7690 (whitelisted resident rodata).  Also guards the title-hang
    regression: nothing is written into the PsII libgraph SDK data block."""
    if not os.path.isfile(PATCHED_EXE):
        raise Skip("build/SLPM_653.78_patched missing")
    with open(PATCHED_EXE, "rb") as fh:
        data = fh.read()

    SAFE_HI = RELOC.ARENA_SAFE_HI  # 0x4B0DCF

    # 1) EVERY relocated cave (P27 + the v148 CAVE_RELOC map) lies below the safe boundary.
    p27_end = RELOC.P27_VA + len(RELOC.P27_WORDS) * 4
    assert p27_end <= SAFE_HI, (
        "P27 cave VA 0x%06X..0x%06X spills into/over the arena (>= 0x%06X)"
        % (RELOC.P27_VA, p27_end, SAFE_HI)
    )
    for label, (old_va, new_va, size) in RELOC.CAVE_RELOC.items():
        assert new_va + size <= SAFE_HI, (
            "%s cave VA 0x%06X..0x%06X is in/over the battle-heap arena (>= 0x%06X)"
            % (label, new_va, new_va + size, SAFE_HI)
        )
    # The canonical tables ARE in-arena (read-only resident rodata, whitelisted -- not code).
    assert RELOC.ADV_VA in RELOC.CANONICAL_TABLE_VAS and RELOC.LSH_VA in RELOC.CANONICAL_TABLE_VAS

    # 2) The relocated P27 cave words byte-match the design module.
    f = RELOC.fo(RELOC.P27_VA)
    got = [struct.unpack_from("<I", data, f + i * 4)[0] for i in range(len(RELOC.P27_WORDS))]
    assert got == list(RELOC.P27_WORDS), "relocated P27 cave words != design module"
    # v158: the P27 cave reads the R2100 ADV2 table (lui 0x4B + lbu 0x1000) — the
    # 0x3A2EF0 renderer draws the R2100 upright font in modes 5/7, NOT R1188.
    assert any((w >> 26) == 0x24 and (w & 0xFFFF) == (RELOC.ADV2_VA & 0xFFFF)
               for w in RELOC.P27_WORDS), (
        "relocated P27 cave must read R2100 ADV2 @0x%X" % (RELOC.ADV2_VA & 0xFFFF)
    )
    assert any((w >> 26) == 0x0F and (w & 0xFFFF) == (RELOC.ADV2_VA >> 16)
               for w in RELOC.P27_WORDS), (
        "relocated P27 cave must lui the R2100 ADV2 table base 0x%X0000" % (RELOC.ADV2_VA >> 16)
    )

    # 3) The P27 hook AND the P14 hooks (= the gate marker) j into the RELOCATED caves below
    #    the arena.  All j-targets must be below the arena.
    p27_hook = struct.unpack_from("<I", data, 0x2A3220)[0]
    assert p27_hook == RELOC.P27_HOOK_JWORD, (
        "P27 hook 0x3A31A0 = 0x%08X, expected j relocated cave 0x%08X" % (p27_hook, RELOC.P27_HOOK_JWORD)
    )
    for nm, off, want in [
        ("P27 hook 0x3A31A0", 0x2A3220, RELOC.P27_HOOK_JWORD),
        ("P14 hook1/gate 0x3097A0", 0x209820, RELOC.P14_HOOK1_JWORD),
        ("P14 hook2 0x309750", 0x2097D0, RELOC.P14_HOOK2_JWORD),
    ]:
        w = struct.unpack_from("<I", data, off)[0]
        assert w == want, "%s = 0x%08X, expected j relocated cave 0x%08X" % (nm, w, want)
        assert ((w & 0x3FFFFFF) << 2) < SAFE_HI, "%s j-target is in the arena!" % nm
    assert RELOC.NEW_GATE_MARKER == RELOC.P14_HOOK1_JWORD, (
        "gate marker must be j relocated P14 cave1 (0x%08X), got 0x%08X"
        % (RELOC.P14_HOOK1_JWORD, RELOC.NEW_GATE_MARKER)
    )

    # 4) The OLD battle-stompable cave sites are pristine-zero (no stompable code left).
    for old_va, size in [(0x4C7410, 84),                       # old P27
                         (0x4C7540, 36), (0x4C7670, 28),       # old P14 c1/c2
                         (0x4C7790, 104), (0x4CAA30, 24),      # old P26 / P24
                         (0x4D6600, 68), (0x4D6660, 48),       # old P19 c1/c2
                         (0x4B0DD0, 32)]:                      # old P6
        fz = RELOC.fo(old_va)
        assert all(b == 0 for b in data[fz:fz + size]), (
            "old cave site 0x%06X is NOT zero -- stompable code left in the arena" % old_va
        )

    # 5) TITLE-HANG REGRESSION GUARD: the PsII libgraph SDK data block stays PRISTINE.
    #    The over-engineered v147 relocated the ADV table to 0x4AF336, smearing the high
    #    2 bytes of the final libgraph GS-write descriptor word (0x4AF334=0x000002FF) ->
    #    the title screen rendered then hung.  Nothing may be written here.
    import os as _os
    pris_path = _os.path.join(ROOT, "extracted", "SLPM_653.78")
    if _os.path.isfile(pris_path):
        with open(pris_path, "rb") as pfh:
            pris = pfh.read()
        flo, fhi = RELOC.fo(LIBGRAPH_LO), RELOC.fo(LIBGRAPH_HI)
        assert data[flo:fhi] == pris[flo:fhi], (
            "PsII libgraph SDK data block 0x%06X..0x%06X is NOT pristine -- a relocated "
            "table/cave landed on live GS/DMA descriptor data (the v147 title-hang bug)"
            % (LIBGRAPH_LO, LIBGRAPH_HI)
        )


# ── G2: forbid inline width recompute outside glyph_metrics ──────────────────
_RECOMPUTE_TOKENS = (
    re.compile(r"min\(\s*23"),
    re.compile(r"max\(\s*6"),
    re.compile(r"\+\s*GAP"),
    re.compile(r"iw\s*\+\s*3"),
    re.compile(r"clamp"),
)
_SCAN_SOURCES = [
    os.path.join(ROOT, "build", "patch_exe.py"),
    os.path.join(ROOT, "build", "build_v9.py"),
    os.path.join(ROOT, "tools", "patch_r1193_narration.py"),
    os.path.join(ROOT, "tools", "patch_r2138.py"),
]


def _strip_comments(src):
    """Drop the trailing '#...' from every line (so doc comments are exempt)."""
    out = []
    for line in src.splitlines():
        out.append(line.split("#", 1)[0])
    return "\n".join(out)


def test_g2_no_inline_width_recompute():
    offenders = []
    for path in _SCAN_SOURCES:
        require_file(path, "pipeline source for width-recompute scan")
        raw = open(path, encoding="utf-8").read()
        imports_metrics = "glyph_metrics" in raw  # exempt files that read the SoT
        code = _strip_comments(raw)
        if "ink_width" not in code:
            continue
        recompute = any(tok.search(code) for tok in _RECOMPUTE_TOKENS)
        if recompute and not imports_metrics:
            offenders.append(os.path.relpath(path, ROOT))
    assert not offenders, (
        "inline glyph-width recompute (ink_width + clamp/+GAP/min(23/...) WITHOUT "
        "importing glyph_metrics -- the SILENT DESYNC bug. Offenders: %s"
        % ", ".join(offenders)
    )


# ── G3: glyph_metrics internal self-consistency ──────────────────────────────
def test_g3_metrics_self_consistent():
    adv = glyph_metrics.ADV
    assert len(adv) == 95, "ADV must have 95 entries, got %d" % len(adv)
    assert adv[0] == 9, "ADV[0] (space) must be 9, got %d" % adv[0]
    for g in range(1, 95):
        assert 6 <= adv[g] <= 23, (
            "ADV[%d] = %d outside the clamp window [6,23]" % (g, adv[g])
        )
    enc = lambda c: ord(c) - 32  # noqa: E731  ('A' -> 33)
    assert glyph_metrics.px_width("A", enc) == adv[33], (
        "px_width('A') = %d != ADV[33] = %d -- enc family mismatch"
        % (glyph_metrics.px_width("A", enc), adv[33])
    )
    # v158: the R2100 (16px font) tables are self-consistent too.
    adv2 = glyph_metrics.ADV2
    lsh2 = glyph_metrics.LEFTSHIFT2
    assert len(adv2) == 95 and len(lsh2) == 95
    assert adv2[0] == glyph_metrics.SPACE_ADV2, (
        "ADV2[0] (space) must be SPACE_ADV2 (%d), got %d"
        % (glyph_metrics.SPACE_ADV2, adv2[0])
    )
    assert lsh2[0] == 0, "LEFTSHIFT2[0] (space) must be 0"
    for g in range(1, 95):
        assert 4 <= adv2[g] <= 15, (
            "ADV2[%d] = %d outside the 16px-font clamp window [4,15]" % (g, adv2[g])
        )
        assert 0 <= lsh2[g] <= 15, "LEFTSHIFT2[%d] = %d outside a 16px cell" % (g, lsh2[g])
    # v170: the RELOCATED tables are 95 bytes (gid 0..94 only) -- the 95..255 tail is
    # reproduced by each cave's gid>=95 guard (ADV2 tail default 0x12, LSH2 tail 0).
    a95 = glyph_metrics.adv2_table_95()
    l95 = glyph_metrics.leftshift2_table_95()
    assert len(a95) == 95 and len(l95) == 95, (
        "adv2/leftshift2_table_95() must be 95 bytes, got %d/%d" % (len(a95), len(l95))
    )
    assert bytes(adv2) == a95 and bytes(lsh2) == l95, (
        "the 95B tables must equal the raw ADV2/LEFTSHIFT2 gid 0..94 slots"
    )


TESTS = [
    test_g1_built_exe_tables_match_metrics,
    test_g1b_relocated_caves_below_arena,
    test_g2_no_inline_width_recompute,
    test_g3_metrics_self_consistent,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_glyph_metrics_sync")
