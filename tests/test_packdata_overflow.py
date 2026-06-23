#!/usr/bin/env python3
"""
test_packdata_overflow.py -- TIER 3: PACKDATA / BSN2_0.DSI overflow integrity.

ISO path: $BUSIN_ISO, default build/BUSIN0_EN_v85.iso (absent by default ->
SKIP). All tests SKIP when no ISO is present. Directory entries are read via the
ISO9660 PVD root directory (iso_root_entries), NEVER a hardcoded LBA.

Why this exists:
  The rebuilt PACKDATA.DIG is larger than the original and overflows past its
  end into BSN2_0.DSI (audio). build_v9.py Step 8.2 self-heals by relocating the
  subsequent files (name-path, not raw-LBA -- real-PS2-safe) and rewriting their
  directory LBAs + the PVD volume size. This test is the post-build guard:

    1. The PACKDATA->next-file shift must stay within the tracked budget
       (PACKDATA_OVERFLOW_BUDGET_SECTORS). A blow-past means PACKDATA grew
       unexpectedly -- investigate before bumping the budget.
    2. BSN2_0.DSI's first sector in the SHIPPED ISO must NOT be PACKDATA content
       -- i.e. Step 8.2 actually relocated the real audio and did not leave
       PACKDATA bytes overwriting it.

  NEVER assert shift == 0: Step 8.2 self-heals an existing overflow, so a healthy
  build legitimately has a positive shift already applied in the directory.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (
    PACKDATA_OVERFLOW_BUDGET_SECTORS,
    ROOT,
    SECTOR,
    Skip,
    default_iso_path,
    iso_root_entries,
    main_exit,
)

# The original (unbuilt) disc. The original PACKDATA->BSN2_0.DSI boundary is the
# FIXED reference the rebuilt PACKDATA grows past; Step 8.2 shifts BSN2_0.DSI
# forward to start exactly at the new PACKDATA end, so the shipped slack is ~0
# by construction. To measure actual growth we compare the shipped PACKDATA end
# against this original boundary.
_ORIG_ISO = os.path.join(
    ROOT, "Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso"
)


def _iso_path():
    iso = default_iso_path()
    if not os.path.isfile(iso):
        raise Skip("ISO not found: %s (set BUSIN_ISO or build a release)" % iso)
    return iso


def _entries():
    """Return (entries, pack(lba,size), bsn(lba,size)) from the shipped ISO."""
    with open(_iso_path(), "rb") as fh:
        entries = iso_root_entries(fh)
    pack = next((v for k, v in entries.items() if "PACKDATA" in k), None)
    bsn = next((v for k, v in entries.items() if "BSN2_0" in k), None)
    if pack is None:
        raise Skip("no PACKDATA.DIG in ISO root directory")
    if bsn is None:
        raise Skip("no BSN2_0.DSI in ISO root directory")
    return entries, pack, bsn


def _computed_shift(entries, pack):
    """Reproduce Step 8.2's overflow math from the SHIPPED directory.

    The directory in a built ISO has ALREADY been relocated by Step 8.2, so the
    overflow we recompute here from the live LBAs is the residual: in a healthy
    build PACKDATA's end no longer collides with the next file (shift == 0),
    because the next file was already pushed forward. The directory-recorded
    relocation magnitude is what we budget-check below via the gap, so we report
    the raw collision here purely as a sanity figure.
    """
    pack_lba, pack_size = pack
    pack_end = pack_lba + math.ceil(pack_size / SECTOR)
    after = sorted(
        lba for k, (lba, _s) in entries.items()
        if lba > pack_lba and "PACKDATA" not in k
    )
    if not after:
        return 0, pack_end, None
    first_after = after[0]
    return max(0, pack_end - first_after), pack_end, first_after


def test_no_residual_overflow_in_shipped_iso():
    """After Step 8.2, the SHIPPED directory must have no PACKDATA->next collision."""
    entries, pack, _bsn = _entries()
    shift, pack_end, first_after = _computed_shift(entries, pack)
    assert shift == 0, (
        "Shipped ISO still has PACKDATA overflowing the next file by %d "
        "sectors (PACKDATA ends at LBA %d, next file at %d) -- Step 8.2 "
        "self-heal did not run or was incomplete; real-PS2 audio at risk"
        % (shift, pack_end, first_after)
    )


def test_packdata_growth_within_budget():
    """How far the rebuilt PACKDATA grew past the ORIGINAL boundary <= budget.

    Step 8.2 pushes BSN2_0.DSI forward to start exactly at the new PACKDATA end,
    so the SHIPPED slack is ~0 and tells us nothing about growth. The actual
    growth = shipped_PACKDATA_end - ORIGINAL_BSN2_0_start (the fixed pre-build
    boundary). That overflow magnitude is what Step 8.2 had to absorb and what
    encroaches toward the audio region; it must stay within the tracked budget.
    SKIPs if the original disc image is not present.
    """
    entries, pack, _bsn = _entries()
    pack_lba, pack_size = pack
    pack_end = pack_lba + math.ceil(pack_size / SECTOR)

    if not os.path.isfile(_ORIG_ISO):
        raise Skip("original disc image not found: %s" % os.path.basename(_ORIG_ISO))
    with open(_ORIG_ISO, "rb") as fh:
        orig_entries = iso_root_entries(fh)
    orig_bsn = next(
        (v for k, v in orig_entries.items() if "BSN2_0" in k), None
    )
    if orig_bsn is None:
        raise Skip("no BSN2_0.DSI in ORIGINAL ISO root directory")
    orig_boundary = orig_bsn[0]  # original BSN2_0.DSI start == original pack end

    growth = pack_end - orig_boundary
    assert growth >= 0, (
        "shipped PACKDATA ends (LBA %d) BEFORE the original BSN2_0.DSI boundary "
        "(LBA %d) -- PACKDATA unexpectedly SHRANK; verify the build"
        % (pack_end, orig_boundary)
    )
    assert growth <= PACKDATA_OVERFLOW_BUDGET_SECTORS, (
        "Rebuilt PACKDATA grew %d sectors past the original BSN2_0.DSI boundary "
        "(> budget %d) -- it is encroaching further into the audio region than "
        "tracked; investigate before bumping PACKDATA_OVERFLOW_BUDGET_SECTORS"
        % (growth, PACKDATA_OVERFLOW_BUDGET_SECTORS)
    )


def test_bsn2_first_sector_not_packdata():
    """BSN2_0.DSI's first sector in the SHIPPED ISO must be audio, not PACKDATA.

    Step 8 wrote PACKDATA over BSN2_0.DSI's ORIGINAL sectors; Step 8.2 then
    relocated BSN2_0.DSI forward, reading from the ORIGINAL ISO. If the
    relocation failed (or read from the clobbered working copy), BSN2_0.DSI's
    first sector would equal PACKDATA's first sector. PACKDATA begins with its
    TOC (well-known structure), so we compare the two first sectors directly.
    """
    entries, pack, bsn = _entries()
    pack_lba, _ps = pack
    bsn_lba, _bs = bsn
    with open(_iso_path(), "rb") as fh:
        fh.seek(pack_lba * SECTOR)
        pack_first = fh.read(SECTOR)
        fh.seek(bsn_lba * SECTOR)
        bsn_first = fh.read(SECTOR)
    assert bsn_first != pack_first, (
        "BSN2_0.DSI first sector (LBA %d) == PACKDATA first sector (LBA %d) -- "
        "Step 8.2 left PACKDATA bytes over the audio instead of relocating the "
        "original BSN2_0.DSI; real-PS2 audio would be corrupted"
        % (bsn_lba, pack_lba)
    )


TESTS = [
    test_no_residual_overflow_in_shipped_iso,
    test_packdata_growth_within_budget,
    test_bsn2_first_sector_not_packdata,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_packdata_overflow")
