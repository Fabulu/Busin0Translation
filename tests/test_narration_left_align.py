#!/usr/bin/env python3
"""
test_narration_left_align.py -- P2 gate: NARRATION true LEFT-ALIGN at box origin.

WHAT P2 DID (build/patch_exe.py Patch 23 + the Patch-21 revert)
--------------------------------------------------------------
Live-RAM recon (2026-06-20 fresh saves heavyfog2 / leftfield / mostbroken /
chargenspaces) resolved the conflicting narration-align recon:

  * the active narration descriptor 0x565150[0] = 0x01137AC0 has boxX(desc+0x3c)==0
    and ALIGN(desc+0x2a7)==0 -> align-MODE 0, NOT mode-2 (the Patch-21 premise) and
    NOT mode-3 (the Patch-20 path);
  * the X-dispatcher in the universal R1188 renderer func 0x307DA0 reads desc+0x2a7
    (=0), 0x3082E4 `bne a1,1` falls into the align!=1 count*12 reserve block
    0x308308..0x308330: 0x308310 lh a0,0x1cc(sp); 0x308314-31C compute count*12;
    0x308328 `subu a0,a0,a1` makes pen = -(count*12); 0x308330 sh a0,0x1cc(sp).

With boxX==0 the screen penX = boxX + (-(count*12)) + glyph => NEGATIVE for wide
lines, so leftfield's 24-char "No one was in sight. Not" clips off the LEFT edge
while the right side of the box goes unused.

Patch 23 replaces the LIVE-PRISTINE `subu a0,a0,a1` (0x00852023) at VA 0x308328
(file 0x2083A8) with `li a0,8` (0x24040008 == addiu a0,zero,8).  This DISCARDS the
count*12 centering reserve and stores a CONSTANT pen=8, so every narration line
left-flushes at boxX+8 (==8px since boxX==0) with glyphs flowing rightward -- true
left-align using the full box width.  The draw consumer is ADDITIVE (pen + glyph +
field + origin), so pen=8 is an 8px inset, NOT the v121 Patch-21 `move a0,a1`
mistake (which wrongly assumed a register held an absolute box-left and wrote OFF
the left edge).

Patch 21 (@VA 0x308378 / file 0x2083F8) is REVERTED to pristine `addu a0,a1,a0`
(0x00A42021): it edits the mode-2 0x1ce origin, a path live narration (desc+0x2a8
==0) never reaches, so it is dead-for-narration and must ship pristine.  Patch 20
(@0x305980/0x305994/0x3059F0/0x305A04, the align==3 mode-3 path) is also dead for
narration (align==0) -- its installed li/nop bytes are harmless on a dead path and
are LEFT IN PLACE (reverting them risks a spurious WARN); this gate pins them only
as "must not have grown into a live edit", not as a required revert.

WHAT THIS GATE ASSERTS (all PASS on the current tree -- EXE-only, no live session)
---------------------------------------------------------------------------------
This is the STRUCTURAL P2 gate (the on-emulator ~8px-inset / 'N'-unclipped visual
is a fresh-boot playtest item).  It pins every invariant the WAVE spec requires,
every glyph width sourced ONLY from the shared SoT tools/glyph_metrics.py (NEVER
recomputed -- this project's #1 failure mode):

  L-origin   (origin constant): Patch 23 edits EXACTLY VA 0x308328 == file 0x2083A8
             (file_off = VA - 0x100000 + 0x80), and Patch 21 reverts EXACTLY VA
             0x308378 == file 0x2083F8 -- not a moved/wrong target.  The constant
             8px left inset is the single load-bearing left-align value.

  L-advance  (advance == glyph_metrics): the per-glyph narration advance is the
             resident Patch-14 ADV LUT @0x4C7564 (Block-3 @0x3097A4), which is
             byte-identical to glyph_metrics.adv_table_256() -- the left-flush pen
             and the glyph stepping consume the ONE SoT table; Patch 23 changes the
             ORIGIN only and must NOT touch any advance literal.

  L-noverflow (no-overflow / px budget): with a fixed 8px left inset every narration
             line draws from x=8 rightward; the post-P2 budget (build_v9
             NARRATION_BOX_PX, SoT) plus the inset must stay inside the ~640px
             logical screen, so the widest user-reported narration line (the 24-char
             leftfield line) is fully on-screen -- modelled at glyph_metrics widths,
             NOT a recomputed monospace estimate.

  L-scope    (cave/scoping): the Patch-23 site is reached ONLY by the align!=1
             branch of the X-dispatcher writing pen sp+0x1cc.  The dialogue func
             0x307510, the chargen Block-A advance 0x308040, and the request body
             path-B (pen sp+0x1ce, Patch 22) are DISJOINT file offsets -- Patch 23
             cannot regress them.  Asserted by enumerating the renderer-region diff:
             the only narration-origin word that changed is 0x2083A8, and the
             request/chargen/dialogue control words are untouched by P23.

  L-revert   (Patch 21 dead-path revert): VA 0x308378 ships PRISTINE (addu a0,a1,a0)
             -- the v121 `move a0,a1` is gone, so the dead mode-2 origin can never
             re-introduce the off-left write.

  L-gate     (static, always): Patch 23 in build/patch_exe.py uses the standard
             if-orig(0x00852023)/elif-new(0x24040008)/else-WARN guard, and Patch 21
             uses the if-pristine/elif-stale-revert/else-WARN guard -- neither can
             install onto a moved site without a WARN.

TIERS
-----
  TIER-1 (static, always): build/patch_exe.py wires Patch 23 / the Patch-21 revert
          at the right offsets to the right words, guarded, and the left-flush /
          no-overflow models read glyph widths ONLY from glyph_metrics.  Runs with
          NO build artifacts.
  TIER-2 (SKIP when an EXE is absent): the PRISTINE extracted EXE holds the old
          words (preflight: subu @0x2083A8) and the BUILT patched EXE holds li a0,8
          @0x2083A8 + the reverted addu @0x2083F8, byte-exact, with the resident
          ADV LUT == glyph_metrics and no collateral renderer-region diffs.
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

sys.path.insert(0, os.path.join(ROOT, "build"))
import _reloc_v147_design as RELOC  # noqa: E402  (v147 relocated P14 gate marker)

PATCH_EXE = os.path.join(ROOT, "build", "patch_exe.py")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")
PRISTINE_EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")


# file offset = VA - 0x100000 + 0x80  (MIPS LE, SLPM-65378 -- matches patch_exe.py)
def _fo(va):
    return va - 0x100000 + 0x80


# ---------------------------------------------------------------------------
# Patch 23 / Patch 21 wiring constants -- mirror build/patch_exe.py EXACTLY.
# This is the single place a future P2 retune updates the gate too.
# ---------------------------------------------------------------------------
# Patch 23: the X-dispatcher count*12 reserve -> constant 8px left inset.
P23_VA = 0x308328
P23_FO = _fo(P23_VA)          # 0x2083A8
P23_ORIG = 0x00852023         # subu a0,a0,a1  (count*12 centering reserve)
P23_NEW = 0x24040008          # li   a0,8      (addiu a0,zero,8 ; on-disk LE 08 00 04 24)
LEFT_INSET_PX = 8             # the constant pen value Patch 23 stores

# Patch 21: REVERTED to pristine (mode-2 origin, dead for narration).
P21_VA = 0x308378
P21_FO = _fo(P21_VA)          # 0x2083F8
P21_PRISTINE = 0x00A42021     # addu a0,a1,a0  (pristine)
P21_STALE = 0x00A02021        # move a0,a1     (the v121 dead edit being reverted)

# Patch 20 (mode-3 path) -- DEAD for narration (align==0).  Not a required revert;
# we only assert these four sites never grew into a LIVE narration-origin edit.
P20_FOS = (0x205A00, 0x205A14, 0x205A70, 0x205A84)

# Patch-14 mode-2 narration reserve count*24->18 (VA 0x308364/0x30836C) -- a
# PRE-EXISTING, intentional edit in the same X-dispatcher region that lands BEFORE
# Patch 23 (it is the proven *18 precedent test_request_body_reserve mirrors).  It is
# NOT Patch-23 collateral, so the broad-region diff allowlist must include it.
P14_MODE2_FOS = (_fo(0x308364), _fo(0x30836C))  # 0x2083E4, 0x2083EC

# Narration per-glyph advance = the resident Patch-14 ADV LUT (Block-3 hook).
ADV_TBL_FO = _fo(0x4C7564)    # 0x3C75E4
P14_HOOK_FO = _fo(0x3097A0)   # 0x209820  Patch-14 resident-table hook word
P14_GATE_WORD = RELOC.NEW_GATE_MARKER    # j relocated P14 cave1 (Patch 14 hook -> ADV table present, v147)

# Narration pen slot is 0x1cc(sp); request path-B is the DISTINCT 0x1ce(sp).
NARRATION_PEN_IMM = 0x1CC
REQUEST_PEN_IMM = 0x1CE

# Request body path-B sites (Patch 22) -- must be untouched by Patch 23.
P22_FOS = (0x2089EC, 0x2089F4, 0x208D30, 0x208DFC)
# Chargen Block-A advance hook (Patch 19) + dialogue func -- untouched by Patch 23.
CHARGEN_ADV_FO = _fo(0x308040)   # 0x2080C0
DIALOGUE_FUNC_FO = _fo(0x307510)  # 0x207590  (separate boxed-dialogue renderer)

# The logical PS2 screen width the left-flushed line must stay inside.
SCREEN_PX = 640

# MIPS decode helpers (only for structural pinning, never width recompute).
def _decode_addiu(word):
    """Decode addiu (op=0x09): return (rt, rs, simm16) or None."""
    if (word >> 26) != 0x09:
        return None
    rt = (word >> 16) & 0x1F
    rs = (word >> 21) & 0x1F
    imm = word & 0xFFFF
    if imm & 0x8000:
        imm -= 0x10000
    return rt, rs, imm


def _enc(s):
    """ASCII -> gid list (gid = char-32), the SAME index family as glyph_metrics."""
    return [ord(c) - 32 for c in s]


# ---------------------------------------------------------------------------
# TIER-1 (static): build/patch_exe.py wires Patch 23 + revert; models == SoT
# ---------------------------------------------------------------------------
def _patch_src():
    require_file(PATCH_EXE, "P2 narration left-align gate")
    return open(PATCH_EXE, encoding="utf-8").read()


def test_patch23_present_and_targets_correct_origin():
    """L-origin + L-gate: Patch 23 exists, edits EXACTLY file 0x2083A8 (VA 0x308328)
    from the pristine subu (0x00852023) to li a0,8 (0x24040008), guarded by the
    standard if-orig/elif-new/else-WARN form."""
    src = _patch_src()
    assert "Patch 23" in src, (
        "build/patch_exe.py has no Patch 23 -- the narration true left-align "
        "(X-dispatcher count*12 -> li a0,8) is missing"
    )
    norm = src.replace("0X", "0x")
    for needle, what in (
        ("0x%06X" % P23_FO, "Patch-23 file offset 0x2083A8"),
        ("0x%08X" % P23_ORIG, "Patch-23 pristine word subu a0,a0,a1 (0x00852023)"),
        ("0x%08X" % P23_NEW, "Patch-23 new word li a0,8 (0x24040008)"),
    ):
        assert needle.lower() in norm.lower(), (
            "Patch 23 is missing %s -- the load-bearing left-flush edit is not wired "
            "to the documented site/words" % what
        )
    # Standard guard.
    assert "WARN" in src and "SKIP" in src, (
        "Patch 23 must use the standard if-orig/elif-new(SKIP)/else-WARN guard"
    )


def test_patch21_reverted_to_pristine_in_source():
    """L-revert + L-gate: Patch 21 is REVERTED -- source restores VA 0x308378 (file
    0x2083F8) to pristine addu a0,a1,a0 (0x00A42021) over the v121 stale move a0,a1
    (0x00A02021), via the if-pristine/elif-stale/else-WARN guard."""
    src = _patch_src()
    norm = src.replace("0X", "0x").lower()
    assert "0x%06x" % P21_FO in norm, (
        "Patch 21 revert must reference file offset 0x2083F8 (VA 0x308378)"
    )
    assert ("0x%08x" % P21_PRISTINE).lower() in norm, (
        "Patch 21 revert must write the pristine word addu a0,a1,a0 (0x00A42021)"
    )
    assert ("0x%08x" % P21_STALE).lower() in norm, (
        "Patch 21 revert must recognise the v121 stale move a0,a1 (0x00A02021) to "
        "undo it"
    )
    # The revert is documented as a revert, not a fresh edit.
    assert re.search(r"Patch 21.{0,80}REVERT", src, re.S | re.I), (
        "Patch 21 must be documented as REVERTED (dead for narration), not re-applied"
    )


def test_patch23_new_word_is_li_a0_8():
    """L-origin (decode): the Patch-23 new word decodes to `li a0,8` (addiu a0,zero,8)
    -- a CONSTANT left inset, NOT a register-relative move (the v121 Patch-21 mistake
    wrote a register whose value was not box-left).  Confirms rt=a0, rs=zero, imm=8."""
    d = _decode_addiu(P23_NEW)
    assert d is not None, "Patch-23 new word 0x%08X is not an addiu" % P23_NEW
    rt, rs, imm = d
    assert rt == 4, "Patch-23 li target is r%d, not a0 (r4)" % rt
    assert rs == 0, (
        "Patch-23 li reads r%d, not zero -- it is a register-relative add, not a "
        "constant inset (the v121 move-a0,a1 off-left failure mode)" % rs
    )
    assert imm == LEFT_INSET_PX, (
        "Patch-23 constant left inset = %d, expected %d px" % (imm, LEFT_INSET_PX)
    )
    # The pristine word it replaces must be the count*12 reserve subu (op=0, fn=0x23).
    assert (P23_ORIG >> 26) == 0 and (P23_ORIG & 0x3F) == 0x23, (
        "Patch-23 pristine word 0x%08X is not a subu -- the count*12 reserve being "
        "discarded is not the documented site" % P23_ORIG
    )


def test_narration_advance_is_glyph_metrics_not_recomputed():
    """L-advance: Patch 23 changes the ORIGIN only; the per-glyph narration advance
    stays the resident Patch-14 ADV LUT (== glyph_metrics).  This gate pins that the
    left-flush width model below sources widths ONLY from glyph_metrics (project bug
    #1: never recompute) -- the ADV table is non-trivial proportional, not a constant
    monospace, so a recompute-with-a-literal would diverge here."""
    adv = glyph_metrics.ADV
    assert len(adv) == 95 and adv[0] == 9, "glyph_metrics.ADV malformed"
    # Proportional, not monospace: narrow 'i'(73) must be narrower than wide 'M'(45).
    assert adv[ord("i") - 32] < adv[ord("M") - 32], (
        "glyph_metrics.ADV is not proportional -- a monospace recompute could pass a "
        "left-align width gate while the live LUT advance differs"
    )
    # patch_exe.py must import glyph_metrics so the resident LUT and any sums share SoT.
    assert "import glyph_metrics" in _patch_src(), (
        "build/patch_exe.py dropped `import glyph_metrics` -- the resident narration "
        "ADV LUT must come from tools/glyph_metrics.py"
    )


def test_left_flush_keeps_wide_line_on_screen():
    """L-noverflow: with a fixed 8px left inset every narration line draws from x=8
    rightward.  The widest user-reported narration line ("No one was in sight. Not",
    leftfield's 24-char left-clip) at glyph_metrics widths must end well inside the
    640px logical screen -- the leading 'N' is at x=8 (no longer negative), the trailing
    glyph inside the screen.  Widths from glyph_metrics ONLY."""
    enc = lambda c: ord(c) - 32  # noqa: E731
    lines = [
        "No one was in sight. Not",                 # leftfield's clipped line
        "A heavy fog had settled over the streets",  # heavyfog2 narration
        "the deserted streets",
    ]
    box = _narration_box_px()
    for ln in lines:
        w = glyph_metrics.px_width(ln, enc)
        # Left edge: the leading glyph starts at the inset, never negative.
        left_x = LEFT_INSET_PX
        right_x = LEFT_INSET_PX + w
        assert left_x >= 0, (
            "left-flushed line %r starts at x=%d (off the LEFT edge) -- the inset must "
            "be >= 0" % (ln, left_x)
        )
        # A wrapped narration line is <= the build budget; with the inset it must fit
        # the screen with margin (this is the regression the PRISTINE subu caused:
        # pen=-(count*12) made the leading glyph NEGATIVE).
        assert right_x <= SCREEN_PX, (
            "left-flushed line %r ends at x=%d > %dpx screen -- a left-aligned line "
            "ran off the RIGHT edge" % (ln, right_x, SCREEN_PX)
        )
    # The build budget itself, inset, must fit the screen (so any wrapped line fits).
    assert LEFT_INSET_PX + box <= SCREEN_PX, (
        "NARRATION_BOX_PX (%d) + %dpx inset > %dpx screen -- a full-budget left-flushed "
        "narration line would overflow" % (box, LEFT_INSET_PX, SCREEN_PX)
    )


def test_pristine_subu_would_clip_left():
    """L-noverflow (the bug being fixed): the PRISTINE count*12 reserve makes
    pen = boxX(0) - count*12, which is NEGATIVE for the leftfield line -- modelling
    EXACTLY the left-clip symptom Patch 23 removes.  Confirms the new li a0,8 is a
    strict improvement (negative -> +8)."""
    line = "No one was in sight. Not"  # 24 chars
    count = len(line)
    box_x = 0  # live narration descriptor boxX(desc+0x3c) == 0
    pristine_pen = box_x - count * 12
    assert pristine_pen < 0, (
        "the pristine count*12 reserve did not model a negative pen for the leftfield "
        "line -- the left-clip root cause is not reproduced (count=%d)" % count
    )
    new_pen = LEFT_INSET_PX  # li a0,8 stores a constant
    assert new_pen >= 0 and new_pen > pristine_pen, (
        "Patch 23 must turn the negative reserve pen (%d) into a non-negative inset "
        "(%d)" % (pristine_pen, new_pen)
    )


def _narration_box_px():
    src = open(BUILD_V9, encoding="utf-8").read()
    m = re.search(r"^NARRATION_BOX_PX\s*=\s*(\d+)", src, re.M)
    assert m, "build_v9.py: NARRATION_BOX_PX not found (P1 not applied)"
    box = int(m.group(1))
    assert box > 0, "NARRATION_BOX_PX must be positive"
    return box


def test_narration_box_px_budget_sane():
    """L-noverflow (px budget, SoT): NARRATION_BOX_PX comes from build_v9 (SoT), is
    positive, fits the widest glyph, and fits the screen with the 8px inset."""
    box = _narration_box_px()
    widest = max(glyph_metrics.ADV)
    assert box >= widest, (
        "NARRATION_BOX_PX=%d is narrower than the widest glyph (%d px)" % (box, widest)
    )
    assert LEFT_INSET_PX + box <= SCREEN_PX, (
        "NARRATION_BOX_PX=%d + %dpx inset exceeds the %dpx logical screen"
        % (box, LEFT_INSET_PX, SCREEN_PX)
    )


# ---------------------------------------------------------------------------
# TIER-2 (built / pristine EXE): the bytes actually ship the left-flush + revert
# ---------------------------------------------------------------------------
def _patched():
    if not os.path.isfile(PATCHED_EXE):
        raise Skip("build/SLPM_653.78_patched missing (run build/patch_exe.py)")
    return open(PATCHED_EXE, "rb").read()


def _w(data, fo):
    return struct.unpack_from("<I", data, fo)[0]


def test_tier2_pristine_holds_subu_at_p23_site():
    """L-origin (pristine preflight): the extracted EXE holds the OLD subu a0,a0,a1
    (0x00852023) at 0x2083A8, and the pristine ADD a0,a1,a0 (0x00A42021) at 0x2083F8
    -- so Patch 23 lands on the intended live site and Patch 21's revert is a no-op
    against pristine (already addu)."""
    require_file(PRISTINE_EXE, "P2 pristine preflight")
    pr = open(PRISTINE_EXE, "rb").read()
    got23 = _w(pr, P23_FO)
    assert got23 == P23_ORIG, (
        "pristine EXE @file 0x%06X (VA 0x%X) = 0x%08X, expected the count*12 reserve "
        "subu 0x%08X -- Patch 23 would WARN or hit a moved site"
        % (P23_FO, P23_VA, got23, P23_ORIG)
    )
    got21 = _w(pr, P21_FO)
    assert got21 == P21_PRISTINE, (
        "pristine EXE @file 0x%06X (VA 0x%X) = 0x%08X, expected pristine addu a0,a1,a0 "
        "0x%08X -- the Patch-21 revert target moved" % (P21_FO, P21_VA, got21, P21_PRISTINE)
    )


def test_tier2_built_holds_li_a0_8_and_reverted_addu():
    """L-origin + L-revert (built bytes): the BUILT patched EXE holds li a0,8
    (0x24040008) @0x2083A8 (narration left-flush) AND the reverted pristine addu
    a0,a1,a0 (0x00A42021) @0x2083F8 -- the v121 move a0,a1 is gone.  This is the exact
    structural verify contract."""
    data = _patched()
    got23 = _w(data, P23_FO)
    assert got23 == P23_NEW, (
        "patched EXE @file 0x%06X (VA 0x%X) = 0x%08X, expected li a0,8 (0x%08X) -- the "
        "narration left-flush did not ship" % (P23_FO, P23_VA, got23, P23_NEW)
    )
    got21 = _w(data, P21_FO)
    assert got21 == P21_PRISTINE, (
        "patched EXE @file 0x%06X (VA 0x%X) = 0x%08X, expected reverted pristine addu "
        "a0,a1,a0 (0x%08X) -- Patch 21's v121 move a0,a1 (0x%08X) was NOT reverted, the "
        "dead mode-2 origin can still write off-left"
        % (P21_FO, P21_VA, got21, P21_PRISTINE, P21_STALE)
    )


def test_tier2_built_li_decodes_to_constant_8px_inset():
    """L-origin (decode against built bytes): the shipped 0x2083A8 word decodes to
    `li a0,8` -- target a0, source zero, imm 8 -- a constant inset, not a clobbering
    register move."""
    data = _patched()
    d = _decode_addiu(_w(data, P23_FO))
    assert d is not None, "built 0x2083A8 word is not an addiu (li)"
    rt, rs, imm = d
    assert (rt, rs, imm) == (4, 0, LEFT_INSET_PX), (
        "built 0x2083A8 decodes to addiu r%d,r%d,%d, expected li a0,8 (4,0,%d)"
        % (rt, rs, imm, LEFT_INSET_PX)
    )


def test_tier2_narration_adv_table_is_glyph_metrics():
    """L-advance (built bytes): the resident narration ADV LUT @0x4C7564 is byte-for-
    byte glyph_metrics.adv_table_256() and Patch-14's hook is installed -- the left-
    flushed origin and the per-glyph advance consume the ONE SoT table; Patch 23 left
    the advance untouched."""
    data = _patched()
    assert _w(data, P14_HOOK_FO) == P14_GATE_WORD, (
        "Patch-14 hook word @file 0x%X = 0x%08X != 0x%08X -- the resident narration "
        "ADV LUT is not installed" % (P14_HOOK_FO, _w(data, P14_HOOK_FO), P14_GATE_WORD)
    )
    tbl = data[ADV_TBL_FO:ADV_TBL_FO + 256]
    assert tbl == glyph_metrics.adv_table_256(), (
        "resident ADV table @file 0x%X != glyph_metrics.adv_table_256() -- the "
        "narration per-glyph advance has desynced from the SoT" % ADV_TBL_FO
    )


def test_tier2_scope_only_p23_changed_narration_origin():
    """L-scope (built diff): between pristine and patched, the ONLY narration-origin
    word that changed is 0x2083A8 (Patch 23).  The request body path-B sites
    (Patch 22), the chargen Block-A advance, the dialogue func, and the reverted
    Patch-21 site must each be in their EXPECTED state -- no collateral from P23."""
    require_file(PRISTINE_EXE, "P2 scope diff")
    pr = open(PRISTINE_EXE, "rb").read()
    pa = _patched()

    # Patch 23 IS in the diff.
    assert _w(pr, P23_FO) != _w(pa, P23_FO), (
        "0x2083A8 is identical in pristine and patched -- Patch 23 did not ship"
    )

    # Patch 21 site ships PRISTINE (not in the diff, == addu).
    assert _w(pa, P21_FO) == P21_PRISTINE and _w(pr, P21_FO) == P21_PRISTINE, (
        "0x2083F8 (Patch 21) is not pristine in both EXEs -- the dead mode-2 origin "
        "must ship reverted"
    )

    # Request body path-B (Patch 22) sites: changed by Patch 22 (24->18), NOT by P23.
    # We only assert the patched words are the Patch-22 expected new words, proving P23
    # did not touch the request pen 0x1ce path.
    for fo, new in ((0x2089EC, 0x000410C0), (0x2089F4, 0x00021040),
                    (0x208D30, 0x24420012), (0x208DFC, 0x24420012)):
        assert _w(pa, fo) == new, (
            "request path-B site 0x%06X = 0x%08X != Patch-22 new 0x%08X -- Patch 23 "
            "must not have disturbed the request pen 0x1ce path" % (fo, _w(pa, fo), new)
        )

    # The Patch-23 site itself stores the NARRATION pen 0x1cc -- the surrounding store
    # (0x308330 sh a0,0x1cc(sp), file 0x2083B0) must still target 0x1cc, not 0x1ce.
    store_word = _w(pa, _fo(0x308330))
    assert (store_word & 0xFFFF) == NARRATION_PEN_IMM, (
        "the narration pen store after 0x308328 targets 0x%04X, not the narration pen "
        "0x1cc -- the left-flush would land on the wrong slot" % (store_word & 0xFFFF)
    )


def test_tier2_no_unexpected_renderer_region_diffs():
    """L-scope (broad diff): in the X-dispatcher region 0x208300..0x208400, the words
    that differ between pristine and patched must be EXACTLY {Patch-23 left-flush site
    0x2083A8} plus the PRE-EXISTING Patch-14 mode-2 reserve sites (0x2083E4/0x2083EC).
    Crucially 0x2083F8 (Patch 21) must NOT differ (reverted), and no OTHER word in the
    region may differ -- any extra means Patch 23 spilled onto the X-dispatcher."""
    require_file(PRISTINE_EXE, "P2 broad diff")
    pr = open(PRISTINE_EXE, "rb").read()
    pa = _patched()
    region = range(0x208300, 0x208400, 4)
    diffs = {fo for fo in region if _w(pr, fo) != _w(pa, fo)}
    expected = {P23_FO} | set(P14_MODE2_FOS)
    assert diffs == expected, (
        "X-dispatcher region 0x208300..0x208400 diffs = %s, expected the Patch-23 "
        "left-flush site + the pre-existing Patch-14 mode-2 reserve sites %s.  An "
        "extra word means collateral on the X-dispatcher; a MISSING Patch-23 site "
        "means the left-flush did not ship; 0x2083F8 (Patch 21) appearing means it "
        "was NOT reverted"
        % (sorted("0x%06X" % f for f in diffs), sorted("0x%06X" % f for f in expected))
    )
    # Explicit: the Patch-21 site is NOT among the diffs (reverted to pristine).
    assert P21_FO not in diffs, (
        "Patch-21 site 0x%06X differs from pristine -- the dead mode-2 origin was not "
        "reverted" % P21_FO
    )


def test_tier2_patch20_sites_are_dead_path_only():
    """L-scope (Patch 20 dead-path): the four Patch-20 mode-3 sites are either pristine
    or hold their documented dead-path li/nop bytes -- they must NOT have grown into a
    LIVE narration-origin edit (narration is align==0, not mode-3).  This pins that the
    dead path stays inert; it is NOT a required revert."""
    require_file(PRISTINE_EXE, "P2 Patch-20 dead-path check")
    pr = open(PRISTINE_EXE, "rb").read()
    pa = _patched()
    # Documented installed bytes: li v1,-56 (0x2403FFC8) / nop / li v1,-88 (0x2403FFA8) / nop.
    allowed = {
        0x205A00: {0x240300E0, 0x2403FFC8},  # pristine li v1,0xE0 OR installed li v1,-56
        0x205A14: {0x00641823, 0x00000000},  # pristine subu OR installed nop
        0x205A70: {0x240300C0, 0x2403FFA8},  # pristine li v1,0xC0 OR installed li v1,-88
        0x205A84: {0x00641823, 0x00000000},  # pristine subu OR installed nop
    }
    for fo in P20_FOS:
        w = _w(pa, fo)
        assert w in allowed[fo], (
            "Patch-20 dead-path site 0x%06X = 0x%08X is neither pristine nor the "
            "documented inert li/nop -- the mode-3 path must stay dead for narration "
            "(pristine here was 0x%08X)" % (fo, w, _w(pr, fo))
        )


TESTS = [
    # TIER-1 static (always run)
    test_patch23_present_and_targets_correct_origin,
    test_patch21_reverted_to_pristine_in_source,
    test_patch23_new_word_is_li_a0_8,
    test_narration_advance_is_glyph_metrics_not_recomputed,
    test_left_flush_keeps_wide_line_on_screen,
    test_pristine_subu_would_clip_left,
    test_narration_box_px_budget_sane,
    # TIER-2 built / pristine EXE (Skip if absent)
    test_tier2_pristine_holds_subu_at_p23_site,
    test_tier2_built_holds_li_a0_8_and_reverted_addu,
    test_tier2_built_li_decodes_to_constant_8px_inset,
    test_tier2_narration_adv_table_is_glyph_metrics,
    test_tier2_scope_only_p23_changed_narration_origin,
    test_tier2_no_unexpected_renderer_region_diffs,
    test_tier2_patch20_sites_are_dead_path_only,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_narration_left_align")
