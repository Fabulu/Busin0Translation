#!/usr/bin/env python3
"""test_chargen_cave_imports_metrics.py -- static pre-guard for the (live-gated)
chargen proportional-spacing cave.

The chargen prose path (data/chargen_spacing_backlog.md: R1188 Path 1, func
0x307DA0, advance @0x308040, left-shift feed @0x307FBC) is HARD live-gated -- it
needs a PCSX2 single-step before any cave is installed.  This module places the
STATIC guard NOW so that whenever that cave IS added it is FORCED to source its
256-byte advance table from glyph_metrics.adv_table_256() (the single source of
truth), never an inline literal.  Autonomous-safe: asserts only on source text.

PASSES on the current tree (no chargen hook exists yet -- grep 0x308040/0x307FBC
=> 0 hits in patch_exe.py).  Only trips when a future chargen advance table is
added inline without glyph_metrics.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import BUILD_V9, main_exit, require_file  # noqa: E402

PATCH_EXE = os.path.join(os.path.dirname(BUILD_V9), "patch_exe.py")
# chargen advance / left-shift hook VAs (data/chargen_spacing_backlog.md)
CHARGEN_VAS = (0x308040, 0x307FBC, 0x307DA0)
# any of the VA literals, in the hex forms patch_exe.py uses (0x308040 etc.)
_VA_RE = re.compile(r"0x3080[0-9A-Fa-f]{2}|0x307F[0-9A-Fa-f]{2}|0x307D[0-9A-Fa-f]{2}")
_RAW_ADV_TBL = re.compile(r"bytearray\(\s*\[\s*0x12\s*\]\s*\)\s*\*\s*256")

# Resident SoT-table displacements that the Patch-14 hook writes into the EXE from
# glyph_metrics (adv_table_256 @VA 0x4C7564, leftshift_table_256 @VA 0x4C7690): the
# Patch-19 chargen caves MUST index THESE same resident tables (lbu ...0x7564 /
# ...0x7690) rather than carry their own advance/left-shift literals.  Match either
# the bare displacement (lbu comment / cave machine word low half) or the full VA.
_ADV_TABLE_REF = re.compile(r"0x4C7564|0x7564\b")
_LEFTSHIFT_TABLE_REF = re.compile(r"0x4C7690|0x7690\b")


def _src():
    require_file(PATCH_EXE, "chargen-cave guard")
    return open(PATCH_EXE, encoding="utf-8").read()


def _strip(src):
    return "\n".join(l.split("#", 1)[0] for l in src.splitlines())


def test_patch_exe_imports_glyph_metrics():
    """patch_exe.py must import glyph_metrics (the SoT for cave width tables)."""
    assert "import glyph_metrics" in _src(), (
        "build/patch_exe.py dropped `import glyph_metrics` -- the chargen and "
        "narration caves must read tools/glyph_metrics.py, never inline widths"
    )


def test_no_inline_advance_table_near_chargen_hook():
    """If a chargen advance/left-shift hook (0x308040/0x307FBC/0x307DA0) is
    present, forbid a raw 256-byte advance literal in the same window -- it must
    be glyph_metrics.adv_table_256().  PASSES today (no such hook installed)."""
    code = _strip(_src())
    lines = code.splitlines()
    hook_lines = [i for i, ln in enumerate(lines) if _VA_RE.search(ln)]
    if not hook_lines:
        return  # no chargen hook yet -- the guard is correctly inert (PASS)
    WINDOW = 25  # lines either side: a cave + its table live in one block
    for hl in hook_lines:
        lo, hi = max(0, hl - WINDOW), min(len(lines), hl + WINDOW + 1)
        block = "\n".join(lines[lo:hi])
        if _RAW_ADV_TBL.search(block):
            assert "glyph_metrics.adv_table_256()" in block, (
                "a raw 256-byte advance table (bytearray([0x12])*256) sits "
                "within %d lines of a chargen hook (%s) WITHOUT "
                "glyph_metrics.adv_table_256() -- the chargen cave must source "
                "its advance table from glyph_metrics, never an inline literal "
                "(silent desync, project bug #1)"
                % (WINDOW, ", ".join("0x%X" % v for v in CHARGEN_VAS))
            )


def test_patch19_caves_index_shared_sot_tables():
    """Patch 19 (the chargen Path-1 proportional caves) MUST index the SAME
    resident SoT tables Patch 14 fills from glyph_metrics -- the resident ADV table
    @VA 0x4C7564 (filled from glyph_metrics.adv_table_256()) and the resident
    LEFTSHIFT table @VA 0x4C7690 (from glyph_metrics.leftshift_table_256()) -- and
    must NOT carry its own advance/left-shift literals.

    This is the POSITIVE complement to test_no_inline_advance_table_near_chargen_hook:
    that test forbids an inline 256-byte table near the hooks; this one requires the
    cave to actually reference the shared resident tables.  Static source guard
    (autonomous-safe); inert until the chargen hooks (0x308040 advance, 0x307FBC
    summed-centering) are installed -- PASSES on the current tree where Patch 19 is
    present and reads 0x7564 / 0x7690."""
    src = _src()
    # Gate on the chargen-hook VAs actually being present (Patch 19 installed).
    if "0x308040" not in src or "0x307FBC" not in src:
        return  # no chargen hooks yet -- guard correctly inert (PASS)

    # The cave must read the resident ADV table (advance LUT + summed centering) and
    # the resident LEFTSHIFT table (draw-shift) -- the exact tables Patch 14 writes
    # from glyph_metrics.  No reference => the cave recomputed widths (project bug #1).
    assert _ADV_TABLE_REF.search(src), (
        "Patch 19 chargen caves do NOT index the resident ADV table (0x4C7564 / "
        "lbu 0x7564) that Patch 14 fills from glyph_metrics.adv_table_256() -- the "
        "advance LUT + summed-centering caves must read the shared SoT table, never "
        "recompute (silent desync, project bug #1)"
    )
    assert _LEFTSHIFT_TABLE_REF.search(src), (
        "Patch 19 chargen draw-shift cave does NOT index the resident LEFTSHIFT "
        "table (0x4C7690 / lbu 0x7690) that Patch 14 fills from "
        "glyph_metrics.leftshift_table_256() -- it must read the shared SoT table, "
        "never recompute (silent desync, project bug #1)"
    )

    # And the resident tables those caves index MUST themselves be populated from
    # glyph_metrics by Patch 14 (else the caves would index stale/inline data).
    assert "glyph_metrics.adv_table_256()" in src, (
        "patch_exe.py no longer fills the resident ADV table from "
        "glyph_metrics.adv_table_256() -- Patch 19's caves would index non-SoT data"
    )
    assert "glyph_metrics.leftshift_table_256()" in src, (
        "patch_exe.py no longer fills the resident LEFTSHIFT table from "
        "glyph_metrics.leftshift_table_256() -- Patch 19's draw-shift cave would "
        "index non-SoT data"
    )


TESTS = [
    test_patch_exe_imports_glyph_metrics,
    test_no_inline_advance_table_near_chargen_hook,
    test_patch19_caves_index_shared_sot_tables,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_chargen_cave_imports_metrics")
