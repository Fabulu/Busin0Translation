#!/usr/bin/env python3
"""
test_chargen_race_nudge_patch28.py -- lock Patch 28 (chargen race-NAME column
X origin) at STOCK -216, REVERTED in v158.

HISTORY: Patch 28 pulled the race-select NAME column (Human/Gnome/Hobbit/...)
left (-241 in v156, -260 overshoot in v157) to clear the parchment right edge.
v158 root-caused the overflow itself: the name lists flow through renderer
0x3A2EF0 (Patch 27), which applied the R1188 ADV table (avg 17.4px, oblique
24px font) to text drawn from the R2100 upright 16px font ("H u m a n" ~97px).
With the v158 R2100 ADV2 tables (avg 10.4px) "Human" is ~56px and fits at the
stock origin, so the nudge is no longer needed and the three X immediates ship
PRISTINE (-216).  The lever itself stays documented in patch_exe.py (P28_NEW)
in case a fresh capture shows residual clipping.

The lever (traced byte-for-byte, still valid): baseX = sext16(t2)+28, t2=-216
carried by ALL THREE handlers 0x142410 dispatches to:
  VA 0x149788 (file 0x49808), 0x1498A0 (file 0x49920), 0x149E5C (file 0x49EDC).

FIVE earlier candidates were FALSIFIED live and MUST stay pristine:
  * 0x4C0F0  = the "Sex" info-banner pen origin  (word 0x2402FF98)
  * 0x1498A8 (file 0x49928) = the Y-axis sibling (word 0x240BFF98; box moved up)
  * 0x3D02F0 = a marker coord table            (untouched -> == pristine EXE)
  * 0x4D0270 (off-screen markers) / t0=17 (a2)  -- not addressed here

This module pins:
  TIER-1 (static, always): build/patch_exe.py Patch 28 block still references
     P28_SITES + the three file offsets, sets P28_NEW = -216 (stock), gates on
     the pristine word 0x240AFF28 -- and touches NONE of the falsified sites.
  TIER-2 (built EXE, SKIP when build/SLPM_653.78_patched absent): all three X
     sites are PRISTINE -216 (0x240AFF28); the Y sibling + 0x4C0F0 + 0x3D02F0
     stay pristine.  TEETH: fail if any X site was nudged (-241/-260 or other).
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, Skip, require_file, main_exit  # noqa: E402

PATCH_EXE = os.path.join(ROOT, "build", "patch_exe.py")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")
PRISTINE_EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")

# --- Patch 28 constants (byte-for-byte, see build/patch_exe.py) --------------
P28_SITES = (0x49808, 0x49920, 0x49EDC)   # file offs of the 3 race-NAME X handlers
PRISTINE_X = 0x240AFF28                    # addiu t2,zero,-216 (pristine / v158 STOCK)
Y_SIBLING_FO = 0x49928                     # VA 0x1498A8 -- Y axis, must stay pristine
Y_SIBLING_PRISTINE = 0x240BFF98            # addiu t3,zero,-104
SEX_BANNER_FO = 0x4C0F0                    # VA 0x14C070 -- Sex banner, must stay pristine
SEX_BANNER_PRISTINE = 0x2402FF98           # addiu v0,zero,-104
MARKER_TBL_FO = 0x3D02F0                   # marker coord table -- must stay == pristine EXE
MARKER_TBL_LEN = 12                        # 6 x u16 entries


# ── TIER-1: static source invariants (always run) ────────────────────────────
def _block():
    require_file(PATCH_EXE, "Patch 28 gate")
    src = open(PATCH_EXE, encoding="utf-8").read()
    i = src.find("PATCH 28")
    assert i != -1, "build/patch_exe.py has no PATCH 28 block"
    j = src.find("PATCH 30", i)
    return "\n".join(
        ln.split("#", 1)[0] for ln in src[i : j if j != -1 else len(src)].splitlines()
    )


def test_t1_reverted_to_stock():
    """Patch 28 is REVERTED: the block still documents the lever (P28_SITES + the
    pristine gate word) but P28_NEW is stock -216, so nothing is written."""
    code = _block()
    assert "P28_SITES" in code, "Patch 28 must reference P28_SITES"
    for tok in ("0x49808", "0x49920", "0x49EDC"):
        assert tok in code, "Patch 28 code must reference X site %s" % tok
    assert "P28_NEW = -216" in code, (
        "Patch 28 must set P28_NEW = -216 (v158 stock revert; the R2100 ADV2 tables "
        "removed the overflow the nudge compensated for)"
    )
    assert "0x240AFF28" in code, "Patch 28 must gate on the pristine word 0x240AFF28"


def test_t1_no_falsified_sites_in_code():
    """The falsified sites (0x4C0F0 Sex banner, 0x3D02F0 marker table) must NOT be
    written in any non-comment code."""
    code = _block()
    for tok in ("0x4C0F0", "0x3D02F0"):
        assert tok not in code, (
            "Patch 28 executable code must not touch falsified site %s" % tok
        )


# ── TIER-2: built-EXE invariants (SKIP when patched EXE absent) ───────────────
def _load_patched():
    if not os.path.isfile(PATCHED_EXE):
        raise Skip("build/SLPM_653.78_patched missing (run the build)")
    with open(PATCHED_EXE, "rb") as fh:
        return fh.read()


def _u32(data, off):
    return struct.unpack_from("<I", data, off)[0]


def test_t2_x_sites_stock():
    """All THREE race-name X handlers ship PRISTINE -216 (0x240AFF28).  TEETH: any
    nudge (-241/-260/...) is a v158 regression -- the R2100 ADV2 tables removed the
    overflow, and a leftover nudge would push the names off the parchment LEFT edge."""
    data = _load_patched()
    for s in P28_SITES:
        w = _u32(data, s)
        assert w == PRISTINE_X, (
            "X site 0x%X = 0x%08X, expected STOCK -216 (0x%08X) -- Patch 28 must stay "
            "reverted in v158" % (s, w, PRISTINE_X)
        )


def test_t2_y_sibling_pristine():
    """The Y-axis sibling 0x1498A8 (file 0x49928) stays pristine 0x240BFF98."""
    data = _load_patched()
    w = _u32(data, Y_SIBLING_FO)
    assert w == Y_SIBLING_PRISTINE, (
        "Y sibling 0x%X = 0x%08X, expected pristine 0x%08X (must NOT move)"
        % (Y_SIBLING_FO, w, Y_SIBLING_PRISTINE)
    )


def test_t2_sex_banner_pristine():
    """The Sex info-banner origin 0x4C0F0 stays pristine 0x2402FF98 (falsified)."""
    data = _load_patched()
    w = _u32(data, SEX_BANNER_FO)
    assert w == SEX_BANNER_PRISTINE, (
        "Sex banner 0x%X = 0x%08X, expected pristine 0x%08X (falsified site touched!)"
        % (SEX_BANNER_FO, w, SEX_BANNER_PRISTINE)
    )


def test_t2_marker_table_pristine():
    """The marker coord table 0x3D02F0 is byte-identical to the pristine EXE
    (falsified site -- must NOT be touched)."""
    data = _load_patched()
    require_file(PRISTINE_EXE, "marker-table pristine compare")
    with open(PRISTINE_EXE, "rb") as fh:
        pri = fh.read()
    got = data[MARKER_TBL_FO : MARKER_TBL_FO + MARKER_TBL_LEN]
    want = pri[MARKER_TBL_FO : MARKER_TBL_FO + MARKER_TBL_LEN]
    assert got == want, (
        "marker table 0x%X changed vs pristine: got %s want %s (falsified site touched!)"
        % (MARKER_TBL_FO, got.hex(), want.hex())
    )


TESTS = [
    test_t1_reverted_to_stock,
    test_t1_no_falsified_sites_in_code,
    test_t2_x_sites_stock,
    test_t2_y_sibling_pristine,
    test_t2_sex_banner_pristine,
    test_t2_marker_table_pristine,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_chargen_race_nudge_patch28")
