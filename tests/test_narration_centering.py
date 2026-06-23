#!/usr/bin/env python3
"""
test_narration_centering.py -- P2 gate: narration SUMMED-WIDTH centering cave.

WHAT P2 DID (build/patch_exe.py Patch 20)
-----------------------------------------
Patch 14 (Stage 0) made every narration glyph advance by its OWN proportional
width (tools/glyph_metrics.ADV) via the resident 256-byte ADV table @VA 0x4C7564.
But the line CENTERING still reserved a glyph-COUNT term (Patch 13's count*18 at
the two desc-store sites VA 0x305988 / 0x3059F8), so with proportional widths the
reserve no longer matched the true pixel width and lines drifted LEFT ~11-34px
(thing4/5/7: bottom-line centers measured 222-276px vs screen-center 320).

Patch 20 replaces the count reserve with the TRUE SUM(ADV) of the line's glyphs.
Two caves (NS_A @VA 0x4C7860 store desc+0x3c, NS_B @VA 0x4CAA30 store desc+0x3e)
walk the line glyph array at s5+0x40 (LE i16, stride 2, gid=char-32, -1 / >=0xFE00
terminator), accumulate SUM += ADV[gid & 0xFF] from the SAME resident table
@0x4C7564 that Patch 14 installed, then store BASE - SUM and j back into the flow.
The downstream consumer halves the reserve (x0 = (desc+0x3c)/2 + 167), so a stored
reserve of pixel-width SUM geometrically centers a line that is SUM px wide.

WHAT THIS GATE ASSERTS (all PASS on the current tree -- EXE-only, no live session)
---------------------------------------------------------------------------------
This is the STRUCTURAL P2 gate (pixel-centering correctness is a playtest item).
It pins the four invariants the WAVE spec requires, every width sourced ONLY from
the shared SoT tools/glyph_metrics.py (NEVER recomputed -- project bug #1):

  C-sum  (centering sum == build width): the in-EXE cave's accumulation, MODELLED
         in Python directly from the cave's instruction stream (the lbu 0x7564
         table-read + addu accumulate), equals sum(glyph_metrics.ADV[gid]) for any
         glyph line -- i.e. the reserve the renderer centers on IS the line's true
         glyph_metrics pixel width.  If Patch 20 ever read a different table, used
         a different stride, or summed differently, this trips.

  C-adv  (advance cave bytes == glyph_metrics): the resident ADV table the cave
         reads (@file 0x3C75E4, VA 0x4C7564) is byte-identical to
         glyph_metrics.adv_table_256(), AND the cave's lbu literally addresses
         0x7564 off the 0x4C0000 base -- so the centering sum and the per-glyph
         advance (Patch 14) and the build wrap all consume the ONE table.

  C-px   (px_width <= box_px at the NEW budget): for the user-reported narration
         lines, the cave's reserved width (== glyph_metrics px width of the line)
         is <= the post-P2 centered span so a centered line stays on screen.  The
         post-P2 budget is read straight from build_v9 NARRATION_BOX_PX (SoT).

  C-cave (cave installed, reads SoT, returns into flow): hook @0x305988 == j NS_A,
         hook @0x3059F8 == j NS_B, each delay slot a nop; cave A stores desc+0x3c
         and returns to 0x30599C, cave B stores desc+0x3e and returns to 0x305A0C;
         the pads are confirmed PRISTINE-zero in the un-patched EXE (real-PS2
         safety: no live game data clobbered).

  C-gate (static, always): Patch 20 in build/patch_exe.py is GATED on Patch 14's
         resident-table hook word, sources its sum from glyph_metrics, and reuses
         the documented freed Patch-16/18 pads -- so the cave can never be
         installed without the table it sums from being present.

TIERS
-----
  TIER-1 (static, always): assert build/patch_exe.py wires Patch 20 correctly and
          the Python cave model == glyph_metrics.  Runs with NO build artifacts.
  TIER-2 (SKIP when build/SLPM_653.78_patched absent): the BUILT patched EXE has
          the caves installed, byte-identical to the model, reading the SoT table.
"""

import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (  # noqa: E402  (path insert first)
    BUILD_V9,
    ROOT,
    Skip,
    main_exit,
    require_file,
)

import glyph_metrics  # noqa: E402  (TOOLS_DIR put on sys.path by _helpers)

# ---------------------------------------------------------------------------
# Patch 20 wiring constants -- mirror build/patch_exe.py exactly.  Kept here as
# the single place a future Patch-20 retune updates the gate too.
# ---------------------------------------------------------------------------
PATCH_EXE = os.path.join(ROOT, "build", "patch_exe.py")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")
PRISTINE_EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")

# file offset = VA - 0x100000 + 0x80  (MIPS LE, SLPM-65378 -- see header doc)
def _fo(va):
    return va - 0x100000 + 0x80


HOOK_A_FO = _fo(0x305988)   # 0x205A08  the sll Patch-20 NS_A trampolines
HOOK_B_FO = _fo(0x3059F8)   # 0x205A78  the sll Patch-20 NS_B trampolines
CAVE_A_FO = _fo(0x4C7860)   # 0x3C78E0  NS_A cave (Patch-18 freed pad)
CAVE_B_FO = _fo(0x4CAA30)   # 0x3CAAB0  NS_B cave (Patch-16 freed pad)
P14_HOOK1_FO = _fo(0x3097A0)  # 0x209820  Patch-14 resident-table gate word
ADV_TBL_FO = _fo(0x4C7564)  # 0x3C75E4  the resident ADV table Patch 14 installs

J_A_WORD = 0x08131E18  # j 0x4C7860
J_B_WORD = 0x08132A8C  # j 0x4CAA30
P14_GATE_WORD = 0x08131D50  # j 0x4C7540 (Patch 14 hook -> table present)
J_RET_A = 0x080C1667  # j 0x30599C  (cave A returns into flow)
J_RET_B = 0x080C1683  # j 0x305A0C  (cave B returns into flow)

# The resident-table read the cave performs: `lbu $t1, 0x7564($t1)` with
# $t1 = 0x4C0000 + (gid & 0xFF) -> 0x4C7564 + gid.  imm16 == ADV-table file-VA low.
LBU_IMM = 0x7564
NOP = 0x00000000


# ---------------------------------------------------------------------------
# Python MODEL of the NS cave's summed-width accumulation.
#
# This is NOT an independent width recompute (project bug #1): it sources the
# per-glyph value EXCLUSIVELY from glyph_metrics.adv_table_256() -- the very 256-
# byte table the cave's lbu reads from 0x4C7564.  It models only the cave's
# CONTROL FLOW (walk s5+0x40, stride 2, gid&0xFF, accumulate, -1 terminator) so a
# desync in HOW the cave sums (wrong stride, wrong mask, wrong table base) trips.
# ---------------------------------------------------------------------------
def _cave_sum(gids, adv_table):
    """Reproduce the in-EXE NS cave: SUM += adv_table[gid & 0xFF] until a
    negative (>= 0x8000 as i16) glyph terminates the line."""
    total = 0
    for g in gids:
        if g & 0x8000:  # lh sign bit set -> bltz terminator (-1 / 0xFE00 / 0xFFFF)
            break
        total += adv_table[g & 0xFF]
    return total


# ---------------------------------------------------------------------------
# TIER-1 (static): patch_exe.py wires Patch 20 correctly + cave model == SoT
# ---------------------------------------------------------------------------
def _patch_src():
    require_file(PATCH_EXE, "P2 narration-centering gate")
    return open(PATCH_EXE, encoding="utf-8").read()


def test_patch20_present_and_gated_on_patch14():
    """Patch 20 must exist, be gated on the Patch-14 resident-table hook word, and
    source its sum from the same 0x7564 table -- never installed without the table
    it sums from being present."""
    src = _patch_src()
    assert "Patch 20" in src, (
        "build/patch_exe.py has no Patch 20 -- the narration summed-width "
        "centering cave (P2) is missing"
    )
    # Gate: Patch 20 checks the Patch-14 hook word (0x08131D50) before installing.
    assert "0x08131D50" in src, (
        "Patch 20 must gate on the Patch-14 resident-table hook word 0x08131D50 "
        "(so the cave's lbu 0x7564 table is guaranteed present) -- gate missing"
    )
    # The cave's table read literal must be the resident ADV table @0x4C7564.
    assert "0x91297564" in src or "0x7564" in src, (
        "Patch 20 cave must read the resident ADV table at 0x...7564 (the Patch-14 "
        "table) -- the table-read literal is gone"
    )
    # Patch 20 must reuse the documented freed pads (real-PS2 safety, EXE-only).
    assert "0x4C7860" in src and "0x4CAA30" in src, (
        "Patch 20 must place its caves in the freed Patch-18 (0x4C7860) and "
        "Patch-16 (0x4CAA30) pads"
    )


def test_patch_exe_imports_glyph_metrics():
    """The centering sum must come from the SoT: patch_exe.py imports
    glyph_metrics (the same module the cave's resident table is baked from)."""
    assert "import glyph_metrics" in _patch_src(), (
        "build/patch_exe.py dropped `import glyph_metrics` -- the Patch-20 sum and "
        "the resident ADV table it reads must both come from tools/glyph_metrics.py"
    )


def test_cave_sum_model_equals_glyph_metrics_width():
    """C-sum: the in-EXE cave's accumulation (modelled from its instruction flow,
    reading glyph_metrics.adv_table_256()) equals sum(glyph_metrics.ADV[gid]) for
    every glyph line -- the reserve the renderer centers on IS the line's true
    glyph_metrics pixel width.  Pure SoT, no build artifact needed."""
    adv = glyph_metrics.adv_table_256()
    # exercise the whole printable range + the user-reported narration phrases
    lines = [
        [g for g in range(0, 95)],                       # every printable glyph
        glyph_metrics_enc("A heavy fog had settled over the deserted streets."),
        glyph_metrics_enc("the deserted streets"),
        glyph_metrics_enc("iiii"),  # all-narrow
        glyph_metrics_enc("MMMM"),  # all-wide
        [],                          # empty line
    ]
    for gids in lines:
        model = _cave_sum(gids, adv)
        truth = sum(glyph_metrics.ADV[g] for g in gids if 0 <= g < 95)
        assert model == truth, (
            "cave summed-width model (%d) != sum(glyph_metrics.ADV) (%d) for "
            "line %r -- the in-EXE centering reserve has desynced from the SoT"
            % (model, truth, gids)
        )
    # Terminator handling: a -1 / 0xFFFF / 0xFE00 glyph must stop the sum.
    for term in (0xFFFF, 0xFE00, 0x8000):
        gids = glyph_metrics_enc("ab") + [term] + glyph_metrics_enc("XX")
        assert _cave_sum(gids, adv) == glyph_metrics.ADV[ord("a") - 32] + glyph_metrics.ADV[ord("b") - 32], (
            "cave model did not terminate on glyph 0x%04X (bltz) -- the line walk "
            "would run past the line end and over-reserve" % term
        )


def glyph_metrics_enc(s):
    """ASCII -> gid list (gid = char-32), the SAME index family as glyph_metrics."""
    return [ord(c) - 32 for c in s]


def test_narration_box_px_matches_reservable_width():
    """C-px: the post-P2 narration budget (build_v9 NARRATION_BOX_PX) must be a
    width the SUM(ADV) reserve can actually center.  A line of px-width <= the
    budget reserves <= the budget, so origin = center - reserve/2 keeps it on
    screen.  Read NARRATION_BOX_PX straight from the build source (SoT)."""
    src = open(BUILD_V9, encoding="utf-8").read()
    m = re.search(r"^NARRATION_BOX_PX\s*=\s*(\d+)", src, re.M)
    assert m, "build_v9.py: NARRATION_BOX_PX not found (P1 not applied)"
    box = int(m.group(1))
    assert box > 0, "NARRATION_BOX_PX must be positive"
    # The reserve is SUM(ADV); a wrapped line is <= box px, so the cave reserves
    # <= box.  Sanity: the widest single glyph (23px) must fit the budget, and the
    # budget must stay inside the centered span the cave can address with BASE_A
    # (224) -- a line wider than ~2*167 would push origin off-screen.
    assert box >= max(glyph_metrics.ADV), (
        "NARRATION_BOX_PX=%d is narrower than the widest glyph (%d px) -- no line "
        "could ever be reserved" % (box, max(glyph_metrics.ADV))
    )
    assert box <= 360, (
        "NARRATION_BOX_PX=%d exceeds the pre-confirmed centered span (360). A "
        "line wider than ~360px only stays on screen once a fresh GS dump confirms "
        "the SUM(ADV) reserve centers it -- bump only after that playtest" % box
    )


# ---------------------------------------------------------------------------
# TIER-2 (built patched EXE): caves installed, byte-identical, reading the SoT
# ---------------------------------------------------------------------------
def _patched():
    if not os.path.isfile(PATCHED_EXE):
        raise Skip("build/SLPM_653.78_patched missing (run build/patch_exe.py)")
    return open(PATCHED_EXE, "rb").read()


def _w(data, fo):
    return struct.unpack_from("<I", data, fo)[0]


def test_tier2_patch20_superseded_caves_not_installed():
    """SUPERSEDED (P2 final design, 2026-06-20): the summed-width centering caves
    (Patch 20) were ABANDONED in favour of the simpler, RAM-confirmed left-flush
    (Patch 23: `subu a0,a0,a1` @VA 0x308328 -> `li a0,8`, gated by
    test_narration_left_align).  The live narration X-dispatcher path is mode-2
    pen sp+0x1cc (0x308328), NOT this mode-3 desc-store path, so Patch 20's caves
    were never the load-bearing align and are NOT installed.

    This gate now pins the SUPERSEDED reality so the build stays real-PS2 safe:
    the two cave pads (0x4C7860 / 0x4CAA30) ship ALL-ZERO (no dead/stale cave
    code), i.e. the hooks @0x305988 / 0x3059F8 do NOT trampoline to them.  The
    Patch-14 resident ADV table the abandoned design would have summed is still
    present (Patch 14 is live for proportional advance), so the other tier-2
    tests in this file remain valid."""
    data = _patched()
    assert _w(data, P14_HOOK1_FO) == P14_GATE_WORD, (
        "Patch-14 hook word @file 0x%X = 0x%08X != 0x%08X -- the resident ADV "
        "table (live for proportional advance) is missing"
        % (P14_HOOK1_FO, _w(data, P14_HOOK1_FO), P14_GATE_WORD)
    )
    # Patch 20 ABANDONED: the hooks must NOT trampoline to the (uninstalled) caves.
    assert _w(data, HOOK_A_FO) != J_A_WORD, (
        "NS_A hook @0x305988 trampolines to the ABANDONED Patch-20 cave 0x4C7860 "
        "-- the summed-width centering design was superseded by Patch 23 left-flush"
    )
    assert _w(data, HOOK_B_FO) != J_B_WORD, (
        "NS_B hook @0x3059F8 trampolines to the ABANDONED Patch-20 cave 0x4CAA30 "
        "-- the summed-width centering design was superseded by Patch 23 left-flush"
    )
    # NS_A (0x4C7860) still ships pristine-zero (no stale Patch-20 cave code).
    assert all(b == 0 for b in data[CAVE_A_FO:CAVE_A_FO + 16 * 4]), (
        "NS_A 0x4C7860 cave pad is NOT all-zero -- abandoned Patch-20 cave installed"
    )
    # NS_B (0x4CAA30) is REUSED by PATCH 24: narration boxX=+96, GATED on boxX==0 so
    # the shared 0x3060b0 draw path keeps dialogue's -228 / request's value untouched
    # (the unconditional li t2,96 shoved dialogue off-screen -- oops.p2s).  The draw-X
    # load 0x30973c trampolines here; verify the exact gated cave + clean tail.
    P24_CAVE = [0x860A003C, 0x15400002, 0x00000000, 0x240A0060, 0x080C25D1, 0x00000000]
    got = [_w(data, CAVE_B_FO + i * 4) for i in range(len(P24_CAVE))]
    assert got == P24_CAVE, (
        "NS_B 0x4CAA30 does not hold the Patch-24 gated boxX cave -- got %s"
        % [hex(x) for x in got]
    )
    assert all(b == 0 for b in data[CAVE_B_FO + len(P24_CAVE) * 4:CAVE_B_FO + 16 * 4]), (
        "stale bytes after the Patch-24 cave in the 0x4CAA30 pad"
    )


def test_tier2_live_left_align_is_patch23_not_patch20():
    """C-cave (superseded): the LIVE narration left-align is Patch 23's single
    edit at VA 0x308328 (file 0x2083A8) -> `li a0,8` (0x24040008), NOT a Patch-20
    summed-width cave.  This pins that the load-bearing align edit is present (the
    full Patch-23 contract is gated by test_narration_left_align)."""
    data = _patched()
    P23_FO = _fo(0x308328)
    LI_A0_8 = 0x24040008  # li a0,8 == addiu a0,zero,8
    assert _w(data, P23_FO) == LI_A0_8, (
        "narration left-align @VA 0x308328 (file 0x%X) = 0x%08X, expected `li a0,8` "
        "0x%08X -- the live Patch-23 left-flush (which SUPERSEDED Patch 20) is not "
        "installed; narration would not left-align" % (P23_FO, _w(data, P23_FO), LI_A0_8)
    )


def test_tier2_cave_adv_table_is_glyph_metrics():
    """C-adv: the resident ADV table the caves read (@file 0x3C75E4) is byte-for-
    byte glyph_metrics.adv_table_256() -- the centering sum, the Patch-14 per-glyph
    advance and the build wrap all consume the ONE SoT table."""
    data = _patched()
    got = data[ADV_TBL_FO:ADV_TBL_FO + 256]
    assert got == glyph_metrics.adv_table_256(), (
        "resident ADV table @file 0x%X != glyph_metrics.adv_table_256() -- the "
        "Patch-20 cave would sum a table that has desynced from the SoT" % ADV_TBL_FO
    )


def test_tier2_cave_sum_equals_live_table_sum():
    """C-sum (against the BUILT bytes): summing the cave's own resident table for a
    real narration line equals sum(glyph_metrics.ADV) -- the live reserve the
    renderer centers on IS the SoT pixel width."""
    data = _patched()
    live_tbl = data[ADV_TBL_FO:ADV_TBL_FO + 256]
    for phrase in ("A heavy fog had settled over the deserted streets.",
                   "the deserted streets", "OK"):
        gids = glyph_metrics_enc(phrase)
        model = _cave_sum(gids, live_tbl)
        truth = glyph_metrics.px_width(phrase, lambda c: ord(c) - 32)
        assert model == truth, (
            "live-table cave sum (%d) != glyph_metrics.px_width (%d) for %r -- the "
            "built centering reserve does not equal the SoT line width"
            % (model, truth, phrase)
        )


def test_tier2_pads_were_pristine_zero():
    """C-cave (real-PS2 safety): the two cave pads are confirmed ALL-ZERO in the
    PRISTINE extracted EXE, so Patch 20 clobbers no live game code (EXE-only fix,
    works on real PS2)."""
    require_file(PRISTINE_EXE, "pristine-pad zero check")
    pristine = open(PRISTINE_EXE, "rb").read()
    for label, cave in (("NS_A 0x4C7860", CAVE_A_FO), ("NS_B 0x4CAA30", CAVE_B_FO)):
        chunk = pristine[cave:cave + 16 * 4]
        assert all(b == 0 for b in chunk), (
            "%s pad is NOT all-zero in the pristine EXE -- Patch 20 would overwrite "
            "live game data (NOT real-PS2 safe)" % label
        )


TESTS = [
    # TIER-1 static (always run)
    test_patch20_present_and_gated_on_patch14,
    test_patch_exe_imports_glyph_metrics,
    test_cave_sum_model_equals_glyph_metrics_width,
    test_narration_box_px_matches_reservable_width,
    # TIER-2 built EXE (Skip if absent)
    test_tier2_patch20_superseded_caves_not_installed,
    test_tier2_live_left_align_is_patch23_not_patch20,
    test_tier2_cave_adv_table_is_glyph_metrics,
    test_tier2_cave_sum_equals_live_table_sum,
    test_tier2_pads_were_pristine_zero,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_narration_centering")
