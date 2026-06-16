#!/usr/bin/env python3
"""
test_no_auto_pagebreak.py -- gate against SPURIOUS 0xFFD2 page breaks in
injected type-2 text (the v90 narration/dialogue fat-gap regression).

THE BUG THIS CATCHES (v90 fat-gap / over-wide / both-edge clip)
---------------------------------------------------------------
build_v9 Step 4 used to AUTO-insert a 0xFFD2 PAGE break after every 3rd " / "
line break (`if line_count >= 3: glyphs.append(0xFFD2)`).  The centered-narration
renderer (e.g. the R1196 intro: "No one was in sight. Not a sound, not even the
wind"; "A man approached, staggering on his feet"; the Shady Man dialogue) does
NOT paginate on a mid-message 0xFFD2 -- it draws the following text INLINE on the
same baseline, producing the fat internal gap, the over-wide both-edge clipping,
and the dropped trailing word the user saw.  Pristine JP narration groups use
ONLY 0xFFFE line breaks and never a mid-message 0xFFD2.

THE RULE
--------
The ONLY legitimate source of a 0xFFD2 in an injected-English group is an authored
" // " page break in the translation JSON.  So for every translated, non-choice
type-02 group, the number of 0xFFD2 words in the BUILT group must EQUAL the number
of " // " markers in its source english string.  An auto-inserted page break makes
actual > expected and trips this gate; legitimately authored " // " breaks are
fully accounted for, so there are no false positives.

This complements test_line_width (which gates per-line WIDTH).  Width alone did not
catch this bug: the merged over-wide line is the renderer's reaction to an
unhonored page break, not a too-wide encoded line -- the encoded segments are all
<=16 glyphs.  Only counting the spurious 0xFFD2 catches it.

TIER
----
  TIER-2 : build/patched_type2/*.raw cross-checked against data/type2_translated
           (Skip if either is absent -- run a build first).
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (
    PATCHED_TYPE2_DIR,
    ROOT,
    Skip,
    decode_glyphs,
    group_offsets,
    parse_type02,
    require_dir,
)

PAGE_BREAK = 0xFFD2
CHOICE_LO = 0xFFC0
CHOICE_HI = 0xFFCF

# Visible-glyph boundary (every control/marker word is >= 0xFB00) and the
# ASCII-English ceiling -- mirrors test_line_width.  We gate ONLY groups whose
# visible glyphs are all ASCII English: those are the ones build_v9 re-encoded
# from a translation (the regression surface).  Untranslated groups still carry
# Japanese glyphs AND their legitimate pristine 0xFFD2 page breaks -- exempt.
CONTROL_FLOOR = 0xFB00
ENGLISH_GLYPH_HI = 94

# Narration groups the user reported broken -- listed only to enrich the failure
# message; the general oracle below already covers them (their source has no
# " // " so expected == 0).
KNOWN_NARRATION = {1196: (569, 575, 577, 616)}


def _load_translations():
    """Mirror build_v9's batch loader: {resource: {msg_index: english}}.

    Same filters build_v9 applies (skip empty, [DATA]/[MAP]/... markers, and any
    entry containing non-ASCII -- those are untranslated and not re-encoded)."""
    trans = {}
    for fn in sorted(glob.glob(os.path.join(ROOT, "data", "type2_translated",
                                            "batch_*.json"))):
        try:
            d = json.load(open(fn, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, list):
            continue
        for e in d:
            if not isinstance(e, dict) or "resource" not in e or "msg_index" not in e:
                continue
            en = e.get("english", "")
            if not en:
                continue
            if en[:6] in ("[DATA]", "[MAP]", "[SYST", "[GLYP", "[DEBU", "[LAYO",
                          "[BINA"):
                continue
            if any(ord(c) > 127 for c in en):
                continue
            trans.setdefault(e["resource"], {})[e["msg_index"]] = en
    return trans


def _is_choice_group(group):
    return any(CHOICE_LO <= w <= CHOICE_HI for w in group)


def _offenders():
    trans = _load_translations()
    offenders = []
    checked = 0
    for path in sorted(glob.glob(os.path.join(PATCHED_TYPE2_DIR, "*.raw"))):
        res = int(os.path.basename(path)[:4])
        if res not in trans:
            continue
        try:
            words = parse_type02(open(path, "rb").read())["words"]
            groups, _trailing = group_offsets(words)
        except Exception:
            continue
        for mi, en in trans[res].items():
            if mi >= len(groups):
                continue  # capped/overflow group (e.g. R1203) -- not injected
            gs, ge = groups[mi]
            group = words[gs:ge]
            if _is_choice_group(group):
                continue  # choice page breaks are re-segmented separately
            # Only gate re-encoded ALL-ENGLISH groups; an untranslated group keeps
            # Japanese glyphs and its legitimate pristine 0xFFD2 breaks.
            visible = [w for w in group if w < CONTROL_FLOOR]
            if not visible or any(w > ENGLISH_GLYPH_HI for w in visible):
                continue
            # v97: auto-pagination was REVERTED (0xFFD2 is a color code, not a page
            # break).  So NO injected group may gain a 0xFFD2 beyond its authored
            # " // " — this gate is back to guarding ALL groups (narration AND
            # dialogue) against a spurious 0xFFD2.
            checked += 1
            # The bug's page break is always INTERIOR (text on both sides).
            # inject_and_patch preserves the pristine group's leading/trailing
            # control run (incl. a real between-message 0xFFD2 and the 0xFFFF
            # terminator), so strip those runs before counting -- only an
            # authored " // " may produce an interior 0xFFD2.
            lo, hi = 0, len(group)
            while lo < hi and group[lo] >= CONTROL_FLOOR:
                lo += 1
            while hi > lo and group[hi - 1] >= CONTROL_FLOOR:
                hi -= 1
            interior = group[lo:hi]
            expected = en.count(" // ")
            actual = sum(1 for w in interior if w == PAGE_BREAK)
            if actual > expected:
                offenders.append((res, mi, actual, expected,
                                  decode_glyphs(group).strip()[:56]))
    return offenders, checked


def test_no_spurious_pagebreak():
    """No injected-English group may carry more 0xFFD2 page breaks than its source
    english authored via " // ".  Catches the v90 auto-3-line-page-break that the
    narration renderer drew as a fat inline gap."""
    require_dir(PATCHED_TYPE2_DIR, "run a build first (Step 4 type-02 injection)")
    offenders, checked = _offenders()
    if checked == 0:
        raise Skip("no translated type-02 groups in build/patched_type2 -- build first")
    if offenders:
        offenders.sort(key=lambda o: o[2] - o[3], reverse=True)
        worst = "; ".join(
            "R%d g%d FFD2=%d (authored %d) %r" % (r, g, a, e, t)
            for (r, g, a, e, t) in offenders[:12]
        )
        known = ", ".join(
            "R%d g%d" % (r, g)
            for r, gs in KNOWN_NARRATION.items() for g in gs
            if any(o[0] == r and o[1] == g for o in offenders)
        )
        raise AssertionError(
            "%d injected group(s) have AUTO-inserted 0xFFD2 page breaks the source "
            "did not author (v90 narration fat-gap regression)%s. Worst: %s"
            % (len(offenders), (" [incl. known: %s]" % known) if known else "", worst)
        )


TESTS = [test_no_spurious_pagebreak]

if __name__ == "__main__":
    from _helpers import main_exit

    main_exit(TESTS, "test_no_auto_pagebreak")
