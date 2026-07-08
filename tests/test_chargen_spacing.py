#!/usr/bin/env python3
"""
test_chargen_spacing.py -- pin the v175 Option E "holy fix": the SHIPPED chargen
draw-spacing must use the MATCHED R2100 advance/leftshift pair (ADV2 + LSH2), NOT
the mismatched ADV2 + R1188-leftshift pair that produced the "worse than ever"
first-letter blow-out.

BACKGROUND
  The chargen renderer advances the pen by ADV2[gid] (the tight R2100 advance) and
  draws each glyph at   drawX = pen - LEFTSHIFT[gid].  v174 gave chargen the tight
  ADV2 advance but left the LEFTSHIFT aliased to the WIDE R1188 leftshift (LSH), so
  drawX = pen - R1188_lsh yanked glyphs past the small pen advance -> jittery gaps.
  Option E ships the real R2100 leftshift as a SEPARATE 4th table (LSH2), so the
  advance and the draw-shift are a MATCHED pair and the gaps are clean.

THE GATE (simulate the exact chargen draw on the SHIPPED tables):
    pen += ADV2[gid] ; drawX = pen - LSH2[gid]    (gaps = consecutive drawX deltas)

  * MATCHED  (ADV2 + LSH2)  -> the CLEAN gap set (e.g. "Select" == [10,8,8,9,9]).
  * MISMATCH (ADV2 + LSH )  -> the JITTERY gap set (e.g. "Select" == [6,12,4,12,9]).

  If a future change re-aliases LSH2 to LSH (or swaps/desyncs the table), the
  MATCHED gaps collapse onto the MISMATCH gaps and BOTH pins below FAIL loudly.

The tables come STRAIGHT from RELOC.build_metric_tables() (the SHIPPED bytes,
single source), so this proves the actual on-disc behaviour, not a model.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, main_exit  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "build"))
import _reloc_v147_design as RELOC  # noqa: E402  (relocation single source)

import glyph_metrics  # noqa: E402  (TOOLS_DIR put on sys.path by _helpers)


# ── shipped tables (single source: the exact bytes patch_exe writes) ─────────
def _tables():
    tbls = dict(RELOC.build_metric_tables())
    return tbls[RELOC.ADV2_VA], tbls[RELOC.LSH2_VA], tbls[RELOC.LSH_VA]


def _gid(c):
    return ord(c) - 0x20


def _draw_gaps(s, adv, lsh):
    """Simulate the chargen glyph draw and return the per-pair draw-X gaps.
    pen += adv[gid] ; drawX = pen - lsh[gid]."""
    pen = 0
    xs = []
    for c in s:
        g = _gid(c)
        assert 0 <= g < RELOC.TABLE_ENTRIES, (
            "test string glyph %r (gid %d) is out of the %d-entry table -- pick "
            "printable ASCII < 'z'" % (c, g, RELOC.TABLE_ENTRIES)
        )
        xs.append(pen - lsh[g])
        pen += adv[g]
    return [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]


def _spread(gaps):
    return max(gaps) - min(gaps)


# Flagship acceptance criterion (from the proven simulation): "Select".
FLAGSHIP = "Select"
CLEAN_GAPS = [10, 8, 8, 9, 9]     # ADV2 + LSH2  (matched -- the holy fix)
JITTER_GAPS = [6, 12, 4, 12, 9]   # ADV2 + LSH   (mismatched -- the v174 blow-out)

# Broader coverage: real chargen labels.  For each we require the matched pair to be
# no more jittery than the mismatched pair AND to differ from it (so a re-alias fails).
SAMPLE_STRINGS = ["Select", "Gender", "Allocate", "Enter your name"]


def test_flagship_matched_pair_is_clean():
    """The SHIPPED matched pair (ADV2 + LSH2) reproduces the proven CLEAN gap set for
    'Select' -- this is the exact acceptance criterion for Option E."""
    adv2, lsh2, _ = _tables()
    gaps = _draw_gaps(FLAGSHIP, adv2, lsh2)
    assert gaps == CLEAN_GAPS, (
        "SHIPPED chargen draw of %r with the matched R2100 pair (ADV2+LSH2) = %s, "
        "expected the clean %s -- the R2100 leftshift (LSH2) has desynced or been "
        "re-aliased; the holy fix is broken" % (FLAGSHIP, gaps, CLEAN_GAPS)
    )


def test_flagship_mismatched_pair_is_jittery():
    """The deliberately-mismatched pair (ADV2 + R1188 LSH) reproduces the JITTERY gap
    set -- proving the gate can TELL the two apart, so a re-alias to LSH is caught."""
    adv2, _, lsh = _tables()
    gaps = _draw_gaps(FLAGSHIP, adv2, lsh)
    assert gaps == JITTER_GAPS, (
        "the mismatched pair (ADV2 + R1188 LSH) draw of %r = %s, expected the jittery "
        "%s -- the mismatch reference drifted; the regression can no longer be pinned"
        % (FLAGSHIP, gaps, JITTER_GAPS)
    )


def test_matched_beats_mismatched_everywhere():
    """For every representative chargen label the matched pair (ADV2+LSH2) must be
    strictly cleaner-or-equal (smaller gap spread) than the mismatched pair AND must
    differ from it -- so ANY future re-alias / table swap FAILS this gate."""
    adv2, lsh2, lsh = _tables()
    problems = []
    for s in SAMPLE_STRINGS:
        matched = _draw_gaps(s, adv2, lsh2)
        mismatched = _draw_gaps(s, adv2, lsh)
        if matched == mismatched:
            problems.append(
                "%r: matched gaps %s == mismatched gaps -- LSH2 is not a distinct "
                "R2100 table (a re-alias to R1188 LSH would look like this)"
                % (s, matched)
            )
        if _spread(matched) > _spread(mismatched):
            problems.append(
                "%r: matched spread %d > mismatched spread %d -- the matched R2100 "
                "pair is JITTERIER than the mismatched pair, the fix is inverted"
                % (s, _spread(matched), _spread(mismatched))
            )
    assert not problems, "chargen spacing regressions:\n  " + "\n  ".join(problems)


def test_lsh2_is_separate_r2100_table():
    """Structural teeth: LSH2 is a SEPARATE, non-aliased R2100 leftshift table packed
    directly after ADV2, and its bytes ARE glyph_metrics.leftshift2_table_256()."""
    adv2, lsh2, lsh = _tables()
    N = RELOC.TABLE_ENTRIES
    assert RELOC.LSH2_VA == RELOC.ADV2_VA + N, (
        "LSH2 must pack directly after ADV2 (ADV2_VA + %d); got ADV2=0x%06X LSH2=0x%06X"
        % (N, RELOC.ADV2_VA, RELOC.LSH2_VA)
    )
    assert RELOC.LSH2_VA != RELOC.LSH_VA and lsh2 != lsh, (
        "LSH2 must be a genuinely SEPARATE R2100 leftshift table, NOT aliased to the "
        "R1188 LSH -- the alias is exactly the chargen blow-out Option E removes"
    )
    assert lsh2 == bytes(glyph_metrics.leftshift2_table_256()[:N]), (
        "the shipped LSH2 table != glyph_metrics.leftshift2_table_256()[:%d] -- the "
        "chargen leftshift has desynced from the R2100 SoT" % N
    )
    assert adv2 == bytes(glyph_metrics.adv2_table_256()[:N]), (
        "the shipped ADV2 table != glyph_metrics.adv2_table_256()[:%d]" % N
    )


TESTS = [
    test_flagship_matched_pair_is_clean,
    test_flagship_mismatched_pair_is_jittery,
    test_matched_beats_mismatched_everywhere,
    test_lsh2_is_separate_r2100_table,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_chargen_spacing")
