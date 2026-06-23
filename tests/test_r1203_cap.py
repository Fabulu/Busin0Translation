#!/usr/bin/env python3
"""
test_r1203_cap.py -- [G6] R1203 Section-2 cap RE-DERIVATION gate.

WHY THIS EXISTS
---------------
R1203's Section-2 per-group word offsets are u16, so the whole Section 2 must
stay <= 65,535 words.  The English translation is large enough that the upper
groups must be DROPPED to stay under the limit.  The exact cap depends on the
ENCODING (how many 0xFFFE line-break words each group costs), so it MUST be
re-derived whenever the wrap path changes -- the T4 px-wrap (build_v9.wrap_px)
packs more glyphs per line => fewer 0xFFFE => a SMALLER Section 2 => the cap can
only rise vs the old char-wrap literal (1016).

This test NEVER asserts a literal cap (the project's no-stale-constant rule).  It:
  1. RE-DERIVES the cap by binary-searching the REAL inject_and_patch output
     word count (header 0x14 // 2), exactly as build_v9.derive_r1203_cap does,
     from an encoded dict it rebuilds the SAME way the build does (choice groups
     unwrapped; dialogue -> wrap_px @324px; else wrap_type2_text; glyphs + 0xFFFE
     only, NEVER 0xFFD2).  It then asserts the derived cap keeps Section 2 <=
     65,535 AND the next group over the cap OVERFLOWS (a genuine boundary).
  2. Asserts build_v9.py actually CALLS derive_r1203_cap( and no longer applies a
     hardcoded `R1203_MAX_GROUP = <int>` literal to the filter.

The build_v9 wrap helpers are EXEC-ISOLATED from build_v9 (build_v9.py runs a
full ISO build at import -- os.chdir + os.system, no __main__ guard) so they are
pulled from source by name, mirroring build/qa_corpus_dryrun.py.

Skips cleanly when the inputs (1203_type02.raw / opcode table / batch jsons) are
absent.
"""

import glob
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, Skip  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "tools"))

R1203 = 1203
S2_LIMIT = 65535
SKIP_STRUCTURAL = {(1197, 1)}
SKIP_PREFIXES = ("[DATA]", "[LAYOUT]", "[BINARY]", "[MAP]",
                 "[SYSTEM]", "[GLYPH", "[DEBUG]")


# ---- pull the wrap helpers out of build_v9 WITHOUT running the build ---------
def _load_wrap_helpers(enc):
    """Extract DIALOGUE_BOX_PX, TYPE2_WRAP_WIDTH and the pure wrap defs from
    build_v9.py source (it cannot be imported -- it builds at import time).

    `enc` (the char->glyph-id callable) is bound into the exec namespace so
    wrap_px / _wrap_line_px can call glyph_metrics.px_width(seg, enc) exactly as
    they do in build_v9 (module-level enc).  glyph_metrics widths are the shared
    SoT -- NEVER a recompute."""
    src = open(os.path.join(ROOT, "build", "build_v9.py"), encoding="utf-8").read()
    import glyph_metrics
    ns = {"glyph_metrics": glyph_metrics, "enc": enc}
    for cm, name in ((r"^TYPE2_WRAP_WIDTH\s*=\s*(\d+)", "TYPE2_WRAP_WIDTH"),
                     (r"^DIALOGUE_BOX_PX\s*=\s*(\d+)", "DIALOGUE_BOX_PX")):
        m = re.search(cm, src, re.M)
        assert m, "%s not found in build_v9.py" % name
        ns[name] = int(m.group(1))
    for fn in ("_wrap_line", "wrap_type2_text", "reflow_dialogue",
               "_wrap_line_px", "wrap_px"):
        mm = re.search(r"^def %s\(.*?(?=^\S|\Z)" % fn, src, re.M | re.S)
        assert mm, "def %s not found in build_v9.py" % fn
        exec(compile(mm.group(0), "build_v9:%s" % fn, "exec"), ns)
    return ns


# enc family identical to build_v9 (char-32; English fallback 31, space->table)
def _make_enc():
    tbl_path = os.path.join(ROOT, "data", "english_glyph_table.json")
    tbl = json.load(open(tbl_path, encoding="utf-8"))

    def enc(ch):
        if ch in tbl:
            return int(tbl[ch])
        if ch.lower() in tbl:
            return int(tbl[ch.lower()])
        return 31
    return enc


def _src_uses_derived_cap():
    src = open(os.path.join(ROOT, "build", "build_v9.py"), encoding="utf-8").read()
    return src


def _build_r1203_encoded(ns, enc):
    """Rebuild R1203's encoded_trans EXACTLY as build_v9's Step-4 loop does."""
    from patch_section1_offsets import group_choice_markers  # noqa: F401
    from dialogue_classifier import build_dialogue_map

    # Load translations with the same filters as build_v9 (all_trans).
    msg_trans = {}
    batches = sorted(glob.glob(os.path.join(ROOT, "data", "type2_translated",
                                            "batch_*.json")))
    if not batches:
        raise Skip("no data/type2_translated/batch_*.json")
    for fn in batches:
        for e in json.load(open(fn, encoding="utf-8")):
            if e.get("resource") != R1203:
                continue
            mi = e.get("msg_index")
            if mi is None:
                continue
            if (R1203, mi) in SKIP_STRUCTURAL:
                continue
            en = e.get("english", "")
            if not en or any(en.startswith(p) for p in SKIP_PREFIXES):
                continue
            if any(ord(c) > 127 for c in en):
                continue
            msg_trans[mi] = en
    if not msg_trans:
        raise Skip("no translatable R1203 groups in the corpus")

    # choice groups (pristine FFC0..FFCF) + dialogue map -- same primitives.
    choice_groups = _load_pristine_choice_groups(R1203)
    dialogue_groups = build_dialogue_map(R1203)

    wrap_px = ns["wrap_px"]
    wrap_type2_text = ns["wrap_type2_text"]
    box_px = ns["DIALOGUE_BOX_PX"]

    encoded = {}
    for mi, en_text in msg_trans.items():
        if mi not in choice_groups:
            if mi in dialogue_groups:
                en_text = wrap_px(en_text, box_px)
            else:
                en_text = wrap_type2_text(en_text)
        glyphs = []
        parts = [seg for page in en_text.split(" // ")
                 for seg in page.split(" / ")]
        for pi, part in enumerate(parts):
            if pi > 0:
                glyphs.append(0xFFFE)
            for ch in part:
                glyphs.append(enc(ch))
        # NEVER 0xFFD2 (v97 colour-code rule) -- assert it for the gate.
        assert 0xFFD2 not in glyphs, "encoder emitted forbidden 0xFFD2 (v97)"
        encoded[mi] = glyphs
    return encoded


def _load_pristine_choice_groups(res_idx):
    """Mirror build_v9.load_pristine_choice_groups for R1203."""
    from patch_section1_offsets import group_choice_markers
    raw = os.path.join(ROOT, "extracted", "packdata_raw",
                       "%04d_type02.raw" % res_idx)
    if not os.path.isfile(raw):
        return set()
    try:
        data = open(raw, "rb").read()
        sec2_size = struct.unpack_from("<I", data, 0x14)[0]
        sec2_off = struct.unpack_from("<I", data, 0x18)[0]
        sec2 = data[sec2_off:sec2_off + sec2_size]
        n = len(sec2) // 2
        words = [struct.unpack_from(">H", sec2, i * 2)[0] for i in range(n)]
        choice = set()
        gi = 0
        start = 0
        for i in range(n):
            if words[i] == 0xFFFF:
                if group_choice_markers(words[start:i]):
                    choice.add(gi)
                gi += 1
                start = i + 1
        return choice
    except Exception:
        return set()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_r1203_cap_under_65535():
    """RE-DERIVE the R1203 cap and prove it is a genuine boundary: the derived
    cap keeps Section 2 <= 65,535 words AND the next group over it overflows."""
    raw = os.path.join(ROOT, "extracted", "packdata_raw", "1203_type02.raw")
    if not os.path.isfile(raw):
        raise Skip("extracted/packdata_raw/1203_type02.raw absent")
    try:
        from patch_section1_offsets import inject_and_patch
    except Exception as e:  # opcode table / disasm deps absent
        raise Skip("patch_section1_offsets import failed: %s" % e)

    enc = _make_enc()
    ns = _load_wrap_helpers(enc)
    encoded = _build_r1203_encoded(ns, enc)

    import tempfile
    out_dir = tempfile.mkdtemp(prefix="r1203cap_")
    raw_dir = os.path.join(ROOT, "extracted", "packdata_raw")

    def words_at(cap):
        capped = {mi: g for mi, g in encoded.items() if mi <= cap}
        res = inject_and_patch(R1203, capped, raw_dir, out_dir)
        if res[0] is None:
            raise Skip("inject_and_patch could not patch R1203: %s" % res[1])
        out = open(os.path.join(out_dir, res[0]), "rb").read()
        return struct.unpack_from("<I", out, 0x14)[0] // 2

    keys = sorted(encoded)
    # binary search highest cap whose REAL injected word count <= limit
    lo, hi, best = 0, len(keys) - 1, keys[0]
    while lo <= hi:
        mid = (lo + hi) // 2
        if words_at(keys[mid]) <= S2_LIMIT:
            best = keys[mid]
            lo = mid + 1
        else:
            hi = mid - 1

    w_best = words_at(best)
    assert w_best <= S2_LIMIT, (
        "derived R1203 cap group %d still overflows Section 2: %d > %d words"
        % (best, w_best, S2_LIMIT)
    )
    # Genuine-boundary check: the next group over the cap must overflow (unless
    # the cap is already the last group -- then the whole corpus fits).
    over = [k for k in keys if k > best]
    if over:
        w_next = words_at(over[0])
        assert w_next > S2_LIMIT, (
            "R1203 cap group %d is NOT a true boundary: next group %d gives %d "
            "<= %d words (cap should be higher)"
            % (best, over[0], w_next, S2_LIMIT)
        )

    print("  R1203 re-derived cap = group %d (%d words, next overflows)"
          % (best, w_best))


def test_build_uses_derived_cap():
    """The build must CALL derive_r1203_cap( and must NOT apply a hardcoded
    R1203_MAX_GROUP literal to the encoded_trans filter (no stale constant)."""
    src = _src_uses_derived_cap()
    assert "derive_r1203_cap(" in src, (
        "build_v9.py no longer calls derive_r1203_cap( -- the R1203 cap must be "
        "re-derived, never a stale literal"
    )
    # No `R1203_MAX_GROUP = <int literal>` assignment may remain (the cap must be
    # produced by derive_r1203_cap, whose result is assigned WITHOUT an int RHS).
    bad = re.search(r"^\s*R1203_MAX_GROUP\s*=\s*\d", src, re.M)
    assert not bad, (
        "build_v9.py still assigns a hardcoded R1203_MAX_GROUP integer literal: "
        "%r -- the cap must come from derive_r1203_cap()" % bad.group(0).strip()
    )


TESTS = [
    test_r1203_cap_under_65535,
    test_build_uses_derived_cap,
]

if __name__ == "__main__":
    from _helpers import main_exit

    main_exit(TESTS, "test_r1203_cap")
