#!/usr/bin/env python3
"""
test_r39_quests.py -- TIER 2: R39 quest text injection (BUG-7).

Checks the built build/packdata_resources/0039_type15.raw:
  * G353 (quest description shown in the v83 screenshot) decodes to English
    mentioning the 500G stipend,
  * G388 (client) decodes to 'Mayor' (round-3: 'Mayor' alone read as the city; guide p127 client = the Mayor; round-2 had shortened 'Mayor of Duhan'
    to clear the fixed 'Client' label -- see tests/test_r39_client_cap.py),
  * ALL non-zero slots of the four offset tables (G346/G381/G411/G442)
    resolve to the same (group index, glyph ordinal) as in the pristine
    extracted/packdata_raw/0039_type15.raw -- the table-remap correctness
    invariant,
  * group count unchanged and total size <= 16 sectors (rebuild_packdata
    TOC budget).
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (
    PACKDATA_RES_DIR,
    RAW_DIR,
    SECTOR,
    Skip,
    decode_glyphs,
    main_exit,
    require_file,
)

GLYPH_DATA_START = 632          # R39 FFFF group stream starts here
TABLE_GROUPS = (346, 381, 411, 442)
MAX_SECTORS = 16

_CACHE = {}


def _built_path():
    p = os.path.join(PACKDATA_RES_DIR, "0039_type15.raw")
    if not os.path.isfile(p):
        raise Skip("build/packdata_resources/0039_type15.raw missing (run a build)")
    return p


def _scan_groups(data):
    """Return (groups, starts): FFFF-delimited glyph groups from byte 632."""
    pos = GLYPH_DATA_START
    groups, starts, cur, cs = [], [], [], pos
    n = len(data)
    while pos + 1 < n:
        w = struct.unpack_from(">H", data, pos)[0]
        if w == 0xFFFF:
            groups.append(cur)
            starts.append(cs)
            cur = []
            cs = pos + 2
        else:
            cur.append(w)
        pos += 2
    return groups, starts


def _load(which):
    if which in _CACHE:
        return _CACHE[which]
    if which == "built":
        data = open(_built_path(), "rb").read()
    else:
        data = open(
            require_file(os.path.join(RAW_DIR, "0039_type15.raw"), "pristine"), "rb"
        ).read()
    groups, starts = _scan_groups(data)
    _CACHE[which] = (data, groups, starts)
    return _CACHE[which]


def _table_semantics(groups, starts, t):
    """For each slot of offset table t: None (zero/sentinel) or the
    (group index, glyph ordinal) the offset points at.

    BASE = byte address of the table's FIRST NON-ZERO slot (the renderer's base,
    proven by P5 ground truth -- see tests/test_r39_title_table.py and
    inject_r39_quest.py).  The old `starts[t] + len*2 + 2` after-FFFF anchor was
    the DEBUNKED base that produced the "rt" title fragment; using it here made
    this semantics check compare against a wrong model (stale false-positive).
    """
    fnz = next((i for i, v in enumerate(groups[t]) if v != 0), 0)
    base = starts[t] + fnz * 2  # firstNZ slot byte address == renderer base
    sem = []
    for v in groups[t]:
        if v in (0, 0xFFFE, 0xFFFF):
            sem.append(None)
            continue
        target = base + v
        hit = None
        for gi, gs in enumerate(starts):
            ge = gs + len(groups[gi]) * 2 + 2
            if gs <= target < ge:
                hit = (gi, (target - gs) // 2)
                break
        sem.append(hit)
    return sem


def test_g353_description_english():
    _data, groups, _starts = _load("built")
    assert len(groups) > 353, "only %d groups in built R39" % len(groups)
    text = decode_glyphs([g for g in groups[353] if g < 0xFB00])
    assert "500G" in text, (
        "G353 quest description lost the English 500G stipend text; "
        "decodes to %r" % text[:80]
    )
    # must not contain undecodable (Japanese) glyphs
    assert "[" not in text, "G353 contains non-English glyphs: %r" % text[:80]


def test_g388_client_duhan():
    # ROUND-2 (W1-REQ): G388 was shortened "Mayor of Duhan" -> "Mayor" to stop the
    # count-anchored client value walking LEFT under the fixed "Client" label (the
    # v132 "Ma[Client] Duhan" horizontal collision, almostrequest.p2s).  "Mayor"
    # also matches the castle name used in the quest title/description.  The
    # <=8-cell client-name budget is gated in detail by tests/test_r39_client_cap.py.
    _data, groups, _starts = _load("built")
    assert len(groups) > 388, "only %d groups in built R39" % len(groups)
    text = decode_glyphs(groups[388], linebreak="\n")
    norm = text.replace("\n", " ").strip()
    assert norm == "Mayor", (
        "G388 client name is %r, expected 'Mayor' (round-2 cap that fixes the "
        "'Ma[Client] Duhan' horizontal collision)" % norm
    )


def test_offset_tables_preserve_semantics():
    _bd, bg, bs = _load("built")
    _pd, pg, ps = _load("pristine")
    for t in TABLE_GROUPS:
        assert len(bg[t]) == len(pg[t]), (
            "table G%d slot count changed %d -> %d" % (t, len(pg[t]), len(bg[t]))
        )
        sem_b = _table_semantics(bg, bs, t)
        sem_p = _table_semantics(pg, ps, t)
        bad = [
            (i, p, b)
            for i, (p, b) in enumerate(zip(sem_p, sem_b))
            if p != b
        ]
        assert not bad, (
            "table G%d: %d slot(s) no longer resolve to the pristine "
            "(group, glyph ordinal), first: slot %d %s -> %s"
            % (t, len(bad), bad[0][0], bad[0][1], bad[0][2])
        )


def test_group_count_and_size_budget():
    bd, bg, _bs = _load("built")
    _pd, pg, _ps = _load("pristine")
    assert len(bg) == len(pg), (
        "R39 group count changed %d -> %d" % (len(pg), len(bg))
    )
    sectors = (len(bd) + SECTOR - 1) // SECTOR
    assert sectors <= MAX_SECTORS, (
        "R39 is %d sectors (> %d) -- shorten quest descriptions"
        % (sectors, MAX_SECTORS)
    )


TESTS = [
    test_g353_description_english,
    test_g388_client_duhan,
    test_offset_tables_preserve_semantics,
    test_group_count_and_size_budget,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_r39_quests")
