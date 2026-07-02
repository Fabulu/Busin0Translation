#!/usr/bin/env python3
"""
test_r39_section_table.py -- TIER 2: R39 top-level section table (freeze root).

The request-menu softlock root cause is the 15-record section table at R39
bytes 0..240 (LE [group_idx, size, file_offset, 0] x 16 bytes).  The tavern
request chooser (loader fn 0x492700 -> chooser loop 0x313A40) walks these
records; if a record's offset/size points out of bounds or the records the
chooser depends on (recs 0..5, the structural prefix) drift, the menu freezes.

inject_r39_quest.py grows the quest block (rec 6) and re-maps recs 6..14 forward,
keeping recs 0..5 byte-identical to the pristine resource.  This module guards
that invariant -- the ONLY R39 axis that test_r39_quests.py /
test_r39_title_table.py do NOT cover (reconB5 GAP 1):

  * records 0..5 byte-identical to the pristine extracted R39,
  * every record's off + size lands within the file (off + size <= filelen),
  * records 6..14 are non-overlapping and forward-ordered (each off >= the
    previous record's off + size),
  * total file size <= 32768 bytes (16-sector cap).

Mirrors tests/test_r39_quests.py style: loads built
build/packdata_resources/0039_type15.raw and pristine
extracted/packdata_raw/0039_type15.raw, Skips cleanly when inputs are absent.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (
    PACKDATA_RES_DIR,
    RAW_DIR,
    Skip,
    main_exit,
    require_file,
)

SECTION_TABLE_BYTES = 240        # 15 records x 16 bytes (bytes 0..240)
SECTION_REC_SIZE = 16
SECTION_N_RECORDS = 15
# v148: the spell-description block (record 2) is INTENTIONALLY re-encoded with proper-case
# English by tools/patch_r39_spell_desc.py, which grows rec2's size and forward-shifts the
# file offsets of recs 3..14 (the data they point at moves VERBATIM -- the patcher has its own
# PRISTINE-DIFF gate proving the tail is byte-identical at the shifted position).  Only recs
# 0 and 1 are the immutable chooser prefix; the freeze root was an UN-remapped grow, NOT a
# correctly-remapped one.  So the frozen-prefix invariant is recs 0..1, and recs 2..5 are
# checked for a CORRECT spell-desc remap (size grew, offsets forward, content intact via the
# other in-bounds / forward-ordered gates below).
FROZEN_RECORDS = 2               # recs 0..1 must stay byte-identical (chooser prefix)
FROZEN_RECORDS_EXTENDED = 6      # recs 2..5 = the old prefix; now CORRECT-remap-checked
MAX_BYTES = 32768               # 16 sectors

_CACHE = {}


def _built_path():
    p = os.path.join(PACKDATA_RES_DIR, "0039_type15.raw")
    if not os.path.isfile(p):
        raise Skip("build/packdata_resources/0039_type15.raw missing (run a build)")
    return p


def _records(data):
    """Return [(group_idx, size, file_offset, zero), ...] for the 15-record
    section table at bytes 0..240 (LE u32 fields)."""
    if len(data) < SECTION_TABLE_BYTES:
        raise AssertionError(
            "R39 too small for a 240-byte section table (len=%d)" % len(data)
        )
    return [
        struct.unpack_from("<IIII", data, i * SECTION_REC_SIZE)
        for i in range(SECTION_N_RECORDS)
    ]


def _load(which):
    if which in _CACHE:
        return _CACHE[which]
    if which == "built":
        data = open(_built_path(), "rb").read()
    else:
        data = open(
            require_file(os.path.join(RAW_DIR, "0039_type15.raw"), "pristine"), "rb"
        ).read()
    _CACHE[which] = (data, _records(data))
    return _CACHE[which]


def test_frozen_records_byte_identical():
    """Records 0..1 (the immutable chooser prefix) must be byte-identical to pristine --
    a drift here is the documented request-menu freeze root.  Records 2..5 legitimately
    change because the spell-description block (rec2) is re-encoded with proper-case
    English (tools/patch_r39_spell_desc.py) and recs 3..5 are forward-remapped -- that is a
    CORRECT remap (validated by test_records_in_bounds / test_records_forward_non_overlapping
    + the patcher's own PRISTINE-DIFF gate), NOT the freeze (which was an UN-remapped grow)."""
    bd, _br = _load("built")
    pd, _pr = _load("pristine")
    n = FROZEN_RECORDS * SECTION_REC_SIZE
    assert bd[:n] == pd[:n], (
        "R39 section-table records 0..1 differ from pristine -- request-menu "
        "freeze root (chooser prefix corrupted)"
    )
    # Sanity (v161): records 2..5 are ALL legitimately rebuilt now -- rec2 by
    # patch_r39_spell_desc (Step 3.3) and recs 3/4/5 (AA names/descriptions/UI)
    # by patch_r39_aa (Step 3.4). Each may GROW (never shrink), and every
    # record's offset must be forward-shifted by exactly the CUMULATIVE growth
    # of the rebuilt blocks before it -- an un-remapped grow (the documented
    # request-menu-freeze class) still fails.
    bd_recs = _records(bd)
    pd_recs = _records(pd)
    cum_delta = 0
    for i in range(2, FROZEN_RECORDS_EXTENDED):
        assert bd_recs[i][2] == pd_recs[i][2] + cum_delta, (
            "rec%d offset not forward-shifted by the cumulative growth (%d) of "
            "the rebuilt blocks before it -- bad remap (freeze class)" % (i, cum_delta)
        )
        grow = bd_recs[i][1] - pd_recs[i][1]
        assert grow >= 0, "rec%d shrank unexpectedly (%d bytes)" % (i, grow)
        cum_delta += grow


def test_records_in_bounds():
    """Every record's off + size must land within the file."""
    bd, br = _load("built")
    n = len(bd)
    bad = [
        (i, off, size)
        for i, (idx, size, off, z) in enumerate(br)
        if off + size > n
    ]
    assert not bad, (
        "R39 section-table records reach past end of file (len=%d): %s"
        % (n, bad[:3])
    )


def test_records_forward_non_overlapping():
    """Records 6..14 must be forward-ordered and non-overlapping (each off >=
    previous off + size)."""
    _bd, br = _load("built")
    prev_end = None
    bad = []
    for i in range(6, SECTION_N_RECORDS):
        idx, size, off, z = br[i]
        if prev_end is not None and off < prev_end:
            bad.append((i, off, prev_end))
        prev_end = off + size
    assert not bad, (
        "R39 section-table records 6..14 overlap / not forward-ordered "
        "(rec, off, prev_end): %s" % bad[:3]
    )


def test_total_size_budget():
    """Total file size must stay within the 16-sector cap (32768 bytes)."""
    bd, _br = _load("built")
    assert len(bd) <= MAX_BYTES, (
        "R39 is %d bytes (> %d, the 16-sector cap) -- shorten quest text"
        % (len(bd), MAX_BYTES)
    )


TESTS = [
    test_frozen_records_byte_identical,
    test_records_in_bounds,
    test_records_forward_non_overlapping,
    test_total_size_budget,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_r39_section_table")
