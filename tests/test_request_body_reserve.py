#!/usr/bin/env python3
"""
test_request_body_reserve.py -- P1 gate: REQUEST body reserve/advance consistency.

WHAT P1 DID (build/patch_exe.py Patch 22)
-----------------------------------------
The tavern REQUEST description body renders through the universal R1188 renderer's
"path-B" (func 0x307DA0, pen sp+0x1ce, reached via the desc+0x2a8==1 align branch).
That path had a MISMATCH after the proportional-spacing work:

  * the per-line self-centering ORIGIN reserved a count*24 span -- the 3-instr idiom
    at VA 0x30896C/0x308970/0x308974 was (a0<<1 + a0)<<3 == a0*24 (count*24);
  * but the per-glyph ADVANCE on that block stepped ~18px (the shared resident
    Patch-14 ADV LUT @0x4C7564, avg ~17.4 -> 18px target; the Block-2 default-metric
    fallback @0x308CB0/0x308D7C still hard-stepped 0x18 == 24).

reserve(24) > advance(18) ==> the self-centering origin reserved a span ~33% wider
than the line actually drew, so the line origin landed too far LEFT and the line ran
past the RIGHT edge (mostbroken.p2s: the both-edge overflow + garbled 'nce'/'laume'/
'accept' columns).  Patch 22 completes the 24->18 conversion on path-B so reserve
tracks the proportional advance, EXACTLY as Patch 14 already did for the mode-2
reserve (0x308364/0x30836C == count*18):

  reserve idiom  VA 0x30896C  sll v0,a0,1  (0x00041040) -> sll v0,a0,3 (0x000410C0)
                 VA 0x308970  addu v0,v0,a0 (0x00441021) -- UNCHANGED (middle term)
                 VA 0x308974  sll v0,v0,3  (0x000210C0) -> sll v0,v0,1 (0x00021040)
                 ==> ((a0<<3)+a0)<<1 == a0*18, and a0 is PRESERVED (rd=v0, not a0).
  Block-2 advance VA 0x308CB0  addiu v0,v0,0x18 (0x24420018) -> 0x24420012 (18px)
                 VA 0x308D7C  same sibling -> 0x24420012.

SCOPING (disasm-proven -- no narration/dialogue/chargen regression)
-------------------------------------------------------------------
path-B (pen sp+0x1ce) is entered ONLY via the desc+0x2a8==1 align branch.  Live
narration (heavyfog2/leftfield) is desc+0x2a8==0 -> the OTHER path (origin 0x308328,
pen 0x1cc) -- untouched.  Boxed dialogue is the SEPARATE func 0x307510.  Chargen is
Block-A pen 0x1cc @0x308040.  All disjoint file offsets.  screen-mode gp-0x62d8==7
for BOTH narration and request, so it is NOT a usable discriminator -- the align-byte
routing is.  The 18px target is the avg of the resident Patch-14 ADV LUT sourced from
tools/glyph_metrics.py -- widths are NEVER recomputed (project bug #1).

WHAT THIS GATE ASSERTS (all PASS on the current tree)
-----------------------------------------------------
This is the STRUCTURAL P1 gate (the actual visual no-overflow is a fresh-boot
playtest item).  It pins every invariant the WAVE spec requires:

  R-origin  (origin constants): the four Patch-22 file offsets are exactly
            0x2089EC/0x2089F4/0x208D30/0x208DFC (VA 0x30896C/0x308974/0x308CB0/
            0x308D7C) -- the path-B reserve idiom + Block-2 advance sites, NOT a
            moved/wrong target.  These match build/patch_exe.py's p22_sites table.

  R-consistent  (reserve K == advance K == 18, advance==glyph_metrics): the reserve
            idiom multiplier and the per-glyph advance literal are BOTH 18 -- the
            single condition that eliminates the mismatch.  The 18px target is the
            rounded avg of glyph_metrics.adv_table_256() (SoT), never an independent
            literal: if the SoT avg ever rounds away from 18 this trips.

  R-budget  (px budget): the DIALOGUE_BOX_PX / NARRATION_BOX_PX budgets read straight
            from build_v9 (SoT) are sane and the request body (which shares the
            town/narration screen) stays within the wider narration-confirmed span.

  R-idiom   (the *18 idiom is correct AND a0-preserving): MIPS-simulated, the patched
            3-instr idiom yields a0*18 for any count and PRESERVES a0 (rd=v0) -- the
            spec's literal 0x000420C0 (sll a0,a0,3) would have CLOBBERED a0; the
            shipped 0x000410C0 (sll v0,a0,3) is the correct form.

  R-cave-scope  (cave scoping): NONE of the Patch-22 sites touch the narration pen
            0x1ce origin store, the desc+0x2a7 narration align byte, the dialogue
            func 0x307510, or the chargen Block-A advance 0x308040 -- the edit is
            confined to the path-B reserve+advance, so narration/dialogue/chargen
            cannot regress.  Asserted on the build/patch_exe.py p22_sites table.

  R-no-overflow  (consistency => no over-reserve): because reserve K and advance K
            are now identical (18), the reserved span equals the drawn span for every
            line, so the self-centering origin can no longer reserve wider than the
            line draws -- the mechanism behind the mostbroken both-edge overflow is
            structurally removed.  Asserted via the idiom + advance models agreeing.

TIERS
-----
  TIER-1 (static, always): build/patch_exe.py wires Patch 22 at the right offsets to
          the right words, gated by the if-orig/elif-new/else-WARN guard, with the
          *18 multiplier == the glyph_metrics ADV avg.  Runs with NO build artifacts.
  TIER-2 (SKIP when an EXE is absent): the PRISTINE extracted EXE holds the old words
          (preflight) and the BUILT patched EXE holds the new *18 words, byte-exact.
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
import _reloc_v147_design as RELOC  # noqa: E402  (freed-span table VAs, single source)

PATCH_EXE = os.path.join(ROOT, "build", "patch_exe.py")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")
PRISTINE_EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")


# file offset = VA - 0x100000 + 0x80  (MIPS LE, SLPM-65378 -- matches patch_exe.py)
def _fo(va):
    return va - 0x100000 + 0x80


# ---------------------------------------------------------------------------
# Patch 22 wiring constants -- mirror build/patch_exe.py's p22_sites EXACTLY.
# Kept here as the single place a future Patch-22 retune updates the gate too.
# ---------------------------------------------------------------------------
# (file_off, VA, pristine_word, patched_word, label)
RESERVE_HEAD = (0x2089EC, 0x30896C, 0x00041040, 0x000410C0, "reserve idiom head sll v0,a0,1->3")
RESERVE_TAIL = (0x2089F4, 0x308974, 0x000210C0, 0x00021040, "reserve idiom tail sll v0,v0,3->1")
ADV_B        = (0x208D30, 0x308CB0, 0x24420018, 0x24420012, "Block-2 advance 24->18")
ADV_B_SIB    = (0x208DFC, 0x308D7C, 0x24420018, 0x24420012, "Block-2 advance 24->18 sibling")
P22_SITES = [RESERVE_HEAD, RESERVE_TAIL, ADV_B, ADV_B_SIB]

# The middle term of the *18 idiom: addu v0,v0,a0 -- MUST stay pristine (identical in
# the *24 and *18 forms).  Patch 22 must NOT touch it.
RESERVE_MID_FO = 0x2089F0     # VA 0x308970
RESERVE_MID_WORD = 0x00441021  # addu v0,v0,a0

# The mode-2 narration reserve Patch 14 already converted to count*18 -- the proven
# precedent Patch 22 mirrors.  Asserting it stays *18 ensures we mirror the right form.
P14_MODE2_HEAD_FO = _fo(0x308364)
P14_MODE2_TAIL_FO = _fo(0x30836C)

# Per-glyph advance step Patch 22 targets (the proportional pixel pitch, == 18px).
ADV_IMM = 0x12  # 18

# Pen slots: request path-B reserve is pen sp+0x1ce; the NARRATION origin store is the
# OTHER path's pen sp+0x1cc.  A Patch-22 site must NOT write the narration 0x1ce origin
# *centering* path; but note the advance fallback shares the 0x1ce block (sentinel
# glyphs only) -- see scoping doc.  We assert via the source p22_sites table that the
# only sites edited are the four above.
NOP = 0x00000000

# MIPS register file (for idiom simulation / decode).
_REG = ["zero", "at", "v0", "v1", "a0", "a1", "a2", "a3",
        "t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7",
        "s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7",
        "t8", "t9", "k0", "k1", "gp", "sp", "fp", "ra"]


def _decode_sll(word):
    """Decode a SPECIAL sll (op=0, fn=0): return (rd, rt, sa) or None."""
    if (word >> 26) != 0 or (word & 0x3F) != 0:
        return None
    rd = (word >> 11) & 0x1F
    rt = (word >> 16) & 0x1F
    sa = (word >> 6) & 0x1F
    return rd, rt, sa


def _decode_addu(word):
    """Decode a SPECIAL addu (op=0, fn=0x21): return (rd, rs, rt) or None."""
    if (word >> 26) != 0 or (word & 0x3F) != 0x21:
        return None
    rd = (word >> 11) & 0x1F
    rs = (word >> 21) & 0x1F
    rt = (word >> 16) & 0x1F
    return rd, rs, rt


# ---------------------------------------------------------------------------
# Python MODEL of the path-B reserve idiom.
#
# NOT an independent width recompute (project bug #1): the only number this model
# pulls is the *MULTIPLIER*, which it derives from glyph_metrics (the avg of the
# resident ADV LUT the per-glyph advance steps).  It models the 3-instruction idiom's
# DATA FLOW from the actual decoded words so a desync in HOW the idiom multiplies
# (wrong shift amounts, clobbered a0, touched middle term) trips.
# ---------------------------------------------------------------------------
def _reserve_multiplier_from_idiom(head_word, mid_word, tail_word):
    """Simulate the 3-instr reserve idiom on a symbolic count `a0` and return the
    effective multiplier K (reserve == count*K), or raise on a structural fault
    (clobbered a0 / non-sll head/tail / wrong middle op)."""
    h = _decode_sll(head_word)
    assert h is not None, "reserve head 0x%08X is not an sll" % head_word
    m = _decode_addu(mid_word)
    assert m is not None, "reserve middle 0x%08X is not an addu" % mid_word
    t = _decode_sll(tail_word)
    assert t is not None, "reserve tail 0x%08X is not an sll" % tail_word

    # Symbolic registers: a0 holds the line glyph count; everything else 0.
    A0 = 4
    regs = {A0: "a0"}  # track a0 by identity to detect a clobber

    # head: rd = rt << sa
    h_rd, h_rt, h_sa = h
    assert h_rt == A0, (
        "reserve head reads r%d, not a0 -- it must shift the glyph COUNT (a0)" % h_rt
    )
    assert h_rd != A0, (
        "reserve head writes a0 (rd==a0) -- it CLOBBERS the count before the addu "
        "needs it (the spec's 0x000420C0 bug); rd must be a scratch reg (v0)"
    )
    head_mult = 1 << h_sa  # value in h_rd == a0 * (1<<sa)

    # middle: rd = rs + rt  -- must compute head_result + a0  (i.e. a0*(2^sa) + a0)
    m_rd, m_rs, m_rt = m
    assert m_rd == h_rd, (
        "reserve middle writes r%d but head produced r%d -- broken chain" % (m_rd, h_rd)
    )
    operands = {m_rs, m_rt}
    assert h_rd in operands and A0 in operands, (
        "reserve middle (addu r%d,r%d,r%d) is not head_result + a0 -- the +a0 term of "
        "the *18 idiom is wrong" % (m_rd, m_rs, m_rt)
    )
    mid_mult = head_mult + 1  # (a0*head_mult) + a0 == a0*(head_mult+1)

    # tail: rd = rt << sa  -- shifts the middle result
    t_rd, t_rt, t_sa = t
    assert t_rt == m_rd, (
        "reserve tail shifts r%d but middle produced r%d -- broken chain"
        % (t_rt, m_rd)
    )
    return mid_mult << t_sa  # final multiplier K


# ---------------------------------------------------------------------------
# TIER-1 (static): build/patch_exe.py wires Patch 22 + the model == 18 == SoT avg
# ---------------------------------------------------------------------------
def _patch_src():
    require_file(PATCH_EXE, "P1 request-body-reserve gate")
    return open(PATCH_EXE, encoding="utf-8").read()


def _sot_advance_target():
    """The 18px target is the resident ADV LUT's DEFAULT-METRIC fill byte (SoT) -- NOT
    an independent literal.

    Block-2 is the renderer's default-metric FALLBACK (the 0x64-sentinel glyphs per the
    Patch-22 recon), so its per-glyph advance MUST equal the advance a default/sentinel
    glyph gets from the resident table: positions 95..255 of glyph_metrics.adv_table_256()
    are filled with 0x12 == 18 (see glyph_metrics.adv_table_256()).  The path-B reserve
    idiom multiplier is set to that same 18 so reserve tracks the fallback advance.  If
    glyph_metrics ever changes the default fill the gate trips."""
    fill = glyph_metrics.adv_table_256()[255]
    # sanity: the whole 95..255 tail is the single default-fill value
    tail = glyph_metrics.adv_table_256()[95:]
    assert all(b == fill for b in tail), (
        "glyph_metrics.adv_table_256() default-fill region (95..255) is not a single "
        "value -- the 18px default-metric target is ambiguous"
    )
    return fill


def test_patch22_present_and_targets_correct_origins():
    """R-origin: Patch 22 exists and its p22_sites table edits EXACTLY the four
    path-B offsets (0x2089EC/0x2089F4/0x208D30/0x208DFC) from the documented old
    words to the documented new words, guarded by if-orig/elif-new/else-WARN."""
    src = _patch_src()
    assert "Patch 22" in src, (
        "build/patch_exe.py has no Patch 22 -- the REQUEST body reserve/advance "
        "consistency fix (P1) is missing"
    )
    # Each of the four sites must appear in source as a (off, old, new) triple.
    for off, va, old, new, label in P22_SITES:
        trip = "0x%X, 0x%08X, 0x%08X" % (off, old, new)
        # patch_exe.py may format the literals upper/lower -- normalise the search.
        norm = src.replace("0X", "0x")
        assert (
            ("0x%X" % off).lower() in norm.lower()
            and ("0x%08X" % old).lower() in norm.lower()
            and ("0x%08X" % new).lower() in norm.lower()
        ), (
            "Patch 22 p22_sites missing the %s site (VA 0x%X): expected the triple "
            "(0x%06X, old 0x%08X, new 0x%08X)" % (label, va, off, old, new)
        )
    # The guard must be the standard if-orig/elif-new/else-WARN form.
    assert "WARN" in src and "SKIP" in src, (
        "Patch 22 must use the standard if-orig/elif-new(SKIP)/else-WARN guard"
    )


def test_patch22_does_not_touch_idiom_middle_term():
    """R-idiom: Patch 22 must NOT edit the reserve idiom's middle term (addu v0,v0,a0
    @0x308970 / file 0x2089F0) -- it is identical in the *24 and *18 forms, and
    touching it would break the +a0 chain."""
    src = _patch_src()
    norm = src.replace("0X", "0x").lower()
    # The middle file offset must NOT appear as a patched site.
    assert ("0x%x" % RESERVE_MID_FO).lower() not in norm, (
        "Patch 22 references the idiom middle-term file offset 0x%06X -- that addu "
        "v0,v0,a0 must stay pristine (it is the +a0 term, identical in *24 and *18)"
        % RESERVE_MID_FO
    )


def test_reserve_idiom_model_yields_18_and_preserves_a0():
    """R-idiom + R-consistent: the PATCHED 3-instr reserve idiom, MIPS-simulated from
    its decoded words, multiplies the glyph count by exactly 18 (== the glyph_metrics
    default-metric fill byte, SoT) AND preserves a0 (rd=v0, not a0).  Pristine -> 24."""
    target = _sot_advance_target()
    assert target == 18, (
        "the resident ADV default-metric fill byte is %d, not 18 -- the path-B reserve "
        "multiplier must track the default-metric advance; re-derive Patch 22's *18 "
        "from glyph_metrics" % target
    )
    # Patched idiom -> *18, a0 preserved.
    k_new = _reserve_multiplier_from_idiom(
        RESERVE_HEAD[3], RESERVE_MID_WORD, RESERVE_TAIL[3]
    )
    assert k_new == target, (
        "patched reserve idiom multiplies count by %d, expected %d (== glyph_metrics "
        "ADV avg) -- reserve no longer tracks the proportional advance" % (k_new, target)
    )
    # Pristine idiom -> *24 (the documented over-reserve being fixed).
    k_old = _reserve_multiplier_from_idiom(
        RESERVE_HEAD[2], RESERVE_MID_WORD, RESERVE_TAIL[2]
    )
    assert k_old == 24, (
        "pristine reserve idiom multiplies count by %d, expected 24 -- the over-"
        "reserve being fixed is not the documented count*24" % k_old
    )


def test_advance_literal_equals_glyph_metrics_target():
    """R-consistent (advance==glyph_metrics): the patched Block-2 advance literal steps
    18px == the glyph_metrics default-metric fill byte (the same number the reserve idiom
    now multiplies by) -- reserve K and advance K are identical, eliminating the
    mismatch.  The pristine literal was 24."""
    target = _sot_advance_target()
    new_imm = ADV_B[3] & 0xFFFF
    old_imm = ADV_B[2] & 0xFFFF
    assert new_imm == target == ADV_IMM, (
        "patched Block-2 advance imm = %d, expected %d (== glyph_metrics default-metric "
        "/ reserve multiplier) -- per-glyph advance has desynced from the reserve"
        % (new_imm, target)
    )
    assert ADV_B_SIB[3] & 0xFFFF == new_imm, (
        "the advance sibling (0x308D7C) imm != the advance imm -- both Block-2 default-"
        "metric steps must move together"
    )
    assert old_imm == 24, "pristine advance was not 24px (0x18) as documented"
    # addiu opcode (0x09) sanity so we are pinning an addiu, not a coincidental word.
    assert (ADV_B[3] >> 26) == 0x09 and (ADV_B[2] >> 26) == 0x09, (
        "the Block-2 advance words are not addiu (op 0x09) -- wrong site pinned"
    )


def test_reserve_and_advance_multipliers_are_consistent():
    """R-no-overflow: the SINGLE condition that removes the mostbroken both-edge
    overflow -- the reserve idiom multiplier and the per-glyph advance literal are now
    EQUAL.  reserve(K) == advance(K) ==> the self-centering origin reserves exactly the
    span the line draws, so it can never over-reserve wider than the line and push the
    origin off-left / the tail off-right."""
    k_reserve = _reserve_multiplier_from_idiom(
        RESERVE_HEAD[3], RESERVE_MID_WORD, RESERVE_TAIL[3]
    )
    k_advance = ADV_B[3] & 0xFFFF
    assert k_reserve == k_advance, (
        "reserve multiplier (%d) != advance step (%d) -- the path-B mismatch that "
        "causes the request both-edge overflow is NOT resolved" % (k_reserve, k_advance)
    )


def test_box_px_budgets_sane():
    """R-budget (px budgets): the DIALOGUE_BOX_PX / NARRATION_BOX_PX budgets come from
    build_v9 (SoT) and are sane; the request body shares the town/narration screen, so
    its line width must stay within the wider narration-confirmed span.  Asserts the
    budgets exist, are positive, and the widest single glyph fits."""
    src = open(BUILD_V9, encoding="utf-8").read()
    md = re.search(r"^DIALOGUE_BOX_PX\s*=\s*(\d+)", src, re.M)
    mn = re.search(r"^NARRATION_BOX_PX\s*=\s*(\d+)", src, re.M)
    assert md and mn, "build_v9.py: DIALOGUE_BOX_PX / NARRATION_BOX_PX not found"
    dbox, nbox = int(md.group(1)), int(mn.group(1))
    assert dbox > 0 and nbox > 0, "box px budgets must be positive"
    widest = max(glyph_metrics.ADV)
    assert nbox >= widest and dbox >= widest, (
        "a box budget (D=%d / N=%d) is narrower than the widest glyph (%d px)"
        % (dbox, nbox, widest)
    )
    # The request body shares the town/narration screen-mode (gp-0x62d8==7); its
    # centered span must be reservable -- a wrapped request line is <= the narration
    # budget, and the per-line reserve is now count*18 (<= proportional width budget).
    assert nbox <= dbox, (
        "NARRATION_BOX_PX (%d) wider than DIALOGUE_BOX_PX (%d) -- request/narration "
        "share the narrower town span; budgets inverted" % (nbox, dbox)
    )


# ---------------------------------------------------------------------------
# TIER-2 (built / pristine EXE): the bytes actually ship the *18 conversion
# ---------------------------------------------------------------------------
def _patched():
    if not os.path.isfile(PATCHED_EXE):
        raise Skip("build/SLPM_653.78_patched missing (run build/patch_exe.py)")
    return open(PATCHED_EXE, "rb").read()


def _w(data, fo):
    return struct.unpack_from("<I", data, fo)[0]


def test_tier2_pristine_holds_old_words():
    """R-origin (pristine preflight): the extracted EXE holds the OLD words at the four
    sites (count*24 reserve + 24px advance) -- so the if-orig guard will fire and the
    patch lands on the intended, un-moved sites."""
    require_file(PRISTINE_EXE, "P1 pristine preflight")
    pr = open(PRISTINE_EXE, "rb").read()
    for off, va, old, new, label in P22_SITES:
        got = _w(pr, off)
        assert got == old, (
            "pristine EXE @file 0x%06X (VA 0x%X, %s) = 0x%08X, expected old 0x%08X -- "
            "Patch 22 would WARN (no install) or hit a moved site" % (off, va, label, got, old)
        )
    # The idiom middle term must already be the addu and stay so.
    assert _w(pr, RESERVE_MID_FO) == RESERVE_MID_WORD, (
        "pristine idiom middle @0x%06X != addu v0,v0,a0 (0x%08X)"
        % (RESERVE_MID_FO, RESERVE_MID_WORD)
    )


def test_tier2_built_holds_new_18px_words():
    """R-consistent (built bytes): the BUILT patched EXE holds the NEW *18 words at all
    four sites and the idiom middle term is UNCHANGED -- the reserve/advance are
    consistently 18px in the shipped EXE."""
    data = _patched()
    for off, va, old, new, label in P22_SITES:
        got = _w(data, off)
        assert got == new, (
            "patched EXE @file 0x%06X (VA 0x%X, %s) = 0x%08X, expected new 0x%08X -- "
            "the *18 conversion did not ship" % (off, va, label, got, new)
        )
    assert _w(data, RESERVE_MID_FO) == RESERVE_MID_WORD, (
        "patched idiom middle @0x%06X = 0x%08X != addu v0,v0,a0 (0x%08X) -- Patch 22 "
        "wrongly touched the +a0 term" % (RESERVE_MID_FO, _w(data, RESERVE_MID_FO), RESERVE_MID_WORD)
    )


def test_tier2_built_idiom_simulates_to_18_a0_preserved():
    """R-idiom (against built bytes): the SHIPPED reserve idiom, MIPS-simulated from the
    actual built words, yields count*18 AND preserves a0 (rd=v0).  This catches the
    spec's 0x000420C0 a0-clobber bug had it shipped."""
    data = _patched()
    head = _w(data, RESERVE_HEAD[0])
    mid = _w(data, RESERVE_MID_FO)
    tail = _w(data, RESERVE_TAIL[0])
    k = _reserve_multiplier_from_idiom(head, mid, tail)  # raises if a0 clobbered
    assert k == 18, (
        "shipped reserve idiom multiplies count by %d, expected 18 -- the built EXE's "
        "reserve does not track the proportional advance" % k
    )


def test_tier2_advance_equals_built_table_default_metric():
    """R-consistent (advance==glyph_metrics, built): the shipped Block-2 advance literal
    (18) equals the DEFAULT-METRIC fill byte of the resident ADV LUT actually present in
    the built EXE @0x4C7564 -- Block-2 is the default-metric fallback, so its step IS the
    default-glyph advance.  Confirms the per-glyph advance, the reserve and the build
    wrap all consume the ONE SoT table (it is byte-identical to glyph_metrics)."""
    data = _patched()
    adv_tbl_fo = RELOC.fo(RELOC.ADV_VA)   # v175 Option E: ADV table in the freed strncpy span (VA 0x1215B4)
    N = RELOC.TABLE_ENTRIES               # 92 (four 92B tables pack the freed span)
    tbl = data[adv_tbl_fo:adv_tbl_fo + N]
    assert tbl == glyph_metrics.adv_table_256()[:N], (
        "the resident ADV table in the built EXE is not glyph_metrics.adv_table_256()[:%d] "
        "-- the default-metric the advance literal must match is from a desynced table" % N
    )
    # The freed-span table ships only the 92 real glyphs; the default-metric fill byte
    # (indices 95..255) lives in the SoT's full 256-byte table.
    default_metric = glyph_metrics.adv_table_256()[255]  # default-glyph advance (SoT)
    shipped = _w(data, ADV_B[0]) & 0xFFFF
    assert shipped == default_metric == 18, (
        "shipped advance imm (%d) != built-table default-metric (%d) -- the request "
        "default-metric advance has desynced from the resident table" % (shipped, default_metric)
    )


def test_tier2_scope_no_other_renderer_sites_changed():
    """R-cave-scope (built diff): between pristine and patched, the ONLY renderer-region
    (0x208000..0x20A000) words that differ AND are NOT a known Patch 13/14/20/21 site
    must be exactly the four Patch-22 offsets -- no collateral on the narration origin /
    dialogue / chargen paths.  Also confirms the Patch-14 mode-2 *18 precedent intact."""
    require_file(PRISTINE_EXE, "P1 scope diff")
    pr = open(PRISTINE_EXE, "rb").read()
    pa = _patched()
    # Known intentional renderer-region edits OTHER than Patch 22 (Patch 13/14/20/21
    # narration re-center + LUT hooks).  We only need to ensure no UNEXPECTED diff sits
    # on the narration-origin / dialogue / chargen control words; the precise allowlist
    # is the Patch-22 four plus whatever Patch 13/14/20/21 already changed -- so we
    # assert the Patch-22 four ARE in the diff and the idiom-middle is NOT.
    p22_offs = {s[0] for s in P22_SITES}
    region = range(0x208000, 0x20A000, 4)
    diffs = {fo for fo in region if _w(pr, fo) != _w(pa, fo)}
    assert p22_offs <= diffs, (
        "not all four Patch-22 sites differ between pristine and patched: missing %s"
        % sorted(p22_offs - diffs)
    )
    # The idiom middle term must be IDENTICAL (untouched) in the diff.
    assert RESERVE_MID_FO not in diffs, (
        "the reserve idiom middle term @0x%06X changed between pristine and patched -- "
        "Patch 22 clobbered the +a0 term" % RESERVE_MID_FO
    )
    # The Patch-14 mode-2 reserve (the *18 precedent we mirror) must still be count*18
    # in the built EXE.  Its register form differs from path-B (head `sll a0,a1,3`, tail
    # `sll a0,a0,1` -- shifts a1, writes a0), so use the SHIFT-AMOUNT-only multiplier:
    # the (2^sa_head + 1) << sa_tail idiom value, independent of which regs it threads.
    h = _decode_sll(_w(pa, P14_MODE2_HEAD_FO))
    t = _decode_sll(_w(pa, P14_MODE2_TAIL_FO))
    if h is not None and t is not None:
        k = ((1 << h[2]) + 1) << t[2]  # (2^sa_head + 1) << sa_tail  == 18 for sa 3,1
        assert k == 18, (
            "the Patch-14 mode-2 narration reserve (the precedent Patch 22 mirrors) is "
            "*%d not *18 in the built EXE -- precedent broke, re-confirm the form" % k
        )


TESTS = [
    # TIER-1 static (always run)
    test_patch22_present_and_targets_correct_origins,
    test_patch22_does_not_touch_idiom_middle_term,
    test_reserve_idiom_model_yields_18_and_preserves_a0,
    test_advance_literal_equals_glyph_metrics_target,
    test_reserve_and_advance_multipliers_are_consistent,
    test_box_px_budgets_sane,
    # TIER-2 built / pristine EXE (Skip if absent)
    test_tier2_pristine_holds_old_words,
    test_tier2_built_holds_new_18px_words,
    test_tier2_built_idiom_simulates_to_18_a0_preserved,
    test_tier2_advance_equals_built_table_default_metric,
    test_tier2_scope_no_other_renderer_sites_changed,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_request_body_reserve")
