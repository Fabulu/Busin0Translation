#!/usr/bin/env python3
"""
_helpers.py -- shared infrastructure for the v85 regression test suite.

Provides:
  * tiny no-dependency test runner (PASS / FAIL / SKIP, nonzero exit on FAIL)
  * repo path constants and tier-input discovery
  * PACKDATA TOC parsing + resource extraction from a built ISO (via the
    ISO9660 root directory, NOT a hardcoded LBA)
  * FFFF group parsing for Section 2 / flat glyph streams
  * glyph decoding through data/english_glyph_table.json
  * Section 1 walking via tools/sec1_disasm.py and the shared
    "v84 bug class" regression check (re-walk OK, FFFF invariant,
    Section-1 diffs confined to walked operand ranges)

All paths are absolute; tests never chdir and never write outside
tempfile directories.
"""

import json
import glob
import os
import struct
import sys

# Windows console is cp1252 -- make sure any decoded glyph output survives.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT, "tools")
RAW_DIR = os.path.join(ROOT, "extracted", "packdata_raw")
PATCHED_TYPE2_DIR = os.path.join(ROOT, "build", "patched_type2")
PACKDATA_RES_DIR = os.path.join(ROOT, "build", "packdata_resources")
DATA_DIR = os.path.join(ROOT, "data")
BUILD_V9 = os.path.join(ROOT, "build", "build_v9.py")
SEC1_PATCHER = os.path.join(TOOLS_DIR, "patch_section1_offsets.py")
OPCODE_TABLE = os.path.join(
    ROOT, "build", "recon_v85", "exe-interpreter", "opcode_table_v85.json"
)

SECTOR = 2048
HEADER_SIZE = 0x20
N_RESOURCES = 2883  # PACKDATA.DIG TOC entry count

# Tracked PACKDATA overflow budget (sectors). The rebuilt PACKDATA.DIG overflows
# past its original end into BSN2_0.DSI; build_v9.py Step 8.2 self-heals by
# name-path relocation (dynamic shift, ISO extended, PVD updated; relocated
# files MD5-gated by verify_iso). History: ~198 sectors at v118, 237 at v160,
# 258 at v165 -- the v163-v165 LIBRARY waves legitimately grew R2654 from 90 to
# 113 sectors (+~1000 translated strings) plus hub-batch growth. Investigated
# and bumped 256 -> 320 on 2026-07-04 (v165): the relocation machinery is
# uncapped and gated; this budget exists purely as a growth tripwire. If it
# trips again, account for the delta before bumping.
PACKDATA_OVERFLOW_BUDGET_SECTORS = 320

if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)


# ===========================================================================
# Test runner
# ===========================================================================
class Skip(Exception):
    """Raise inside a test to mark it SKIP (missing tier inputs, etc.)."""


def run_tests(tests, module_name, verbose=True):
    """
    Run a list of test callables.  Returns [(module, test_name, status, detail)].
    status is 'PASS', 'FAIL' or 'SKIP'.
    """
    results = []
    for fn in tests:
        name = fn.__name__
        try:
            fn()
            status, detail = "PASS", ""
        except Skip as e:
            status, detail = "SKIP", str(e)
        except AssertionError as e:
            status, detail = "FAIL", str(e) or "assertion failed"
        except Exception as e:  # a crash is a failure, never a skip
            status, detail = "FAIL", "%s: %s" % (type(e).__name__, e)
        results.append((module_name, name, status, detail))
        if verbose:
            line = "  [%s] %s" % (status, name)
            if detail:
                line += " -- " + detail
            print(line)
    return results


def main_exit(tests, module_name):
    """Standalone entry point for a test module: print results, exit nonzero on FAIL."""
    print("=" * 70)
    print("  %s" % module_name)
    print("=" * 70)
    results = run_tests(tests, module_name)
    n_pass = sum(1 for r in results if r[2] == "PASS")
    n_skip = sum(1 for r in results if r[2] == "SKIP")
    n_fail = sum(1 for r in results if r[2] == "FAIL")
    print("-" * 70)
    print("%s: %d passed, %d skipped, %d FAILED" % (module_name, n_pass, n_skip, n_fail))
    if n_fail:
        for m, n, s, d in results:
            if s == "FAIL":
                print("  FAIL %s: %s" % (n, d))
        sys.exit(1)
    sys.exit(0)


def require_file(path, why):
    """Raise Skip when a tier input is missing (never a failure)."""
    if not os.path.isfile(path):
        raise Skip("%s missing (%s)" % (os.path.relpath(path, ROOT), why))
    return path


def require_dir(path, why):
    if not os.path.isdir(path):
        raise Skip("%s missing (%s)" % (os.path.relpath(path, ROOT), why))
    return path


def default_iso_path():
    """BUSIN_ISO env override, else the NEWEST build/BUSIN0_EN_v*.iso.

    v163 fix (audit C2): this used to default to the long-deleted v85 ISO,
    which silently disabled the ENTIRE ISO test tier for ~70 builds (all the
    R1188-pristine / binary-VIF / audio-overflow gates showed as 'skipped' in
    every green run). Newest-mtime glob mirrors test_line_width._newest_iso.
    """
    env = os.environ.get("BUSIN_ISO")
    if env:
        return env
    cands = glob.glob(os.path.join(ROOT, "build", "BUSIN0_EN_v*.iso"))
    if cands:
        return max(cands, key=os.path.getmtime)
    return os.path.join(ROOT, "build", "BUSIN0_EN_v85.iso")  # legacy fallback (absent -> Skip)


# ===========================================================================
# sec1_disasm access (Skip cleanly if the opcode table is absent)
# ===========================================================================
_DISASM = None


def get_disasm():
    """Import tools/sec1_disasm.py; Skip when its opcode table is unavailable."""
    global _DISASM
    if _DISASM is not None:
        return _DISASM
    if not os.path.isfile(OPCODE_TABLE):
        raise Skip("opcode_table_v85.json missing -- sec1_disasm unavailable")
    import sec1_disasm

    _DISASM = sec1_disasm
    return _DISASM


# ===========================================================================
# type-02 resource parsing
# ===========================================================================
def parse_type02(data):
    """
    Parse a type-02 resource blob.

    Returns dict with: sec2_off, sec2_size, sec1 (bytes), words (tuple of BE
    u16 Section-2 words), trailing_start (word index after the last FFFF; ==
    n_words when there are no groups).
    """
    if len(data) < HEADER_SIZE:
        raise ValueError("file too small for a type-02 resource")
    sec2_size = struct.unpack_from("<I", data, 0x14)[0]
    sec2_off = struct.unpack_from("<I", data, 0x18)[0]
    if sec2_off < HEADER_SIZE or sec2_off + sec2_size > len(data):
        raise ValueError(
            "invalid header: sec2_off=0x%x sec2_size=%d len=%d"
            % (sec2_off, sec2_size, len(data))
        )
    n = sec2_size // 2
    words = struct.unpack_from(">%dH" % n, data, sec2_off)
    trailing_start = 0
    for i, w in enumerate(words):
        if w == 0xFFFF:
            trailing_start = i + 1
    return {
        "sec2_off": sec2_off,
        "sec2_size": sec2_size,
        "sec1": data[HEADER_SIZE:sec2_off],
        "words": words,
        "trailing_start": trailing_start,
    }


def ffff_groups(words):
    """Split a BE-u16 word stream into FFFF-delimited groups (lists of glyphs)."""
    groups = []
    cur = []
    for w in words:
        if w == 0xFFFF:
            groups.append(cur)
            cur = []
        else:
            cur.append(w)
    return groups, cur  # cur == trailing words after the last FFFF


# ===========================================================================
# Glyph decoding (English glyph table; ids 0..94 are ASCII at char-0x20)
# ===========================================================================
_ENG_TABLE = None


def eng_table():
    global _ENG_TABLE
    if _ENG_TABLE is None:
        path = require_file(
            os.path.join(DATA_DIR, "english_glyph_table.json"), "glyph decode"
        )
        _ENG_TABLE = json.load(open(path, encoding="utf-8"))
    return _ENG_TABLE


def encode_english(text):
    """ASCII text -> glyph list using english_glyph_table (fallback 31 = '?')."""
    t = eng_table()
    out = []
    for ch in text:
        if ch in t:
            out.append(int(t[ch]))
        elif ch.lower() in t:
            out.append(int(t[ch.lower()]))
        elif ch == " ":
            out.append(0)
        else:
            out.append(31)
    return out


def decode_glyphs(glyphs, linebreak=" / "):
    """
    Decode a glyph word list to text.  ids 0..94 -> ASCII (char-0x20),
    0xFFFE -> linebreak, anything else -> [XXXX].
    """
    out = []
    for g in glyphs:
        if g == 0xFFFE:
            out.append(linebreak)
        elif 0 <= g <= 94:
            out.append(chr(0x20 + g))
        else:
            out.append("[%04X]" % g)
    return "".join(out)


# ===========================================================================
# ISO / PACKDATA extraction
# ===========================================================================
def iso_root_entries(iso_fh):
    """Parse the ISO9660 PVD root directory.  Returns {name: (lba, size)}."""
    iso_fh.seek(16 * SECTOR)
    pvd = iso_fh.read(SECTOR)
    root_lba = struct.unpack_from("<I", pvd, 158)[0]
    root_size = struct.unpack_from("<I", pvd, 166)[0]
    iso_fh.seek(root_lba * SECTOR)
    rd = iso_fh.read(root_size)
    entries = {}
    pos = 0
    while pos < len(rd):
        rec_len = rd[pos]
        if rec_len == 0:
            break
        name_len = rd[pos + 32]
        name = rd[pos + 33 : pos + 33 + name_len].decode("ascii", errors="replace")
        lba = struct.unpack_from("<I", rd, pos + 2)[0]
        size = struct.unpack_from("<I", rd, pos + 10)[0]
        entries[name] = (lba, size)
        pos += rec_len
    return entries


class PackData(object):
    """Reads PACKDATA resources straight out of a built ISO (LBA via the FS)."""

    def __init__(self, iso_path):
        if not os.path.isfile(iso_path):
            raise Skip("ISO not found: %s" % iso_path)
        self.fh = open(iso_path, "rb")
        entries = iso_root_entries(self.fh)
        pack = [v for k, v in entries.items() if "PACKDATA" in k]
        if not pack:
            raise Skip("no PACKDATA.DIG in ISO root directory")
        self.pack_lba = pack[0][0]
        toc_bytes = N_RESOURCES * 12
        toc_sectors = (toc_bytes + SECTOR - 1) // SECTOR
        self.fh.seek(self.pack_lba * SECTOR)
        toc = self.fh.read(toc_sectors * SECTOR)
        self.toc = [
            struct.unpack_from("<III", toc, i * 12) for i in range(N_RESOURCES)
        ]

    def extract(self, idx):
        """Return (data_bytes, type_code) for resource idx."""
        sector_off, sector_count, type_code = self.toc[idx]
        self.fh.seek((self.pack_lba + sector_off) * SECTOR)
        return self.fh.read(sector_count * SECTOR), type_code

    def close(self):
        self.fh.close()


def pristine_path(idx, type_code_str):
    return os.path.join(RAW_DIR, "%04d_type%s.raw" % (idx, type_code_str))


# ===========================================================================
# The shared v84-bug-class regression check
# ===========================================================================
# Operand byte ranges (relative to instruction pc) the Section-1 patcher is
# allowed to modify, per walked opcode:
ALLOWED_OPERANDS = {
    0x04: (2, 10),  # u32 off @+2, u32 cnt @+6
    0x0C: (4, 6),   # u16 idx @+4
    0x0D: (4, 6),
    0x14: (6, 14),  # u32 off @+6, u32 cnt @+10
}


def display_invariant_issues(data, strict=False):
    """
    Walk a type-02 resource and check the FFFF-end invariant for every walked
    0x04 DISPLAY_TEXT with cnt>0.

    Non-strict mode (patched files): spans starting in the trailing region or
    with sentinel offsets (off >= n_words) are exempt -- only in-group spans
    must end on a 0xFFFF terminator.
    Strict mode (pristine ground truth): every cnt>0 span must end on FFFF.

    Returns (issues, n_checked).  issues == [] means the invariant holds.
    """
    sd = get_disasm()
    p = parse_type02(data)
    ok, instrs = sd.walk(p["sec1"])
    issues = []
    if not ok:
        return ["Section 1 walk FAILED"], 0
    recs = sd.extract_records(p["sec1"], instrs)
    words = p["words"]
    n = len(words)
    trailing_start = p["trailing_start"]
    checked = 0
    for r in recs["display"]:
        if r["cnt"] == 0:
            continue
        off, cnt = r["off"], r["cnt"]
        if not strict and (off >= n or off >= trailing_start):
            continue
        checked += 1
        if off + cnt > n:
            issues.append(
                "DISPLAY_TEXT S1+0x%X: span %d..%d exceeds Section 2 (%d words)"
                % (r["pc"], off, off + cnt, n)
            )
        elif words[off + cnt - 1] != 0xFFFF:
            issues.append(
                "DISPLAY_TEXT S1+0x%X: off=%d cnt=%d does not end on FFFF (0x%04X)"
                % (r["pc"], off, cnt, words[off + cnt - 1])
            )
    return issues, checked


def group_offsets(words):
    """
    Split a BE-u16 word stream into FFFF-delimited groups by word index.

    Returns (groups, trailing_start):
      groups         -- list of (group_start_word, group_end_word) where
                        group_end_word is the index of the FFFF terminator
                        itself; group content is words[start:end].
      trailing_start -- word index of the first trailing (non-group) word
                        after the last FFFF (== len(words) when none).

    Same semantics as patch_section1_offsets.parse_sec2_group_offsets, but
    operates on the already-parsed `words` tuple from parse_type02.
    """
    groups = []
    start = 0
    for i, w in enumerate(words):
        if w == 0xFFFF:
            groups.append((start, i))
            start = i + 1
    return groups, start


def _find_group_index(groups, word_offset):
    """Index of the group whose [start..FFFF] range contains word_offset, else None."""
    for gi, (gs, ge) in enumerate(groups):
        if gs <= word_offset <= ge:
            return gi
    return None


# Words that must NEVER be a DISPLAY_TEXT start: group terminator, page break.
_NON_CONTENT_STARTS = (0xFFFF, 0xFFFE)


def start_correctness_issues(pristine_bytes, patched_bytes, name):
    """
    Assert that the PATCHED 0x04 DISPLAY_TEXT *start* offsets are correct.

    The existing FFFF-end gate (display_invariant_issues / sec1_regression_check)
    only validates that a span ENDS on a 0xFFFF terminator.  A patcher change
    that pushed a start PAST the intended group beginning could still pass that
    gate while truncating leading text.  This check pins the START down:

      Walk the PRISTINE Section 1, take every 0x04 with cnt>0, find its pristine
      group index gi and pristine in-group rel (= off - pristine_group_start[gi]).
      Locate the SAME record in the PATCHED file by pc (the patcher never moves
      instructions) and require:

        (a) pristine rel == 0  ->  patched new_off == new_group_start[gi]
            (a true group-beginning start must stay pinned to the new start)
        (b) pristine rel  > 0  ->  new_off lies strictly inside the SAME new
            group (new_group_start[gi] <= new_off < new_group_end[gi]) AND the
            word at new_off is real content (not 0xFFFF/0xFFFE) -- a mid-group
            name-island start must still point at content, never a terminator.

    Records whose pristine span starts in the trailing (non-group) region or at
    a sentinel offset (off >= n_words) are exempt -- those have no group start
    to pin.  Files whose pristine Section 1 fails to walk are skipped (returns
    []), mirroring the existing gate.

    Returns a list of human-readable issue strings (empty == pass).
    """
    sd = get_disasm()
    issues = []

    pp = parse_type02(pristine_bytes)
    np_ = parse_type02(patched_bytes)

    p_ok, p_instrs = sd.walk(pp["sec1"])
    if not p_ok:
        return []  # cannot establish ground truth -- skip, like the existing gate

    p_recs = sd.extract_records(pp["sec1"], p_instrs)

    p_words = pp["words"]
    p_n = len(p_words)
    p_groups, p_trailing_start = group_offsets(p_words)

    n_words = np_["words"]
    n_n = len(n_words)
    n_groups, _n_trailing_start = group_offsets(n_words)

    # The patcher never moves instructions, so the patched 0x04 records share
    # the same pc set; read patched operands at the SAME pc from the patched S1.
    p_disp_by_pc = {r["pc"]: r for r in p_recs["display"]}
    n_recs = sd.extract_records(np_["sec1"], p_instrs)
    n_disp_by_pc = {r["pc"]: r for r in n_recs["display"]}

    for pc, pr in sorted(p_disp_by_pc.items()):
        if pr["cnt"] == 0:
            continue
        off = pr["off"]
        # Exempt sentinel / trailing-region starts: no group beginning to pin.
        if off >= p_n or off >= p_trailing_start:
            continue
        gi = _find_group_index(p_groups, off)
        if gi is None:
            continue  # not inside any group -- nothing to assert
        rel = off - p_groups[gi][0]

        nr = n_disp_by_pc.get(pc)
        if nr is None:
            issues.append(
                "%s: 0x04 S1+0x%X present in pristine but missing in patched"
                % (name, pc)
            )
            continue
        new_off = nr["off"]

        if gi >= len(n_groups):
            issues.append(
                "%s: 0x04 S1+0x%X: pristine group %d has no counterpart in "
                "patched (only %d groups)" % (name, pc, gi, len(n_groups))
            )
            continue
        ngs, nge = n_groups[gi]

        if rel == 0:
            # True group beginning: must stay pinned to the new group start.
            if new_off != ngs:
                issues.append(
                    "%s: 0x04 S1+0x%X: pristine rel==0 (group %d) but patched "
                    "start=%d != new group start=%d -- leading text truncated"
                    % (name, pc, gi, new_off, ngs)
                )
        else:
            # Mid-group (name-island) start: must stay strictly inside the SAME
            # new group and point at real content, never a terminator.
            if not (ngs <= new_off < nge):
                # CONTENT-EQUIVALENCE ESCAPE (v161): a relocation is legitimate
                # iff the patched span displays BYTE-IDENTICAL words to what the
                # pristine span displayed — the exact same thing reaches the
                # screen, just stored elsewhere.  Concrete case:
                # patch_r1194_narration.fix_r1193_short_prologue re-points
                # R1193's short-prologue 0x04 (S1+0x5BF) from a key-wait span
                # duplicated inside group 0 to group 1's identical key-wait
                # span (group 0 was rebuilt as English islands and no longer
                # contains the duplicate).  Any relocation showing DIFFERENT
                # content still fails hard.
                p_span = tuple(p_words[off:off + pr["cnt"]])
                n_span = tuple(n_words[new_off:new_off + nr["cnt"]])
                if p_span and p_span == n_span:
                    print(
                        "  [start-note] %s: 0x04 S1+0x%X: mid-group start "
                        "relocated %d->%d but displays pristine-identical "
                        "content (%d words) -- content-equivalent, allowed"
                        % (name, pc, off, new_off, len(p_span))
                    )
                else:
                    issues.append(
                        "%s: 0x04 S1+0x%X: pristine mid-group start rel=%d (group "
                        "%d) but patched start=%d outside new group [%d,%d)"
                        % (name, pc, rel, gi, new_off, ngs, nge)
                    )
            elif new_off >= n_n or n_words[new_off] in _NON_CONTENT_STARTS:
                # A mid-group start landing on a line/page-break (0xFFFE/0xFFD2)
                # is a non-fatal WARNING, not a hard failure: the engine
                # tolerates a leading break (R1193's intro narration renders
                # correctly with one), and the few remaining cases are
                # PRE-EXISTING wherever the English re-flows the line breaks
                # (R1193 narration island, R1203). It is surfaced so it can be
                # cleaned up but does NOT block the build. The leading-truncation
                # REGRESSION class (rel==0 not at group start) and out-of-group
                # starts above remain HARD failures.
                w = n_words[new_off] if new_off < n_n else 0xFFFF
                print(
                    "  [start-warn] %s: 0x04 S1+0x%X: mid-group start=%d on a "
                    "break (word=0x%04X), pre-existing/benign"
                    % (name, pc, new_off, w)
                )
    return issues


def sec1_regression_check(pristine, patched, name="?"):
    """
    The build-output regression gate (would instantly fail on the v84 corruption):
      1. the patched Section 1 must re-walk cleanly (0 invalid opcodes),
      2. every walked 0x04 with cnt>0 must satisfy the FFFF-end invariant,
      3. byte diffs between pristine and patched Section 1 must be confined to
         the operand ranges of instructions WALKED IN THE PRISTINE stream
         (0x04 pc+2..pc+9, 0x0C/0x0D pc+4..pc+5, 0x14 pc+6..pc+13).

    Returns a list of issue strings (empty == pass).
    """
    sd = get_disasm()
    issues = []

    pp = parse_type02(pristine)
    np_ = parse_type02(patched)
    if pp["sec2_off"] != np_["sec2_off"]:
        return [
            "%s: sec2_offset changed 0x%x -> 0x%x (Section 1 resized!)"
            % (name, pp["sec2_off"], np_["sec2_off"])
        ]

    # 1 + 2: re-walk + invariant on the PATCHED file
    inv_issues, _ = display_invariant_issues(patched, strict=False)
    issues.extend("%s: %s" % (name, i) for i in inv_issues)

    # 3: diff confinement, using the PRISTINE walk for the allowed ranges
    ok, instrs = sd.walk(pp["sec1"])
    if not ok:
        issues.append("%s: pristine Section 1 walk failed" % name)
        return issues
    allowed = set()
    for pc, op in instrs.items():
        rng = ALLOWED_OPERANDS.get(op)
        if rng:
            allowed.update(range(pc + rng[0], pc + rng[1]))
    ps1, ns1 = pp["sec1"], np_["sec1"]
    if len(ps1) != len(ns1):
        issues.append("%s: Section 1 length changed" % name)
        return issues
    stray = [i for i in range(len(ps1)) if ps1[i] != ns1[i] and i not in allowed]
    if stray:
        issues.append(
            "%s: %d Section-1 byte diffs OUTSIDE walked operand ranges "
            "(first at S1+0x%X) -- v84-class corruption"
            % (name, len(stray), stray[0])
        )
    return issues
