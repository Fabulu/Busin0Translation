#!/usr/bin/env python3
"""
test_r39_spell_desc_alignment.py -- regression gates for the THREE v159
data-corruption classes (see runs/CLAUDE-RUNS/AUDIT-20260702-full-project.md):

(a) R39 SPELL-DESCRIPTION MISALIGNMENT (+3..+5 shift).  The original
    data/r39_spell_descriptions.json was authored from an enumeration that
    SKIPPED 5 near-duplicate block-2 records (g23/24/25/27/39) and SPLIT one
    record (g53) into two entries, so every key from 23 up pointed 3..5 slots
    past its real spell -- Feel showed Yaiba's text, Revive lost its
    caster-dies warning, etc.  v159 realigned the JSON to the TRUE 1-based
    FFFF-record indices (g3..g58, injected by tools/patch_r39_spell_desc.py:
    block-2 record k == FFFF-group k, block1 g(k+1) == the spell NAME for
    name-record k in tools/patch_r39_inline.py SPELL_NAMES).
    Gates: T1 (JSON invariants), T2 (semantic anchor pins), T3 (built block 2
    decodes each key at the RIGHT record).

(b) POISONED msg_glyph_map.json KANJI ENTRIES.  Glyph ids 608/876/722/350
    were mapped to the wrong kanji (treasure-box vocabulary instead of battle
    vocabulary), which produced mistranslations like the battle order-confirm
    prompt reading "Open box?" instead of "Start turn?".
    Gates: T4 (glyph-map tripwire), T5 (built R47 sub0 battle prompts).

(c) R2654 LIBRARY ROWS 1886/1887 MISSING from
    data/translate_chunks/chunk_r2654_library_fix.json (now "Guide"/"Books").
    Gate: T6 (built R2654 rows decode to Guide/Books).

TIERS: T1/T2/T4 are static (always run); T3/T5/T6 are TIER-2 (Skip when the
build outputs are absent).  All decoders are self-contained -- the tests never
import the build scripts they gate.
"""

import glob
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import DATA_DIR, PACKDATA_RES_DIR, ROOT, Skip, main_exit

SPELL_DESC_JSON = os.path.join(DATA_DIR, "r39_spell_descriptions.json")
GLYPH_MAP_JSON = os.path.join(DATA_DIR, "msg_glyph_map.json")
BUILT_R39 = os.path.join(PACKDATA_RES_DIR, "0039_type15.raw")
BUILT_R47 = os.path.join(PACKDATA_RES_DIR, "0047_type03.raw")

# Spell descriptions live in R39 block 2: keys g3..g58 (1-based FFFF-record
# index; g1 = offset table, g2 = separator -- see tools/patch_r39_spell_desc.py).
KEY_LO, KEY_HI = 3, 58
MAX_LINE_CELLS = 26   # spell-desc window budget per line
MAX_LINES = 2

# The history lesson every alignment failure must teach (bug class (a)):
SHIFT_BUG = (
    "HISTORY (v159): the pre-v159 JSON was authored from an enumeration that "
    "skipped 5 near-duplicate block-2 records (g23/24/25/27/39) and split g53, "
    "shifting keys 23..58 by +3..+5 records -- Feel displayed Yaiba's buff "
    "text, Revive lost its caster-dies warning. If a re-import regresses this, "
    "REALIGN against the pristine block-2 decode (scratchpad audit10 ground "
    "truth / runs/CLAUDE-RUNS/AUDIT-20260702-full-project.md) before shipping."
)


# ---------------------------------------------------------------------------
# Self-contained decode helpers (mirror the PROVEN glyph rule: ASCII glyph id
# gid renders chr(gid+32) for 0..94; 0xFFFE = line break; ids >= 0xFB00 are
# control words). 0x0000 pad cells therefore decode to ' ' -- strip them.
# ---------------------------------------------------------------------------
def _split_ffff_groups(blob, start, size):
    """BE-u16 stream [start, start+size) -> list of FFFF-delimited groups."""
    groups, cur = [], []
    end = min(start + size, len(blob))
    pos = start
    while pos + 2 <= end:
        w = struct.unpack_from(">H", blob, pos)[0]
        if w == 0xFFFF:
            groups.append(cur)
            cur = []
        else:
            cur.append(w)
        pos += 2
    return groups


def _decode_cells(cells, linebreak=" / "):
    out = []
    for g in cells:
        if g == 0xFFFE:
            out.append(linebreak)
        elif 0 <= g <= 94:
            out.append(chr(0x20 + g))
        else:
            out.append("[%04X]" % g)
    return "".join(out)


def _clean_text(cells):
    """Decode a group dropping control words (>= 0xFB00, incl. the trailing
    0xFFFE line terminator some slots keep) and stripping 0x0000 pad spaces
    and underscore padders."""
    content = [g for g in cells if g < 0xFB00]
    return _decode_cells(content).strip(" _")


def _norm_ws(s):
    """Whitespace-normalize for text comparison (collapses pads and ' / ')."""
    return " ".join(s.split())


def _load_spell_json():
    spec = json.load(open(SPELL_DESC_JSON, encoding="utf-8"))
    return spec, spec.get("descriptions", {})


# ---------------------------------------------------------------------------
# T1 (static): JSON structural invariants
# ---------------------------------------------------------------------------
def test_json_invariants():
    spec, desc = _load_spell_json()
    # keys exactly 3..58 -- g1 (offset table) and g2 (separator) must NEVER
    # appear (writing text into them corrupts block-2 record addressing).
    keys = sorted(int(k) for k in desc)
    expected = list(range(KEY_LO, KEY_HI + 1))
    assert keys == expected, (
        "descriptions keys are not exactly %d..%d (%d entries): missing=%s "
        "extra=%s. g1/g2 are structural (offset table / separator) and keys "
        "outside 3..58 do not exist in block 2. %s"
        % (
            KEY_LO,
            KEY_HI,
            len(expected),
            sorted(set(expected) - set(keys)),
            sorted(set(keys) - set(expected)),
            SHIFT_BUG,
        )
    )
    for k in sorted(desc, key=int):
        v = desc[k]
        try:
            v.encode("ascii")
        except UnicodeEncodeError:
            raise AssertionError(
                "descriptions[%s] is not ASCII-encodable (%r) -- the spell "
                "font encoder (english_glyph_table.json) only draws the "
                "char-32 ASCII set" % (k, v)
            )
        lines = v.split(" / ")
        assert len(lines) <= MAX_LINES, (
            "descriptions[%s] has %d lines (max %d): %r"
            % (k, len(lines), MAX_LINES, v)
        )
        for li, line in enumerate(lines):
            assert len(line) <= MAX_LINE_CELLS, (
                "descriptions[%s] line %d is %d cells (max %d): %r"
                % (k, li, len(line), MAX_LINE_CELLS, line)
            )
    # v159 translates ALL 56 records; a non-empty pristine list would leave
    # untranslated JP records shipping silently.
    pjr = spec.get("_pristine_jp_records")
    assert pjr == [], (
        "_pristine_jp_records is %r, expected [] -- v159 authored English for "
        "all of g3..g58; re-adding pristine passthroughs ships JP text" % (pjr,)
    )


# ---------------------------------------------------------------------------
# T2 (static): SEMANTIC ANCHOR PINS.  These five slots are the bug's
# diagnostic fingerprint: under the pre-v159 +3..+5 shift each of them showed
# a NEIGHBORING spell's text, so pinning their MEANING (not exact wording)
# catches any future re-import that regresses the alignment.
# ---------------------------------------------------------------------------
def test_semantic_anchor_pins():
    _spec, desc = _load_spell_json()

    def pin(key, predicate, need, meaning):
        v = desc.get(str(key), "")
        lv = v.lower()
        assert predicate(lv), (
            "ANCHOR PIN key %d (%s) violated: %r must contain %s. %s"
            % (key, meaning, v, need, SHIFT_BUG)
        )

    # key 31 = Feel, a HEAL. Under the shift it displayed Yaiba's BUFF text
    # (the original bug sighting, feeldesc.p2s).
    pin(31, lambda s: "estor" in s and "hp" in s,
        "'estor' (restore) AND 'HP'", "Feel: restores HP")
    # key 35 = Yaiba, the hit/attack BUFF that Feel was wrongly showing.
    pin(35, lambda s: "hit" in s, "'hit'", "Yaiba: raises hit (buff)")
    # key 58 = Revive. Its caster-DIES cost is gameplay-critical; the shifted
    # JSON dropped the warning entirely.
    pin(58, lambda s: "aster" in s, "'aster' (caster sacrifice)",
        "Revive: costs the caster's life")
    # key 3 = Creta, single-target FIRE (element anchor at the low, unshifted
    # end -- if even THIS moves, the whole table slid).
    pin(3, lambda s: "fire" in s, "'fire'", "Creta: fire element")
    # key 23 = JCreta, ALL-ENEMY fire. This slot sat exactly on a skipped
    # near-duplicate record, ground zero of the enumeration bug.
    pin(23, lambda s: "fire" in s or "all" in s or "every" in s,
        "'fire' or 'all'/'every'", "JCreta: all-enemy fire")


# ---------------------------------------------------------------------------
# T3 (TIER-2): decode the BUILT R39 block 2 and prove the injector wrote each
# JSON key to the RIGHT record (the exact failure mode of bug class (a)).
# ---------------------------------------------------------------------------
def test_built_block2_alignment():
    if not os.path.isfile(BUILT_R39):
        raise Skip("build/packdata_resources/0039_type15.raw missing (run a build)")
    _spec, desc = _load_spell_json()
    data = open(BUILT_R39, "rb").read()
    # 15-record LE header (16 bytes each): rec[2] = (idx, size, off, 0) is
    # block 2 = spell descriptions.
    idx, size, off, _z = struct.unpack_from("<4I", data, 2 * 16)
    assert idx == 2, "R39 header rec[2] idx is %d, expected 2" % idx
    assert off + size <= len(data), (
        "R39 block 2 (off=%d size=%d) exceeds file (%d bytes)"
        % (off, size, len(data))
    )
    groups = _split_ffff_groups(data, off, size)
    assert len(groups) == 58, (
        "built R39 block 2 has %d FFFF-groups, expected exactly 58 "
        "(g1 offset table + g2 separator + g3..g58 descriptions). A different "
        "count means the block-2 rebuild broke record addressing. %s"
        % (len(groups), SHIFT_BUG)
    )
    # group index k (0-based) == g(k+1); JSON key g == groups[g-1].
    for key in (31, 35, 58):
        built = _norm_ws(_decode_cells(groups[key - 1]))
        want = _norm_ws(desc[str(key)])
        assert built == want, (
            "built R39 block-2 record g%d decodes to %r but the JSON key %d "
            "says %r -- the injector wrote this description to the WRONG "
            "record. %s" % (key, built, key, want, SHIFT_BUG)
        )


# ---------------------------------------------------------------------------
# T4 (static): glyph-map poison tripwire (bug class (b)).
# ---------------------------------------------------------------------------
# The v159-corrected kanji for the four poisoned glyph ids
# (written as escapes so the source survives any console codec):
POISON_FIXES = {
    "608": "闘",  # tou  (fight)   -- was 箱 hako (box)
    "876": "始",  # shi  (begin)   -- was 錠 jou  (lock)
    "722": "攻",  # kou  (attack)  -- was 獲 kaku (seize)
    "350": "撃",  # geki (strike)  -- was 得 toku (gain)
    # v161 additions (names workstream): proven by the live 騎士団長 nameplate
    # (fuckingthisguyman.p2s) + the R1193 intro-narration slice for 404, and a
    # corpus-wide before/after key audit (5 name_labels keys re-derived).
    "483": "騎",  # ki   (knight)  -- was 無 mu   (nothing)
    "494": "士",  # shi  (warrior) -- was 帰 ki   (return)
    "510": "団",  # dan  (group)   -- was 前 mae  (front)
    "404": "長",  # chou (leader)  -- was 像 zou  (statue)
}


def test_glyph_map_poison_tripwire():
    m = json.load(open(GLYPH_MAP_JSON, encoding="utf-8"))
    for gid, want in POISON_FIXES.items():
        got = m.get(gid)
        assert got == want, (
            "msg_glyph_map.json[%s] is %s, expected %s. HISTORY (v159): these "
            "four entries were POISONED with treasure-box vocabulary "
            "(608=box, 876=lock, 722=seize, 350=gain), which made the battle "
            "order-confirm prompt translate as 'Open box?' instead of "
            "'Start turn?' (JP 'commence battle' -- see build/inject_r46_r47.py "
            "R47_SUB0 g12..g18 and AUDIT-20260702). Do NOT revert this entry "
            "without re-anchoring the kanji semantically against pristine RAM "
            "decodes (scratchpad audit10 ground truth)."
            % (gid, ascii(got), ascii(want))
        )


# ---------------------------------------------------------------------------
# T5 (TIER-2): built R47 sub0 battle order-confirm prompts (bug class (b)).
# ---------------------------------------------------------------------------
def _r47_sub0_groups():
    data = open(BUILT_R47, "rb").read()
    # Sub table at file start: 16-byte LE records (idx, size, offset, 0).
    idx, size, off, _z = struct.unpack_from("<4I", data, 0)
    assert idx == 0, "R47 sub-table rec[0] idx is %d, expected 0" % idx
    assert off + size <= len(data), (
        "R47 sub0 (off=%d size=%d) exceeds file (%d bytes)"
        % (off, size, len(data))
    )
    return _split_ffff_groups(data, off, size)


def test_built_r47_battle_prompts():
    if not os.path.isfile(BUILT_R47):
        raise Skip("build/packdata_resources/0047_type03.raw missing (run a build)")
    groups = _r47_sub0_groups()
    assert len(groups) > 18, "built R47 sub0 has only %d groups" % len(groups)
    texts = {g: _clean_text(groups[g]) for g in (12, 13, 18)}

    # v160: the trailing 0xFFFE line terminator is the RELEASE format for R47.
    # Every pristine R47 group ends with 0xFFFE; the injector used to overwrite
    # it with 0x0000 padding, which made every battle title pill render its
    # text one full line BELOW the pill (long-standing cosmetic bug, live
    # A/B-PROVEN 2026-07-02 via the v159 R47_FFFE_EXPERIMENT diagnostic ISO).
    # v160 preserves the terminator by default and ships strings authored to
    # fit cap-1 ('Yes', 'Atk', 'Start turn'; #28 renamed Go!!->Yes).
    for g in (12, 13, 18):
        assert groups[g] and groups[g][-1] == 0xFFFE, (
            "built R47 sub0 g%d does NOT end with the 0xFFFE line terminator "
            "-- the v160 pill fix regressed: without the terminator the "
            "battle title pills render their text one line below the pill "
            "(see AUDIT-20260702 + inject_r46_r47.py keep_fffe)." % g
        )

    poison = (
        "HISTORY (v159): before the msg_glyph_map poison fix these battle "
        "pills decoded through box/lock/seize/gain kanji and were translated "
        "as the 'Open box?' treasure prompt. The real JP is the per-turn "
        "order-confirm flow (proven via "
        "weirdasfuckdialogueatendofcombatturn.p2s + R34 prose anchors)."
    )
    assert texts[12].startswith("Start turn"), (
        "built R47 sub0 g12 is %r, expected it to start 'Start turn' (the "
        "order-confirm prompt). %s" % (texts[12], poison)
    )
    assert texts[13] == "Yes", (
        "built R47 sub0 g13 is %r, expected 'Yes' (confirm choice, JP "
        "'commence battle'; issue #28 renamed Go!!->Yes; 5-cell slot minus the "
        "preserved 0xFFFE terminator). %s" % (texts[13], poison)
    )
    assert texts[18] == "Atk", (
        "built R47 sub0 g18 is %r, expected 'Atk' (per-attack pill; was "
        "'Gain' under the 722/350 seize/gain mis-decode; 5-cell FFFE budget). %s"
        % (texts[18], poison)
    )


# ---------------------------------------------------------------------------
# T6 (TIER-2): built R2654 library rows 1886/1887 (bug class (c)).
# ---------------------------------------------------------------------------
def test_built_r2654_library_rows():
    hits = glob.glob(os.path.join(PACKDATA_RES_DIR, "2654*.raw"))
    if not hits:
        raise Skip("build/packdata_resources/2654*.raw missing (run a build)")
    data = open(hits[0], "rb").read()
    # R2654 is a FLAT BE-u16 FFFF-group stream (Step 2 flat format, whole file).
    groups = _split_ffff_groups(data, 0, len(data))
    assert len(groups) > 1886, (
        "built R2654 has only %d FFFF-groups, need > 1886" % len(groups)
    )
    missing = (
        "HISTORY (v159): library rows 1886 ('Guide') and 1887 ('Books') were "
        "MISSING from data/translate_chunks/chunk_r2654_library_fix.json and "
        "shipped untranslated JP. group index = message - 1 (0-indexed FFFF "
        "groups)."
    )
    g1886 = _clean_text(groups[1885])
    assert g1886 == "Guide", (
        "built R2654 group[1885] (message 1886) decodes to %r, expected "
        "'Guide'. %s" % (g1886, missing)
    )
    g1887 = _clean_text(groups[1886])
    assert g1887 == "Books", (
        "built R2654 group[1886] (message 1887) decodes to %r, expected "
        "'Books'. %s" % (g1887, missing)
    )


TESTS = [
    test_json_invariants,
    test_semantic_anchor_pins,
    test_built_block2_alignment,
    test_glyph_map_poison_tripwire,
    test_built_r47_battle_prompts,
    test_built_r2654_library_rows,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_r39_spell_desc_alignment")
