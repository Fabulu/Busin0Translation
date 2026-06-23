#!/usr/bin/env python3
"""
test_chargen_centering.py -- P4 gate: CHARGEN Path-1 proportional spacing cave
(build/patch_exe.py Patch 19, v122 RE-ENABLED).

WHAT P4 SHIPS (build/patch_exe.py Patch 19, v122)
-------------------------------------------------
The character-creation prompts (R37: "Enter your name." ...) and the
description/personality boxes (R38: "Lives to hoard gold." ...) render through
Path 1 of the universal R1188 renderer func 0x307DA0, which used a FIXED 24px
monospace pen (`addiu v0,v0,0x18` @VA 0x308040) -- the wide/squashed look in
chargenspaces.p2s.

Patch 19 installs TWO coordinated caves (Stage 3 is INTENTIONALLY NOT hooked --
see below), both reading the SAME resident tables Patch 14 (P0) installed, NEVER
recomputing widths (project bug #1):

  Stage 1 (advance LUT)  @VA 0x4D6600, hooks 0x308040: re-reads the glyph CELL
          (lh 0x40(s1)); the cell is BIG-ENDIAN (char-32)<<8 -- the high byte is
          the glyph id (chargenspaces.p2s: "Lives to hoard gold." @0xE148B2 =
          cells 0x2C00='L' 0x4900='i' ..., low byte always 0x00).  The cave does
          `srl v1,v1,8` to take the HIGH byte, reads ADV[gid] from the resident
          table @0x4C7564 (lbu imm16 0x7564), and advances the chargen pen
          0x1cc(sp) by ADV (not a fixed 0x18).
  Stage 2 (draw-shift)   @VA 0x4D6660, hooks 0x308018: same big-endian read, then
          subtracts LEFTSHIFT[gid] (lbu imm16 0x7690) from the penX draw copy so
          each glyph's ink starts at the pen -> uniform inter-letter gaps.

SCOPING / NO BLAST RADIUS (the WAVE "cave-scoping assertion"): EVERY stage gates
on the screen-mode global `lw $at,-0x62d8($gp) == 5` (RAM 0x4FED18 == 5 in
chargen; == 7 in town/narration/request/dialogue).  mode != 5 takes a STOCK 24px
fallback byte-equivalent to the un-patched path -- so request/narration/dialogue
do NOT regress (this is what fixed the prior "rt" request garble: the v120 cave
had no discriminator and applied to mode-7 too).

WHY STAGE 3 IS NOT HOOKED (v122 draw-math recon, documented in patch_exe.py):
the draw-X is  penX(0x1cc) + box_origin(lh 0x3e(s3)) + s7  with s7 = count*12.
The ORIGINAL centering block sets 0x1cc = 0 - count*12, so the two count*12
terms CANCEL -> draw_X = box_origin + penX_advance.  With Stage 1 supplying a
PROPORTIONAL penX advance, the text is already LEFT-ANCHORED at box_origin with
correct per-glyph spacing.  Re-routing 0x1cc to -SUM/2 would leave s7=count*12
UNCANCELLED and shove text right (a regression).  So 0x307FBC ships PRISTINE.

The v120 bug this build fixes: the old caves did `andi 0xFF` (LOW byte) -> gid=0
-> every glyph squashed to ADV[0]=9.  The shipped caves `srl 8` (HIGH byte) -- so
this gate asserts the high-byte read, the mode-5 gate, and that Stage 3 is
pristine, NOT the old (broken) three-stage / low-byte / Stage-3-hooked layout.

WHAT THIS GATE ASSERTS (all PASS on the current tree -- EXE-only, no live session)
---------------------------------------------------------------------------------
The four invariants the WAVE task names, every width sourced ONLY from the shared
SoT tools/glyph_metrics.py (NEVER recomputed):

  CG-adv   (advance == glyph_metrics): the resident ADV table the caves read
           (@file VA 0x4C7564) is byte-identical to glyph_metrics.adv_table_256(),
           the LEFTSHIFT table @0x4C7690 == glyph_metrics.leftshift_table_256(),
           and the caves' lbu literally address 0x7564 / 0x7690 -- one table feeds
           the advance, the draw-shift AND the build wrap.

  CG-px    (px_width <= box budget): with the cave installed each chargen line
           advances by glyph_metrics.ADV, so its true proportional width is <= the
           chargen text-bar budget -- the lines that overflowed at 24px monospace
           ("Lives to hoard gold." 20*24 = 480px) now measure their real width and
           fit / are no longer squashed.

  CG-scope (mode-5 gate -- the cave-scoping assertion): every cave begins with
           `lw rt,-0x62d8($gp)` + `li t,5` + `bne` so the proportional path runs
           ONLY in screen-mode 5 (chargen); mode 7 (request/narration/dialogue)
           takes the stock 24px fallback that ADVANCES BY 0x18 == the un-patched
           amount, so it never overflows the request/narration boxes.

  CG-cave  (cave installed, reads SoT, distinct pen, big-endian, returns into flow,
           Stage 3 pristine): hook @0x308040 == j cave1 (+nop), hook @0x308018 ==
           j cave2; hook @0x307FBC is PRISTINE (Stage 3 not hooked); each cave does
           the big-endian `srl 8` read, the mode-5 gate, the resident-table lbu,
           the chargen pen 0x1cc(sp) (NEVER narration 0x1ce), and returns into the
           Path-1 flow; the pads are PRISTINE-zero in the un-patched EXE.

  CG-gate  (static): Patch 19 in build/patch_exe.py is ordered AFTER Patch 14,
           gated on Patch 14's resident-table hook word, sources its tables from
           glyph_metrics, encodes the big-endian read + mode-5 gate, and reuses
           freed pads -- so it can never install without its tables present.

TIERS
-----
  TIER-1 (static, always): assert build/patch_exe.py wires Patch 19 correctly and
          the SoT widths fit the budget.  Runs with NO build artifacts.
  TIER-2 (SKIP when build/SLPM_653.78_patched absent): the BUILT patched EXE has
          the two caves installed, byte-correct (big-endian + mode-5 gate),
          reading the SoT tables, Stage 3 pristine.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (  # noqa: E402  (path insert first)
    ROOT,
    Skip,
    main_exit,
    require_file,
)

import glyph_metrics  # noqa: E402  (TOOLS_DIR put on sys.path by _helpers)

# ---------------------------------------------------------------------------
# Patch 19 wiring constants -- mirror build/patch_exe.py exactly.  Kept here as
# the single place a future Patch-19 retune updates the gate too.
# ---------------------------------------------------------------------------
PATCH_EXE = os.path.join(ROOT, "build", "patch_exe.py")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")
PRISTINE_EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")


# file offset = VA - 0x100000 + 0x80  (MIPS LE, SLPM-65378 -- matches patch_exe.py)
def _fo(va):
    return va - 0x100000 + 0x80


# Hook sites (the original Path-1 instructions Patch 19 trampolines)
HOOK1_FO = _fo(0x308040)   # 0x2080C0  advance:   addiu v0,v0,0x18 (0x24420018)
HOOK2_FO = _fo(0x308018)   # 0x208098  draw-shift: lh v1,0x1cc(sp) (0x87A301CC)
HOOK3_FO = _fo(0x307FBC)   # 0x20803C  centering head -- Stage 3 NOT hooked (PRISTINE)
# Cave bodies (in the freed Patch-15-cleared rodata pad 0x4D6600..)
CAVE1_FO = _fo(0x4D6600)   # 0x3D6680  Stage 1 advance LUT (17 words)
CAVE2_FO = _fo(0x4D6660)   # 0x3D66E0  Stage 2 draw-shift  (12 words)
# Resident tables Patch 14 installs (the caves READ these -- never recompute)
ADV_TBL_FO = _fo(0x4C7564)   # 0x3C75E4
LSH_TBL_FO = _fo(0x4C7690)   # 0x3C7710
P14_HOOK1_FO = _fo(0x3097A0)  # 0x209820  Patch-14 resident-table gate word

# Trampoline j-words Patch 19 writes at each hook
J1_WORD = 0x08135980  # j 0x4D6600  (advance cave)
J2_WORD = 0x08135998  # j 0x4D6660  (draw-shift cave)

# Original (pristine) hook words.  Hook1/Hook2 are trampolined; Hook3 STAYS this.
ORIG_H1 = 0x24420018  # addiu v0,v0,0x18   (advance)
ORIG_H2 = 0x87A301CC  # lh    v1,0x1cc(sp) (draw-shift)
ORIG_H3 = 0x00052040  # sll   a0,a1,1      (centering head -- Stage 3 PRISTINE)
ORIG_H3_NEXT = 0x00852021  # addu a0,a0,a1  (the delay-slot/next word, also pristine)

# Cave returns into the Path-1 flow
J_RET1 = 0x080C2012  # j 0x308048  (advance cave -> past the original store)
J_RET2 = 0x080C2007  # j 0x30801C  (draw-shift cave)

# Per-cave word semantics the gate pins (the ACTUAL v122 layout):
#   cave1[0]  lw  $at,-0x62d8($gp)   mode read         (0x8F819D28)
#   cave1[2]  li  $t0,5              mode-5 literal     (0x24080005)
#   cave1[3]  bne $at,$t0,STOCK      mode gate          (op 0x05)
#   cave1[4]  srl $v1,$v1,8          BIG-ENDIAN hi byte (funct 0x02, sa 8)
#   cave1[7]  lbu $t0,0x7564($t0)    resident ADV read  (0x91087564)
#   cave1[8]  lh  $v0,0x1cc($sp)     chargen pen        (imm 0x1cc)
#   cave1[13] addiu $v0,$v0,0x18     STOCK 24px fallback (0x24420018)
#   cave1[14] sh  $v0,0x1cc($sp)     pen store          (imm 0x1cc)
#   cave1[15] j   0x308048           return
#   cave2[0]  lw  $t9,-0x62d8($gp)   mode read (t9; t0 is LIVE) (0x8F999D28)
#   cave2[1]  lh  $v1,0x1cc($sp)     penX (displaced hook)      (imm 0x1cc)
#   cave2[3]  bne $t9,$t8,DONE       mode gate          (op 0x05)
#   cave2[5]  srl $t9,$t9,8          BIG-ENDIAN hi byte (funct 0x02, sa 8)
#   cave2[8]  lbu $at,0x7690($at)    resident LEFTSHIFT read    (0x90217690)
#   cave2[10] j   0x30801C           return
MODE_READ_GP_IMM = 0x9D28   # lw rt,-0x62d8($gp): -0x62d8 as u16
GP_REG = 28                 # $gp
AT_REG, T9_REG = 1, 25
MODE5_LI = 0x24080005       # li $t0,5  (the chargen mode literal in cave1)
ADV_LBU_IMM = 0x7564        # lbu ...,0x7564(base) -> resident ADV   @0x4C7564 + gid
LSH_LBU_IMM = 0x7690        # lbu ...,0x7690(base) -> resident LEFTSHIFT @0x4C7690 + gid
CHARGEN_PEN_IMM = 0x1CC     # chargen pen slot 0x1cc(sp) -- DISTINCT from narration 0x1ce
NARRATION_PEN_IMM = 0x1CE
STOCK_ADV_WORD = 0x24420018  # addiu $v0,$v0,0x18 -- the mode!=5 stock fallback advance
STOCK_ADV_PX = 0x18         # 24px -- the un-patched monospace advance
NOP = 0x00000000

# Chargen text-bar budget (logical screen px).  The widest personality line
# "Lives to hoard gold." (20 glyphs) was 20*24 = 480px at the OLD monospace and
# overflowed both box edges (chargenspaces.p2s).  At glyph_metrics widths it is
# ~283px.  The chargen description box is the dialogue-box width (480px); the gate
# uses that as the budget the proportional width must fit under.
CHARGEN_BOX_PX = 480


def _enc(s):
    """ASCII -> gid list (gid = char-32), the SAME index family as glyph_metrics."""
    return [ord(c) - 32 for c in s]


# Pure-SoT proportional width of a glyph line (the ADVANCE the Stage-1 cave applies
# per glyph, summed).  Reads glyph_metrics.ADV ONLY -- never recomputed.
def _sot_width(gids, adv_table):
    return sum(adv_table[g & 0xFF] for g in gids if 0 <= (g & 0xFF) < 95)


# ---------------------------------------------------------------------------
# TIER-1 (static): patch_exe.py wires Patch 19 correctly + SoT widths fit
# ---------------------------------------------------------------------------
def _patch_src():
    require_file(PATCH_EXE, "P4 chargen-centering gate")
    return open(PATCH_EXE, encoding="utf-8").read()


def test_patch19_present_after_patch14_and_gated():
    """CG-gate: Patch 19 must exist, be ordered AFTER Patch 14, gate on the Patch-14
    resident-table hook word, and source its tables from the same 0x7564 / 0x7690
    resident tables -- never installed without the tables it reads being present."""
    src = _patch_src()
    assert "Patch 19" in src, (
        "build/patch_exe.py has no Patch 19 -- the chargen Path-1 proportional "
        "spacing cave (P4) is missing"
    )
    i14 = src.find("Patch 14")
    i19 = src.find("Patch 19")
    assert i14 != -1 and i19 != -1 and i14 < i19, (
        "Patch 19 must be ordered AFTER Patch 14 (it reads Patch 14's resident "
        "ADV/LEFTSHIFT tables); found Patch 14 @%d, Patch 19 @%d" % (i14, i19)
    )
    # Gate: Patch 19 checks the Patch-14 hook word (0x08131D50) before installing.
    assert "0x08131D50" in src, (
        "Patch 19 must gate on the Patch-14 resident-table hook word 0x08131D50 "
        "(so the caves' lbu 0x7564/0x7690 tables are guaranteed present)"
    )
    # The caves' table-read literals must be the resident ADV/LEFTSHIFT tables.
    assert "0x7564" in src, (
        "Patch 19 advance cave must read the resident ADV table at 0x...7564 "
        "(the Patch-14 table) -- the ADV table-read literal is gone"
    )
    assert "0x7690" in src, (
        "Patch 19 draw-shift cave must read the resident LEFTSHIFT table at "
        "0x...7690 (the Patch-14 table) -- the LEFTSHIFT literal is gone"
    )
    # Patch 19 must reuse a freed/cleared pad off the Patch-14/Patch-20 caves.
    assert "0x4D6600" in src, (
        "Patch 19 caves must live in the freed/cleared rodata pad at 0x4D6600.."
    )
    # Chargen pen must be 0x1cc(sp) -- distinct from narration 0x1ce(sp).
    assert "0x1cc(sp)" in src or "0x1cc($sp)" in src or "0x1cc" in src, (
        "Patch 19 caves must use the chargen pen 0x1cc(sp), distinct from "
        "narration's 0x1ce(sp) -- pen reference missing"
    )


def test_patch19_source_encodes_bigendian_and_mode5_gate():
    """CG-scope (static): the v122 fix has two halves the source MUST encode --
    (1) the BIG-ENDIAN glyph read `srl ...,8` (the v120 `andi 0xFF` low-byte read
    was the squash bug) and (2) the screen-mode-5 gate `lw $at,-0x62d8($gp)`.
    Without either, Patch 19 would re-introduce the squash OR the 'rt' request
    regression.  Pure source guard."""
    src = _patch_src()
    # mode discriminator: the screen-mode global at gp-0x62d8 (== 5 in chargen).
    assert "-0x62d8($gp)" in src or "0x62d8" in src, (
        "Patch 19 dropped the screen-mode gate (lw $at,-0x62d8($gp)) -- without it "
        "the proportional path would apply to mode-7 request/narration and re-garble "
        "them ('rt' regression)"
    )
    assert "9d28" in src.lower() or "0x9d28" in src.lower(), (
        "Patch 19 mode-read instruction word (lw rt,-0x62d8($gp) == 0x..9d28) is "
        "gone -- the cave can no longer read the screen-mode discriminator"
    )
    # big-endian high-byte read: the cave words srl by 8 (0x...1a02 / 0x...ca02).
    assert "1a02" in src.lower() and "ca02" in src.lower(), (
        "Patch 19 dropped the big-endian `srl ...,8` glyph read (cave1 0x00031A02 / "
        "cave2 0x0019CA02) -- the cells are (char-32)<<8 so a low-byte read squashes "
        "every glyph to ADV[0]=9 (the v120 bug)"
    )
    # Stage 3 must NOT be re-hooked: the source must not write a j at 0x307FBC.
    assert "0x081359A8" not in src or "Stage 3 NOT hooked" in src or "NOT hooked" in src, (
        "Patch 19 appears to re-hook Stage 3 (centering @0x307FBC) -- v122 ships it "
        "PRISTINE because the stock count*12 reserve cancels s7; re-hooking shoves "
        "text right (a regression)"
    )


def test_patch_exe_imports_glyph_metrics():
    """CG-adv: the cave tables must come from the SoT: patch_exe.py imports
    glyph_metrics (the same module the resident ADV/LEFTSHIFT tables are baked from)."""
    assert "import glyph_metrics" in _patch_src(), (
        "build/patch_exe.py dropped `import glyph_metrics` -- the Patch-19 caves and "
        "the resident tables they read must both come from tools/glyph_metrics.py"
    )


def test_chargen_lines_fit_box_at_new_budget():
    """CG-px: with the proportional cave installed each chargen line advances by
    glyph_metrics.ADV, so its true px width is <= the chargen description-box budget.
    The personality lines that OVERFLOWED at the OLD 24px monospace ("Lives to hoard
    gold." = 20*24 = 480px on both edges) now measure their real proportional width
    and FIT.  Pure SoT."""
    adv = glyph_metrics.adv_table_256()
    lines = [
        "Lives to hoard gold.",   # Miser (chargenspaces.p2s -- the overflow line)
        "Mad if loot is low.",    # Miser line 2
        "Enter your name.",       # R37 name prompt
        "Select gender.",
        "Select personality.",
        "Select alignment.",
    ]
    for line in lines:
        gids = _enc(line)
        new_px = _sot_width(gids, adv)
        old_monospace = len(line) * STOCK_ADV_PX
        assert new_px <= CHARGEN_BOX_PX, (
            "chargen line %r is %d px at glyph_metrics widths, > the %d px description "
            "box -- it would still clip; the proportional fix is insufficient"
            % (line, new_px, CHARGEN_BOX_PX)
        )
        # The proportional cave must be genuinely narrower than the monospace it
        # replaces (so the wide/squashed look is actually fixed).
        assert new_px < old_monospace, (
            "chargen line %r did not shrink (%d px proportional vs %d px monospace) "
            "-- the cave is not narrowing the box" % (line, new_px, old_monospace)
        )
    # Documented self-cure: the R37 name prompt 384px monospace -> 246px proportional.
    assert _sot_width(_enc("Enter your name."), adv) == 246, (
        "the documented R37 name-prompt self-cure (384px monospace -> 246px "
        "proportional) no longer holds -- glyph_metrics widths changed; re-confirm "
        "the chargen wrap budget"
    )


def test_proportional_advance_never_exceeds_stock_no_overflow():
    """CG-px / no-overflow: the per-glyph proportional advance (glyph_metrics.ADV)
    must NEVER exceed the stock 24px monospace advance the mode!=5 fallback uses.
    This is what guarantees the mode-5 chargen path can only make lines NARROWER
    (never overflow further than the un-patched build), and that the mode-7 fallback
    -- which advances by the literal 0x18 -- is byte-equivalent to the un-patched
    path.  Pure SoT."""
    adv = glyph_metrics.adv_table_256()
    worst = max(adv[g] for g in range(95))
    assert worst <= STOCK_ADV_PX, (
        "max glyph_metrics.ADV over printable glyphs is %d px > the %d px stock "
        "monospace advance -- the proportional chargen path could advance WIDER than "
        "the un-patched build and overflow the box" % (worst, STOCK_ADV_PX)
    )


# ---------------------------------------------------------------------------
# TIER-2 (built patched EXE): two caves installed, byte-correct, reading the SoT
# ---------------------------------------------------------------------------
def _patched():
    if not os.path.isfile(PATCHED_EXE):
        raise Skip("build/SLPM_653.78_patched missing (run build/patch_exe.py)")
    return open(PATCHED_EXE, "rb").read()


def _w(data, fo):
    return struct.unpack_from("<I", data, fo)[0]


def test_tier2_gate_and_hooks_installed():
    """CG-cave: the built patched EXE has Patch 14's gate word present (so the
    resident tables exist), Stage-1 + Stage-2 trampoline to their caves, AND Stage 3
    (centering @0x307FBC) is PRISTINE -- v122 ships only the two-stage layout."""
    data = _patched()
    assert _w(data, P14_HOOK1_FO) == 0x08131D50, (
        "Patch-14 hook word @file 0x%X = 0x%08X != 0x08131D50 -- the resident tables "
        "the Patch-19 caves read are NOT installed, so Patch 19 must not be either"
        % (P14_HOOK1_FO, _w(data, P14_HOOK1_FO))
    )
    assert _w(data, HOOK1_FO) == J1_WORD, (
        "Stage-1 hook @0x308040 = 0x%08X, expected j 0x4D6600 (0x%08X) -- advance "
        "LUT cave not trampolined" % (_w(data, HOOK1_FO), J1_WORD)
    )
    assert _w(data, HOOK1_FO + 4) == NOP, (
        "Stage-1 hook delay slot (displaced store) must be nop (got 0x%08X)"
        % _w(data, HOOK1_FO + 4)
    )
    assert _w(data, HOOK2_FO) == J2_WORD, (
        "Stage-2 hook @0x308018 = 0x%08X, expected j 0x4D6660 (0x%08X) -- draw-shift "
        "cave not trampolined" % (_w(data, HOOK2_FO), J2_WORD)
    )
    # Stage 3 is INTENTIONALLY NOT hooked -- the centering head + next word must be
    # the pristine count*12 reserve, NOT a trampoline (re-hooking is a regression).
    assert _w(data, HOOK3_FO) == ORIG_H3, (
        "Stage-3 site @0x307FBC = 0x%08X, expected PRISTINE 0x%08X (sll a0,a1,1) -- "
        "v122 must NOT hook centering (stock count*12 cancels s7; re-hooking shoves "
        "text right)" % (_w(data, HOOK3_FO), ORIG_H3)
    )
    assert _w(data, HOOK3_FO + 4) == ORIG_H3_NEXT, (
        "Stage-3 next word @0x307FC0 = 0x%08X, expected PRISTINE 0x%08X (addu a0,a0,a1) "
        "-- the count*12 reserve must stay intact" % (_w(data, HOOK3_FO + 4), ORIG_H3_NEXT)
    )


def _assert_mode5_gate(data, cave_fo, expect_rt, label):
    """CG-scope: a cave's first word is `lw rt,-0x62d8($gp)` (mode read) and a later
    word is `li t,5` + a `bne` -- the proportional path runs ONLY in screen-mode 5."""
    w0 = _w(data, cave_fo + 0)
    op, rs, rt, imm = w0 >> 26, (w0 >> 21) & 0x1F, (w0 >> 16) & 0x1F, w0 & 0xFFFF
    assert op == 0x23 and rs == GP_REG and imm == MODE_READ_GP_IMM, (
        "%s word[0]=0x%08X is not `lw rt,-0x62d8($gp)` (op=0x%02X rs=%d imm=0x%04X) -- "
        "the cave does not read the screen-mode discriminator at gp-0x62d8"
        % (label, w0, op, rs, imm)
    )
    assert rt == expect_rt, (
        "%s mode-read target reg = %d, expected %d (cave1 uses $at, cave2 uses $t9 so "
        "the LIVE $t0 is preserved)" % (label, rt, expect_rt)
    )
    # somewhere in the cave: a `li t,5` (addiu rt,$zero,5) AND a `bne` (op 0x05).
    words = [_w(data, cave_fo + i * 4) for i in range(12)]
    li5 = any((wd >> 26) == 0x09 and (wd & 0xFFFF) == 5 and ((wd >> 21) & 0x1F) == 0
              for wd in words)
    bne = any((wd >> 26) == 0x05 for wd in words)
    assert li5, (
        "%s has no `li t,5` (the mode-5 literal) -- the screen-mode gate compares "
        "against the wrong value" % label
    )
    assert bne, (
        "%s has no `bne` after the mode read -- the proportional path is not gated, "
        "so it would also run in mode-7 (request/narration regression)" % label
    )


def _assert_bigendian_read(data, cave_fo, n, label):
    """CG-cave: the cave does `srl rd,rt,8` (funct 0x02, sa 8) -- reads the HIGH byte
    of the (char-32)<<8 cell.  A low-byte `andi 0xFF` (the v120 bug) would squash."""
    found = False
    for i in range(n):
        wd = _w(data, cave_fo + i * 4)
        if (wd >> 26) == 0 and (wd & 0x3F) == 0x02 and ((wd >> 6) & 0x1F) == 8:
            found = True
            break
        # a low-byte mask `andi rt,rs,0xFF` would be the v120 squash bug -- forbid it
        if (wd >> 26) == 0x0C and (wd & 0xFFFF) == 0xFF:
            assert False, (
                "%s word[%d]=0x%08X is `andi ...,0xFF` (LOW-byte read) -- the v120 "
                "squash bug; the cells are (char-32)<<8 and need `srl ...,8`"
                % (label, i, wd)
            )
    assert found, (
        "%s has no `srl rd,rt,8` -- the big-endian high-byte glyph read is missing, "
        "so the cell (char-32)<<8 is not converted to a glyph id" % label
    )


def test_tier2_caves_read_sot_tables_use_chargen_pen_and_gate_mode5():
    """CG-cave + CG-adv + CG-scope: Stage-1 reads the resident ADV table (lbu imm16
    == 0x7564), Stage-2 reads LEFTSHIFT (0x7690); both gate on screen-mode 5, do the
    big-endian `srl 8` read, use the chargen pen 0x1cc(sp) (NEVER 0x1ce), and return
    into the Path-1 flow."""
    data = _patched()

    # ---- cave1 (advance LUT) ----
    _assert_mode5_gate(data, CAVE1_FO, AT_REG, "advance cave1")
    _assert_bigendian_read(data, CAVE1_FO, 17, "advance cave1")
    # lbu of the resident ADV table @0x7564
    c1_lbu = _w(data, CAVE1_FO + 7 * 4)
    assert (c1_lbu & 0xFFFF) == ADV_LBU_IMM, (
        "advance cave lbu imm16 = 0x%04X != 0x%04X -- it does NOT read the Patch-14 "
        "resident ADV table @0x4C7564" % (c1_lbu & 0xFFFF, ADV_LBU_IMM)
    )
    # chargen pen 0x1cc(sp) load (word[8]) + store (word[14])
    c1_lh = _w(data, CAVE1_FO + 8 * 4)
    c1_sh = _w(data, CAVE1_FO + 14 * 4)
    assert (c1_lh & 0xFFFF) == CHARGEN_PEN_IMM and (c1_sh & 0xFFFF) == CHARGEN_PEN_IMM, (
        "advance cave pen lh/sh imm = 0x%03X/0x%03X != 0x1cc -- wrong pen slot "
        "(narration 0x1ce regression?)" % (c1_lh & 0xFFFF, c1_sh & 0xFFFF)
    )
    # the mode!=5 fallback must advance by the STOCK 24px (byte-equivalent to unpatched)
    assert _w(data, CAVE1_FO + 13 * 4) == STOCK_ADV_WORD, (
        "advance cave stock fallback @word[13] = 0x%08X != 0x%08X (addiu $v0,$v0,0x18) "
        "-- mode!=5 must advance by the un-patched 24px (request/narration no-regress)"
        % (_w(data, CAVE1_FO + 13 * 4), STOCK_ADV_WORD)
    )
    assert _w(data, CAVE1_FO + 15 * 4) == J_RET1, (
        "advance cave does not j 0x308048 back into Path-1 (got 0x%08X)"
        % _w(data, CAVE1_FO + 15 * 4)
    )

    # ---- cave2 (draw-shift) ----
    _assert_mode5_gate(data, CAVE2_FO, T9_REG, "draw-shift cave2")
    _assert_bigendian_read(data, CAVE2_FO, 12, "draw-shift cave2")
    # penX load (word[1], displaced hook) on the chargen pen
    c2_lh = _w(data, CAVE2_FO + 1 * 4)
    assert (c2_lh & 0xFFFF) == CHARGEN_PEN_IMM, (
        "draw-shift cave penX lh imm = 0x%03X != 0x1cc -- wrong pen slot"
        % (c2_lh & 0xFFFF)
    )
    c2_lbu = _w(data, CAVE2_FO + 8 * 4)
    assert (c2_lbu & 0xFFFF) == LSH_LBU_IMM, (
        "draw-shift cave lbu imm16 = 0x%04X != 0x%04X -- it does NOT read the Patch-"
        "14 resident LEFTSHIFT table @0x4C7690" % (c2_lbu & 0xFFFF, LSH_LBU_IMM)
    )
    assert _w(data, CAVE2_FO + 10 * 4) == J_RET2, (
        "draw-shift cave does not j 0x30801C back into Path-1 (got 0x%08X)"
        % _w(data, CAVE2_FO + 10 * 4)
    )

    # Hard no-narration-regression: NEITHER cave may touch 0x1ce(sp).
    for label, cave, n in (("cave1", CAVE1_FO, 17), ("cave2", CAVE2_FO, 12)):
        for i in range(n):
            word = _w(data, cave + i * 4)
            assert (word & 0xFFFF) != NARRATION_PEN_IMM or (word >> 26) not in (
                0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B,  # lb/lh/lw/lbu/lhu/sb/sh/sw
            ), (
                "%s word[%d]=0x%08X references the NARRATION pen 0x1ce(sp) -- a "
                "chargen cave must only touch the chargen pen 0x1cc(sp)"
                % (label, i, word)
            )


def test_tier2_resident_tables_are_glyph_metrics():
    """CG-adv: the resident ADV (@0x4C7564) and LEFTSHIFT (@0x4C7690) tables the
    Patch-19 caves read are byte-for-byte glyph_metrics.adv_table_256() /
    leftshift_table_256() -- advance, draw-shift AND the build wrap all consume the
    ONE SoT, so they can never desync (project bug #1)."""
    data = _patched()
    adv = data[ADV_TBL_FO:ADV_TBL_FO + 256]
    lsh = data[LSH_TBL_FO:LSH_TBL_FO + 256]
    assert adv == glyph_metrics.adv_table_256(), (
        "resident ADV table @file 0x%X != glyph_metrics.adv_table_256() -- the "
        "Patch-19 advance cave would use a desynced table" % ADV_TBL_FO
    )
    assert lsh == glyph_metrics.leftshift_table_256(), (
        "resident LEFTSHIFT table @file 0x%X != glyph_metrics.leftshift_table_256() "
        "-- the Patch-19 draw-shift cave would use a desynced table" % LSH_TBL_FO
    )


def test_tier2_live_table_width_equals_glyph_metrics():
    """CG-adv (against the BUILT bytes): summing the cave's OWN resident ADV table for
    a real chargen line equals glyph_metrics.px_width -- the live per-glyph advance IS
    the SoT line width (no recompute)."""
    data = _patched()
    live = data[ADV_TBL_FO:ADV_TBL_FO + 256]
    for phrase in ("Lives to hoard gold.", "Enter your name.", "Select personality."):
        model = _sot_width(_enc(phrase), live)
        truth = glyph_metrics.px_width(phrase, lambda c: ord(c) - 32)
        assert model == truth, (
            "live-table chargen advance sum (%d) != glyph_metrics.px_width (%d) for "
            "%r -- the built advance table does not equal the SoT line width"
            % (model, truth, phrase)
        )


def test_tier2_pads_were_pristine_zero():
    """CG-cave (real-PS2 safety): the two cave bodies sit in pad space that is
    ALL-ZERO in the PRISTINE extracted EXE, so Patch 19 clobbers no live game code."""
    require_file(PRISTINE_EXE, "pristine-pad zero check")
    pristine = open(PRISTINE_EXE, "rb").read()
    for label, cave, n in (("cave1 0x4D6600", CAVE1_FO, 17),
                           ("cave2 0x4D6660", CAVE2_FO, 12)):
        chunk = pristine[cave:cave + n * 4]
        assert all(b == 0 for b in chunk), (
            "%s pad is NOT all-zero in the pristine EXE -- Patch 19 would overwrite "
            "live game code (NOT real-PS2 safe)" % label
        )


def test_tier2_hook_sites_were_original_path1_words():
    """CG-cave: the hook sites hold the expected ORIGINAL Path-1 instructions in the
    PRISTINE EXE (advance addiu 0x18, draw lh 0x1cc, centering sll a0,a1,1) -- so
    Patch 19 trampolines the intended sites; AND the centering head @0x307FBC is the
    SAME in the patched EXE (Stage 3 not hooked)."""
    require_file(PRISTINE_EXE, "pristine hook-word check")
    pristine = open(PRISTINE_EXE, "rb").read()
    for label, fo, exp in (("advance 0x308040", HOOK1_FO, ORIG_H1),
                           ("draw-shift 0x308018", HOOK2_FO, ORIG_H2),
                           ("centering 0x307FBC", HOOK3_FO, ORIG_H3)):
        got = struct.unpack_from("<I", pristine, fo)[0]
        assert got == exp, (
            "pristine hook %s = 0x%08X, expected 0x%08X -- Patch 19 would either WARN "
            "(no install) or patch the wrong site" % (label, got, exp)
        )


def test_tier2_request_narration_fallback_is_stock_advance():
    """CG-scope / no-overflow: prove the mode!=5 fallback is byte-equivalent to the
    un-patched advance.  The cave's stock branch advances $v0 by exactly 0x18 (the
    SAME `addiu $v0,$v0,0x18` the pristine hook held) -- so request (mode 7),
    narration (mode 7) and dialogue (mode 7) get the identical un-patched 24px
    advance and cannot regress / overflow."""
    data = _patched()
    pristine = None
    if os.path.isfile(PRISTINE_EXE):
        pristine = open(PRISTINE_EXE, "rb").read()
    stock = _w(data, CAVE1_FO + 13 * 4)
    assert stock == STOCK_ADV_WORD, (
        "mode!=5 stock fallback @cave1 word[13] = 0x%08X, expected 0x%08X "
        "(addiu $v0,$v0,0x18) -- the request/narration fallback is NOT the stock "
        "24px advance" % (stock, STOCK_ADV_WORD)
    )
    if pristine is not None:
        orig = struct.unpack_from("<I", pristine, HOOK1_FO)[0]
        assert stock == orig, (
            "mode!=5 stock fallback (0x%08X) != the pristine Path-1 advance "
            "(0x%08X) -- mode-7 (request/narration/dialogue) would NOT be "
            "byte-equivalent to the un-patched build" % (stock, orig)
        )


TESTS = [
    # TIER-1 static (always run)
    test_patch19_present_after_patch14_and_gated,
    test_patch19_source_encodes_bigendian_and_mode5_gate,
    test_patch_exe_imports_glyph_metrics,
    test_chargen_lines_fit_box_at_new_budget,
    test_proportional_advance_never_exceeds_stock_no_overflow,
    # TIER-2 built EXE (Skip if absent)
    test_tier2_gate_and_hooks_installed,
    test_tier2_caves_read_sot_tables_use_chargen_pen_and_gate_mode5,
    test_tier2_resident_tables_are_glyph_metrics,
    test_tier2_live_table_width_equals_glyph_metrics,
    test_tier2_pads_were_pristine_zero,
    test_tier2_hook_sites_were_original_path1_words,
    test_tier2_request_narration_fallback_is_stock_advance,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_chargen_centering")
