#!/usr/bin/env python3
"""
test_r1193_narration.py -- TIER 1: R1193 intro prologue builder (BUG-10).

Runs tools/patch_r1193_narration.build_r1193 against the pristine extract
into a tempfile directory (never build/patched_type2) and asserts:
  * exactly 23 trailing 0x14 line records, page structure 4/3/2/4/1/3/2/3/1,
  * every line <= 23 glyphs, all glyph ids < 0xFB00 (control-code free),
  * every line decodes to non-empty text; the prologue reads as English,
  * deterministic: two runs produce byte-identical output,
  * sec2_size header field == actual Section 2 length (only zero padding
    after it, sector-aligned file),
  * the output Section 1 still walks cleanly.
"""

import os
import shutil
import struct
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (
    DATA_DIR,
    HEADER_SIZE,
    RAW_DIR,
    SECTOR,
    Skip,
    decode_glyphs,
    get_disasm,
    main_exit,
    parse_type02,
    require_file,
)

EXPECTED_PAGES = [4, 3, 2, 4, 1, 3, 2, 3, 1]
MAX_LINE_GLYPHS = 23

_BUILT = None  # cache: (pristine_bytes, output_bytes, records)


def _module():
    get_disasm()
    require_file(os.path.join(RAW_DIR, "1193_type02.raw"), "pristine extract")
    require_file(
        os.path.join(DATA_DIR, "type2_translated", "batch_intro_narration.json"),
        "intro translation",
    )
    try:
        import patch_r1193_narration as m
    except ImportError as e:
        raise Skip("tools/patch_r1193_narration.py not importable: %s" % e)
    return m


def _build():
    """Build twice into temp dirs; cache (pristine, output, pristine_records)."""
    global _BUILT
    if _BUILT is not None:
        return _BUILT
    m = _module()
    raw_path = os.path.join(RAW_DIR, "1193_type02.raw")
    pristine = open(raw_path, "rb").read()
    translations = m._load_translations()
    assert m.TRAILING_MSG_INDEX in translations, (
        "batch_intro_narration.json lost the msg_index-%d trailing prologue "
        "entry" % m.TRAILING_MSG_INDEX
    )
    tmp1 = tempfile.mkdtemp(prefix="busin_test_r1193a_")
    tmp2 = tempfile.mkdtemp(prefix="busin_test_r1193b_")
    try:
        out1 = m.build_r1193(raw_path, translations, tmp1)
        out2 = m.build_r1193(raw_path, translations, tmp2)
        file1 = open(os.path.join(tmp1, "1193_type02.raw"), "rb").read()
    finally:
        shutil.rmtree(tmp1, ignore_errors=True)
        shutil.rmtree(tmp2, ignore_errors=True)
    records, _ts, _nw = m.find_trailing_records(pristine)
    _BUILT = (pristine, out1, out2, file1, records)
    return _BUILT


def _read_output_records(out, records):
    """Read back the (off, cnt) each trailing 0x14 record carries in the output."""
    p = parse_type02(out)
    sec1 = p["sec1"]
    rows = []
    for pc, idx, _ooff, _ocnt in records:
        off = struct.unpack_from(">I", sec1, pc + 6)[0]
        cnt = struct.unpack_from(">I", sec1, pc + 10)[0]
        rows.append((pc, idx, off, cnt))
    return p, rows


def test_exactly_23_records_with_page_structure():
    pristine, out, _o2, _f1, records = _build()
    assert len(records) == 23, "expected 23 trailing 0x14 records, found %d" % len(records)
    # page structure from LINE_IDX resets (new page when idx <= previous idx)
    pages, run, prev = [], 0, None
    for _pc, idx, _off, _cnt in records:
        if prev is not None and idx <= prev:
            pages.append(run)
            run = 0
        run += 1
        prev = idx
    pages.append(run)
    assert pages == EXPECTED_PAGES, (
        "page structure %s != expected %s" % (pages, EXPECTED_PAGES)
    )
    # records must tile the new trailing region exactly, in order
    p, rows = _read_output_records(out, records)
    rows_sorted = sorted(rows, key=lambda r: r[2])
    pos = p["trailing_start"]
    for pc, _idx, off, cnt in rows_sorted:
        assert off == pos, (
            "record S1+0x%X: off=%d does not tile (expected %d)" % (pc, off, pos)
        )
        pos += cnt
    assert pos == len(p["words"]), (
        "trailing lines do not tile to the end of Section 2 (%d != %d)"
        % (pos, len(p["words"]))
    )


def test_line_constraints_and_decode():
    _pristine, out, _o2, _f1, records = _build()
    p, rows = _read_output_records(out, records)
    words = p["words"]
    joined = []
    for pc, _idx, off, cnt in rows:
        assert cnt >= 1, "record S1+0x%X has cnt=%d (< 1)" % (pc, cnt)
        assert cnt <= MAX_LINE_GLYPHS, (
            "record S1+0x%X line is %d glyphs (> %d, would clip)"
            % (pc, cnt, MAX_LINE_GLYPHS)
        )
        gl = words[off : off + cnt]
        assert all(g < 0xFB00 for g in gl), (
            "record S1+0x%X: control code in line glyphs" % pc
        )
        text = decode_glyphs(gl)
        assert len(text) > 0, "record S1+0x%X decodes to empty text" % pc
        assert "[" not in text, (
            "record S1+0x%X: non-English glyph in line: %r" % (pc, text)
        )
        joined.append(text)
    prologue = " ".join(joined)
    assert "Duhan" in prologue, (
        "prologue no longer mentions Duhan -- wrong text shipped? %r"
        % prologue[:120]
    )
    # the bulk of the 23 lines must carry real text (surplus pads are spaces)
    real = sum(1 for t in joined if t.strip())
    assert real >= 18, "only %d/23 lines carry text" % real


def test_deterministic():
    _pristine, out1, out2, file1, _records = _build()
    assert out1 == out2, "two build_r1193 runs differ -- builder is not deterministic"
    assert file1 == out1, "bytes written to disk differ from returned bytes"


def test_header_and_padding():
    _pristine, out, _o2, _f1, _records = _build()
    sec2_size = struct.unpack_from("<I", out, 0x14)[0]
    sec2_off = struct.unpack_from("<I", out, 0x18)[0]
    assert len(out) % SECTOR == 0, "output not sector-padded (%d bytes)" % len(out)
    assert sec2_off + sec2_size <= len(out), "sec2_size overruns the file"
    tail = out[sec2_off + sec2_size :]
    assert not any(tail), (
        "non-zero bytes after Section 2 -- sec2_size at header 0x14 does not "
        "match the actual Section 2 length"
    )


def test_output_walks_cleanly():
    pristine, out, _o2, _f1, _records = _build()
    sd = get_disasm()
    p = parse_type02(out)
    ok, instrs = sd.walk(p["sec1"])
    assert ok, "output Section 1 walk FAILED"
    # FFFF group count must equal pristine (group structure preserved)
    pp = parse_type02(pristine)
    n_p = sum(1 for w in pp["words"] if w == 0xFFFF)
    n_o = sum(1 for w in p["words"] if w == 0xFFFF)
    assert n_p == n_o, "FFFF group count changed %d -> %d" % (n_p, n_o)


TESTS = [
    test_exactly_23_records_with_page_structure,
    test_line_constraints_and_decode,
    test_deterministic,
    test_header_and_padding,
    test_output_walks_cleanly,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_r1193_narration")
