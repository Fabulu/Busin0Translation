#!/usr/bin/env python3
"""
test_v192_spell_quest_fixes.py -- TIER-1 data-level regression gates for the
v192 fix wave (issues #33-#39), all fixed in translation JSON / injector
source (no build/EXE changes). Anchored by (resource, msg_index) rather than
full-string match so unrelated rewording doesn't false-positive the gate.

Issue map:
  #33  Kreta/Zakreta/Through-stone quest lines: 魔法剣 mis-rendered as
       "sword" instead of the established item-name convention "stone"
       (batch_01/03/04/zzz_choicefix/zzz_restore_labels R1196/R1203/R1205).
  #34  B1F item narration: "stairs" -> "barrels" (batch_03 R1203 msg1534).
  #35  "you were ambushed" -> "we were ambushed"; "corridor" -> "bridge"
       (batch_03 R1203 msg1164/1166/1173).
  #36  Lang quest medicine item: "Barrier"/"Potion" -> "Medicine", scoped to
       the Lang R1197 sequence + its R39 quest-text mirror.
  #37  Spell リープ ("Leap") and リピール ("Repeal") were BOTH mis-decoded as
       "Ripu" -- split back into their real, distinct names. Touches R46
       bulletin board (build/inject_r46_r47.py string literals), R34 item
       DB, and R39 spell-name table.
  #38  Spleem / Salome stone descriptions said single-target; both are
       actually group-effect spells (R34 sub9 idx10/idx11).
  #39  Vigger storage "buy back from player" option mislabeled "Buy" (should
       read "Sell" from the player's perspective) -- R45 message 67/85.

TIER-1: all source files are plain data checked into the repo (not build- or
ISO-gated), so these gates always run.
"""
import ast
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import DATA_DIR, ROOT, main_exit, require_file

TYPE2_DIR = os.path.join(DATA_DIR, "type2_translated")
CHUNK_DIR = os.path.join(DATA_DIR, "translate_chunks")

R46R47_SRC = os.path.join(ROOT, "build", "inject_r46_r47.py")
R34 = os.path.join(DATA_DIR, "r34_english_aligned.json")
R39_QUEST = os.path.join(DATA_DIR, "r39_quest_text_aligned.json")
R2654_NAMES = os.path.join(DATA_DIR, "r2654_library_names.json")
BATCH_01 = os.path.join(TYPE2_DIR, "batch_01.json")
BATCH_03 = os.path.join(TYPE2_DIR, "batch_03.json")
BATCH_04 = os.path.join(TYPE2_DIR, "batch_04.json")
BATCH_ZZZ_CHOICEFIX = os.path.join(TYPE2_DIR, "batch_zzz_choicefix.json")
BATCH_ZZZ_RESTORE = os.path.join(TYPE2_DIR, "batch_zzz_restore_labels.json")
CHUNK_06 = os.path.join(CHUNK_DIR, "chunk_06_translated.json")
CHUNK_R43_R45 = os.path.join(CHUNK_DIR, "chunk_r43_r45_translated.json")
BUILD_FULL_V2 = os.path.join(ROOT, "build", "build_full_english_v2.py")


# ===========================================================================
# Generic helpers
# ===========================================================================
def _load_list(path):
    require_file(path, "v192 fix wave data")
    return json.load(open(path, encoding="utf-8"))


def _find(entries, resource, idx):
    """Find a type-2-style entry by (resource, msg_index|message). Hard-fails
    (not Skip) when absent -- an anchor going missing is itself a regression
    signal (the entry got dropped/renumbered), not an absent tier."""
    for e in entries:
        if e.get("resource") != resource:
            continue
        mi = e.get("msg_index", e.get("message"))
        if mi == idx:
            return e
    raise AssertionError(
        "anchor (resource=%s, msg_index=%s) not found in data -- entry "
        "renumbered or dropped" % (resource, idx)
    )


def _eng(entries, resource, idx):
    return _find(entries, resource, idx)["english"]


def _r34_entries():
    require_file(R34, "R34 aligned item DB")
    return json.load(open(R34, encoding="utf-8"))["entries"]


def _r34_eng(sub, idx):
    for e in _r34_entries():
        if e.get("sub") == sub and e.get("idx") == idx:
            return e["english"]
    raise AssertionError("R34 anchor (sub=%d, idx=%d) not found" % (sub, idx))


# ===========================================================================
# Issue #37 -- Ripu -> Leap / Repeal
# ===========================================================================
def _r46_dicts():
    """Extract R46_SUB0 / R46_SUB2 / _RECAP_PROPER dict literals from the
    injector source via AST (never execute the module -- it os.chdir()s and
    loads the glyph table as an import-time side effect)."""
    require_file(R46R47_SRC, "R46/R47 injector")
    src = open(R46R47_SRC, encoding="utf-8").read()
    tree = ast.parse(src)
    wanted = {"R46_SUB0", "R46_SUB2", "_RECAP_PROPER"}
    out = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in wanted
        ):
            out[node.targets[0].id] = ast.literal_eval(node.value)
    missing = wanted - set(out)
    assert not missing, (
        "build/inject_r46_r47.py lost dict literal(s) %s" % sorted(missing)
    )
    return out


def test_issue37_r46_board_leap_not_ripu():
    d = _r46_dicts()
    sub0, sub2, recap = d["R46_SUB0"], d["R46_SUB2"], d["_RECAP_PROPER"]
    for gi in (15, 18, 19):
        text = sub0[gi]
        assert "leap" in text, (
            "issue #37 regression: R46_SUB0[%d] lost 'leap' -- %r" % (gi, text)
        )
        assert "ripu" not in text, (
            "issue #37 regression: R46_SUB0[%d] still says 'ripu' -- %r" % (gi, text)
        )
    assert sub2[17] == "leap", (
        "issue #37 regression: R46_SUB2[17] (bulletin tab label) = %r, "
        "expected 'leap'" % sub2[17]
    )
    assert recap.get("leap") == "Leap", (
        "issue #37 regression: _RECAP_PROPER['leap'] missing/wrong (%r) -- "
        "the bulletin recap pass won't capitalize 'leap' -> 'Leap'"
        % recap.get("leap")
    )
    assert "ripu" not in recap, (
        "issue #37 regression: _RECAP_PROPER still has a 'ripu' entry"
    )


def test_issue37_r34_leap_repeal_stones():
    assert _r34_eng(8, 19) == "Repeal Stone", (
        "issue #37 regression: R34 sub8/idx19 (msg805) = %r, expected "
        "'Repeal Stone'" % _r34_eng(8, 19)
    )
    assert _r34_eng(8, 30) == "Leap Stone", (
        "issue #37 regression: R34 sub8/idx30 (msg816) = %r, expected "
        "'Leap Stone'" % _r34_eng(8, 30)
    )
    desc19 = _r34_eng(9, 19)
    assert "Repeal" in desc19 and "Ripu" not in desc19, (
        "issue #37 regression: R34 sub9/idx19 (msg864) description = %r, "
        "expected it to teach 'Repeal' not 'Ripu'" % desc19
    )
    desc30 = _r34_eng(9, 30)
    assert "Leap" in desc30 and "Ripu" not in desc30, (
        "issue #37 regression: R34 sub9/idx30 (msg875) description = %r, "
        "expected it to teach 'Leap' not 'Ripu'" % desc30
    )


def test_issue37_r2654_library_canon():
    require_file(R2654_NAMES, "R2654 library spell-name canon")
    d = json.load(open(R2654_NAMES, encoding="utf-8"))
    sub41 = d.get("41", {})
    assert sub41.get("19") == "Repeal", (
        "issue #37 regression: R2654 library sub41 id19 = %r, expected "
        "'Repeal' (canon reference)" % sub41.get("19")
    )
    assert sub41.get("30") == "Leap", (
        "issue #37 regression: R2654 library sub41 id30 = %r, expected "
        "'Leap' (canon reference)" % sub41.get("30")
    )


def _live_type2_files():
    # batch_r39_equip_a/_b carry R39 (type-15) entries: the type-2 loader globs
    # them but the type_code==2 filter drops every entry, so nothing here ships
    # via the type-2 path (_b is injected by inject_r39_quest; _a is a dead
    # source superseded by r39_quest_text_aligned.json). Exclude them so this
    # sweep matches what actually ships as type-2 dialogue.
    _excl = {"batch_r39_equip_a.json", "batch_r39_equip_b.json"}
    return sorted(
        f for f in glob.glob(os.path.join(TYPE2_DIR, "batch_*.json"))
        if os.path.basename(f) not in _excl
    )


def _live_chunk_files():
    """The exact translate_chunks/ inputs build_full_english_v2.py loads:
    chunk_00..09 + its hardcoded fix_files list. Extracted via AST from the
    pipeline source itself so this test can't drift from what actually ships
    (rather than re-hardcoding a second copy of the list here)."""
    require_file(BUILD_FULL_V2, "v2 build pipeline")
    src = open(BUILD_FULL_V2, encoding="utf-8").read()
    tree = ast.parse(src)
    fix_files = None
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "fix_files"
        ):
            fix_files = ast.literal_eval(node.value)
            break
    assert fix_files is not None, (
        "could not locate 'fix_files = [...]' in build_full_english_v2.py "
        "-- pipeline input list changed shape, update this test"
    )
    names = ["chunk_%02d_translated.json" % i for i in range(10)] + list(fix_files)
    return [os.path.join(CHUNK_DIR, n) for n in names if os.path.isfile(os.path.join(CHUNK_DIR, n))]


_RIPU_WORD = re.compile(r"\bripu\b", re.IGNORECASE)


def test_issue37_no_stray_ripu_in_live_pipeline_data():
    """Systemic gate: sweep every file the v2 build pipeline actually loads
    (type2 batches auto-discovered by glob + the exact chunk/fix-file list
    build_full_english_v2.py reads) for a leftover 'Ripu' spell name. This
    catches recurrences beyond the specific lines fixed above. Deliberately
    excludes data/translate_chunks/chunk_md_import.json and data/glossary.json
    -- neither is loaded by the live pipeline (md_import is a raw import
    artifact/tool input, glossary.json only feeds tools/build_glossary.py),
    so a stale 'Ripu' there is not a shipping regression."""
    hits = []
    for path in _live_type2_files() + _live_chunk_files():
        entries = json.load(open(path, encoding="utf-8"))
        if not isinstance(entries, list):
            continue
        for e in entries:
            eng = e.get("english")
            if isinstance(eng, str) and _RIPU_WORD.search(eng):
                hits.append((os.path.basename(path), e.get("resource"),
                             e.get("msg_index", e.get("message")), eng))
    assert not hits, (
        "issue #37 regression: %d live dialogue entr(y/ies) still say "
        "'Ripu' instead of Leap/Repeal: %s" % (len(hits), hits[:5])
    )


# ===========================================================================
# Issue #38 -- Spleem / Salome are group-target, not single-target
# ===========================================================================
def test_issue38_spleem_salome_group_target():
    spleem = _r34_eng(9, 10)
    assert "group" in spleem, (
        "issue #38 regression: R34 sub9/idx10 (msg855, Spleem) = %r, "
        "expected it to describe an enemy GROUP" % spleem
    )
    assert "a single enemy" not in spleem, (
        "issue #38 regression: R34 sub9/idx10 (msg855, Spleem) still says "
        "'a single enemy' -- %r" % spleem
    )
    salome = _r34_eng(9, 11)
    assert "group" in salome, (
        "issue #38 regression: R34 sub9/idx11 (msg856, Salome) = %r, "
        "expected it to describe an enemy GROUP" % salome
    )
    assert "a single enemy" not in salome, (
        "issue #38 regression: R34 sub9/idx11 (msg856, Salome) still says "
        "'a single enemy' -- %r" % salome
    )


# ===========================================================================
# Issue #39 -- Vigger storage "buy back from player" = Sell, not Buy
# ===========================================================================
def test_issue39_vigger_storage_sell_not_buy():
    e6 = _load_list(CHUNK_06)
    eng6 = _eng(e6, 45, 85)
    assert eng6.strip() == "Sell /", (
        "issue #39 regression: chunk_06 R45 message85 = %r, expected "
        "'Sell / ' (kaitori = shop buys FROM player = Sell, player's "
        "perspective)" % eng6
    )

    e45 = _load_list(CHUNK_R43_R45)
    eng45 = _eng(e45, 45, 85)
    assert eng45.strip() == "Sell /", (
        "issue #39 regression: chunk_r43_r45 R45 message85 = %r, expected "
        "'Sell / '" % eng45
    )
    eng67 = _eng(e45, 45, 67)
    assert "sell" in eng67.lower() and "buy" not in eng67.lower(), (
        "issue #39 regression: chunk_r43_r45 R45 message67 = %r, expected "
        "'Sell anytime...' not 'Buy anytime...'" % eng67
    )


# ===========================================================================
# Issue #33 -- 魔法剣 mis-rendered "sword" instead of "stone"
# ===========================================================================
def _assert_stone_not_sword(entries, resource, idx, label):
    eng = _eng(entries, resource, idx).lower()
    assert "sword" not in eng, (
        "issue #33 regression: %s (resource=%d msg_index=%d) still says "
        "'sword' -- %r" % (label, resource, idx, eng)
    )
    assert "stone" in eng, (
        "issue #33 regression: %s (resource=%d msg_index=%d) lost 'stone' "
        "-- %r" % (label, resource, idx, eng)
    )


def test_issue33_r1196_girls_magic_stone_not_sword():
    for path, label in ((BATCH_01, "batch_01"), (BATCH_ZZZ_RESTORE, "batch_zzz_restore_labels")):
        entries = _load_list(path)
        for idx in (59, 60, 62, 66):
            _assert_stone_not_sword(entries, 1196, idx, label)


def test_issue33_zakreta_stone_not_sword():
    for path, label in ((BATCH_03, "batch_03"), (BATCH_ZZZ_CHOICEFIX, "batch_zzz_choicefix")):
        entries = _load_list(path)
        for idx in (958,):
            _assert_stone_not_sword(entries, 1203, idx, label)
    entries = _load_list(BATCH_03)
    _assert_stone_not_sword(entries, 1203, 961, "batch_03")


def test_issue33_melanie_through_stone_not_sword():
    entries = _load_list(BATCH_04)
    for idx in (817, 819, 820, 821, 826, 840):
        _assert_stone_not_sword(entries, 1205, idx, "batch_04")


# ===========================================================================
# Issue #34 -- B1F narration: barrels, not stairs
# ===========================================================================
def test_issue34_b1f_barrels_not_stairs():
    entries = _load_list(BATCH_03)
    eng = _eng(entries, 1203, 1534).lower()
    assert "stairs" not in eng, (
        "issue #34 regression: batch_03 R1203 msg1534 still says 'stairs' "
        "-- %r" % eng
    )
    assert "barrels" in eng, (
        "issue #34 regression: batch_03 R1203 msg1534 lost 'barrels' -- %r"
        % eng
    )


# ===========================================================================
# Issue #35 -- "we were ambushed" (not "you"); corridor -> bridge
# ===========================================================================
def test_issue35_bridge_not_corridor():
    entries = _load_list(BATCH_03)
    for idx in (1164, 1166):
        eng = _eng(entries, 1203, idx).lower()
        assert "corridor" not in eng, (
            "issue #35 regression: batch_03 R1203 msg%d still says "
            "'corridor' -- %r" % (idx, eng)
        )
        assert "bridge" in eng, (
            "issue #35 regression: batch_03 R1203 msg%d lost 'bridge' -- %r"
            % (idx, eng)
        )


def test_issue35_we_were_ambushed():
    entries = _load_list(BATCH_03)
    eng = _eng(entries, 1203, 1173).lower()
    norm = " ".join(eng.replace("/", " ").split())  # collapse the " / " line breaks
    assert "you were ambushed" not in norm, (
        "issue #35 regression: batch_03 R1203 msg1173 reverted to 'you were "
        "ambushed' -- %r" % eng
    )
    assert "we were ambushed" in norm, (
        "issue #35 regression: batch_03 R1203 msg1173 lost 'we were "
        "ambushed' -- %r" % eng
    )


# ===========================================================================
# Issue #36 -- Lang quest item: Medicine, not Barrier/Potion
# ===========================================================================
def test_issue36_lang_r1197_medicine_not_potion():
    entries = _load_list(BATCH_01)
    for idx in (617, 620, 622, 623, 625, 636):
        eng = _eng(entries, 1197, idx).lower()
        assert "potion" not in eng and "barrier" not in eng, (
            "issue #36 regression: batch_01 R1197 msg%d still says "
            "'potion'/'barrier' -- %r" % (idx, eng)
        )
        assert "medicine" in eng, (
            "issue #36 regression: batch_01 R1197 msg%d lost 'medicine' "
            "-- %r" % (idx, eng)
        )


def test_issue36_r39_quest_text_medicine():
    require_file(R39_QUEST, "R39 quest text (Lang secret-medicine mirror)")
    d = json.load(open(R39_QUEST, encoding="utf-8"))
    for key in ("374", "375", "376"):
        eng = d[key]["english"].lower()
        assert "potion" not in eng, (
            "issue #36 regression: r39_quest_text_aligned id%s still says "
            "'potion' -- %r" % (key, eng)
        )
        assert "medicine" in eng, (
            "issue #36 regression: r39_quest_text_aligned id%s lost "
            "'medicine' -- %r" % (key, eng)
        )


TESTS = [
    test_issue37_r46_board_leap_not_ripu,
    test_issue37_r34_leap_repeal_stones,
    test_issue37_r2654_library_canon,
    test_issue37_no_stray_ripu_in_live_pipeline_data,
    test_issue38_spleem_salome_group_target,
    test_issue39_vigger_storage_sell_not_buy,
    test_issue33_r1196_girls_magic_stone_not_sword,
    test_issue33_zakreta_stone_not_sword,
    test_issue33_melanie_through_stone_not_sword,
    test_issue34_b1f_barrels_not_stairs,
    test_issue35_bridge_not_corridor,
    test_issue35_we_were_ambushed,
    test_issue36_lang_r1197_medicine_not_potion,
    test_issue36_r39_quest_text_medicine,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_v192_spell_quest_fixes")
