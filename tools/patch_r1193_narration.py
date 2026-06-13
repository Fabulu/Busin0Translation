#!/usr/bin/env python3
"""
patch_r1193_narration.py -- R1193 intro narration: English trailing block (BUG-10)
===================================================================================

R1193 (type-02) carries the game's intro prologue.  Its Section 2 has TWO
narration line sets, both drawn line-by-line by Section-1 0x14 records
(14 bytes BE: u16 0x0014, u16 LINE_IDX, s16 0xFFFF, u32 WORD_OFF absolute
Section-2 word index, u32 GLYPH_CNT):

  * Group 0, words 0..98     -- 10 records, a SHORT prologue variant.  These
    are "name islands" handled by inject_and_patch (kept verbatim, offsets
    remapped).  Translating them is out of scope here.
  * TRAILING block, pristine words 117..350 (234 words after the last FFFF
    group terminator) -- 23 records in pages of 4/3/2/4/1/3/2/3/1 lines.
    This is the full boot prologue (BUG-10) and is rebuilt in English here.

Pipeline (build_r1193):
  1. FFFF-group injection via patch_section1_offsets.inject_and_patch
     (preserves the group-0 narration islands, preserves the trailing block,
     runs patch_section1 internally -- the trailing 0x14s get a generic
     delta shift there).
  2. Rebuild the trailing block as 23 control-code-free English lines
     (<= 23 glyphs each; 24px pitch from x~64 in a 640px frame), preserving
     the page structure.  Section 2 grows freely; sec2_size at header 0x14
     is recomputed.
  3. Rewrite each of the 23 0x14 records (located by pattern scan of the
     PRISTINE Section 1, cross-checked against the sec1_disasm walk) with
     the EXACT new WORD_OFF / GLYPH_CNT of its line, overriding the generic
     delta remap from step 1.  Section 1 never moves, so the record byte
     positions are stable.

The narration renderer was proven (GS dump 20260612061701) to render English
glyph ids 0-94 directly (cell index == english_glyph_table slot), so no font
work is needed.

Usage:
    python tools/patch_r1193_narration.py            # standalone build + verify
    from patch_r1193_narration import build_r1193
"""

import json
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from patch_section1_offsets import inject_and_patch
from sec1_disasm import walk, extract_records

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECTOR = 2048
HEADER_SIZE = 0x20
MAX_LINE_GLYPHS = 23           # 24px pitch from x~64 in a 640px frame
PAGE_LINES = [4, 3, 2, 4, 1, 3, 2, 3, 1]   # original page structure, 23 lines
N_TRAILING_RECORDS = sum(PAGE_LINES)        # 23
TRAILING_MSG_INDEX = 99        # batch_intro_narration.json marker for the block

# ---------------------------------------------------------------------------
# Trailing prologue text.
#
# Condensed from data/type2_translated/batch_intro_narration.json
# (resource 1193, msg_index 99).  The batch English flows to 35 display
# lines / 622 glyphs, but the renderer has a FIXED budget: 23 line records
# of <= 23 glyphs each (529 max), in pages of 4/3/2/4/1/3/2/3/1.  The text
# below is the same prologue condensed to fit that budget; one entry per
# page, greedily word-wrapped into the page's line budget at build time.
# ---------------------------------------------------------------------------
TRAILING_PAGES = [
    "For thirty long years, a war plunged the Kingdom of Duhan"
    " into blood and terror.",                                          # 4 lines
    "The devastating war that cut the kingdom's people to two-thirds",  # 3
    "would be remembered as the Battle of Banquo.",                     # 2
    "Possessed by a death spirit, the San-Goth king led his beastmen"
    " forth to attack, and",                                            # 4
    "war engulfed all Venoa.",                                          # 1
    "Without one hero, Duhan would have vanished from the earth"
    " forever.",                                                        # 3
    "He was Ortrud, later known as the Holy King.",                     # 2
    "He defeated San-Goth and restored peace and prosperity to Duhan.", # 3
    "Twenty years passed...",                                           # 1
]

# -- lazily-loaded english glyph table ---------------------------------------
_ENG_TABLE = None


def _load_eng_table():
    global _ENG_TABLE
    if _ENG_TABLE is None:
        _ENG_TABLE = json.load(
            open(os.path.join(_ROOT, "data", "english_glyph_table.json"),
                 encoding="utf-8")
        )
    return _ENG_TABLE


def _enc_char(ch):
    """English char -> glyph index (same fallback rule as the build pipeline)."""
    t = _load_eng_table()
    if ch in t:
        return t[ch]
    if ch.lower() in t:
        return t[ch.lower()]
    return 31


def encode_group_text(en_text):
    """
    Encode a ' / '-separated dialogue translation exactly like build_v9 Step 4/5:
    ' / ' -> 0xFFFE line break, with 0xFFD2 (page break) every 3rd break.
    """
    glyphs = []
    line_count = 0
    for pi, part in enumerate(en_text.split(" / ")):
        if pi > 0:
            line_count += 1
            if line_count >= 3:
                glyphs.append(0xFFD2)
                line_count = 0
            else:
                glyphs.append(0xFFFE)
        for ch in part:
            glyphs.append(_enc_char(ch))
    return glyphs


# ---------------------------------------------------------------------------
# Line segmentation
# ---------------------------------------------------------------------------
def _flow_page(text, n_lines, max_len=MAX_LINE_GLYPHS):
    """
    Greedy word-wrap one page's text into at most n_lines lines of <= max_len
    glyphs.  Surplus records get a single space (glyph id 0, cnt 1) -- never
    cnt 0.  Raises if the text overflows the page budget.
    """
    lines = []
    cur = ""
    for w in text.split():
        if len(w) > max_len:
            raise ValueError("word %r longer than %d glyphs" % (w, max_len))
        cand = w if not cur else cur + " " + w
        if len(cand) <= max_len:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > n_lines:
        raise ValueError(
            "page %r needs %d lines, budget is %d" % (text, len(lines), n_lines)
        )
    while len(lines) < n_lines:
        lines.append(" ")  # surplus record: single space glyph (id 0, cnt 1)
    return lines


def build_trailing_lines():
    """Return the 23 prologue lines (page structure 4/3/2/4/1/3/2/3/1)."""
    assert len(TRAILING_PAGES) == len(PAGE_LINES)
    lines = []
    for text, n in zip(TRAILING_PAGES, PAGE_LINES):
        lines.extend(_flow_page(text, n))
    assert len(lines) == N_TRAILING_RECORDS
    for ln in lines:
        assert 1 <= len(ln) <= MAX_LINE_GLYPHS, repr(ln)
    return lines


# ---------------------------------------------------------------------------
# 0x14 record location (pristine Section 1)
# ---------------------------------------------------------------------------
def find_trailing_records(orig_data):
    """
    Locate the trailing-block 0x14 records in the PRISTINE resource.

    Scans Section 1 (file bytes 0x20..sec2_offset) at every byte offset for
    the 14-byte BE pattern  0014 idx FFFF 0000 OFF 0000 CNT  filtered to
    records whose OFF/CNT fall within the original trailing region, and
    cross-checks the result against the sec1_disasm BFS walk.

    Returns (records, trailing_start, n_words):
      records -- [(pc, line_idx, off, cnt)] sorted by off (== pc order),
                 asserted to be exactly 23 records tiling the trailing region.
    """
    sec2_size = struct.unpack_from("<I", orig_data, 0x14)[0]
    sec2_off = struct.unpack_from("<I", orig_data, 0x18)[0]
    n_words = sec2_size // 2
    words = struct.unpack_from(">%dH" % n_words, orig_data, sec2_off)
    trailing_start = 0
    for i, w in enumerate(words):
        if w == 0xFFFF:
            trailing_start = i + 1

    sec1 = orig_data[HEADER_SIZE:sec2_off]

    def in_trailing(off, cnt):
        return off >= trailing_start and cnt > 0 and off + cnt <= n_words

    # (1) byte-wise pattern scan
    scanned = []
    for pc in range(0, len(sec1) - 13):
        if struct.unpack_from(">H", sec1, pc)[0] != 0x0014:
            continue
        if struct.unpack_from(">H", sec1, pc + 4)[0] != 0xFFFF:
            continue
        off = struct.unpack_from(">I", sec1, pc + 6)[0]
        cnt = struct.unpack_from(">I", sec1, pc + 10)[0]
        if in_trailing(off, cnt):
            scanned.append((pc, struct.unpack_from(">H", sec1, pc + 2)[0], off, cnt))

    # (2) disassembler walk cross-check
    ok, instrs = walk(sec1)
    if not ok:
        raise ValueError("R1193: pristine Section 1 walk failed")
    recs = extract_records(sec1, instrs)
    walked = [
        (r["pc"], r["param"], r["off"], r["cnt"])
        for r in recs["label"]
        if in_trailing(r["off"], r["cnt"])
    ]

    if sorted(scanned) != sorted(walked):
        raise ValueError(
            "R1193: pattern scan (%d) and disasm walk (%d) disagree on the "
            "trailing 0x14 records" % (len(scanned), len(walked))
        )
    if len(scanned) != N_TRAILING_RECORDS:
        raise ValueError(
            "R1193: expected exactly %d trailing 0x14 records, found %d"
            % (N_TRAILING_RECORDS, len(scanned))
        )

    records = sorted(scanned, key=lambda r: r[2])  # by WORD_OFF == line order
    # The records must tile the trailing region exactly, one line each.
    pos = trailing_start
    for _pc, _idx, off, cnt in records:
        if off != pos:
            raise ValueError(
                "R1193: trailing 0x14 records do not tile (expected off=%d, "
                "got %d)" % (pos, off)
            )
        pos += cnt
    if pos != n_words:
        raise ValueError("R1193: trailing tiling ends at %d != %d" % (pos, n_words))

    # Verify the page structure from LINE_IDX resets (new page when idx <= prev).
    pages = []
    run = 0
    prev = None
    for _pc, idx, _off, _cnt in records:
        if prev is not None and idx <= prev:
            pages.append(run)
            run = 0
        run += 1
        prev = idx
    pages.append(run)
    if pages != PAGE_LINES:
        raise ValueError(
            "R1193: trailing page structure %r != expected %r" % (pages, PAGE_LINES)
        )

    return records, trailing_start, n_words


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------
def build_r1193(raw_path, translations, out_dir="build/patched_type2"):
    """
    Build the fully patched R1193 resource.

    raw_path:     pristine extracted/packdata_raw/1193_type02.raw
    translations: {msg_index: english_text} for resource 1193 (as loaded by
                  build_v9 from data/type2_translated/batch_*.json).  The
                  msg_index-99 entry marks the trailing prologue; FFFF-group
                  entries (msg_index < group count) are injected normally.

    Writes <out_dir>/1193_type02.raw (sector-padded) and returns its bytes.
    """
    orig_data = open(raw_path, "rb").read()

    if TRAILING_MSG_INDEX not in translations:
        raise ValueError(
            "R1193: no msg_index %d (trailing prologue) entry in translations "
            "-- refusing to ship a half-translated intro" % TRAILING_MSG_INDEX
        )

    # --- locate the 23 trailing line records in the PRISTINE Section 1 ------
    records, _old_trailing_start, _old_n_words = find_trailing_records(orig_data)

    # --- step 1: FFFF-group injection (name islands + trailing preserved,
    #     patch_section1 runs inside) ---------------------------------------
    group_trans = {
        mi: encode_group_text(en)
        for mi, en in translations.items()
        if mi != TRAILING_MSG_INDEX
    }
    raw_dir = os.path.dirname(raw_path) or "."
    out_name, status = inject_and_patch(1193, group_trans, raw_dir, out_dir)
    if out_name is None:
        raise RuntimeError("R1193: inject_and_patch failed: %s" % status)
    print("  R1193 group injection: %s" % status)

    out_path = os.path.join(out_dir, out_name)
    patched = open(out_path, "rb").read()

    # --- step 2: rebuild the trailing block as 23 English lines -------------
    sec2_off = struct.unpack_from("<I", patched, 0x18)[0]
    sec2_size = struct.unpack_from("<I", patched, 0x14)[0]
    n_words = sec2_size // 2
    words = list(struct.unpack_from(">%dH" % n_words, patched, sec2_off))
    new_trailing_start = 0
    for i, w in enumerate(words):
        if w == 0xFFFF:
            new_trailing_start = i + 1
    n_old_trailing = n_words - new_trailing_start
    if n_old_trailing != _old_n_words - _old_trailing_start:
        raise ValueError(
            "R1193: injected file trailing block is %d words, expected %d "
            "(inject_and_patch must preserve it)"
            % (n_old_trailing, _old_n_words - _old_trailing_start)
        )

    lines = build_trailing_lines()
    line_glyphs = [[_enc_char(c) for c in ln] for ln in lines]
    for ln, gl in zip(lines, line_glyphs):
        if any(g >= 0xFB00 for g in gl):
            raise ValueError("R1193: control code in line %r" % ln)
        if 0xFFFF in gl:
            raise ValueError("R1193: FFFF glyph in line %r" % ln)

    new_words = words[:new_trailing_start]
    line_offsets = []
    for gl in line_glyphs:
        line_offsets.append(len(new_words))
        new_words.extend(gl)

    new_sec2 = struct.pack(">%dH" % len(new_words), *new_words)

    # --- step 3: exact per-line 0x14 rewrite (overrides the delta remap) ----
    sec1 = bytearray(patched[HEADER_SIZE:sec2_off])
    for (pc, _idx, _off, _cnt), new_off, gl in zip(records, line_offsets, line_glyphs):
        struct.pack_into(">I", sec1, pc + 6, new_off)
        struct.pack_into(">I", sec1, pc + 10, len(gl))

    header = bytearray(patched[:HEADER_SIZE])
    struct.pack_into("<I", header, 0x14, len(new_sec2))

    result = bytes(header) + bytes(sec1) + new_sec2
    pad = (SECTOR - len(result) % SECTOR) % SECTOR
    result += b"\x00" * pad

    open(out_path, "wb").write(result)
    print(
        "  R1193 trailing block: %d -> %d words (%d lines, pages %s), "
        "sec2 %d bytes, file %d bytes"
        % (
            n_old_trailing,
            len(new_words) - new_trailing_start,
            len(lines),
            "/".join(map(str, PAGE_LINES)),
            len(new_sec2),
            len(result),
        )
    )
    return result


# ---------------------------------------------------------------------------
# Standalone build + self-verification
# ---------------------------------------------------------------------------
def _load_translations():
    """Load the resource-1193 translations from batch_intro_narration.json."""
    path = os.path.join(_ROOT, "data", "type2_translated",
                        "batch_intro_narration.json")
    trans = {}
    for e in json.load(open(path, encoding="utf-8")):
        if e.get("resource") != 1193:
            continue
        en = e.get("english", "")
        if en and not any(ord(c) > 127 for c in en):
            trans[e["msg_index"]] = en
    return trans


def verify(raw_path, out_path):
    """Self-verification of the built file.  Returns True when all checks pass."""
    orig = open(raw_path, "rb").read()
    out = open(out_path, "rb").read()
    table = _load_eng_table()
    rev = {}
    for ch, g in table.items():
        rev.setdefault(g, ch)

    failures = []

    records, _ts, _nw = find_trailing_records(orig)

    sec2_off = struct.unpack_from("<I", out, 0x18)[0]
    sec2_size = struct.unpack_from("<I", out, 0x14)[0]
    n_words = sec2_size // 2
    words = struct.unpack_from(">%dH" % n_words, out, sec2_off)
    trailing_start = 0
    for i, w in enumerate(words):
        if w == 0xFFFF:
            trailing_start = i + 1
    sec1 = out[HEADER_SIZE:sec2_off]

    # (a) the 23 records: read back, decode, print
    print("Decoded trailing lines (23 records):")
    pos = trailing_start
    li = 0
    page_no = 1
    page_left = PAGE_LINES[0]
    for pc, idx, _ooff, _ocnt in records:
        off = struct.unpack_from(">I", sec1, pc + 6)[0]
        cnt = struct.unpack_from(">I", sec1, pc + 10)[0]
        gl = words[off : off + cnt]
        txt = "".join(
            rev.get(g, chr(g + 0x20) if g <= 94 else "?") for g in gl
        )
        print("  page %d line idx=%d  S1+0x%04X off=%4d cnt=%2d  |%s|"
              % (page_no, idx, pc, off, cnt, txt))
        if off != pos:
            failures.append("record S1+0x%X: off %d != expected %d" % (pc, off, pos))
        if not (trailing_start <= off and off + cnt <= n_words):
            failures.append("record S1+0x%X outside new trailing region" % pc)
        if cnt < 1:
            failures.append("record S1+0x%X has cnt %d" % (pc, cnt))
        # (b) glyph constraints
        if any(g >= 0xFB00 for g in gl):
            failures.append("record S1+0x%X: control code in line" % pc)
        if any(g > 94 for g in gl):
            failures.append("record S1+0x%X: glyph > 94" % pc)
        if cnt > MAX_LINE_GLYPHS:
            failures.append("record S1+0x%X: line %d > %d glyphs" % (pc, cnt, MAX_LINE_GLYPHS))
        pos = off + cnt
        li += 1
        page_left -= 1
        if page_left == 0 and page_no < len(PAGE_LINES):
            page_no += 1
            page_left = PAGE_LINES[page_no - 1]
    if pos != n_words:
        failures.append("lines do not tile to end of Section 2 (%d != %d)" % (pos, n_words))

    # (c) sec2_size matches actual Section 2 byte length
    body_after = out[sec2_off + sec2_size :]
    if any(body_after):
        failures.append("non-zero bytes after Section 2 (padding expected)")
    if len(out) % SECTOR != 0:
        failures.append("output not sector-padded (%d bytes)" % len(out))
    print("sec2_size @0x14 = %d bytes (%d words), file = %d bytes, "
          "padding after sec2 = %d zero bytes"
          % (sec2_size, n_words, len(out), len(body_after)))

    # (d) re-walk the output Section 1
    ok, instrs = walk(sec1)
    print("output Section 1 re-walk: %s (%d instrs)" % ("OK" if ok else "FAILED", len(instrs)))
    if not ok:
        failures.append("output Section 1 walk failed")
    recs = extract_records(sec1, instrs)
    for r in recs["display"]:
        if r["cnt"] == 0:
            continue
        end = r["off"] + r["cnt"]
        if end > n_words or words[end - 1] != 0xFFFF:
            failures.append("DISPLAY_TEXT at S1+0x%X: off=%d cnt=%d does not end on FFFF"
                            % (r["pc"], r["off"], r["cnt"]))
    for r in recs["label"]:
        if r["off"] + r["cnt"] > n_words:
            failures.append("0x14 at S1+0x%X exceeds Section 2" % r["pc"])

    # (e) FFFF group count equals pristine
    o_sec2_off = struct.unpack_from("<I", orig, 0x18)[0]
    o_sec2_size = struct.unpack_from("<I", orig, 0x14)[0]
    o_words = struct.unpack_from(">%dH" % (o_sec2_size // 2), orig, o_sec2_off)
    o_ffff = sum(1 for w in o_words if w == 0xFFFF)
    n_ffff = sum(1 for w in words if w == 0xFFFF)
    print("FFFF terminators: pristine %d, output %d" % (o_ffff, n_ffff))
    if o_ffff != n_ffff:
        failures.append("FFFF group count changed (%d -> %d)" % (o_ffff, n_ffff))

    if failures:
        print("VERIFICATION FAILED:")
        for f in failures:
            print("  - " + f)
        return False
    print("ALL CHECKS PASSED")
    return True


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    os.chdir(_ROOT)
    raw_path = "extracted/packdata_raw/1193_type02.raw"
    out_dir = "build/patched_type2"
    print("=" * 60)
    print("  R1193 INTRO NARRATION PATCHER (BUG-10)")
    print("=" * 60)
    translations = _load_translations()
    print("Loaded %d translation entries for R1193 (msg indices: %s)"
          % (len(translations), sorted(translations)))
    build_r1193(raw_path, translations, out_dir)
    print()
    ok = verify(raw_path, os.path.join(out_dir, "1193_type02.raw"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
