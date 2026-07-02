#!/usr/bin/env python3
"""
patch_r1194_narration.py -- R1194 ending narration: English line records
=========================================================================

R1194 (type-02) carries the game's ENDING epilogue (the "Dark Lord Ashira"
crawl + Oriana's coronation speech).  Structure (pristine):

  * Section 2 = ONE FFFF-group (482 words), NO trailing block.
  * 42 Section-1 0x14 line records (14 bytes BE: u16 0x0014, u16 LINE_IDX,
    s16 0xFFFF, u32 WORD_OFF, u32 GLYPH_CNT) tile words 0..462 -- the JP
    narration lines, in pages of 3/3/4/2/3/3/2/2/2/2/3/1/2/1/3/3/3 lines
    (page = run of LINE_IDX values until the index resets).
  * ONE 0x04 DISPLAY_TEXT at S1+0x155A shows the final sentence, words
    462..482 ("But for now, we set this tale aside."), ending ON the FFFF.

The generic Step-4 injection translates the group but keeps the 42 0x14
slices as a VERBATIM JP prefix (name-island preservation), so the ending
still renders Japanese line-by-line while the 0x04 shows the whole English
body in one box.  This patcher rebuilds the resource from PRISTINE instead:

  1. Group 0 is rebuilt as [42 English narration lines][English tail line]
     with the single FFFF terminator (group/FFFF count unchanged).
  2. Each of the 42 0x14 records (located by pattern scan of the PRISTINE
     Section 1, cross-checked against the sec1_disasm walk) is rewritten
     with the EXACT new WORD_OFF / GLYPH_CNT of its line.
  3. The 0x04 is re-pointed at the tail line (still ending on the FFFF).

Line budget and conventions are identical to tools/patch_r1193_narration.py
(<= 23 glyphs/line at 24px pitch, greedy word-wrap per page, surplus
records get a single space glyph, never cnt 0).

R1193 SHORT PROLOGUE VARIANT (fix_r1193_short_prologue):
  R1193's Section 1 ALSO walks 10 0x14 records tiling group-0 words 0..99
  (a short prologue variant, pages 4/2/4) which patch_r1193_narration.py
  declared out of scope; after Step 5 they still point at the verbatim JP
  prefix.  fix_r1193_short_prologue() post-processes the Step-5 output:
  it APPENDS 10 English lines at the very end of Section 2 (no existing
  word offset moves), re-points the 10 records, and re-points the
  short-variant 0x04 (S1+0x5BF, which the injection had inflated to show
  the whole English body) at the group-1 key-wait span -- byte-identical
  content to what that 0x04 displayed in the pristine file.

Usage:
    python tools/patch_r1194_narration.py [out_dir]   # standalone build + verify
    from patch_r1194_narration import build_r1194, fix_r1193_short_prologue
"""

import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sec1_disasm import walk, extract_records
from patch_r1193_narration import (
    _enc_char,
    _load_eng_table,
    encode_group_text,
    _flow_page,
    MAX_LINE_GLYPHS,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECTOR = 2048
HEADER_SIZE = 0x20

# ---------------------------------------------------------------------------
# R1194 ending narration.
#
# One entry per page; page line budgets from the pristine LINE_IDX structure.
# The text is the data/type2_translated/batch_intro_narration.json msg-0 body
# (the same English the 0x04 already displays), condensed per page to the
# renderer's fixed budget (<= 23 glyphs/line).
# ---------------------------------------------------------------------------
R1194_PAGE_LINES = [3, 3, 4, 2, 3, 3, 2, 2, 2, 2, 3, 1, 2, 1, 3, 3, 3]  # 42
N_R1194_RECORDS = sum(R1194_PAGE_LINES)  # 42

R1194_PAGES = [
    "The Dark Lord Ashira, driven to the brink, sank into the abyss.",   # 3
    "The warriors who fell were sealed as Duhan's war"
    " drew to a close.",                                                 # 3
    "Ortrud too, by his own will, was sealed not as a hero,"
    " but with the fallen of Banquo.",                                   # 4
    "The people shall remember it forever.",                             # 2
    "Snow fell in winter; in spring the sounds of peace"
    " filled the land.",                                                 # 3
    "After long years, Princess Oriana declared herself queen.",         # 3
    "\"The days of bloodshed are over at last.\"",                       # 2
    "\"We must stand as one against our foe.\"",                         # 2
    "\"For the peace of all who dwell in Venoa.\"",                      # 2
    "\"For the souls of the brave who have fallen.\"",                   # 2
    "\"I hereby swear my oath against the lord of darkness.\"",          # 3
    "\"Let me present them.\"",                                          # 1
    "The knights marched forth amid cheers.",                            # 2
    "\"The swords of Venoa!\"",                                          # 1
    "\"The noble Queen's Guard, sworn to fight the darkness!\"",         # 3
    "As confetti rained down, this scene became an eternal legend.",     # 3
    "It was the start of the tale of a fair queen"
    " and her Queen's Guard.",                                           # 3
]

# The 0x04-displayed closing sentence (pristine words 462..482).
R1194_TAIL = "But for now, we / set this tale aside."

# ---------------------------------------------------------------------------
# R1193 short prologue variant (10 records, group-0 words 0..99, pages 4/2/4).
# Same prologue as batch_intro_narration.json msg-0, condensed per page.
# ---------------------------------------------------------------------------
R1193_SHORT_PAGE_LINES = [4, 2, 4]  # 10
N_R1193_SHORT_RECORDS = sum(R1193_SHORT_PAGE_LINES)

R1193_SHORT_PAGES = [
    "For thirty years, a war plunged Venoa into blood and terror.",      # 4
    "Later it was called the Battle of Banquo.",                         # 2
    "It began when the king of San-Goth raised his banner"
    " and attacked the Kingdom of Duhan!",                               # 4
]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _read_sec2(data):
    """Return (sec2_off, sec2_size, n_words, words tuple, sec1 bytes)."""
    sec2_size = struct.unpack_from("<I", data, 0x14)[0]
    sec2_off = struct.unpack_from("<I", data, 0x18)[0]
    n_words = sec2_size // 2
    words = struct.unpack_from(">%dH" % n_words, data, sec2_off)
    sec1 = data[HEADER_SIZE:sec2_off]
    return sec2_off, sec2_size, n_words, words, sec1


def _scan_0x14(sec1, pred):
    """Byte-wise scan for 14-byte 0x14 records (0014 idx FFFF off cnt) whose
    (off, cnt) satisfy pred.  Returns [(pc, idx, off, cnt)]."""
    hits = []
    for pc in range(0, len(sec1) - 13):
        if struct.unpack_from(">H", sec1, pc)[0] != 0x0014:
            continue
        if struct.unpack_from(">H", sec1, pc + 4)[0] != 0xFFFF:
            continue
        off = struct.unpack_from(">I", sec1, pc + 6)[0]
        cnt = struct.unpack_from(">I", sec1, pc + 10)[0]
        if pred(off, cnt):
            hits.append((pc, struct.unpack_from(">H", sec1, pc + 2)[0], off, cnt))
    return hits


def _page_runs(records):
    """Page structure from LINE_IDX resets (new page when idx <= prev)."""
    pages = []
    run = 0
    prev = None
    for _pc, idx, _off, _cnt in records:
        if prev is not None and idx <= prev:
            pages.append(run)
            run = 0
        run += 1
        prev = idx
    if run:
        pages.append(run)
    return pages


def _build_lines(page_texts, page_lines):
    """Flow the per-page texts into the per-page line budgets; returns the
    flat list of lines with the R1193 conventions (surplus = single space)."""
    assert len(page_texts) == len(page_lines)
    lines = []
    for text, n in zip(page_texts, page_lines):
        lines.extend(_flow_page(text, n))
    for ln in lines:
        assert 1 <= len(ln) <= MAX_LINE_GLYPHS, repr(ln)
    return lines


def _encode_lines(lines):
    glyphs = [[_enc_char(c) for c in ln] for ln in lines]
    for ln, gl in zip(lines, glyphs):
        if any(g >= 0xFB00 for g in gl):
            raise ValueError("control code in line %r" % ln)
    return glyphs


def _rev_table():
    rev = {}
    for ch, g in _load_eng_table().items():
        rev.setdefault(g, ch)
    return rev


def _dec_en(words, rev):
    return "".join(
        "[%04X]" % g if g >= 0xFB00
        else rev.get(g, chr(g + 0x20) if g <= 94 else "?")
        for g in words
    )


def _assert_sec1_delta(old_sec1, new_sec1, allowed_ranges, res_name):
    """Assert new_sec1 differs from old_sec1 ONLY inside allowed byte ranges."""
    if len(old_sec1) != len(new_sec1):
        raise ValueError("R%s: Section 1 length changed" % res_name)
    allowed = set()
    for a, b in allowed_ranges:
        allowed.update(range(a, b))
    for i in range(len(old_sec1)):
        if old_sec1[i] != new_sec1[i] and i not in allowed:
            raise ValueError(
                "R%s: unexpected Section-1 byte change at +0x%X" % (res_name, i)
            )


# ---------------------------------------------------------------------------
# R1194 record location (pristine Section 1)
# ---------------------------------------------------------------------------
def find_r1194_records(orig_data):
    """
    Locate the 42 line records and the single 0x04 in the PRISTINE R1194.

    Returns (records, disp_pc, prefix_end, n_words):
      records    -- [(pc, line_idx, off, cnt)] in off order (== pc order),
                    asserted to tile words 0..prefix_end exactly.
      disp_pc    -- pc of the 0x04 DISPLAY_TEXT (off == prefix_end, span
                    ends on the group FFFF == last Section-2 word).
    """
    _off, _size, n_words, words, sec1 = _read_sec2(orig_data)

    # exactly ONE group, no trailing block
    ffff = [i for i, w in enumerate(words) if w == 0xFFFF]
    if len(ffff) != 1 or ffff[0] != n_words - 1:
        raise ValueError(
            "R1194: expected exactly one FFFF terminating Section 2, got %r"
            % ffff[:4]
        )

    def in_sec2(off, cnt):
        return cnt > 0 and off + cnt <= n_words

    scanned = _scan_0x14(sec1, in_sec2)

    ok, instrs = walk(sec1)
    if not ok:
        raise ValueError("R1194: pristine Section 1 walk failed")
    recs = extract_records(sec1, instrs)
    walked = [
        (r["pc"], r["param"], r["off"], r["cnt"])
        for r in recs["label"]
        if in_sec2(r["off"], r["cnt"])
    ]
    if sorted(scanned) != sorted(walked):
        raise ValueError(
            "R1194: pattern scan (%d) and disasm walk (%d) disagree on the "
            "0x14 records" % (len(scanned), len(walked))
        )
    if len(scanned) != N_R1194_RECORDS:
        raise ValueError(
            "R1194: expected exactly %d 0x14 records, found %d"
            % (N_R1194_RECORDS, len(scanned))
        )

    records = sorted(scanned, key=lambda r: r[2])
    if records != sorted(scanned, key=lambda r: r[0]):
        raise ValueError("R1194: 0x14 record off order != pc order")

    pos = 0
    for _pc, _idx, off, cnt in records:
        if off != pos:
            raise ValueError(
                "R1194: 0x14 records do not tile (expected off=%d, got %d)"
                % (pos, off)
            )
        pos += cnt
    prefix_end = pos

    pages = _page_runs(records)
    if pages != R1194_PAGE_LINES:
        raise ValueError(
            "R1194: page structure %r != expected %r" % (pages, R1194_PAGE_LINES)
        )

    disp = [r for r in recs["display"] if r["cnt"] > 0]
    if len(disp) != 1:
        raise ValueError(
            "R1194: expected exactly one live 0x04 DISPLAY_TEXT, found %d"
            % len(disp)
        )
    d = disp[0]
    if d["off"] != prefix_end or d["off"] + d["cnt"] != n_words:
        raise ValueError(
            "R1194: 0x04 span off=%d cnt=%d does not cover prefix_end %d .. "
            "n_words %d" % (d["off"], d["cnt"], prefix_end, n_words)
        )
    if words[n_words - 1] != 0xFFFF:
        raise ValueError("R1194: 0x04 span does not end on FFFF")

    return records, d["pc"], prefix_end, n_words


# ---------------------------------------------------------------------------
# R1194 main builder
# ---------------------------------------------------------------------------
def build_r1194(raw_path, translations, out_dir="build/patched_type2"):
    """
    Build the fully patched R1194 resource from PRISTINE.

    raw_path:     pristine extracted/packdata_raw/1194_type02.raw
    translations: {msg_index: english_text} for resource 1194 (as loaded by
                  build_v9 from data/type2_translated/batch_*.json).  msg 0
                  (the epilogue body) must be present -- it is the gate that
                  the corpus covers this resource; the authored per-page
                  texts above carry the same prose reflowed to the 42-record
                  line budget.

    Writes <out_dir>/1194_type02.raw (sector-padded) and returns its bytes.
    """
    orig_data = open(raw_path, "rb").read()

    if 0 not in translations:
        raise ValueError(
            "R1194: no msg_index 0 (epilogue body) entry in translations "
            "-- refusing to ship a half-translated ending"
        )
    sec2_off, sec2_size, n_words, words, sec1 = _read_sec2(orig_data)
    if any(orig_data[sec2_off + sec2_size:]):
        raise ValueError("R1194: pristine has non-zero bytes after Section 2")

    records, disp_pc, prefix_end, _nw = find_r1194_records(orig_data)

    # --- English lines + tail -------------------------------------------------
    lines = _build_lines(R1194_PAGES, R1194_PAGE_LINES)
    line_glyphs = _encode_lines(lines)

    tail_glyphs = encode_group_text(R1194_TAIL)
    if any(g >= 0xFB00 and g != 0xFFFE for g in tail_glyphs):
        raise ValueError("R1194: tail may only contain 0xFFFE controls")

    # --- assemble the new single group -----------------------------------------
    new_words = []
    line_offsets = []
    for gl in line_glyphs:
        line_offsets.append(len(new_words))
        new_words.extend(gl)
    new_prefix_end = len(new_words)
    new_words.extend(tail_glyphs)
    new_words.append(0xFFFF)
    new_n_words = len(new_words)
    new_sec2 = struct.pack(">%dH" % new_n_words, *new_words)

    # --- rewrite the 42 line records + the 0x04 --------------------------------
    new_sec1 = bytearray(sec1)
    allowed = []
    for (pc, _idx, _off, _cnt), new_off, gl in zip(records, line_offsets, line_glyphs):
        struct.pack_into(">I", new_sec1, pc + 6, new_off)
        struct.pack_into(">I", new_sec1, pc + 10, len(gl))
        allowed.append((pc + 6, pc + 14))
    struct.pack_into(">I", new_sec1, disp_pc + 2, new_prefix_end)
    struct.pack_into(">I", new_sec1, disp_pc + 6, new_n_words - new_prefix_end)
    allowed.append((disp_pc + 2, disp_pc + 10))
    _assert_sec1_delta(sec1, new_sec1, allowed, "1194")

    header = bytearray(orig_data[:HEADER_SIZE])
    struct.pack_into("<I", header, 0x14, len(new_sec2))

    result = bytes(header) + bytes(new_sec1) + new_sec2
    pad = (SECTOR - len(result) % SECTOR) % SECTOR
    result += b"\x00" * pad

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, os.path.basename(raw_path))
    open(out_path, "wb").write(result)
    print(
        "  R1194 ending narration: group 0 %d -> %d words (%d lines, pages %s, "
        "tail %d words), sec2 %d bytes, file %d bytes"
        % (
            n_words,
            new_n_words,
            len(lines),
            "/".join(map(str, R1194_PAGE_LINES)),
            len(tail_glyphs),
            len(new_sec2),
            len(result),
        )
    )
    return result


def verify_r1194(raw_path, out_path):
    """Self-verification of the built R1194.  Returns True when all pass."""
    orig = open(raw_path, "rb").read()
    out = open(out_path, "rb").read()
    rev = _rev_table()
    failures = []

    records, disp_pc, _pe, _nw = find_r1194_records(orig)

    sec2_off, sec2_size, n_words, words, sec1 = _read_sec2(out)

    print("Decoded R1194 line records (%d):" % len(records))
    pos = 0
    page_no = 1
    page_left = R1194_PAGE_LINES[0]
    for pc, idx, _ooff, _ocnt in records:
        off = struct.unpack_from(">I", sec1, pc + 6)[0]
        cnt = struct.unpack_from(">I", sec1, pc + 10)[0]
        gl = words[off : off + cnt]
        print("  page %2d line idx=%d  S1+0x%04X off=%4d cnt=%2d  |%s|"
              % (page_no, idx, pc, off, cnt, _dec_en(gl, rev)))
        if off != pos:
            failures.append("record S1+0x%X: off %d != expected %d" % (pc, off, pos))
        if cnt < 1 or cnt > MAX_LINE_GLYPHS:
            failures.append("record S1+0x%X: cnt %d outside 1..%d"
                            % (pc, cnt, MAX_LINE_GLYPHS))
        if any(g >= 0xFB00 for g in gl) or any(g > 94 for g in gl):
            failures.append("record S1+0x%X: non-plain glyph in line" % pc)
        pos = off + cnt
        page_left -= 1
        if page_left == 0 and page_no < len(R1194_PAGE_LINES):
            page_no += 1
            page_left = R1194_PAGE_LINES[page_no - 1]

    d_off = struct.unpack_from(">I", sec1, disp_pc + 2)[0]
    d_cnt = struct.unpack_from(">I", sec1, disp_pc + 6)[0]
    print("0x04 tail at S1+0x%04X: off=%d cnt=%d |%s|"
          % (disp_pc, d_off, d_cnt, _dec_en(words[d_off : d_off + d_cnt], rev)))
    if d_off != pos:
        failures.append("0x04 off %d != line prefix end %d" % (d_off, pos))
    if d_off + d_cnt != n_words or words[n_words - 1] != 0xFFFF:
        failures.append("0x04 span does not end on the terminating FFFF")

    # structural gates
    o_words = _read_sec2(orig)[3]
    o_ffff = sum(1 for w in o_words if w == 0xFFFF)
    n_ffff = sum(1 for w in words if w == 0xFFFF)
    print("FFFF terminators: pristine %d, output %d" % (o_ffff, n_ffff))
    if o_ffff != n_ffff:
        failures.append("FFFF group count changed (%d -> %d)" % (o_ffff, n_ffff))
    if any(out[sec2_off + sec2_size :]):
        failures.append("non-zero bytes after Section 2")
    if len(out) % SECTOR != 0:
        failures.append("output not sector-padded (%d bytes)" % len(out))

    ok, instrs = walk(sec1)
    print("output Section 1 re-walk: %s (%d instrs)"
          % ("OK" if ok else "FAILED", len(instrs)))
    if not ok:
        failures.append("output Section 1 walk failed")
    recs = extract_records(sec1, instrs)
    for r in recs["display"]:
        if r["cnt"] == 0:
            continue
        end = r["off"] + r["cnt"]
        if end > n_words or words[end - 1] != 0xFFFF:
            failures.append("DISPLAY_TEXT at S1+0x%X does not end on FFFF" % r["pc"])
    for r in recs["label"]:
        if r["off"] + r["cnt"] > n_words:
            failures.append("0x14 at S1+0x%X exceeds Section 2" % r["pc"])

    if failures:
        print("R1194 VERIFICATION FAILED:")
        for f in failures:
            print("  - " + f)
        return False
    print("R1194: ALL CHECKS PASSED")
    return True


# ---------------------------------------------------------------------------
# R1193 short prologue variant (post-Step-5 fixup)
# ---------------------------------------------------------------------------
def _find_r1193_short(orig_data):
    """
    Locate, in PRISTINE R1193, the 10 short-variant 0x14 records (tiling
    group-0 words 0..prefix_end) and the two key-wait 0x04s.

    Returns (records, disp_a_pc, disp_b, prefix_end):
      records   -- [(pc, idx, off, cnt)] in off order, tiling 0..prefix_end
      disp_a_pc -- pc of the group-0 0x04 (the one the injection inflates)
      disp_b    -- {'pc','off','cnt'} of the group-1 key-wait 0x04
    """
    _off, _size, n_words, words, sec1 = _read_sec2(orig_data)

    ffff = [i for i, w in enumerate(words) if w == 0xFFFF]
    if len(ffff) < 2:
        raise ValueError("R1193: expected >= 2 FFFF groups")
    g0_end = ffff[0]           # word index of group 0's FFFF
    g1_end = ffff[1]

    def in_g0(off, cnt):
        return cnt > 0 and off + cnt <= g0_end

    scanned = _scan_0x14(sec1, in_g0)

    ok, instrs = walk(sec1)
    if not ok:
        raise ValueError("R1193: pristine Section 1 walk failed")
    recs = extract_records(sec1, instrs)
    walked = [
        (r["pc"], r["param"], r["off"], r["cnt"])
        for r in recs["label"]
        if in_g0(r["off"], r["cnt"])
    ]
    if sorted(scanned) != sorted(walked):
        raise ValueError(
            "R1193: pattern scan (%d) and walk (%d) disagree on the short-"
            "variant 0x14 records" % (len(scanned), len(walked))
        )
    if len(scanned) != N_R1193_SHORT_RECORDS:
        raise ValueError(
            "R1193: expected %d short-variant 0x14 records, found %d"
            % (N_R1193_SHORT_RECORDS, len(scanned))
        )

    records = sorted(scanned, key=lambda r: r[2])
    if records != sorted(scanned, key=lambda r: r[0]):
        raise ValueError("R1193: short-variant off order != pc order")
    pos = 0
    for _pc, _idx, off, cnt in records:
        if off != pos:
            raise ValueError(
                "R1193: short-variant records do not tile (expected %d, got %d)"
                % (pos, off)
            )
        pos += cnt
    prefix_end = pos

    pages = _page_runs(records)
    if pages != R1193_SHORT_PAGE_LINES:
        raise ValueError(
            "R1193: short-variant page structure %r != expected %r"
            % (pages, R1193_SHORT_PAGE_LINES)
        )

    # The two key-wait 0x04s: identical content in pristine.
    disp = [r for r in recs["display"] if r["cnt"] > 0 and r["off"] < g1_end + 1]
    if len(disp) != 2:
        raise ValueError(
            "R1193: expected exactly two key-wait 0x04s, found %d" % len(disp)
        )
    disp.sort(key=lambda r: r["off"])
    a, b = disp
    if a["off"] != prefix_end or a["off"] + a["cnt"] != g0_end + 1:
        raise ValueError("R1193: group-0 0x04 span unexpected (off=%d cnt=%d)"
                         % (a["off"], a["cnt"]))
    if b["off"] != g0_end + 1 or b["off"] + b["cnt"] != g1_end + 1:
        raise ValueError("R1193: group-1 0x04 span unexpected (off=%d cnt=%d)"
                         % (b["off"], b["cnt"]))
    if words[a["off"] : a["off"] + a["cnt"] - 1] != words[b["off"] : b["off"] + b["cnt"] - 1]:
        raise ValueError("R1193: the two key-wait 0x04 contents differ in pristine")

    return records, a["pc"], b, prefix_end


def fix_r1193_short_prologue(out_dir="build/patched_type2",
                             raw_path="extracted/packdata_raw/1193_type02.raw"):
    """
    Post-process the Step-5 R1193 output: translate the 10 short-prologue
    0x14 line records (pages 4/2/4).

    English lines are APPENDED at the very end of Section 2, so NO existing
    word offset moves (the 23 trailing-block records, the group boundaries
    and every other reference stay byte-identical).  The 10 records are
    re-pointed at the appended lines, and the short-variant 0x04 (which the
    injection inflated to display the whole English body) is re-pointed at
    the group-1 key-wait span -- the same content it displayed in pristine.

    Idempotent: a file whose 10 records already point past the group region
    is verified and left unchanged.
    """
    orig_data = open(raw_path, "rb").read()
    built_path = os.path.join(out_dir, "1193_type02.raw")
    built = open(built_path, "rb").read()

    records, disp_a_pc, disp_b_pr, prefix_end = _find_r1193_short(orig_data)
    o_words = _read_sec2(orig_data)[3]

    sec2_off, sec2_size, n_words, words, sec1 = _read_sec2(built)
    if any(built[sec2_off + sec2_size :]):
        raise ValueError("R1193: built file has non-zero bytes after Section 2")

    # Locate group boundaries and the group-1 key-wait span in the BUILT file.
    ffff = [i for i, w in enumerate(words) if w == 0xFFFF]
    if len(ffff) < 2:
        raise ValueError("R1193: built file lost its FFFF groups")
    g0_end, g1_end = ffff[0], ffff[1]
    g1_off, g1_cnt = g0_end + 1, g1_end - g0_end
    kw = words[g1_off : g1_off + g1_cnt]
    if tuple(kw[:4]) != (0xFFFE, 0xFFFE, 0xFFFE, 0xFFE1) or kw[-1] != 0xFFFF:
        raise ValueError("R1193: built group-1 key-wait span has unexpected shape")
    if kw != o_words[disp_b_pr["off"] : disp_b_pr["off"] + disp_b_pr["cnt"]]:
        raise ValueError("R1193: built group-1 key-wait content != pristine")

    # English lines
    lines = _build_lines(R1193_SHORT_PAGES, R1193_SHORT_PAGE_LINES)
    line_glyphs = _encode_lines(lines)

    # --- idempotence: already patched? -----------------------------------------
    cur = [
        (struct.unpack_from(">I", sec1, pc + 6)[0],
         struct.unpack_from(">I", sec1, pc + 10)[0])
        for (pc, _idx, _off, _cnt) in records
    ]
    if all(
        off + cnt <= n_words and list(words[off : off + cnt]) == gl
        for (off, cnt), gl in zip(cur, line_glyphs)
    ):
        print("  R1193 short prologue: already patched -- left unchanged")
        return built

    # --- must be the fresh Step-5 state: verbatim JP prefix --------------------
    for (pc, _idx, o_off, o_cnt), (c_off, c_cnt) in zip(records, cur):
        if (c_off, c_cnt) != (o_off, o_cnt):
            raise ValueError(
                "R1193: short-variant record S1+0x%X is (off=%d,cnt=%d), "
                "expected pristine (off=%d,cnt=%d) -- unknown file state"
                % (pc, c_off, c_cnt, o_off, o_cnt)
            )
        if words[c_off : c_off + c_cnt] != o_words[o_off : o_off + o_cnt]:
            raise ValueError(
                "R1193: short-variant JP prefix at S1+0x%X not verbatim -- "
                "unknown file state" % pc
            )

    # --- append lines at the very end of Section 2 -----------------------------
    new_words = list(words)
    line_offsets = []
    for gl in line_glyphs:
        line_offsets.append(len(new_words))
        new_words.extend(gl)
    new_sec2 = struct.pack(">%dH" % len(new_words), *new_words)

    new_sec1 = bytearray(sec1)
    allowed = []
    for (pc, _idx, _o, _c), new_off, gl in zip(records, line_offsets, line_glyphs):
        struct.pack_into(">I", new_sec1, pc + 6, new_off)
        struct.pack_into(">I", new_sec1, pc + 10, len(gl))
        allowed.append((pc + 6, pc + 14))
    struct.pack_into(">I", new_sec1, disp_a_pc + 2, g1_off)
    struct.pack_into(">I", new_sec1, disp_a_pc + 6, g1_cnt)
    allowed.append((disp_a_pc + 2, disp_a_pc + 10))
    _assert_sec1_delta(sec1, new_sec1, allowed, "1193")

    header = bytearray(built[:HEADER_SIZE])
    struct.pack_into("<I", header, 0x14, len(new_sec2))

    result = bytes(header) + bytes(new_sec1) + new_sec2
    pad = (SECTOR - len(result) % SECTOR) % SECTOR
    result += b"\x00" * pad
    open(built_path, "wb").write(result)
    print(
        "  R1193 short prologue: %d lines (pages %s) appended at word %d, "
        "0x04@S1+0x%X re-pointed to key-wait (off=%d cnt=%d), sec2 %d -> %d "
        "bytes, file %d bytes"
        % (
            len(lines),
            "/".join(map(str, R1193_SHORT_PAGE_LINES)),
            n_words,
            disp_a_pc,
            g1_off,
            g1_cnt,
            sec2_size,
            len(new_sec2),
            len(result),
        )
    )
    return result


def verify_r1193_short(raw_path, out_path):
    """Verify the short-prologue fixup on the built R1193."""
    orig = open(raw_path, "rb").read()
    out = open(out_path, "rb").read()
    rev = _rev_table()
    failures = []

    records, disp_a_pc, _disp_b, _pe = _find_r1193_short(orig)
    sec2_off, sec2_size, n_words, words, sec1 = _read_sec2(out)

    lines = _build_lines(R1193_SHORT_PAGES, R1193_SHORT_PAGE_LINES)
    line_glyphs = _encode_lines(lines)

    print("Decoded R1193 short-prologue records (%d):" % len(records))
    for (pc, idx, _o, _c), gl_expect in zip(records, line_glyphs):
        off = struct.unpack_from(">I", sec1, pc + 6)[0]
        cnt = struct.unpack_from(">I", sec1, pc + 10)[0]
        gl = words[off : off + cnt]
        print("  idx=%d S1+0x%04X off=%4d cnt=%2d |%s|"
              % (idx, pc, off, cnt, _dec_en(gl, rev)))
        if list(gl) != gl_expect:
            failures.append("record S1+0x%X content mismatch" % pc)
        if cnt < 1 or cnt > MAX_LINE_GLYPHS:
            failures.append("record S1+0x%X cnt %d outside 1..%d"
                            % (pc, cnt, MAX_LINE_GLYPHS))

    a_off = struct.unpack_from(">I", sec1, disp_a_pc + 2)[0]
    a_cnt = struct.unpack_from(">I", sec1, disp_a_pc + 6)[0]
    print("0x04@S1+0x%04X: off=%d cnt=%d" % (disp_a_pc, a_off, a_cnt))
    if a_cnt <= 0 or a_off + a_cnt > n_words or words[a_off + a_cnt - 1] != 0xFFFF:
        failures.append("re-pointed 0x04 does not end on FFFF")
    if tuple(words[a_off : a_off + 4]) != (0xFFFE, 0xFFFE, 0xFFFE, 0xFFE1):
        failures.append("re-pointed 0x04 does not show the key-wait span")

    o_words = _read_sec2(orig)[3]
    o_ffff = sum(1 for w in o_words if w == 0xFFFF)
    n_ffff = sum(1 for w in words if w == 0xFFFF)
    print("FFFF terminators: pristine %d, output %d" % (o_ffff, n_ffff))
    if o_ffff != n_ffff:
        failures.append("FFFF group count changed (%d -> %d)" % (o_ffff, n_ffff))
    if any(out[sec2_off + sec2_size :]):
        failures.append("non-zero bytes after Section 2")
    if len(out) % SECTOR != 0:
        failures.append("output not sector-padded")

    ok, instrs = walk(sec1)
    print("output Section 1 re-walk: %s (%d instrs)"
          % ("OK" if ok else "FAILED", len(instrs)))
    if not ok:
        failures.append("output Section 1 walk failed")
    recs = extract_records(sec1, instrs)
    for r in recs["display"]:
        if r["cnt"] == 0:
            continue
        end = r["off"] + r["cnt"]
        if end > n_words or words[end - 1] != 0xFFFF:
            failures.append("DISPLAY_TEXT at S1+0x%X does not end on FFFF" % r["pc"])
    for r in recs["label"]:
        if r["off"] + r["cnt"] > n_words:
            failures.append("0x14 at S1+0x%X exceeds Section 2" % r["pc"])

    if failures:
        print("R1193-SHORT VERIFICATION FAILED:")
        for f in failures:
            print("  - " + f)
        return False
    print("R1193-SHORT: ALL CHECKS PASSED")
    return True


# ---------------------------------------------------------------------------
# Standalone build + self-verification
# ---------------------------------------------------------------------------
def _load_translations():
    """Load the resource-1194 translations from batch_intro_narration.json."""
    path = os.path.join(_ROOT, "data", "type2_translated",
                        "batch_intro_narration.json")
    trans = {}
    for e in json.load(open(path, encoding="utf-8")):
        if e.get("resource") != 1194:
            continue
        en = e.get("english", "")
        if en and not any(ord(c) > 127 for c in en):
            trans[e["msg_index"]] = en
    return trans


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    os.chdir(_ROOT)
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "build/patched_type2"
    raw_1194 = "extracted/packdata_raw/1194_type02.raw"
    raw_1193 = "extracted/packdata_raw/1193_type02.raw"

    print("=" * 60)
    print("  R1194 ENDING NARRATION PATCHER")
    print("=" * 60)
    translations = _load_translations()
    print("Loaded %d translation entries for R1194 (msg indices: %s)"
          % (len(translations), sorted(translations)))
    build_r1194(raw_1194, translations, out_dir)
    print()
    ok = verify_r1194(raw_1194, os.path.join(out_dir, "1194_type02.raw"))

    print()
    print("=" * 60)
    print("  R1193 SHORT-PROLOGUE VARIANT FIXUP")
    print("=" * 60)
    built_1193 = os.path.join(out_dir, "1193_type02.raw")
    if os.path.exists(built_1193):
        fix_r1193_short_prologue(out_dir, raw_1193)
        print()
        ok = verify_r1193_short(raw_1193, built_1193) and ok
    else:
        print("  %s not found -- run build_v9 Step 5 (patch_r1193_narration) "
              "first; short-variant fixup skipped" % built_1193)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
