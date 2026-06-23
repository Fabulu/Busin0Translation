#!/usr/bin/env python3
"""
test_r1193_narration.py -- TIER 1: R1193 intro prologue builder (BUG-10).

Runs tools/patch_r1193_narration.build_r1193 against the pristine extract
into a tempfile directory (never build/patched_type2) and asserts:
  * exactly 23 trailing 0x14 line records, page structure 4/3/2/4/1/3/2/3/1,
  * every line <= 23 glyphs, all glyph ids < 0xFB00 (control-code free),
  * ADVISORY (WARN-only, never fails): each line's glyph_metrics.px_width is
    reported against the interim NARR_BOX_PX ceiling so a future px conversion of
    patch_r1193_narration.py is forced through the shared metrics module,
  * every line decodes to non-empty text; the prologue reads as English,
  * deterministic: two runs produce byte-identical output,
  * sec2_size header field == actual Section 2 length (only zero padding
    after it, sector-aligned file),
  * the output Section 1 still walks cleanly.
"""

import os
import re
import shutil
import struct
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (
    BUILD_V9,
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

# Pixel-width source of truth.  tests/_helpers put TOOLS_DIR on sys.path, so the
# ONE shared metrics module is importable here.  The new advisory px ceiling MUST
# measure widths through glyph_metrics.px_width and NEVER recompute them — that
# silent desync is this project's #1 bug (see tools/glyph_metrics.py docstring).
import glyph_metrics  # noqa: E402

EXPECTED_PAGES = [4, 3, 2, 4, 1, 3, 2, 3, 1]
MAX_LINE_GLYPHS = 23

# Advisory narration-box right-edge in pixels.  SINGLE SOURCE OF TRUTH: read it
# STRAIGHT FROM build_v9's NARRATION_BOX_PX constant (the same value the build's
# narration px-wrap uses) so the prologue advisory can NEVER drift from the build
# (the #1 desync mode).  No import (build_v9.py runs a full ISO build at import
# time -- os.chdir + os.system, no __main__ guard); extract the module-level
# constant from source text instead (same SoT read as test_line_width).
#
# This check NEVER fails (ADVISORY/WARN ONLY): it reports current offenders
# without asserting, so it can never false-fail.  When patch_r1193_narration.py is
# later converted from the fixed 23-glyph count budget to a real px budget, it will
# be forced through glyph_metrics.px_width and this advisory becomes the lock.
# The HARD renderer budget (MAX_LINE_GLYPHS=23, the 23-record / page-structure
# asserts) is a FIXED renderer constraint and is intentionally NOT sourced here.
def _build_v9_narration_box_px():
    src = open(BUILD_V9, encoding="utf-8").read()
    m = re.search(r"^NARRATION_BOX_PX\s*=\s*(\d+)", src, re.M)
    assert m, "build_v9.py: NARRATION_BOX_PX constant not found"
    return int(m.group(1))


NARR_BOX_PX = _build_v9_narration_box_px()

# The narration glyph stream is already a list of ADV-table indices (gid = char-
# 32), so px_width takes an identity enc — same convention as test_line_width.
_ID_ENC = lambda g: g  # noqa: E731

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


def test_px_ceiling_advisory():
    """
    ADVISORY-ONLY px ceiling for the 23 narration line records.

    This check NEVER fails: it measures each of the 23 trailing lines through the
    shared glyph_metrics.px_width SoT and reports those wider than the interim
    NARR_BOX_PX (300px), but does NOT assert on them.  The real narration-box
    right edge is still un-measured (P3/P4 live-gated), so a hard px gate here
    would false-fail on the current count-budgeted text.  Its purpose is to (a)
    surface the current offenders and (b) force any FUTURE px conversion of
    patch_r1193_narration.py through glyph_metrics — never an inline recompute.

    The hard 23-record / <=23-glyph-per-line / page-structure guarantees are
    asserted by the other tests in this module and are intentionally untouched.
    """
    _pristine, out, _o2, _f1, records = _build()
    p, rows = _read_output_records(out, records)
    words = p["words"]
    # px_width over glyph IDs directly (identity enc) — single SoT, no recompute.
    assert len(rows) == 23, "advisory px check expects 23 line records, got %d" % len(rows)
    offenders = []
    for pc, _idx, off, cnt in rows:
        gl = words[off : off + cnt]
        px = glyph_metrics.px_width(gl, _ID_ENC)
        if px > NARR_BOX_PX:
            offenders.append((pc, cnt, px, decode_glyphs(gl).strip()))
    # ADVISORY: report, never fail.  When NARR_BOX_PX is replaced by the
    # GS-measured box edge and the text is px-wrapped, this list should empty out.
    if offenders:
        offenders.sort(key=lambda o: o[2], reverse=True)
        print(
            "  [px-advisory] %d/23 narration lines exceed the interim %dpx box "
            "(WARN-only until the real box right edge is GS-measured):"
            % (len(offenders), NARR_BOX_PX)
        )
        for pc, cnt, px, txt in offenders:
            print("    S1+0x%04X cnt=%2d px=%3d  |%s|" % (pc, cnt, px, txt))
    else:
        print("  [px-advisory] all 23 narration lines within %dpx" % NARR_BOX_PX)


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
    test_px_ceiling_advisory,
    test_deterministic,
    test_header_and_padding,
    test_output_walks_cleanly,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_r1193_narration")
