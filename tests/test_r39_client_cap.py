#!/usr/bin/env python3
"""
test_r39_client_cap.py -- round-2 gate: REQUEST "Client" name horizontal-collision fix.

THE BUG (v132 almostrequest.p2s / shots/request.png)
----------------------------------------------------
On the tavern request board the "Client" VALUE draws COUNT-ANCHORED -- the origin
walks LEFT as the glyph count grows (universal renderer func 0x307DA0, align==2
branch; line_origin = (box_width - count)*18).  A long client name (e.g. the v132
"Mayor of Duhan") slid LEFT under the fixed "Client" label and collided
horizontally: the screenshot shows "Ma[Client] Duhan" -- the value's head overlaps
the label.  This is a NEW horizontal collision in the Client row, distinct from the
(already-fixed) vertical desc overflow.

THE ROUND-2 FIX (W1-REQ)
------------------------
  * data/r39_quest_text_aligned.json: the 8 over-budget client-name groups are
    capped to <=8 glyph cells (G387 Janken Man->Janken, G388 Mayor of Duhan->Mayor,
    G390 Guillaume->Guillem, G392 Pitiful Imp->Imp, G394 Contest Over->Contest,
    G397 Merchant Guild->Guild, G403 Survey Deadline->Survey, G405 Knight Order->
    Knights), so a short value can no longer walk left under the "Client" label.
  * The 4 notification-bar EVENT sentences (G400/G404/G406/G410) -- which render in
    the thin black event bar, NOT the Client field -- are UNCHANGED (they legitimately
    exceed 8 cells and end with '.'/'!').
  * build/inject_r39_quest.py section 6b adds a build-time CLIENT-NAME CELL-CAP
    ASSERT that FAILS THE BUILD if any G383-G410 non-event client name exceeds 8
    cells, so a future over-long name is caught before it can collide live.

WHAT THIS GATE ASSERTS (data + source level; G388 'Mayor' also checked in built R39)
-----------------------------------------------------------------------------------
  CAP-DATA      every G383-G410 NON-EVENT client name in
                data/r39_quest_text_aligned.json encodes to <= 8 glyph cells
                (the count budget that clears the "Client" label) -- using the EXACT
                inject_r39_quest cell rule (each char incl. space = 1 cell).
  CAP-DUHAN     G388 is 'Mayor' (the v132 collision client; 'Mayor' alone read as the city — guide p127: client is the Mayor), <= 8 cells, matching the
                castle name used in the title/desc.
  EVENT-UNTOUCHED  the 4 event sentences G400/G404/G406/G410 are still full
                sentences ending in '.'/'!' and are NOT shortened to <=8 cells (they
                must stay -- they render in the event bar, not the Client field).
  ASSERT-PRESENT  build/inject_r39_quest.py carries the section-6b CLIENT-NAME
                CELL-CAP ASSERT with the <=8 cap and the event '.'/'!' exemption, so
                the build itself rejects a future over-long name.
  BUILT-DUHAN   (TIER-2, SKIP if no built R39) the built
                build/packdata_resources/0039_type15.raw decodes G388 to 'Mayor'
                and that decoded value is <= 8 cells.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (  # noqa: E402
    PACKDATA_RES_DIR,
    ROOT,
    Skip,
    decode_glyphs,
    main_exit,
    require_file,
)

ALIGNED_JSON = os.path.join(ROOT, "data", "r39_quest_text_aligned.json")
INJECT_SRC = os.path.join(ROOT, "build", "inject_r39_quest.py")
GLYPH_TABLE = os.path.join(ROOT, "data", "english_glyph_table.json")

CLIENT_GROUPS = range(383, 411)        # G383..G410 (the client-name / event band)
CLIENT_NAME_CELL_CAP = 8               # mirror inject_r39_quest CLIENT_NAME_CELL_CAP
EVENT_GROUPS = (400, 404, 406, 410)    # notification-bar sentences (exempt)
# The 8 groups round-2 capped, with their expected shortened values.
CAPPED = {
    387: "Janken", 388: "Mayor", 390: "Guillem", 392: "Imp",
    394: "Contest", 397: "Guild", 403: "Survey", 405: "Knights",
}


def _aligned():
    require_file(ALIGNED_JSON, "R39 client-cap gate")
    return json.load(open(ALIGNED_JSON, encoding="utf-8"))


def _english(entry):
    """The 'english' string of an aligned entry (dict {'english':..} or bare str)."""
    if isinstance(entry, dict):
        return (entry.get("english") or "").strip()
    return (entry or "").strip()


def _cell_count(text):
    """Glyph-cell count using the EXACT inject_r39_quest.encode_english rule: each
    character (including spaces) is one cell; ' / ' becomes a single FFFE break cell.
    Terminators (FFFE/FFFF) are NOT counted toward the Client-label clearance budget,
    matching inject's `cells = [g for g in group if g not in (0xFFFE,0xFFFF)]`."""
    # Mirror inject: ' / ' -> newline -> FFFE break (excluded); count remaining chars.
    parts = text.replace(" / ", "\n").split("\n")
    n = 0
    for pi, part in enumerate(parts):
        seg = part.strip() if pi > 0 else part
        n += len(seg)  # every char incl. space is one cell
    return n


def _is_event(text):
    """An event-bar sentence (exempt) ends in '.' or '!' (inject's exemption rule)."""
    return text.rstrip().endswith((".", "!"))


# ---------------------------------------------------------------------------
# CAP-DATA / CAP-DUHAN
# ---------------------------------------------------------------------------
def test_all_client_names_within_cell_budget():
    """CAP-DATA: every NON-EVENT client name in G383-G410 encodes to <= 8 glyph cells
    so the count-anchored value cannot walk left under the fixed 'Client' label (the
    v132 'Ma[Client] Duhan' collision)."""
    d = _aligned()
    over = []
    for gi in CLIENT_GROUPS:
        entry = d.get(str(gi))
        if entry is None:
            continue
        en = _english(entry)
        if not en or _is_event(en):
            continue
        cells = _cell_count(en)
        if cells > CLIENT_NAME_CELL_CAP:
            over.append((gi, en, cells))
    assert not over, (
        "%d client name(s) exceed the %d-cell budget and will collide with the "
        "'Client' label: %s"
        % (len(over), CLIENT_NAME_CELL_CAP,
           ", ".join("G%d %r=%d" % (g, e, c) for g, e, c in over))
    )


def test_capped_groups_have_expected_short_values():
    """CAP-DUHAN (+ the 8 capped groups): each round-2-capped group holds its
    expected shortened value (G388='Mayor' is the v132 collision client) and each is
    <= 8 cells.  Pins the specific edits so a regression that restores 'Mayor of
    Duhan' (12 cells) trips here."""
    d = _aligned()
    bad = []
    for gi, expected in CAPPED.items():
        entry = d.get(str(gi))
        en = _english(entry) if entry is not None else None
        if en != expected:
            bad.append("G%d=%r (expected %r)" % (gi, en, expected))
            continue
        cells = _cell_count(en)
        if cells > CLIENT_NAME_CELL_CAP:
            bad.append("G%d=%r is %d cells (> %d)" % (gi, en, cells, CLIENT_NAME_CELL_CAP))
    assert not bad, (
        "round-2 client-name caps regressed: %s -- a value reverting to its long form "
        "would re-introduce the Client-label collision" % "; ".join(bad)
    )


# ---------------------------------------------------------------------------
# EVENT-UNTOUCHED
# ---------------------------------------------------------------------------
def test_event_sentences_untouched():
    """EVENT-UNTOUCHED: the 4 notification-bar EVENT sentences (G400/G404/G406/G410)
    render in the event bar -- NOT the Client field -- so they MUST remain full
    sentences (ending '.'/'!') and must NOT have been shortened to <=8 cells.  Capping
    them would corrupt the event-bar messages."""
    d = _aligned()
    bad = []
    for gi in EVENT_GROUPS:
        entry = d.get(str(gi))
        en = _english(entry) if entry is not None else None
        if not en:
            bad.append("G%d missing/empty -- the event-bar sentence was lost" % gi)
            continue
        if not _is_event(en):
            bad.append("G%d=%r does not end in '.'/'!' (no longer an event sentence)" % (gi, en))
            continue
        if _cell_count(en) <= CLIENT_NAME_CELL_CAP:
            bad.append("G%d=%r was shortened to <=%d cells (wrongly capped as a client name)"
                       % (gi, en, CLIENT_NAME_CELL_CAP))
    assert not bad, (
        "event-bar sentence regression: %s -- G400/G404/G406/G410 must stay full "
        "sentences, exempt from the client-name cap" % "; ".join(bad)
    )


# ---------------------------------------------------------------------------
# ASSERT-PRESENT: inject_r39_quest carries the build-time cap assert
# ---------------------------------------------------------------------------
def test_inject_has_client_cell_cap_assert():
    """ASSERT-PRESENT: build/inject_r39_quest.py carries the section-6b CLIENT-NAME
    CELL-CAP ASSERT with the <=8 cap and the event '.'/'!' exemption -- so the BUILD
    rejects a future over-long client name before it can collide live."""
    require_file(INJECT_SRC, "R39 client-cap assert")
    src = open(INJECT_SRC, encoding="utf-8").read()
    assert "CLIENT_NAME_CELL_CAP" in src, (
        "build/inject_r39_quest.py lost the CLIENT_NAME_CELL_CAP constant -- the "
        "build-time guard against over-long client names is gone"
    )
    # The cap value must be 8 (the budget that clears the 'Client' label).
    assert "CLIENT_NAME_CELL_CAP = 8" in src.replace("  ", " ") or \
        "CLIENT_NAME_CELL_CAP=8" in src.replace(" ", ""), (
        "inject_r39_quest CLIENT_NAME_CELL_CAP is not 8 -- the documented budget that "
        "clears the 'Client' label"
    )
    # It must be a hard assert, not a soft warning.
    assert "assert len(cells) <= CLIENT_NAME_CELL_CAP" in src, (
        "inject_r39_quest does not hard-assert len(cells) <= CLIENT_NAME_CELL_CAP -- a "
        "future over-long client name must FAIL THE BUILD, not warn"
    )
    # The event-sentence exemption ('.'/'!') must be present so events stay long.
    assert "endswith(('.', '!'))" in src or "endswith(('.','!'))" in src.replace(" ", ""), (
        "inject_r39_quest lost the event-sentence '.'/'!' exemption -- the assert would "
        "wrongly fire on the legitimate long event-bar sentences"
    )


# ---------------------------------------------------------------------------
# BUILT-DUHAN (TIER-2): the built R39 decodes G388 to 'Mayor'
# ---------------------------------------------------------------------------
import struct  # noqa: E402

GLYPH_DATA_START = 632  # R39 FFFF group stream starts here (mirror test_r39_quests)


def _scan_groups(data):
    pos = GLYPH_DATA_START
    groups, cur = [], []
    n = len(data)
    while pos + 1 < n:
        w = struct.unpack_from(">H", data, pos)[0]
        if w == 0xFFFF:
            groups.append(cur)
            cur = []
        else:
            cur.append(w)
        pos += 2
    return groups


def test_built_g388_is_duhan():
    """BUILT-DUHAN (TIER-2): the built R39 decodes G388 to 'Mayor' (the v132 collision
    client), and that value is <= 8 cells.  SKIP when no built R39 is present (the
    data/source gates above already cover the autonomous path)."""
    p = os.path.join(PACKDATA_RES_DIR, "0039_type15.raw")
    if not os.path.isfile(p):
        raise Skip("build/packdata_resources/0039_type15.raw missing (run a build)")
    data = open(p, "rb").read()
    groups = _scan_groups(data)
    assert len(groups) > 388, "only %d groups in built R39" % len(groups)
    text = decode_glyphs(groups[388], linebreak=" ").strip()
    assert text == "Mayor", (
        "built R39 G388 client decodes to %r, expected 'Mayor' -- the round-2 cap that "
        "fixes the 'Ma[Client] Duhan' collision did not ship" % text
    )
    cells = len([g for g in groups[388] if g not in (0xFFFE, 0xFFFF)])
    assert cells <= CLIENT_NAME_CELL_CAP, (
        "built G388 'Mayor' is %d cells (> %d) -- it could still collide with the "
        "'Client' label" % (cells, CLIENT_NAME_CELL_CAP)
    )


TESTS = [
    test_all_client_names_within_cell_budget,
    test_capped_groups_have_expected_short_values,
    test_event_sentences_untouched,
    test_inject_has_client_cell_cap_assert,
    test_built_g388_is_duhan,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_r39_client_cap")
