#!/usr/bin/env python3
"""
test_token_preservation.py -- every translated type-02 dialogue group keeps the
JP group's functional control words (RUN-20261011-2104, v203).

Background
----------
The Step-4 injector keeps only a group's LEADING and TRAILING control runs;
every control word between the first and last JP text glyph is dropped unless
the English authors it inline as a "[FXXX]" token.  v202 shipped ~1,780 groups
that lost character-name inserts (FFF0-FFF6), number / item inserts (FE0x),
overheard-chat page waits (FFFD), shake / timing / position controls, or left a
glow / highlight run open differently than JP (the Lang's-Potion spring line
among them).  The v203 wave re-authored them with inline tokens.

What this test does
-------------------
For every (resource, msg_index) that the type-2 batch files translate (same
last-wins load order and skip markers as build_v9), it compares the BUILT group
in the newest ISO against the PRISTINE group with tools/token_audit.audit_group:
  * functional multiset equal (minus the deliberately stripped leading name
    insert, token_audit.stripped_leading_vars), and
  * glow / highlight / colour / shake end-state equal (a pristine colour word
    after the last text glyph may be dropped -- inert, see
    _without_inert_trailing_colour).  KNOWN_RESIDUAL groups are listed explicitly.
It also asserts no translated type-02 English contains a literal newline (it
encodes as glyph 31, a visible "?").
TIER-2: SKIPs when the ISO or the pristine raw resources are absent.
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, PackData, Skip, default_iso_path, main_exit, pristine_path

sys.path.insert(0, os.path.join(ROOT, "tools"))
import token_audit as TA  # noqa: E402

BATCH_GLOB = os.path.join(ROOT, "data", "type2_translated", "batch_*.json")
# Mirrors build_v9.SKIP_STRUCTURAL_GROUPS (never injected).
SKIP_STRUCTURAL_GROUPS = {(1197, 1)}
# Menu groups composed ENTIRELY of 0x14 label slices (data/name_labels.json):
# the batch english body is never injected, so its newlines never render.
NEWLINE_EXEMPT = {(1196, 810)}
# Known residual: R1196 G379's English belongs to a shifted scene (the v203
# re-chunk could not realign it) and still drops its 3 overheard-chat FFFD page
# waits.  Cosmetic (no wait between lines); tracked for the misaligned-scene pass.
KNOWN_RESIDUAL = {(1196, 379)}
_SKIP_PREFIXES = ("[DATA]", "[LAYOUT]", "[BINARY]", "[MAP]", "[SYSTEM]",
                  "[GLYPH", "[DEBUG]")


def _translations():
    """{(res, mi): english} exactly as build_v9 loads the batch files."""
    out = {}
    for fn in sorted(glob.glob(BATCH_GLOB)):
        for e in json.load(open(fn, encoding="utf-8")):
            key = (e["resource"], e["msg_index"])
            en = e.get("english", "")
            if (key in SKIP_STRUCTURAL_GROUPS or not en
                    or en.startswith(_SKIP_PREFIXES)
                    or any(ord(c) > 127 for c in en)):
                continue
            out[key] = en
    return out


def _without_inert_trailing_colour(pristine_group):
    """pristine_group minus every colour word (0xFFD0-0xFFD9) AFTER its last
    text glyph.  Such a colour governs no glyph; Step 4 deliberately strips it
    from left-align-padded narration (build_v9 leftalign_pad_groups ->
    _strip_trailing_color_controls), so the built colour end-state must match
    the pristine state WITHOUT it."""
    last_text = max((i for i, w in enumerate(pristine_group) if w < 0xFB00),
                    default=-1)
    return [w for i, w in enumerate(pristine_group)
            if not (i > last_text and 0xFFD0 <= w <= 0xFFD9)]


def test_no_literal_newline_in_type2_english():
    trans = _translations()
    bad = ["R%d G%d" % k for k, en in sorted(trans.items())
           if "\n" in en and k not in NEWLINE_EXEMPT
           and os.path.isfile(pristine_path(k[0], "02"))]
    assert not bad, "literal newline (renders '?'): " + ", ".join(bad[:20])


def test_translated_groups_keep_control_tokens():
    trans = _translations()
    by_res = {}
    for (r, mi) in trans:
        if os.path.isfile(pristine_path(r, "02")):
            by_res.setdefault(r, []).append(mi)
    if not by_res:
        raise Skip("no pristine type-02 raw resources")
    pd = PackData(default_iso_path())
    problems, n = [], 0
    try:
        for r in sorted(by_res):
            pristine = open(pristine_path(r, "02"), "rb").read()
            pg = TA.groups_of(pristine)
            bg = TA.groups_of(pd.extract(r)[0])
            allowed = TA.stripped_leading_vars(pristine)
            for mi in sorted(by_res[r]):
                if mi >= len(pg) or mi >= len(bg):
                    continue
                n += 1
                if (r, mi) in KNOWN_RESIDUAL:
                    continue
                errs, _w = TA.audit_group(pg[mi], bg[mi], allowed.get(mi, ()))
                if any(e.startswith("end-state colour") for e in errs):
                    # Pristine ended on an inert trailing colour (stripped by
                    # Step 4 in padded narration): accept the built state if it
                    # equals pristine minus that colour, or carries no colour.
                    eff = TA.end_state(_without_inert_trailing_colour(pg[mi]))[2]
                    stripped = len(_without_inert_trailing_colour(pg[mi])) < len(pg[mi])
                    if TA.end_state(bg[mi])[2] in ((eff, None) if stripped else (eff,)):
                        errs = [e for e in errs
                                if not e.startswith("end-state colour")]
                problems.extend("R%d G%d: %s" % (r, mi, e) for e in errs)
    finally:
        pd.close()
    assert n, "no translated type-02 groups audited"
    assert not problems, "%d token errors in %d groups audited: %s" % (
        len(problems), n, "; ".join(problems[:15]))


TESTS = [test_no_literal_newline_in_type2_english,
         test_translated_groups_keep_control_tokens]

if __name__ == "__main__":
    main_exit(TESTS, "test_token_preservation")
