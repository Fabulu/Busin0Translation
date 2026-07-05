#!/usr/bin/env python3
"""
test_r2138_containment.py -- prove the BUILT R2138 stat/menu font atlas differs
from pristine ONLY inside the pixel windows tools/patch_r2138.py declares.

R2138 (type-29, ~1.5 MB) is the label-font atlas: 7 self-contained PSMT4
sub-textures are re-inked with English (sub0 town menu, sub4 "Class Reqs"
class-change header, sub6 guild roster, sub7 chargen stats/tabs, sub25 level-up,
sub26 shop/alchemy, sub27 purchase/curse). Each sub's writable window is exactly
[offset+pixel_off, offset+pixel_off+pixel_size) -- the 0x900/0x500/... transfer
header (TBP/TBW/PSM/CLUT/TRXREG GIF tag) that precedes each block, and the whole
resource header, MUST stay byte-identical or the GS upload geometry changes and
the VIF FIFO can overflow.

The window geometry is MIRRORED FROM THE PATCHER by importing its SUB_DEFS (no
hand-derived offsets) -- if patch_r2138.py moves a window, this test moves with
it. sub4's change_box / protect_cols are likewise read from its own SUB_DEF and
verified in DESWIZZLED pixel space (the once-crashy header is the strict-guarded
one, so it gets the strong containment check).

Gates:
  * test_only_pixel_windows_differ -- every byte diff vs pristine falls inside a
    declared pixel window; zero diffs anywhere else (headers + transfer tags
    pristine). This is patch_r2138.py's own build-time integrity assert, re-run
    against the SHIPPED file.
  * test_sub_transfer_headers_pristine -- the per-sub header gap [offset,
    offset+pixel_off) is byte-identical to pristine for all 7 subs (the GS
    upload descriptor is untouched).
  * test_every_sub_actually_patched -- each declared window carries real diffs
    (a WARN-skipped sub would ship JP; sub4 in particular must have LANDED).
  * test_sub4_change_box_contained -- sub4's deswizzled edits all sit inside its
    declared change_box and none touch its protect_cols (the digit strip / the
    already-English cursive labels). Uses the patcher's own psmt4 deswizzle.

TIER-2: SKIPs cleanly when the built/pristine resource (or Pillow/psmt4) is
absent.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import PACKDATA_RES_DIR, RAW_DIR, ROOT, Skip, main_exit, require_file

TOOLS_DIR = os.path.join(ROOT, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

BUILT = os.path.join(PACKDATA_RES_DIR, "2138_type29.raw")
PRISTINE = os.path.join(RAW_DIR, "2138_type29.raw")


def _patcher():
    """Import tools/patch_r2138.py (single source of the window geometry).
    Skip if its deps (Pillow / psmt4_deswizzle) are unavailable -- import
    executes only module-level defs, never main()."""
    try:
        import patch_r2138  # noqa: F401
    except SystemExit as e:  # patch_r2138 sys.exit()s if Pillow is missing
        raise Skip("patch_r2138 import aborted (%s) -- Pillow unavailable" % e)
    except ImportError as e:
        raise Skip("patch_r2138 import failed (%s)" % e)
    return patch_r2138


def _blobs():
    if not os.path.isfile(BUILT):
        raise Skip("build/packdata_resources/2138_type29.raw missing (run a build)")
    require_file(PRISTINE, "pristine R2138")
    return open(BUILT, "rb").read(), open(PRISTINE, "rb").read()


def _windows(P):
    """[(abs_start, abs_end, sub_index)] straight from the patcher's SUB_DEFS."""
    wins = []
    for s in P.SUB_DEFS:
        a = s["offset"] + s["pixel_off"]
        wins.append((a, a + s["pixel_size"], s["sub_index"]))
    return wins


def _sub_def(P, sub_index):
    for s in P.SUB_DEFS:
        if s["sub_index"] == sub_index:
            return s
    raise AssertionError("patch_r2138 SUB_DEFS has no sub_index %d" % sub_index)


# ===========================================================================
# Size sanity (mirror the patcher's own EXPECTED_SIZE).
# ===========================================================================
def test_size_matches_expected():
    P = _patcher()
    built, pris = _blobs()
    assert len(built) == P.EXPECTED_SIZE, (
        "built R2138 is %d bytes, patch_r2138.EXPECTED_SIZE = %d"
        % (len(built), P.EXPECTED_SIZE)
    )
    assert len(pris) == P.EXPECTED_SIZE, (
        "pristine R2138 is %d bytes, patch_r2138.EXPECTED_SIZE = %d -- wrong "
        "extract?" % (len(pris), P.EXPECTED_SIZE)
    )


# ===========================================================================
# CONTAINMENT: every diff is inside a declared pixel window; nothing else moved.
# ===========================================================================
def test_only_pixel_windows_differ():
    P = _patcher()
    built, pris = _blobs()
    assert len(built) == len(pris), "R2138 length changed"
    wins = _windows(P)

    def in_any(i):
        return any(a <= i < e for a, e, _ in wins)

    stray = []
    for i in range(len(built)):
        if built[i] != pris[i] and not in_any(i):
            stray.append(i)
            if len(stray) > 8:
                break
    assert not stray, (
        "%d+ byte diff(s) OUTSIDE the declared R2138 pixel windows (first at "
        "0x%06X). A diff outside a sub's [offset+pixel_off, +pixel_size) window "
        "means a transfer header / GIF tag / resource header was clobbered -- "
        "that changes the GS upload geometry and can crash the VIF FIFO. Windows"
        " (from patch_r2138.SUB_DEFS): %s"
        % (len(stray), stray[0],
           [(hex(a), hex(e), si) for a, e, si in wins])
    )


# ===========================================================================
# Per-sub transfer headers (the gap before pixel data) stay pristine.
# ===========================================================================
def test_sub_transfer_headers_pristine():
    P = _patcher()
    built, pris = _blobs()
    bad = []
    for s in P.SUB_DEFS:
        hs, he = s["offset"], s["offset"] + s["pixel_off"]
        if built[hs:he] != pris[hs:he]:
            bad.append((s["sub_index"], hex(hs), hex(he)))
    assert not bad, (
        "R2138 per-sub transfer header(s) differ from pristine: %s. The "
        "0x900/0x500/... GIF/transfer descriptor (TBP/TBW/PSM/CLUT/TRXREG) must "
        "stay byte-identical so the GS upload geometry matches pristine." % bad
    )


# ===========================================================================
# Every declared sub actually got patched (no silent WARN-skip); sub4 landed.
# ===========================================================================
def test_every_sub_actually_patched():
    P = _patcher()
    built, pris = _blobs()
    unpatched = []
    for a, e, si in _windows(P):
        if built[a:e] == pris[a:e]:
            unpatched.append(si)
    assert not unpatched, (
        "R2138 sub(s) %s are byte-identical to pristine inside their pixel "
        "window -- patch_sub WARN-skipped them and JP text is shipping. sub4 "
        "(the RE-ENABLED 'Class Reqs' header) must be among the patched subs."
        % unpatched
    )


# ===========================================================================
# sub4 change-box containment, verified in DESWIZZLED pixel space.
# ===========================================================================
def test_sub4_change_box_contained():
    P = _patcher()
    built, pris = _blobs()
    try:
        from psmt4_deswizzle import deswizzle_psmt4
    except Exception as e:  # pragma: no cover
        raise Skip("psmt4_deswizzle unavailable (%s)" % e)

    s = _sub_def(P, 4)
    change_box = s.get("change_box")
    assert change_box is not None, (
        "sub4 SUB_DEF lost its change_box -- the strict in-place re-ink guard "
        "is gone; refusing to pass a sub4 containment test without it"
    )
    a = s["offset"] + s["pixel_off"]
    sz = s["pixel_size"]
    tw, th = s["tex_w"], s["tex_h"]
    bw, dbw = s["bw_psmt4"], s["dbw_ct32"]
    lin_b = deswizzle_psmt4(built[a:a + sz], tw, th, bw_psmt4=bw, dbw_ct32=dbw)
    lin_p = deswizzle_psmt4(pris[a:a + sz], tw, th, bw_psmt4=bw, dbw_ct32=dbw)
    assert len(lin_b) == len(lin_p) == tw * th, "sub4 deswizzle size mismatch"

    cx0, cy0, cx1, cy1 = change_box
    protect = s.get("protect_cols", [])
    changed = outside = in_protected = 0
    for i in range(len(lin_b)):
        if lin_b[i] == lin_p[i]:
            continue
        changed += 1
        px, py = i % tw, i // tw
        if not (cx0 <= px <= cx1 and cy0 <= py <= cy1):
            outside += 1
        for plo, phi in protect:
            if plo <= px <= phi:
                in_protected += 1
                break
    assert changed > 0, (
        "sub4 has NO deswizzled pixel diffs -- the 'Class Reqs' re-ink did not "
        "land (WARN-skipped?). sub4 is RE-ENABLED and must ship English."
    )
    assert outside == 0 and in_protected == 0, (
        "sub4 change-box guard VIOLATED: %d changed pixels (of %d) fall outside "
        "change_box %s and %d land in protect_cols %s. A mis-placed rect or "
        "wrong deswizzle width would scatter edits into the digit strip / the "
        "already-English cursive labels -> garbled status screen."
        % (outside, changed, change_box, in_protected, protect)
    )


TESTS = [
    test_size_matches_expected,
    test_only_pixel_windows_differ,
    test_sub_transfer_headers_pristine,
    test_every_sub_actually_patched,
    test_sub4_change_box_contained,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_r2138_containment")
