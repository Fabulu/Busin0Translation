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

# ── Patch 14 wiring constants (build/patch_exe.py L496-497) ──────────────────
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")
P14_TBL1 = 0x3C75E4   # advance LUT table, 256B   (VA 0x4C7564)
P14_TBL2 = 0x3C7710   # left-shift table, 256B    (VA 0x4C7690)
P14_HOOK1 = 0x209820  # j 0x4C7540 -> word 0x08131D50  (VA 0x3097A0)
P14_HOOK2 = 0x2097D0  # j 0x4C7670 -> word 0x08131D9C  (VA 0x309750)
P14_HOOK1_WORD = 0x08131D50
P14_HOOK2_WORD = 0x08131D9C


def test_g1_built_exe_tables_match_metrics():
    """TIER-2: the built patched EXE's caves are byte-identical to glyph_metrics."""
    if not os.path.isfile(PATCHED_EXE):
        raise Skip(
            "build/SLPM_653.78_patched missing (run build/patch_exe.py first)"
        )
    with open(PATCHED_EXE, "rb") as fh:
        data = fh.read()

    want_adv = glyph_metrics.adv_table_256()
    want_lsh = glyph_metrics.leftshift_table_256()
    got_adv = data[P14_TBL1:P14_TBL1 + 256]
    got_lsh = data[P14_TBL2:P14_TBL2 + 256]
    assert got_adv == want_adv, (
        "patched EXE advance LUT @file 0x%X != glyph_metrics.adv_table_256() "
        "(Patch 14 desynced from the metrics module)" % P14_TBL1
    )
    assert got_lsh == want_lsh, (
        "patched EXE left-shift table @file 0x%X != "
        "glyph_metrics.leftshift_table_256()" % P14_TBL2
    )

    h1 = struct.unpack_from("<I", data, P14_HOOK1)[0]
    h2 = struct.unpack_from("<I", data, P14_HOOK2)[0]
    assert h1 == P14_HOOK1_WORD, (
        "patched EXE hook1 @file 0x%X = 0x%08X, expected j 0x4C7540 (0x%08X) -- "
        "Stage 1 advance-LUT trampoline not installed"
        % (P14_HOOK1, h1, P14_HOOK1_WORD)
    )
    assert h2 == P14_HOOK2_WORD, (
        "patched EXE hook2 @file 0x%X = 0x%08X, expected j 0x4C7670 (0x%08X) -- "
        "Stage 2 draw-shift trampoline not installed"
        % (P14_HOOK2, h2, P14_HOOK2_WORD)
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


TESTS = [
    test_g1_built_exe_tables_match_metrics,
    test_g2_no_inline_width_recompute,
    test_g3_metrics_self_consistent,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_glyph_metrics_sync")
