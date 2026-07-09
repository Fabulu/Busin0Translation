#!/usr/bin/env python3
"""
test_dialogue_wrap_force.py -- gate for the DIALOGUE_WRAP_FORCE promotion list
(data/dialogue_wrap_force.json).

Background
----------
build_v9's Step-4 wrap branch sends groups that are neither classifier-dialogue,
narration, pad-narration, nor choice through the narrow char-20 wrap_type2_text.
Most of those are menus/lists/system dialogs that MUST stay narrow -- but the
v171 unwalked-island scenes (R1200 resurrection ceremony, R1208 Aoi/Vera,
R1210 Vile, R1212 Konde/Erika/Iris/Ingo, the Lucy shop visits, ...) are real
BOXED-DIALOGUE prose whose 0x04 DISPLAY opcodes the BFS walk cannot reach, so
build_dialogue_map never sees them and they shipped as choppy under-filled
char-20 lines.  data/dialogue_wrap_force.json promotes the island-mode-verified
PURE-DIALOGUE subset to the identical wrap_px(DIALOGUE_BOX_PX) path.

What this test pins
-------------------
  wellformed  the file parses; entries are unique [resource, msg_index] int
              pairs under the documented key.
  collision   NO entry collides with a pristine choice group, with
              DIALOGUE_WRAP_EXCLUDE / SKIP_STRUCTURAL_GROUPS, or with the
              classifier's own dialogue/narration/pad sets (a collision would
              be a double-wrap or a direct contradiction of the engine rule).
  prose       every entry resolves to a CURRENT effective english translation
              (build_v9's own batch merge + filters) that is multi-line prose:
              >= 40 chars, sentence punctuation, not digit-led -- so a stray
              menu/list/label entry cannot sneak into the wide box.
  wiring      build_v9.py actually loads the file and the force check widens
              ONLY the `mi in dialogue_groups` arm, textually AFTER the
              DIALOGUE_WRAP_EXCLUDE and choice-group gates (their precedence
              is load-bearing).
"""

import glob
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import BUILD_V9, DATA_DIR, RAW_DIR, Skip, main_exit  # noqa: E402

FORCE_PATH = os.path.join(DATA_DIR, "dialogue_wrap_force.json")
TYPE2_TRANS_DIR = os.path.join(DATA_DIR, "type2_translated")

# Mirrors build_v9's Step-4 batch filter (same order as test_choice_groups).
_DROP_PREFIXES = ("[DATA]", "[LAYOUT]", "[BINARY]", "[MAP]", "[SYSTEM]",
                  "[GLYPH", "[DEBUG]")


def _load_force():
    assert os.path.isfile(FORCE_PATH), "missing %s" % FORCE_PATH
    with open(FORCE_PATH, encoding="utf-8") as f:
        d = json.load(f)
    assert "force_dialogue_wrap" in d, "key 'force_dialogue_wrap' missing"
    return d["force_dialogue_wrap"]


def _parse_pair_set(name):
    """Parse a {(a, b), ...} literal set out of build_v9.py source."""
    src = open(BUILD_V9, encoding="utf-8").read()
    m = re.search(r"\b%s\s*=\s*\{(.*?)\}" % re.escape(name), src, re.S)
    assert m, "build_v9.py: %s set not found" % name
    pairs = re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", m.group(1))
    return {(int(a), int(b)) for a, b in pairs}


def _effective_translations(resources):
    """build_v9's Step-4 batch merge (sorted glob, later batches win) restricted
    to `resources`, with the same skip filters."""
    skip_structural = _parse_pair_set("SKIP_STRUCTURAL_GROUPS")
    out = {}
    for fn in sorted(glob.glob(os.path.join(TYPE2_TRANS_DIR, "batch_*.json"))):
        for e in json.load(open(fn, encoding="utf-8")):
            r, mi = e["resource"], e["msg_index"]
            if r not in resources or (r, mi) in skip_structural:
                continue
            en = e.get("english", "")
            if not en or en.startswith(_DROP_PREFIXES):
                continue
            if any(ord(c) > 127 for c in en):
                continue
            out[(r, mi)] = en
    return out


def _pristine_choice_groups(res_idx):
    """Mirror of build_v9's load_pristine_choice_groups (pristine FFC0..FFCF)."""
    from patch_section1_offsets import group_choice_markers, HEADER_SIZE
    path = os.path.join(RAW_DIR, "%04d_type02.raw" % res_idx)
    if not os.path.isfile(path):
        return set()
    raw = open(path, "rb").read()
    if len(raw) < HEADER_SIZE:
        return set()
    sec2_size = struct.unpack_from("<I", raw, 0x14)[0]
    sec2_off = struct.unpack_from("<I", raw, 0x18)[0]
    if sec2_off < HEADER_SIZE or sec2_off >= len(raw) or sec2_size < 4:
        return set()
    sec2 = raw[sec2_off:sec2_off + sec2_size]
    words = [struct.unpack_from(">H", sec2, i * 2)[0]
             for i in range(len(sec2) // 2)]
    choice, gi, start = set(), 0, 0
    for i, w in enumerate(words):
        if w == 0xFFFF:
            if group_choice_markers(words[start:i]):
                choice.add(gi)
            gi += 1
            start = i + 1
    return choice


# ===========================================================================
# TESTS
# ===========================================================================
def test_file_parses_and_entries_wellformed():
    entries = _load_force()
    assert isinstance(entries, list) and entries, "empty/non-list promotion set"
    seen = set()
    for e in entries:
        assert (isinstance(e, list) and len(e) == 2
                and all(isinstance(x, int) and x >= 0 for x in e)), \
            "malformed entry %r (want [resource, msg_index] ints)" % (e,)
        t = tuple(e)
        assert t not in seen, "duplicate entry %r" % (e,)
        seen.add(t)


def test_no_collision_with_choice_exclude_or_classifier():
    if not os.path.isdir(RAW_DIR):
        raise Skip("no extracted/packdata_raw tier")
    from dialogue_classifier import (
        build_dialogue_map, build_narration_map, build_narration_pad_map)
    pairs = {tuple(e) for e in _load_force()}
    exclude = _parse_pair_set("DIALOGUE_WRAP_EXCLUDE")
    structural = _parse_pair_set("SKIP_STRUCTURAL_GROUPS")
    bad = []
    for r in sorted({p[0] for p in pairs}):
        mis = {mi for rr, mi in pairs if rr == r}
        choice = _pristine_choice_groups(r)
        dmap = build_dialogue_map(r)
        nmap = build_narration_map(r)
        pmap = set(build_narration_pad_map(r))
        for mi in sorted(mis):
            for label, s in (("choice group", choice),
                             ("build_dialogue_map (already wrapped)", dmap),
                             ("build_narration_map", nmap),
                             ("build_narration_pad_map", pmap)):
                if mi in s:
                    bad.append((r, mi, label))
            for label, s in (("DIALOGUE_WRAP_EXCLUDE", exclude),
                             ("SKIP_STRUCTURAL_GROUPS", structural)):
                if (r, mi) in s:
                    bad.append((r, mi, label))
    assert not bad, "force entries collide: %s" % bad[:10]


def test_entries_are_multiline_prose():
    pairs = [tuple(e) for e in _load_force()]
    trans = _effective_translations({r for r, _ in pairs})
    bad = []
    for r, mi in pairs:
        en = trans.get((r, mi))
        if en is None:
            bad.append((r, mi, "no effective english translation (dead entry)"))
            continue
        flat = en.replace(" // ", " ").replace(" / ", " ")
        if len(flat) < 40:
            bad.append((r, mi, "too short for multi-line prose: %r" % en))
        elif not re.search(r"[.!?][\")\']?( |$)", en):
            bad.append((r, mi, "no sentence punctuation (list-like?): %r" % en))
        elif re.match(r"^\d", flat) or re.search(r"\b\d+ ?- ?\d+\b", flat):
            bad.append((r, mi, "digit-led / range numbering (list-like?): %r" % en))
    assert not bad, "non-prose force entries: %s" % bad[:10]


def test_force_branch_wired_in_build():
    src = open(BUILD_V9, encoding="utf-8").read()
    assert "dialogue_wrap_force.json" in src, \
        "build_v9.py does not load data/dialogue_wrap_force.json"
    cond = re.search(
        r"if mi in dialogue_groups or \(r_id, mi\) in DIALOGUE_WRAP_FORCE:", src)
    assert cond, "force check must widen ONLY the `mi in dialogue_groups` arm"
    # precedence: the pass-through exclude guard and the choice-group gate must
    # sit textually BEFORE the widened dialogue arm inside the encode loop.
    excl = src.find("if (r_id, mi) in DIALOGUE_WRAP_EXCLUDE:")
    choice = src.find("elif mi not in choice_groups:")
    assert 0 < excl < choice < cond.start(), \
        "DIALOGUE_WRAP_EXCLUDE / choice-group gates must precede the force arm"


TESTS = [
    test_file_parses_and_entries_wellformed,
    test_no_collision_with_choice_exclude_or_classifier,
    test_entries_are_multiline_prose,
    test_force_branch_wired_in_build,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_dialogue_wrap_force")
