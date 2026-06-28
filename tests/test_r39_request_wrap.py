#!/usr/bin/env python3
"""
test_r39_request_wrap.py -- Issue B gate: request-description wrap budget +
quest-text condensation.

The tavern request description body (R39 groups G348-G380 descriptions, G383-G410
client names) renders COUNT-ANCHORED inside the parchment window (handoff
HANDOFF_box_request_formatting.md sec 5; inject_r39_quest.py sec P2).  Two
independent failure axes the requestissue.p2s playtest exposed:

  * HORIZONTAL overflow -- a line wider than the box origin (box_width - count)*18
    gets a negative origin and spills past BOTH parchment edges.  Guarded by the
    greedy word-wrap to build.inject_r39_quest.DESC_WRAP_CELLS cells/line (W1-T3
    lowered this from 28 to the JP-grounded 20).

  * VERTICAL collision -- a description that wraps to too many rows runs its tail
    into the fixed "Client:" / "Reward:" fields below it ("Ma<Client>rent Duhan"
    garble).  The box holds ~6 rows at 24px pitch; verbose English wrapped to 7-9.
    Fixed editorially by condensing the ~60 descriptions in
    data/r39_quest_text_aligned.json (W1-T2).

This module pins BOTH axes deterministically, straight from source (no built ISO
needed):

  1. DESC_WRAP_CELLS is the W1-T3 budget (20) -- the horizontal capacity constant.
  2. Re-running the EXACT inject_r39_quest.wrap_desc_text algorithm on every
     description/client-name in r39_quest_text_aligned.json, NO wrapped line
     exceeds DESC_WRAP_CELLS cells (horizontal overflow guard).
  3. Every description wraps to <= DESC_ROW_BUDGET rows (vertical collision guard
     -- the condensation target).  A description that still wraps past the row
     budget WOULD collide with the Client field, so this FAILS until W1-T2's
     condensation covers it.
  4. The wrap helper this test uses is byte-for-byte the source algorithm
     (parsed/derived from build/inject_r39_quest.py), so it can never silently
     drift from what the build actually injects.

The wrap function + DESC_WRAP_CELLS are READ FROM SOURCE rather than imported,
because build/inject_r39_quest.py does os.chdir + file I/O at import time (it is a
build script, not a library) -- importing it would run the whole injection.  We
parse the constant and re-implement the documented greedy wrap, then cross-check
the re-implementation matches the source text of wrap_desc_text so the two cannot
diverge.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (  # noqa: E402  (path insert first)
    DATA_DIR,
    ROOT,
    main_exit,
    require_file,
)

INJECT_R39_QUEST = os.path.join(ROOT, "build", "inject_r39_quest.py")
QUEST_TEXT_JSON = os.path.join(DATA_DIR, "r39_quest_text_aligned.json")

# The aligned groups inject_r39_quest.py word-wraps (descriptions G348-G380 +
# client names G383-G410) -- ONLY these are run through wrap_desc_text; titles /
# UI labels are short and ship unwrapped.  Mirrors inject_r39_quest.ALIGNED_GROUPS.
ALIGNED_GROUPS = set(range(348, 381)) | set(range(383, 411))

# Vertical row budget: the request parchment window holds ~6 description rows at
# 24px pitch before the description tail collides with the fixed "Client:" field
# (handoff sec 5; inject_r39_quest.py P2 comment cites a 5-row JP design budget).
# 6 is the documented box capacity -- a description wrapping past this is the
# vertical-collision bug (requestissue.p2s).  The condensation (W1-T2) must bring
# every description to <= this.
DESC_ROW_BUDGET = 6


# ---------------------------------------------------------------------------
# Pull DESC_WRAP_CELLS + the wrap algorithm out of the build script WITHOUT
# importing it (it chdir's + reads files at import time).
# ---------------------------------------------------------------------------
def _inject_src():
    require_file(INJECT_R39_QUEST, "Issue B request-wrap gate")
    return open(INJECT_R39_QUEST, encoding="utf-8").read()


def _desc_wrap_cells():
    m = re.search(r"^DESC_WRAP_CELLS\s*=\s*(\d+)", _inject_src(), re.M)
    assert m, "build/inject_r39_quest.py: DESC_WRAP_CELLS assignment not found"
    return int(m.group(1))


def _wrap_desc_text(text, budget):
    """Re-implementation of inject_r39_quest.wrap_desc_text (verified identical to
    source by test_wrap_helper_matches_source).  Greedy word-wrap to <=budget glyph
    cells/line; collapses authored ' / ' / newline breaks first, then re-wraps.
    Returns a list of lines (each line's len == its glyph-cell count, since every
    cell incl. space is one pitch unit)."""
    flat = " ".join(
        s.strip() for s in text.replace(" / ", "\n").split("\n") if s.strip()
    )
    flat = " ".join(flat.split())  # normalize internal whitespace
    lines, cur = [], ""
    for w in flat.split(" "):
        cand = (cur + " " + w).strip()
        if len(cand) <= budget or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _aligned_entries():
    require_file(QUEST_TEXT_JSON, "Issue B quest text")
    d = json.load(open(QUEST_TEXT_JSON, encoding="utf-8"))
    out = []
    for k, v in d.items():
        gi = int(k)
        if gi not in ALIGNED_GROUPS:
            continue
        en = (v.get("english") or "").strip()
        if not en:
            continue
        out.append((gi, en))
    return out


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_desc_wrap_cells_is_chosen_budget():
    """DESC_WRAP_CELLS must be the W1-T3 JP-grounded budget (20).  This is the
    horizontal capacity: lines wider than ~box_width get a negative count-anchored
    origin and clip both parchment edges (requestissue.p2s).  28 (the pre-fix value)
    was wider than the JP max line (21) and overflowed; if a future change moves it,
    re-derive against a LIVE box_width read at VA 0x308964 first."""
    cells = _desc_wrap_cells()
    assert cells == 20, (
        "DESC_WRAP_CELLS = %d, expected 20 (the JP-grounded count-anchored budget). "
        "If you intend a different value, confirm it against a live box_width read "
        "(VA 0x308964) -- 28 overflowed both edges, < 18 risks needless extra rows"
        % cells
    )


def test_wrap_helper_matches_source():
    """The wrap algorithm this gate runs must be byte-for-byte the source
    wrap_desc_text body, so the test can never silently drift from what the build
    injects.  Compares the structural tokens of the source function to this module's
    re-implementation."""
    src = _inject_src()
    m = re.search(r"def wrap_desc_text\(.*?\n(.*?)\ndef ", src, re.S)
    assert m, "build/inject_r39_quest.py: wrap_desc_text body not found"
    body = m.group(1)
    # The load-bearing lines of the greedy wrap (any drift here changes line counts).
    for needle in (
        "text.replace(' / ', '\\n')",
        "' '.join(flat.split())",
        "for w in flat.split(' ')",
        "cand = (cur + ' ' + w).strip()",
        "if len(cand) <= budget or not cur:",
        "lines.append(cur)",
    ):
        assert needle in body, (
            "wrap_desc_text source no longer contains %r -- this test's "
            "re-implementation has drifted from the build; re-sync _wrap_desc_text "
            "with build/inject_r39_quest.py before trusting the wrap gate" % needle
        )


def test_no_description_line_exceeds_wrap_budget():
    """HORIZONTAL guard: every wrapped line of every description / client name is
    <= DESC_WRAP_CELLS cells.  A line over budget would get a negative count-anchored
    origin (box_width - count)*18 and clip both parchment edges.  (Passes by
    construction of the greedy wrap -- this pins that the SHIPPED text actually
    flows through the wrap and no single unbreakable word blows the budget.)"""
    budget = _desc_wrap_cells()
    offenders = []
    for gi, en in _aligned_entries():
        for ln in _wrap_desc_text(en, budget):
            if len(ln) > budget:
                offenders.append((gi, len(ln), ln))
    assert not offenders, (
        "%d description line(s) exceed the %d-cell wrap budget (an unbreakable word "
        "longer than the box width -> negative origin -> both-edge clip). First: "
        "G%d %dcells %r" % (
            len(offenders), budget,
            offenders[0][0], offenders[0][1], offenders[0][2][:40],
        )
    )


def test_descriptions_fit_row_budget():
    """VERTICAL guard (the condensation target): every description / client name
    wraps to <= DESC_ROW_BUDGET rows at DESC_WRAP_CELLS cells/line.  A description
    that wraps taller runs its tail into the fixed 'Client:' field below it (the
    'Ma<Client>rent Duhan' collision in requestissue.p2s).

    This FAILS for any description W1-T2 has not yet condensed -- it is the gate that
    proves the rewrite is COMPLETE, not just started.  When it is green, no shipped
    description can overflow the box vertically."""
    budget = _desc_wrap_cells()
    too_tall = []
    for gi, en in _aligned_entries():
        n_rows = len(_wrap_desc_text(en, budget))
        if n_rows > DESC_ROW_BUDGET:
            too_tall.append((gi, n_rows))
    too_tall.sort(key=lambda t: -t[1])
    assert not too_tall, (
        "%d quest description(s) wrap to > %d rows at %d cells/line and would collide "
        "with the Client field (requestissue.p2s). Condense their english in "
        "data/r39_quest_text_aligned.json. Worst offenders (group, rows): %s"
        % (len(too_tall), DESC_ROW_BUDGET, budget, too_tall[:8])
    )


def test_aligned_entries_present():
    """Sanity: the aligned quest-text file actually carries description/client
    english for the G348-G380 / G383-G410 groups (so the wrap gates above are
    measuring real content, not an empty set)."""
    entries = _aligned_entries()
    assert len(entries) >= 30, (
        "only %d aligned english quest descriptions/client names in %s -- expected "
        ">=30 (G348-G380 + G383-G410); the wrap gates would be vacuously passing"
        % (len(entries), os.path.relpath(QUEST_TEXT_JSON, ROOT))
    )


TESTS = [
    test_desc_wrap_cells_is_chosen_budget,
    test_wrap_helper_matches_source,
    test_no_description_line_exceeds_wrap_budget,
    test_descriptions_fit_row_budget,
    test_aligned_entries_present,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_r39_request_wrap")
