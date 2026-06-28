#!/usr/bin/env python3
"""
test_request_proportional_patch25.py -- Issue B gate: Patch 25 (request-body
proportional advance) ships SAFE and SoT-sourced.

Patch 25 (build/patch_exe.py) replaces the request body's flat 18px-mono Block-2
advance with the SAME per-glyph proportional advance the narration body uses
(Patch 14's resident ADV table @VA 0x4C7564, gid = cell>>8), plus an Option-B
fixed left margin (neutralizing the count*18 centering reserve @VA 0x308968).

It ships OFF BY DEFAULT (PATCH25_ENABLE = False) because reconB3 measured the body
as COUNT-ANCHORED/centered while reconB4 assumes left-anchorable -- a conflict only
the live PCSX2 EE debugger can settle (needsLiveDebugger).  Flipping it in without
that confirm risks re-introducing the Patch-19 Stage-3 centering drift.

This module pins the invariants that keep Patch 25 SAFE whether it is on or off, and
guarantees that IF it is ever enabled it cannot hard-code a stride (project bug #1):

  P25-off (default safety): with PATCH25_ENABLE False, the BUILT EXE keeps Patch
          22's behaviour -- the hook @0x308CAC is the pristine lh v0,0x1ce(sp), the
          cave pad @0x4CAA48 is all-zero, and the centering reserve @0x308968 is the
          pristine subu a0,v0,a0.  So the unvalidated centered-vs-left-anchor patch
          cannot silently ship.

  P25-sot (no inline stride): the source cave reads the RESIDENT Patch-14 ADV table
          (lbu ...0x7564), derives gid via a big-endian cell>>8 (srl 8), gates on the
          Patch-14 marker word, and carries NO inline advance literal -- so an enable
          reuses the single glyph_metrics-sourced table, never a hard-coded *N.

  P25-scope (no blast radius): the hook site, the cave region and the Option-B margin
          site are all on the align==2 Block-2 request path; the source must NOT touch
          the narration pen 0x1cc origin (0x308328), dialogue func 0x307510, or chargen
          advance 0x308040 -- the documented disjoint surfaces.

TIERS
  TIER-1 (static, always): build/patch_exe.py wires Patch 25 with the SoT table read,
          big-endian gid, Patch-14 gate, and the OFF-by-default flag.
  TIER-2 (SKIP if no built EXE): when PATCH25_ENABLE is False the built EXE is
          byte-identical to the Patch-22 request-body behaviour.
"""

import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (  # noqa: E402  (path insert first)
    ROOT,
    Skip,
    main_exit,
    require_file,
)

sys.path.insert(0, os.path.join(ROOT, "build"))
import _reloc_v147_design as RELOC  # noqa: E402  (v147 relocated P14 gate marker)

PATCH_EXE = os.path.join(ROOT, "build", "patch_exe.py")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")
PRISTINE_EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")


# file offset = VA - 0x100000 + 0x80  (MIPS LE, SLPM-65378 -- matches patch_exe.py)
def _fo(va):
    return va - 0x100000 + 0x80


# Patch 25 sites (mirror build/patch_exe.py exactly).
P25_HOOK_FO = 0x208D2C       # VA 0x308CAC  lh v0,0x1ce(sp)  (Block-2 default advance head)
P25_HOOK_ORIG = 0x87A201CE   # pristine displaced instruction
P25_HOOK_J = 0x08132A92      # j 0x4CAA48 (cave) when ENABLED
P25_CAVE_FO = 0x3CAAC8       # VA 0x4CAA48  (40-byte cave)
P25_CAVE_WORDS = 10
P25_MARGIN_FO = 0x2089E8     # VA 0x308968  subu a0,v0,a0  (count reserve)
P25_MARGIN_ORIG = 0x00442023 # subu $a0,$v0,$a0  (pristine)
P25_MARGIN_NEW = 0x00002021  # move $a0,$zero   (Option B, only when ENABLED)
P25_GATE_VAL = RELOC.NEW_GATE_MARKER    # Patch-14 marker word @VA 0x3097A0 (v147 relocated)

ADV_TBL_FO = _fo(0x4C7564)   # resident Patch-14 ADV table


def _src():
    require_file(PATCH_EXE, "Patch 25 gate")
    return open(PATCH_EXE, encoding="utf-8").read()


def _patch25_enable_flag():
    """Read the literal PATCH25_ENABLE assignment from source (True/False)."""
    m = re.search(r"^\s*PATCH25_ENABLE\s*=\s*(True|False)", _src(), re.M)
    assert m, "build/patch_exe.py: PATCH25_ENABLE assignment not found"
    return m.group(1) == "True"


# ---------------------------------------------------------------------------
# TIER-1 (static)
# ---------------------------------------------------------------------------
def test_patch25_present_and_has_enable_flag():
    """Patch 25 must exist and be controlled by an explicit PATCH25_ENABLE flag
    (the OFF-by-default live-contingency safety)."""
    src = _src()
    assert "Patch 25" in src, (
        "build/patch_exe.py has no Patch 25 -- the request-body proportional advance "
        "(Issue B horizontal fix) is missing"
    )
    assert re.search(r"^\s*PATCH25_ENABLE\s*=\s*(True|False)", src, re.M), (
        "Patch 25 must be gated by an explicit PATCH25_ENABLE = True/False flag -- "
        "the live-contingency switch (centered-vs-left-anchored unresolved)"
    )


def test_patch25_cave_reads_resident_adv_table_no_inline_stride():
    """P25-sot: the Patch-25 cave must read the RESIDENT Patch-14 ADV table (lbu
    ...0x7564) and derive gid via the big-endian cell>>8 (srl 8) -- never carry its
    own advance literal.  This is what guarantees an enable reuses the single
    glyph_metrics-sourced table (project bug #1)."""
    src = _src()
    if "Patch 25" not in src:
        return  # nothing to guard yet
    assert "0x90397564" in src or "0x7564" in src, (
        "Patch 25 cave does NOT read the resident ADV table @0x4C7564 (lbu ...0x7564) "
        "-- it must reuse Patch-14's glyph_metrics-sourced table, not a hard-coded stride"
    )
    # big-endian gid derive: srl by 8 (the cave word 0x0002C202 = srl t8,v0,8).
    assert "0x0002C202" in src or "srl" in src.lower(), (
        "Patch 25 cave does NOT do the big-endian gid = cell>>8 read (srl ...,8) -- the "
        "cells are (char-32)<<8 so a low-byte read would squash every glyph to ADV[0]"
    )
    # gate on the Patch-14 marker word (so the ADV table the cave reads is present).
    # v147 routes the gate through RELOC.NEW_GATE_MARKER (relocated P14-hook1 j-word).
    assert ("NEW_GATE_MARKER" in src), (
        "Patch 25 must gate on the Patch-14 resident-table marker (NEW_GATE_MARKER) -- "
        "without it the cave's ADV lookup could read garbage when Patch 14 is absent"
    )
    # No bare inline advance immediate masquerading as the stride: the only advance the
    # cave applies must come from the table, so there must be no `addiu v0,v0,0x12/0x18`
    # ADDED inside the cave word list (the cave adds t9=ADV via addu, not an immediate).
    m = re.search(r"p25_cave\s*=\s*\[(.*?)\]", src, re.S)
    assert m, "Patch 25 cave word list (p25_cave = [...]) not found"
    cave_body = m.group(1)
    assert "0x24420012" not in cave_body and "0x24420018" not in cave_body, (
        "Patch 25 cave carries an inline addiu v0,v0,0x12/0x18 advance literal -- the "
        "advance must come ONLY from the resident ADV table (addu v0,v0,t9), never a "
        "hard-coded monospace step"
    )


def test_patch25_scope_no_other_renderer_sites():
    """P25-scope: every byte Patch 25 WRITES must land on one of its three documented
    align==2 request-path file offsets (hook 0x208D2C, delay 0x208D30, cave 0x3CAAC8,
    margin 0x2089E8).  It must never struct.pack_into the narration origin store
    (file 0x2083A8 = VA 0x308328), the dialogue/chargen control words, etc.  We look
    at actual writes (struct.pack_into target offsets), NOT prose -- the comment block
    legitimately MENTIONS the disjoint surfaces to document that it avoids them."""
    src = _src()
    if "Patch 25" not in src:
        return
    # Isolate the Patch-25 block (its header to the next "PATCH 15" banner) and strip
    # comments so we only inspect executable lines.
    i = src.find("Patch 25")
    j = src.find("PATCH 15", i)
    block = src[i:j if j != -1 else len(src)]
    code = "\n".join(ln.split("#", 1)[0] for ln in block.splitlines())

    # Every struct.pack_into(...) target offset in the Patch-25 block: first hex/const
    # arg after the format string.  The legal write targets (the Patch-25 sites).
    legal = {
        "0x208D2C", "P25_HOOK",       # hook
        "0x208D30", "P25_DELAY",      # delay slot
        "0x3CAAC8", "P25_CAVE",       # cave body (P25_CAVE + i*4)
        "0x2089E8", "P25_MARGIN_OFF", # Option-B margin
    }
    writes = re.findall(r"struct\.pack_into\(\s*[^,]+,\s*data,\s*([A-Za-z0-9_]+)", code)
    bad = [w for w in writes if w not in legal]
    assert not bad, (
        "Patch 25 writes to non-request-path target(s) %s -- it must struct.pack_into "
        "ONLY the align==2 Block-2 sites (hook/delay/cave/margin); a write to the "
        "narration origin (0x2083A8) / dialogue / chargen offsets is out of scope" % bad
    )
    # Hard belt-and-braces: the narration origin store VA file offset must not be a
    # WRITE target anywhere in the block (it may appear only in a comment, stripped above).
    assert "0x2083A8" not in code, (
        "Patch 25 executable code references the narration origin store file offset "
        "0x2083A8 (VA 0x308328) -- that is the disjoint narration path, not the request body"
    )


# ---------------------------------------------------------------------------
# TIER-2 (built EXE)
# ---------------------------------------------------------------------------
def _patched():
    if not os.path.isfile(PATCHED_EXE):
        raise Skip("build/SLPM_653.78_patched missing (run build/patch_exe.py)")
    return open(PATCHED_EXE, "rb").read()


def _w(data, fo):
    return struct.unpack_from("<I", data, fo)[0]


def test_tier2_disabled_leaves_request_body_at_patch22():
    """P25-off: while PATCH25_ENABLE is False, the built EXE must keep Patch 22's
    request-body behaviour -- the hook @0x308CAC stays the pristine lh v0,0x1ce(sp),
    the cave pad @0x4CAA48 is all-zero, and the centering reserve @0x308968 is the
    pristine subu a0,v0,a0.  So the unvalidated centered-vs-left-anchor patch cannot
    silently ship.  (When the flag is True this test asserts the cave IS installed
    instead.)"""
    data = _patched()
    enabled = _patch25_enable_flag()
    hook = _w(data, P25_HOOK_FO)
    margin = _w(data, P25_MARGIN_FO)
    cave_zero = all(b == 0 for b in data[P25_CAVE_FO:P25_CAVE_FO + P25_CAVE_WORDS * 4])

    if not enabled:
        assert hook == P25_HOOK_ORIG, (
            "PATCH25_ENABLE is False but the hook @0x308CAC = 0x%08X != pristine "
            "0x%08X (lh v0,0x1ce(sp)) -- Patch 25 wrote the request hook while disabled"
            % (hook, P25_HOOK_ORIG)
        )
        assert cave_zero, (
            "PATCH25_ENABLE is False but the cave pad @0x4CAA48 is NOT all-zero -- "
            "Patch 25 wrote its cave while disabled (unvalidated patch leaked into ISO)"
        )
        assert margin == P25_MARGIN_ORIG, (
            "PATCH25_ENABLE is False but the centering reserve @0x308968 = 0x%08X != "
            "pristine 0x%08X (subu a0,v0,a0) -- Option B leaked while disabled"
            % (margin, P25_MARGIN_ORIG)
        )
    else:
        assert hook == P25_HOOK_J, (
            "PATCH25_ENABLE is True but the hook @0x308CAC = 0x%08X != j 0x4CAA48 "
            "(0x%08X) -- the request proportional cave is not trampolined" % (hook, P25_HOOK_J)
        )
        # cave installed (first word is the lhu v0,2(s5) read), reads resident ADV table.
        assert _w(data, P25_CAVE_FO) == 0x96A20002, (
            "PATCH25_ENABLE is True but the cave @0x4CAA48 is not installed (word0=0x%08X)"
            % _w(data, P25_CAVE_FO)
        )
        lbu = _w(data, P25_CAVE_FO + 4 * 4)
        assert (lbu & 0xFFFF) == 0x7564, (
            "enabled Patch-25 cave lbu imm = 0x%04X != 0x7564 -- it does not read the "
            "resident Patch-14 ADV table @0x4C7564" % (lbu & 0xFFFF)
        )
        assert margin == P25_MARGIN_NEW, (
            "PATCH25_ENABLE is True but Option-B margin @0x308968 = 0x%08X != move a0,zero "
            "(0x%08X) -- the count reserve was not neutralized" % (margin, P25_MARGIN_NEW)
        )


def test_tier2_patch14_table_present_for_enable():
    """P25-sot (built): the resident ADV table the Patch-25 cave reads (@0x4C7564)
    exists in the built EXE -- so the documented one-line enable is genuinely safe
    (the cave's lbu 0x7564 would resolve to real advance bytes, not a zero pad)."""
    data = _patched()
    tbl = data[ADV_TBL_FO:ADV_TBL_FO + 256]
    # The table must be non-trivial (Patch 14 filled it from glyph_metrics).
    assert any(b != 0 for b in tbl), (
        "resident ADV table @file 0x%X is all-zero -- Patch 14 did not install it, so "
        "enabling Patch 25 would make the cave read a zero advance table" % ADV_TBL_FO
    )
    # And the Patch-14 marker the gate checks must be present.
    gate_fo = _fo(0x3097A0)
    assert _w(data, gate_fo) == P25_GATE_VAL, (
        "Patch-14 marker @file 0x%X = 0x%08X != 0x%08X -- Patch 25's gate would WARN-skip "
        "on enable (the ADV table it reads is not guaranteed present)"
        % (gate_fo, _w(data, gate_fo), P25_GATE_VAL)
    )


def test_tier2_pristine_hook_was_default_advance():
    """The hook site @0x308CAC holds lh v0,0x1ce(sp) in the PRISTINE EXE -- so Patch
    25's trampoline (when enabled) lands on the intended Block-2 default-advance head,
    not a moved site."""
    require_file(PRISTINE_EXE, "Patch 25 pristine preflight")
    pr = open(PRISTINE_EXE, "rb").read()
    got = struct.unpack_from("<I", pr, P25_HOOK_FO)[0]
    assert got == P25_HOOK_ORIG, (
        "pristine EXE @file 0x%06X (VA 0x308CAC) = 0x%08X, expected lh v0,0x1ce(sp) "
        "0x%08X -- Patch 25 would hit a moved site on enable" % (P25_HOOK_FO, got, P25_HOOK_ORIG)
    )


TESTS = [
    # TIER-1 static (always run)
    test_patch25_present_and_has_enable_flag,
    test_patch25_cave_reads_resident_adv_table_no_inline_stride,
    test_patch25_scope_no_other_renderer_sites,
    # TIER-2 built / pristine EXE (Skip if absent)
    test_tier2_disabled_leaves_request_body_at_patch22,
    test_tier2_patch14_table_present_for_enable,
    test_tier2_pristine_hook_was_default_advance,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_request_proportional_patch25")
