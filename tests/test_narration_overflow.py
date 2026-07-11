#!/usr/bin/env python3
"""
test_narration_overflow.py -- build gate against narration WINDOW OVERFLOW.

Background
----------
Narration windows draw all of a group's wrapped lines continuously (no
pagination -- 0xFFD2 is a colour code in this engine, not a page break, see the
v97 render-truth note).  The window holds roughly 5-6 lines; a group whose
English wraps to >= 7 lines spills past the bottom of the frame.

This gate reproduces build_v9.py's Step-4 narration path EXACTLY:
  * it takes, for every translated type-02 resource that is present in the BUILT
    output (build/packdata_resources/*_type02.raw), the WINNING English string
    the build encodes -- the last-sorted data/type2_translated/batch_*.json entry
    for that (resource, msg_index), filtered byte-identically to build_v9.py
    (skip [DATA]/[LAYOUT]/... sentinels and any non-ASCII/untranslated group);
  * it classifies each group with the build's OWN classifier
    (dialogue_classifier.build_narration_map / build_narration_pad_map) and
    applies the same routing excludes the build applies (SKIP_STRUCTURAL_GROUPS,
    DIALOGUE_WRAP_EXCLUDE, NARR_PAD_EXCLUDE, DIALOGUE_WRAP_FORCE);
  * it re-wraps each TRUE narration group with the EXACT narration wrap
    (NARRATION_BOX_PX = 360, collapsing " // " and " / " into one continuous
    block, glyph_metrics.px_width) -- byte-identical to the scout analyzer and to
    build_v9.py's wrap_px(collapse=True) narration branch.

Why the WINNING SOURCE string and not a decode of the built glyph stream:
  name-island ("W1-NARR", build_narration_pad_map) narration groups are stored
  in the built Section 2 as [name-island prefix][wrapped body] -- the prefix is
  drawn SEPARATELY as a nameplate, NOT stacked in the narration window.  Decoding
  the raw group would concatenate prefix + body and over-count lines (e.g. R1206
  g709 reads 18 raw "lines" but renders a 12-line body).  Wrapping the winning
  source string measures exactly the body that stacks in the window -- the same
  quantity the scout analyzer validated.  Reading the source string also lets the
  gate see a text edit immediately (before the raw is rebuilt), while still being
  scoped to the resources the current build actually shipped.

HARD-FAILS if any narration group wraps to >= 7 lines, EXCEPT the shrink-only
OVERFLOW_ALLOWLIST below.  The allowlist may only ever SHRINK: a NEW >= 7-line
narration group that is not already grandfathered in fails the build (same
discipline as test_stale_display_offsets' KNOWN_CHOICE_EVENTS pin).  A group at
exactly 6 lines is WARNED (printed) but does not fail.

Skips cleanly when build/packdata_resources is absent (build-tier test).
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, PACKDATA_RES_DIR, DATA_DIR, Skip, main_exit, require_dir

# build_v9.py's own classifier + the px metrics live under tools/ and build/.
if os.path.join(ROOT, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "tools"))
if os.path.join(ROOT, "build") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "build"))

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
NARRATION_BOX_PX = 360  # build_v9.py line 346
OVERFLOW_LINES = 7      # >= this many wrapped lines HARD-FAILS
WARN_LINES = 6          # == this many wrapped lines WARNS (does not fail)

# ---------------------------------------------------------------------------
# Shrink-only allowlist of grandfathered >= 7-line narration groups.
#
# DISCIPLINE (identical to test_stale_display_offsets): this set may only ever
# SHRINK.  A narration group that wraps to >= OVERFLOW_LINES and is NOT listed
# here fails the gate.  It is seeded EMPTY -- every historical hard offender
# (R1355 g39/41/42/53/54, R1206 g709, R1213 g4, R1210 g101, R1203 g451) was
# condensed below the threshold in data/type2_translated/batch_zz_narration_fix.json.
# Only add a (res, gi) here if it is genuinely impossible to condense, and delete
# entries as they are fixed -- never grow this list to silence a new regression.
# ---------------------------------------------------------------------------
OVERFLOW_ALLOWLIST = set()  # type: set

# ---------------------------------------------------------------------------
# Routing exclusion sets -- byte-identical to analyze.py / build_v9.py.
# ---------------------------------------------------------------------------
SKIP_STRUCTURAL_GROUPS = {(1197, 1)}
DIALOGUE_WRAP_EXCLUDE = {(1194, 0), (1196, 810), (1200, 64),
                         (1212, 1), (1213, 1), (1353, 1)}
NARR_PAD_EXCLUDE = {(1197, 1), (1212, 1), (1213, 1), (1353, 1)}


def _dialogue_wrap_force():
    p = os.path.join(DATA_DIR, "dialogue_wrap_force.json")
    if not os.path.isfile(p):
        return set()
    with open(p, encoding="utf-8") as f:
        return {tuple(e) for e in json.load(f)["force_dialogue_wrap"]}


# ---------------------------------------------------------------------------
# enc + the EXACT narration wrap (copied VERBATIM from the scout's analyze.py,
# which itself mirrors build_v9.py's wrap_px(collapse=True)).  Do NOT invent a
# different wrap here.
# ---------------------------------------------------------------------------
_TABLE = None


def _table():
    global _TABLE
    if _TABLE is None:
        with open(os.path.join(DATA_DIR, "english_glyph_table.json"),
                  encoding="utf-8") as f:
            _TABLE = json.load(f)
    return _TABLE


def enc(ch):
    t = _table()
    if ch in t:
        return t[ch]
    if ch.lower() in t:
        return t[ch.lower()]
    return 31


def _wrap_line_px(seg, box_px, px_width):
    words = seg.split(' ')
    lines, cur = [], ''
    for w in words:
        cand = w if not cur else cur + ' ' + w
        if cur and px_width(cand, enc) > box_px:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines or ['']


def wrap_px_collapse(text, px_width, box_px=NARRATION_BOX_PX):
    flat = ' '.join(s.strip()
                    for s in text.replace(' // ', ' / ').split(' / ')
                    if s.strip())
    return _wrap_line_px(flat, box_px, px_width)


# ---------------------------------------------------------------------------
# Winning-English map: the last-sorted batch entry per (resource, msg_index),
# filtered byte-identically to build_v9.py's translation loader (analyze.py:49).
# ---------------------------------------------------------------------------
def _winning_translations():
    all_trans = {}
    for fn in sorted(glob.glob(os.path.join(DATA_DIR, "type2_translated",
                                            "batch_*.json"))):
        try:
            d = json.load(open(fn, encoding="utf-8"))
        except Exception:
            continue
        for e in d:
            r = e.get("resource")
            mi = e.get("msg_index")
            if r is None or mi is None:
                continue
            if (r, mi) in SKIP_STRUCTURAL_GROUPS:
                continue
            en = e.get("english", "")
            if not en:
                continue
            if en.startswith(("[DATA]", "[LAYOUT]", "[BINARY]", "[MAP]",
                              "[SYSTEM]", "[GLYPH", "[DEBUG]")):
                continue
            if any(ord(c) > 127 for c in en):
                continue
            all_trans.setdefault(r, {})[mi] = en
    return all_trans


def _built_resources():
    """type-02 resource ids that the current build actually shipped."""
    out = set()
    for p in glob.glob(os.path.join(PACKDATA_RES_DIR, "*_type02.raw")):
        try:
            out.add(int(os.path.basename(p).split("_")[0]))
        except ValueError:
            continue
    return out


def _scan_overflows():
    """Return [(res, gi, nlines)] for every TRUE narration group whose winning
    English wraps at 360px, restricted to resources present in the build."""
    require_dir(PACKDATA_RES_DIR, "run a build first")
    import glyph_metrics
    from dialogue_classifier import build_narration_map, build_narration_pad_map

    px_width = glyph_metrics.px_width
    force = _dialogue_wrap_force()
    all_trans = _winning_translations()
    built = _built_resources()
    if not built:
        raise Skip("no build/packdata_resources/*_type02.raw (run a build first)")

    results = []
    for res in sorted(built & set(all_trans)):
        msg = all_trans[res]
        try:
            narr = build_narration_map(res)
            pad = build_narration_pad_map(res)
        except Exception:
            continue
        for gi, en in msg.items():
            if (res, gi) in DIALOGUE_WRAP_EXCLUDE:
                continue
            if (res, gi) in force:
                continue
            is_narr = gi in narr
            is_pad = (gi in pad) and ((res, gi) not in NARR_PAD_EXCLUDE)
            if not (is_narr or is_pad):
                continue
            nlines = len(wrap_px_collapse(en, px_width))
            results.append((res, gi, nlines))
    return results


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_no_narration_overflow():
    """No TRUE narration group may wrap to >= 7 lines, except the shrink-only
    OVERFLOW_ALLOWLIST (seeded empty)."""
    results = _scan_overflows()
    assert results, "no narration groups were scanned -- harness broken"

    overflow = [(r, g, n) for (r, g, n) in results if n >= OVERFLOW_LINES]
    warn = sorted((r, g, n) for (r, g, n) in results if n == WARN_LINES)

    for r, g, n in warn:
        print("  [warn] R%d g%d wraps to %d lines (near the ~5-6 line window)"
              % (r, g, n))

    unexpected = [(r, g, n) for (r, g, n) in overflow
                  if (r, g) not in OVERFLOW_ALLOWLIST]
    grandfathered = [(r, g, n) for (r, g, n) in overflow
                     if (r, g) in OVERFLOW_ALLOWLIST]
    for r, g, n in grandfathered:
        print("  [allowlisted] R%d g%d wraps to %d lines (grandfathered)"
              % (r, g, n))

    assert not unexpected, (
        "narration WINDOW OVERFLOW (>= %d wrapped lines) in %d group(s): %s -- "
        "condense the English (data/type2_translated/batch_zz_narration_fix.json) "
        "or, only if genuinely impossible, add to OVERFLOW_ALLOWLIST"
        % (OVERFLOW_LINES, len(unexpected),
           ["R%d g%d=%d" % (r, g, n) for (r, g, n) in
            sorted(unexpected, key=lambda x: (-x[2], x[0], x[1]))])
    )
    print("  %d narration groups scanned: 0 unexpected window overflows "
          "(>= %d lines); %d warned at %d lines"
          % (len(results), OVERFLOW_LINES, len(warn), WARN_LINES))


def test_allowlist_is_shrink_only():
    """Every entry in OVERFLOW_ALLOWLIST must STILL be a real >= 7-line overflow.
    A grandfathered entry that has since dropped below the threshold (or vanished)
    must be REMOVED -- the allowlist may only shrink."""
    if not OVERFLOW_ALLOWLIST:
        print("  OVERFLOW_ALLOWLIST empty -- nothing to verify")
        return
    results = _scan_overflows()
    live = {(r, g) for (r, g, n) in results if n >= OVERFLOW_LINES}
    stale = sorted(OVERFLOW_ALLOWLIST - live)
    assert not stale, (
        "OVERFLOW_ALLOWLIST has %d stale entry(ies) (remove them -- the allowlist "
        "may only shrink): %s"
        % (len(stale), ["R%d g%d" % (r, g) for (r, g) in stale])
    )
    print("  OVERFLOW_ALLOWLIST: %d entries, all still overflowing"
          % len(OVERFLOW_ALLOWLIST))


TESTS = [
    test_no_narration_overflow,
    test_allowlist_is_shrink_only,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_narration_overflow")
