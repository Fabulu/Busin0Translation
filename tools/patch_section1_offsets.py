#!/usr/bin/env python3
"""
patch_section1_offsets.py -- Patch Section 1 glyph offsets after variable-size Section 2 injection
==================================================================================================

When English translations are injected into Section 2 of type-02 resources, messages
can grow or shrink.  Section 1 contains the scene-script opcode stream that references
Section 2 by word offset (glyph index).  After injection, these offsets become stale
and must be updated to match the new Section 2 layout.

Section 1 is a BYTE-addressed big-endian-u16 opcode stream interpreted by the
dispatcher at VA 0x2F3230 (193-entry handler table; several opcodes have ODD byte
lengths).  It is therefore disassembled with tools/sec1_disasm.py -- a BFS walk
from pc=0 following all jump/gosub/conditional targets -- and ONLY the operands of
WALKED instructions are patched.  Word-grid pattern matching (used through v84) can
never work on this stream and corrupted scenes; it has been removed entirely.

Patched opcodes (byte lengths include the 2-byte opcode; all operands BE):
  0x04 DISPLAY_TEXT  (10 bytes): u32 glyph word offset @pc+2, u32 word count @pc+6.
       For cnt>0 the span ALWAYS ends exactly on a group's 0xFFFF terminator.
       Mid-group starts skip a name-label prefix at the head of the group.
  0x0C SET_NAME_REF / 0x0D CLEAR_NAME_REF (6 bytes): u16 param @pc+2, u16 idx @pc+4.
       NEVER remapped.  `idx` is NOT a Section-2 glyph offset -- it is a
       speaker/portrait CHANNEL BIT index (0..511).  EXE handler 0x2F3BB0 calls
       0x302020(param,idx,set=1), which does table[param][idx>>5] |= 1<<(idx&31)
       (param in [0,12] selects a 512-bit flag register at 0x565090/0x5650D0/
       0x565110/...).  The per-frame portrait-emit branch reads those flags, so
       remapping idx corrupts the speaker->portrait lookup and drops the portrait
       BITBLT (the v86 R1251 portrait regression).  These operands are preserved
       byte-for-byte.
  0x14 NAME/LABEL REF (14 bytes): u16 param @pc+2, s16 @pc+4 (always 0xFFFF),
       u32 NAME_OFF @pc+6 (absolute sec2 word index), u32 NAME_CNT @pc+10.
       Draws character-name labels / floating narration.  Names are plain glyph
       prefixes (<0xFB00) at the head of dialogue groups (sometimes stacked), or
       slices of label-table groups, or point into the trailing (non-group)
       region after the last 0xFFFF.

Jump targets (0x06/0x07/0x08/0x0B/0x11/0x12) are BYTE offsets relative to the
Section-1 base (file offset 0x20) and are NOT affected by Section-2 resizing --
they are never modified.

Name-island preservation (BUG-2):
  inject_and_patch() walks the original Section 1 and buckets 0x14 records by
  target group.  When a translated group's 0x14 slices form a clean prefix
  partition with dialogue after it, the group is rebuilt as
  [English name label(s)][encoded English dialogue]; labels are translated via
  data/name_labels.json (decoded through data/msg_glyph_map.json) and kept as
  the original JP glyphs verbatim when not in the dictionary.  Groups whose
  slices are NOT a clean prefix (label tables) are left untranslated so all
  slice offsets stay valid.

Usage:
    python tools/patch_section1_offsets.py <original.raw> <patched.raw> [output.raw]

    If output.raw is omitted, the patched file is overwritten in-place.

    Can also be called as a library:
        from patch_section1_offsets import patch_section1, inject_and_patch
"""

import sys
import os
import struct
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sec1_disasm import walk, extract_records, LENB

SECTOR = 2048
HEADER_SIZE = 0x20
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The unwalked-island DISPLAY_TEXT sweep (patch_section1 pass a2) is ON by
# default and MUST stay on for shipping builds -- it repoints choice/narration
# display opcodes that live in code islands the BFS walk cannot reach.  The
# toggle exists ONLY so regression tests can capture a sweep-off baseline to
# prove the sweep touches exclusively unwalked opcodes.
ISLAND_SWEEP_ENABLED = True

# -- lazily-loaded shared tables ------------------------------------------------
_GLYPH_MAP = None       # glyph index (str) -> JP char
_NAME_LABELS = None     # JP name string -> English
_NAMEPLATE_OVERRIDES = None  # (res_idx, msg_idx) -> English speaker label
_ENG_TABLE = None       # ASCII char -> glyph index
_ENG_REV = None         # glyph index -> ASCII char (reverse of _ENG_TABLE)


def _load_tables():
    global _GLYPH_MAP, _NAME_LABELS, _NAMEPLATE_OVERRIDES, _ENG_TABLE, _ENG_REV
    if _GLYPH_MAP is None:
        _GLYPH_MAP = json.load(
            open(os.path.join(_ROOT, "data", "msg_glyph_map.json"), encoding="utf-8")
        )
    if _NAME_LABELS is None:
        try:
            d = json.load(
                open(os.path.join(_ROOT, "data", "name_labels.json"), encoding="utf-8")
            )
            _NAME_LABELS = {k: v for k, v in d.items() if not k.startswith("_")}
        except OSError:
            _NAME_LABELS = {}
    if _NAMEPLATE_OVERRIDES is None:
        # Per-(resource, group) 0x14 name-island override. Needed where the
        # decoded JP key is ambiguous across resources (Glyph-Page Law): e.g.
        # 士騎戦 -> "Knight" globally but really 冒険者/Adventurer in specific
        # groups, while other 士騎戦 islands ARE genuine knights (R1196 g752) or
        # a named speaker (R1206 g244 Uuri). Consulted for the ACTIVE speaker
        # slice before the name_labels lookup, so only the listed groups change.
        _NAMEPLATE_OVERRIDES = {}
        try:
            d = json.load(
                open(os.path.join(_ROOT, "data", "nameplate_overrides.json"),
                     encoding="utf-8")
            )
            for res_k, groups in d.items():
                if res_k.startswith("_"):
                    continue
                for grp_k, label in groups.items():
                    _NAMEPLATE_OVERRIDES[(int(res_k), int(grp_k))] = label
        except OSError:
            pass
    if _ENG_TABLE is None:
        _ENG_TABLE = json.load(
            open(os.path.join(_ROOT, "data", "english_glyph_table.json"), encoding="utf-8")
        )
    if _ENG_REV is None:
        # First-wins reverse map so the canonical char per glyph is stable.
        _ENG_REV = {}
        for ch, g in _ENG_TABLE.items():
            _ENG_REV.setdefault(g, ch)


def _enc_char(ch):
    """English char -> glyph index (same fallback rule as the build pipeline)."""
    if ch in _ENG_TABLE:
        return _ENG_TABLE[ch]
    if ch.lower() in _ENG_TABLE:
        return _ENG_TABLE[ch.lower()]
    return 31


def _decode_jp(glyphs):
    """Decode a plain glyph slice to a JP string, or None if not decodable."""
    out = []
    for g in glyphs:
        if g >= 0xFB00:
            return None  # control code -- not a plain name
        ch = _GLYPH_MAP.get(str(g))
        if ch is None:
            return None
        out.append(ch)
    return "".join(out)


# ===============================================================================
# Section 2 group parsing
# ===============================================================================
def parse_sec2_group_offsets(sec2_data):
    """
    Parse Section 2 into FFFF-delimited groups and return their word-start offsets.

    Returns (groups, trailing_start_word):
      groups         -- list of (group_start_word, group_end_word); group_end_word
                        is the index of the FFFF terminator itself.  The group
                        content is words[group_start_word:group_end_word].
      trailing_start -- word index of the first trailing (non-group) word after
                        the last FFFF (== total word count when there is none).
    """
    n_words = len(sec2_data) // 2
    groups = []
    start = 0
    for i in range(n_words):
        w = struct.unpack_from(">H", sec2_data, i * 2)[0]
        if w == 0xFFFF:
            groups.append((start, i))
            start = i + 1
    return groups, start


def _find_group(groups, word_offset):
    """Binary-search the group whose [start..FFFF] range contains word_offset."""
    lo, hi = 0, len(groups) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        gs, ge = groups[mid]
        if word_offset < gs:
            hi = mid - 1
        elif word_offset > ge:
            lo = mid + 1
        else:
            return mid
    return None


# ===============================================================================
# 0x14 label bucketing
# ===============================================================================
def _bucket_labels(label_recs, old_groups, old_trailing_start):
    """
    Bucket walked 0x14 records by target group.

    Returns (per_group, trailing_recs):
      per_group     -- {group_index: sorted unique [(rel_off, cnt), ...]}
      trailing_recs -- list of records whose NAME_OFF >= old_trailing_start
    """
    per_group = {}
    trailing = []
    for r in label_recs:
        if r["off"] >= old_trailing_start:
            trailing.append(r)
            continue
        gi = _find_group(old_groups, r["off"])
        if gi is None:
            trailing.append(r)
            continue
        gs, _ = old_groups[gi]
        per_group.setdefault(gi, set()).add((r["off"] - gs, r["cnt"]))
    return {gi: sorted(s) for gi, s in per_group.items()}, trailing


def _clean_prefix_len(slices):
    """
    If the (rel_off, cnt) slices form a clean prefix partition starting at 0
    (slice k starts at the sum of previous slice counts), return the total
    prefix length.  Otherwise return None.
    """
    if not slices or slices[0][0] != 0:
        return None
    pos = 0
    for so, sc in slices:
        if so != pos or sc <= 0:
            return None
        pos = so + sc
    return pos


# ===============================================================================
# Island digit-table 0x14 slices (issue #44)
# ===============================================================================
# The engine prints runtime numbers (gold, member id, EXP...) through a
# per-message DIGIT-GLYPH TABLE: an 11-word slice [0..9 digit glyphs + minus]
# at the head of a group, registered by opcode 0x14 with p2 (u16 @+4) set to a
# GAME-VARIABLE index (p2 != 0xFFFF, p2 < 0x1B1 -- EXE handler 0x2F3F00 stores
# (off, cnt, p2) into ctx+0xA0+12*p1; the FE0x number formatter 0x307510 then
# reads glyph = Section2[off + digit] LIVE).  The 0x04 display offset points
# PAST the table (rel=11) so the template never renders in JP.
#
# Walked digit-table 0x14s are handled by the ordinary name-plan machinery.
# But three R1200 registrations live in UNWALKED islands; the a3 label sweep's
# cnt<=10 nameplate gate skipped them, so they shipped STALE -- the offsets
# pointed into the grown English Section 2 and numbers rendered as random
# English letters (issue #44 gold garbage).  The helpers below seed the
# name plan for exactly these groups so (a) the injector preserves the
# pristine 11-word table at the group head and (b) the a3 sweep can remap the
# 0x14 (plan-matched cnt==11 ONLY) and its paired mid-group 0x04.
DIGIT_TEMPLATE = tuple(range(0x10, 0x1A)) + (0x0D,)  # ０１２３４５６７８９−


def _island_digit_slices(sec1, instrs, group_ranges, words):
    """
    Find unwalked island 0x14 records that register a digit-glyph table.

    STRICT gate (every clause must hold; anything else is left untouched):
      * opcode bytes not part of any walked instruction (overlap gate);
      * p1 (slot) < 10 and p2 is a real game-variable index
        (p2 != 0xFFFF and p2 < 0x1B1 -- the 0x301E10 bound);
      * cnt == 11 and off == a group start;
      * the pristine slice content is EXACTLY the canonical digit template
        (glyphs 0x10..0x19 + 0x0D).  This is a content check on THIS
        resource's pristine bytes, not a cross-resource glyph-map assumption.

    Returns {group_index: [(0, 11)]}.
    """
    walked_bytes = set()
    for pc, op in instrs.items():
        walked_bytes.update(range(pc, pc + LENB[op]))
    start_to_gi = {gs: gi for gi, (gs, _ge) in enumerate(group_ranges)}
    out = {}
    n = len(sec1)
    for pc in range(0, n - LENB[0x14] + 1):
        if pc in instrs:
            continue
        if struct.unpack_from(">H", sec1, pc)[0] != 0x0014:
            continue
        if not walked_bytes.isdisjoint(range(pc, pc + LENB[0x14])):
            continue
        p1 = struct.unpack_from(">H", sec1, pc + 2)[0]
        p2 = struct.unpack_from(">H", sec1, pc + 4)[0]
        off = struct.unpack_from(">I", sec1, pc + 6)[0]
        cnt = struct.unpack_from(">I", sec1, pc + 10)[0]
        if p1 >= 10 or p2 == 0xFFFF or p2 >= 0x1B1 or cnt != 11:
            continue
        gi = start_to_gi.get(off)
        if gi is None:
            continue
        gs, ge = group_ranges[gi]
        if gs + 11 > ge:
            continue
        if tuple(words[gs:gs + 11]) != DIGIT_TEMPLATE:
            continue
        out.setdefault(gi, [(0, 11)])
    return out


# ===============================================================================
# Section 1 patcher
# ===============================================================================
def patch_section1(orig_data, patched_data, name_plan=None, res_name="?"):
    """
    Patch Section 1 glyph offsets in patched_data to match its (potentially
    resized) Section 2, using orig_data as the reference for old offsets.

    The ORIGINAL Section 1 is disassembled (BFS walk) and ONLY operand bytes of
    walked 0x04 / 0x0C / 0x0D / 0x14 instructions are rewritten.  Jump targets
    are byte offsets into Section 1 and are never modified.

    name_plan (optional, produced by inject_and_patch): {group_index: {
        'old_slices': [(rel_off, cnt), ...],   # 0x14 prefix slices, old layout
        'new_slices': [(rel_off, cnt), ...],   # same slices in the new layout
        'old_prefix_len': int, 'new_prefix_len': int}}
      For groups without an entry the group content is assumed unchanged
      (identity in-group mapping).

    Returns the fully patched file as bytes.  Raises ValueError on any
    structural violation (a corrupted file must never be shipped).
    """
    if len(orig_data) < HEADER_SIZE or len(patched_data) < HEADER_SIZE:
        raise ValueError("Files too small to be type-02 resources")

    orig_sec2_size = struct.unpack_from("<I", orig_data, 0x14)[0]
    orig_sec2_off = struct.unpack_from("<I", orig_data, 0x18)[0]
    pat_sec2_size = struct.unpack_from("<I", patched_data, 0x14)[0]
    pat_sec2_off = struct.unpack_from("<I", patched_data, 0x18)[0]

    if orig_sec2_off != pat_sec2_off:
        raise ValueError(
            "Section 2 offset mismatch (orig=0x%x, patched=0x%x) -- "
            "Section 1 must be preserved byte-for-byte before this step"
            % (orig_sec2_off, pat_sec2_off)
        )
    sec2_off = orig_sec2_off

    orig_sec1 = bytes(orig_data[HEADER_SIZE:sec2_off])
    pat_sec1 = bytes(patched_data[HEADER_SIZE:sec2_off])
    if orig_sec1 != pat_sec1:
        raise ValueError(
            "R%s: Section 1 of patched file differs from original BEFORE offset "
            "patching -- refusing to continue" % res_name
        )

    orig_sec2 = orig_data[sec2_off : sec2_off + orig_sec2_size]
    new_sec2 = patched_data[sec2_off : sec2_off + pat_sec2_size]

    old_groups, old_trailing_start = parse_sec2_group_offsets(orig_sec2)
    new_groups, new_trailing_start = parse_sec2_group_offsets(new_sec2)
    if len(old_groups) != len(new_groups):
        raise ValueError(
            "R%s: group count changed (%d -> %d) -- injection must preserve "
            "the group structure" % (res_name, len(old_groups), len(new_groups))
        )
    trailing_delta = new_trailing_start - old_trailing_start

    old_n_words = len(orig_sec2) // 2
    new_n_words = len(new_sec2) // 2
    new_words = [
        struct.unpack_from(">H", new_sec2, i * 2)[0] for i in range(new_n_words)
    ]
    old_words = [
        struct.unpack_from(">H", orig_sec2, i * 2)[0] for i in range(old_n_words)
    ]

    # Disassemble the ORIGINAL Section 1
    ok, instrs = walk(orig_sec1)
    if not ok:
        raise ValueError(
            "R%s: Section 1 walk failed -- cannot safely patch offsets" % res_name
        )
    recs = extract_records(orig_sec1, instrs)

    if name_plan is None:
        # Standalone use: derive a conservative plan.  For groups whose content
        # is unchanged the identity mapping is always correct; for changed
        # groups, keep the prefix mapping only if the old prefix glyphs are
        # still verbatim at the head of the new group.
        name_plan = {}
        per_group, _ = _bucket_labels(recs["label"], old_groups, old_trailing_start)
        for gi, slices in per_group.items():
            plen = _clean_prefix_len(slices)
            if plen is None:
                continue
            ogs, oge = old_groups[gi]
            ngs, nge = new_groups[gi]
            if (
                old_words[ogs:oge] != new_words[ngs:nge]
                and (nge - ngs < plen
                     or old_words[ogs : ogs + plen] != new_words[ngs : ngs + plen])
            ):
                continue  # prefix not preserved -- no plan for this group
            name_plan[gi] = {
                "old_slices": slices,
                "new_slices": slices,
                "old_prefix_len": plen,
                "new_prefix_len": plen,
            }

    sec1_bytes = bytearray(pat_sec1)
    n_disp = n_disp_remapped = n_name = n_label = 0

    def group_changed(gi):
        ogs, oge = old_groups[gi]
        ngs, nge = new_groups[gi]
        return old_words[ogs:oge] != new_words[ngs:nge]

    def map_rel_offset(gi, rel):
        """Map a group-relative word offset old -> new (start / slice boundaries)."""
        ogs, oge = old_groups[gi]
        ngs, nge = new_groups[gi]
        old_len = oge - ogs
        new_len = nge - ngs
        if rel == 0:
            return 0
        if rel == old_len:
            return new_len  # FFFF terminator position
        plan = name_plan.get(gi)
        if plan is not None:
            # boundary map: cumulative slice sums old -> new
            opos = npos = 0
            if rel == opos:
                return npos
            for (oso, osc), (nso, nsc) in zip(plan["old_slices"], plan["new_slices"]):
                opos = oso + osc
                npos = nso + nsc
                if rel == opos:
                    return npos
        if not group_changed(gi):
            return rel
        if plan is not None:
            # changed group, offset not on a slice boundary: land after the prefix
            print(
                "  WARNING: R%s group %d: mid-group offset rel=%d not on a label "
                "boundary; mapping past the new prefix" % (res_name, gi, rel)
            )
            return plan["new_prefix_len"]
        # changed group with no label plan: show the full new group
        print(
            "  WARNING: R%s group %d: mid-group offset rel=%d in changed group "
            "without label plan; mapping to group start" % (res_name, gi, rel)
        )
        return 0

    # --- (a) 0x04 DISPLAY_TEXT --------------------------------------------------
    for r in recs["display"]:
        pc, old_off, old_cnt = r["pc"], r["off"], r["cnt"]
        n_disp += 1
        if old_cnt == 0:
            continue  # leave the instruction completely untouched
        if old_off >= old_n_words:
            continue  # sentinel offset outside Section 2 -- leave untouched
        if old_off >= old_trailing_start:
            # span in the trailing (non-group) region: shift by the delta
            new_off, new_cnt = old_off + trailing_delta, old_cnt
            struct.pack_into(">I", sec1_bytes, pc + 2, new_off)
            struct.pack_into(">I", sec1_bytes, pc + 6, new_cnt)
            n_disp_remapped += 1
            continue
        old_end = old_off + old_cnt  # exclusive
        gi_start = _find_group(old_groups, old_off)
        gi_last = _find_group(old_groups, old_end - 1)
        if gi_start is None or gi_last is None or old_end > old_n_words:
            raise ValueError(
                "R%s: DISPLAY_TEXT at S1+0x%X: span %d..%d outside Section 2 "
                "group structure" % (res_name, pc, old_off, old_end)
            )
        if old_words[old_end - 1] != 0xFFFF:
            print(
                "  WARNING: R%s DISPLAY_TEXT at S1+0x%X: original span does not "
                "end on FFFF (word=0x%04X); remapping structurally"
                % (res_name, pc, old_words[old_end - 1])
            )
        rel = old_off - old_groups[gi_start][0]
        new_off = new_groups[gi_start][0] + map_rel_offset(gi_start, rel)
        new_end = new_groups[gi_last][1] + 1  # right after the FFFF of the last group
        new_cnt = new_end - new_off
        if new_cnt <= 0 or new_end > new_n_words or new_words[new_end - 1] != 0xFFFF:
            raise ValueError(
                "R%s: DISPLAY_TEXT at S1+0x%X: remapped span off=%d cnt=%d does "
                "not end on FFFF -- refusing to ship a violation"
                % (res_name, pc, new_off, new_cnt)
            )
        struct.pack_into(">I", sec1_bytes, pc + 2, new_off)
        struct.pack_into(">I", sec1_bytes, pc + 6, new_cnt)
        n_disp_remapped += 1

    # --- (a2) UNWALKED 0x04 DISPLAY_TEXT: group-anchored linear sweep ------------
    # The BFS walk from pc=0 only reaches instructions on statically-followable
    # control flow.  Some scene "events" live in Section-1 code ISLANDS entered
    # ONLY by runtime/indirect dispatch (no static edge from pc=0), so their
    # DISPLAY_TEXT opcodes are never walked -- and, before this sweep, never
    # repatched.  When injection GROWS Section 2 their stale (pristine) offsets
    # then point at the WRONG, shifted group: a choice renders as a flat
    # continue-arrow (issue #9: R1200/R1204/R1208/R1210), narration shows the
    # wrong group's text (much of the scattered/wrong-text corpus).
    #
    # This is NOT the banned word-grid pattern matching.  A candidate 0x0004 is
    # accepted ONLY when BOTH endpoints of its span land EXACTLY on group
    # boundaries in the pristine Section 2: its offset is EXACTLY a group-start
    # AND its span ends EXACTLY on a group's 0xFFFF terminator (the START group's
    # terminator for a single-group display, or a LATER group's for a legit
    # multi-group narration run -- the walked pass remaps those the same way, via
    # gi_start..gi_last).  A coincidental 0x0004 in binary Section-1 data
    # satisfying BOTH boundary hits is astronomically improbable; anything
    # failing the gate is left byte-for-byte untouched.
    #
    # ONE degenerate false-positive class is excluded explicitly: a MULTI-group
    # span starting at group 0 (offset 0).  Binary regions are full of
    # `00 04 00 00 00 00 ...`, so offset 0 (== group 0's start) is a common
    # accidental match; a real event-island narration run never starts at the
    # resource's first group.  Single-group offset-0 displays stay allowed
    # (safe: group 0 starts at word 0 in both layouts).
    #
    # Walked pcs are skipped (handled above).  When Section 2 did not grow,
    # new==old and every write is a no-op.
    old_start_to_gi = {gs: gi for gi, (gs, _ge) in enumerate(old_groups)}
    old_term_to_gi = {ge: gi for gi, (_gs, ge) in enumerate(old_groups)}
    walked_pcs = set(instrs)
    n_disp_sweep = 0            # unwalked opcodes remapped by the sweep
    n_disp_sweep_reject = 0     # near-misses (valid group-start, gate failed)
    sweep_hits = []
    sec1_len = len(orig_sec1)
    i = 0
    while ISLAND_SWEEP_ENABLED and i <= sec1_len - 10:
        if struct.unpack_from(">H", orig_sec1, i)[0] != 0x0004 or i in walked_pcs:
            i += 1
            continue
        old_off = struct.unpack_from(">I", orig_sec1, i + 2)[0]
        old_cnt = struct.unpack_from(">I", orig_sec1, i + 6)[0]
        sgi = old_start_to_gi.get(old_off)
        egi = old_term_to_gi.get(old_off + old_cnt - 1) if old_cnt > 0 else None
        # STRICT gate: offset on a group-start AND span end on a group terminator
        # at or after the start group.
        if sgi is None or egi is None or egi < sgi:
            if sgi is not None and old_cnt > 0:
                n_disp_sweep_reject += 1  # group-start but end not a terminator
            i += 1
            continue
        if egi > sgi and old_off == 0:
            # Degenerate binary false positive (multi-group span from group 0).
            n_disp_sweep_reject += 1
            i += 1
            continue
        new_off = new_groups[sgi][0]
        new_end = new_groups[egi][1] + 1   # right after the egi FFFF terminator
        new_cnt = new_end - new_off
        # HARD ASSERT: the remapped span MUST end exactly on 0xFFFF.
        if (new_cnt <= 0 or new_end > new_n_words
                or new_words[new_end - 1] != 0xFFFF):
            raise ValueError(
                "R%s: unwalked DISPLAY_TEXT at S1+0x%X: remapped span off=%d "
                "cnt=%d does not end on FFFF -- refusing to ship a violation"
                % (res_name, i, new_off, new_cnt))
        if (new_off, new_cnt) != (old_off, old_cnt):
            struct.pack_into(">I", sec1_bytes, i + 2, new_off)
            struct.pack_into(">I", sec1_bytes, i + 6, new_cnt)
            n_disp_sweep += 1
            sweep_hits.append((i, sgi, egi, old_off, new_off))
        i += LENB[0x04]  # advance past a confirmed opcode's operands
    if n_disp_sweep or n_disp_sweep_reject:
        print(
            "  Section 1: unwalked-island sweep remapped %d DISPLAY_TEXT "
            "(%d near-misses rejected by the group/terminator gate)"
            % (n_disp_sweep, n_disp_sweep_reject))

    # --- (a3) UNWALKED-ISLAND label-pair sweep: mid-group 0x04 + island 0x14 -----
    # Speaker-labeled dialogue inside an unwalked code island is a 0x14 LABEL
    # (name prefix = the first words of the group) immediately followed by a
    # 0x04 DISPLAY whose offset points MID-group (group_start + prefix_len).
    # Pass a2 only remaps a 0x04 whose offset is EXACTLY a pristine group
    # start, so these island pairs shipped STALE: once English grew Section 2
    # the pristine offset landed inside a DIFFERENT scene's text and the span
    # no longer ended on 0xFFFF -- wrong text + non-terminated display =
    # infinite loop (issues #27/#30/#31).  The island 0x14 labels were never
    # swept at all (pass b patches WALKED labels only) -> stale nameplates.
    #
    # This is NOT pattern matching.  Part 1 (0x04): a candidate is accepted
    # ONLY when its pristine offset lies INSIDE a group (rel > 0; rel == 0 is
    # pass a2's territory and stays with it) AND its pristine span ends
    # EXACTLY on a group's 0xFFFF terminator at/after that group -- the same
    # invariant every real display record satisfies.  The remap goes through
    # map_rel_offset (name_plan aware) and is guarded by the same HARD ASSERT
    # as the walked pass.  Part 2 (0x14): only SHORT slices (cnt <= 10 -- real
    # name prefixes are 3-7 words) whose offset lies inside a group (or the
    # trailing region, handled exactly like pass b) are remapped, through the
    # exact pass-b plan/clamp/identity logic.  Anything failing a gate is left
    # byte-for-byte untouched.
    #
    # OVERLAP GATE (both parts): a candidate whose record span intersects ANY
    # WALKED instruction's bytes is a misaligned byte pattern straddling real
    # code, NOT a record -- writing it would corrupt a walked instruction
    # (proven on R1207: six unwalked "off=1 cnt=1537" 0x0004 patterns overlap
    # walked opcodes; remapping one flipped a walked 0x06 jump to 0x0A and the
    # re-walk failed).  Such candidates are skipped unconditionally.
    walked_bytes = set()
    for _pc, _op in instrs.items():
        walked_bytes.update(range(_pc, _pc + LENB[_op]))
    n_island_disp = 0
    n_island_label = 0
    i = 0
    while ISLAND_SWEEP_ENABLED and i <= sec1_len - 10:
        if struct.unpack_from(">H", orig_sec1, i)[0] != 0x0004 or i in walked_pcs:
            i += 1
            continue
        old_off = struct.unpack_from(">I", orig_sec1, i + 2)[0]
        old_cnt = struct.unpack_from(">I", orig_sec1, i + 6)[0]
        if old_cnt == 0:
            i += 1
            continue
        if not walked_bytes.isdisjoint(range(i, i + LENB[0x04])):
            i += 1  # straddles a walked instruction -- not a record
            continue
        sgi = _find_group(old_groups, old_off)
        if sgi is None:
            i += 1
            continue
        rel = old_off - old_groups[sgi][0]
        if rel == 0:
            # Group-start case: pass a2's territory (already remapped there,
            # or rejected by its gate and intentionally left untouched).
            i += 1
            continue
        egi = old_term_to_gi.get(old_off + old_cnt - 1)
        # STRICT gate: the pristine span must end EXACTLY on a group
        # terminator at/after the containing group.
        if egi is None or egi < sgi:
            i += 1
            continue
        new_off = new_groups[sgi][0] + map_rel_offset(sgi, rel)
        new_end = new_groups[egi][1] + 1   # right after the egi FFFF terminator
        new_cnt = new_end - new_off
        # HARD ASSERT: the remapped span MUST end exactly on 0xFFFF.
        if (new_cnt <= 0 or new_end > new_n_words
                or new_words[new_end - 1] != 0xFFFF):
            raise ValueError(
                "R%s: unwalked mid-group DISPLAY_TEXT at S1+0x%X: remapped "
                "span off=%d cnt=%d does not end on FFFF -- refusing to ship "
                "a violation" % (res_name, i, new_off, new_cnt))
        if (new_off, new_cnt) != (old_off, old_cnt):
            struct.pack_into(">I", sec1_bytes, i + 2, new_off)
            struct.pack_into(">I", sec1_bytes, i + 6, new_cnt)
            n_island_disp += 1
        i += LENB[0x04]  # advance past a confirmed opcode's operands

    # Part 2: unwalked 0x14 island labels.  Pass b below iterates recs["label"]
    # (WALKED labels only); exclude those pcs so no record is double-processed.
    walked_label_pcs = {r["pc"] for r in recs["label"]}
    i = 0
    while ISLAND_SWEEP_ENABLED and i <= sec1_len - LENB[0x14]:
        if (struct.unpack_from(">H", orig_sec1, i)[0] != 0x0014
                or i in walked_pcs or i in walked_label_pcs):
            i += 1
            continue
        old_off = struct.unpack_from(">I", orig_sec1, i + 6)[0]
        old_cnt = struct.unpack_from(">I", orig_sec1, i + 10)[0]
        # Only SHORT label slices are swept (name prefixes are 3-7 words);
        # anything longer is NOT a nameplate and is left untouched -- with ONE
        # plan-gated exception (issue #44): cnt==11 candidates may be island
        # DIGIT-TABLE registrations (see _island_digit_slices).  They are
        # allowed PAST this gate but complete ONLY on an EXACT name_plan slice
        # match below; any cnt==11 record without a seeded plan slice is left
        # byte-for-byte untouched (no trailing-shift, no clamp, no identity
        # rewrite).  The cnt<=10 nameplate path is unchanged.
        if old_cnt == 0 or old_cnt > 11:
            i += 1
            continue
        digit11 = (old_cnt == 11)
        if not walked_bytes.isdisjoint(range(i, i + LENB[0x14])):
            i += 1  # straddles a walked instruction -- not a record
            continue
        if old_off >= old_n_words:
            i += 1  # sentinel offset outside Section 2 -- leave untouched
            continue
        if old_off >= old_trailing_start:
            if digit11:
                i += 1  # digit-table candidates never live in the trailing region
                continue
            # trailing-region narration: shift by the delta, keep cnt (pass b)
            if trailing_delta != 0:
                struct.pack_into(
                    ">I", sec1_bytes, i + 6, old_off + trailing_delta)
                n_island_label += 1
            i += LENB[0x14]
            continue
        gi = _find_group(old_groups, old_off)
        if gi is None:
            i += 1
            continue
        ogs, _oge = old_groups[gi]
        ngs, nge = new_groups[gi]
        rel = old_off - ogs
        plan = name_plan.get(gi)
        new_rel, new_cnt = None, old_cnt
        if plan is not None:
            for (oso, osc), (nso, nsc) in zip(plan["old_slices"],
                                              plan["new_slices"]):
                if oso == rel and osc == old_cnt:
                    new_rel, new_cnt = nso, nsc
                    break
        if digit11 and new_rel is None:
            i += 1  # cnt==11 without an exact plan slice: not ours, untouched
            continue
        if new_rel is None:
            if group_changed(gi):
                # no slice match in a changed group: clamp inside the new group
                new_len = nge - ngs
                new_rel = min(rel, max(new_len - 1, 0))
                new_cnt = max(min(old_cnt, new_len - new_rel), 0)
            else:
                new_rel, new_cnt = rel, old_cnt  # unchanged group: identity
        if (ngs + new_rel, new_cnt) != (old_off, old_cnt):
            struct.pack_into(">I", sec1_bytes, i + 6, ngs + new_rel)
            struct.pack_into(">I", sec1_bytes, i + 10, new_cnt)
            n_island_label += 1
        i += LENB[0x14]  # advance past a confirmed opcode's operands
    if n_island_disp or n_island_label:
        print(
            "  Section 1: island label-pair sweep remapped %d DISPLAY + %d LABEL"
            % (n_island_disp, n_island_label))

    # --- (b) 0x14 NAME/LABEL REF --------------------------------------------------
    for r in recs["label"]:
        pc, old_off, old_cnt = r["pc"], r["off"], r["cnt"]
        if old_off >= old_n_words:
            continue  # sentinel offset outside Section 2 -- leave untouched
        if old_off >= old_trailing_start:
            # trailing-region narration: shift by the delta, keep cnt
            struct.pack_into(">I", sec1_bytes, pc + 6, old_off + trailing_delta)
            n_label += 1
            continue
        gi = _find_group(old_groups, old_off)
        if gi is None:
            raise ValueError(
                "R%s: 0x14 at S1+0x%X: NAME_OFF %d outside groups and trailing "
                "region" % (res_name, pc, old_off)
            )
        ogs, oge = old_groups[gi]
        ngs, nge = new_groups[gi]
        rel = old_off - ogs
        plan = name_plan.get(gi)
        new_rel, new_cnt = None, old_cnt
        if plan is not None:
            for (oso, osc), (nso, nsc) in zip(plan["old_slices"], plan["new_slices"]):
                if oso == rel and osc == old_cnt:
                    new_rel, new_cnt = nso, nsc
                    break
        if new_rel is None:
            if group_changed(gi):
                # no slice match in a changed group: clamp inside the new group
                new_len = nge - ngs
                new_rel = min(rel, max(new_len - 1, 0))
                new_cnt = max(min(old_cnt, new_len - new_rel), 0)
                print(
                    "  WARNING: R%s 0x14 at S1+0x%X: slice (rel=%d,cnt=%d) has no "
                    "plan entry in changed group %d; clamped to (rel=%d,cnt=%d)"
                    % (res_name, pc, rel, old_cnt, gi, new_rel, new_cnt)
                )
            else:
                new_rel, new_cnt = rel, old_cnt  # unchanged group: identity
        struct.pack_into(">I", sec1_bytes, pc + 6, ngs + new_rel)
        struct.pack_into(">I", sec1_bytes, pc + 10, new_cnt)
        n_label += 1

    # --- (c) 0x0C SET_NAME_REF / 0x0D CLEAR_NAME_REF ------------------------------
    # The `idx` operand of 0x0C/0x0D is NOT a Section-2 glyph word offset -- it is
    # a SPEAKER / PORTRAIT CHANNEL BIT INDEX (0..511) and must be PRESERVED.
    #
    # EXE proof (pristine SLPM_653.78, VA->file = vaddr-0x100000+0x80):
    #   0x0C handler @ VA 0x2F3BB0 reads u16 `param` then u16 `idx`, then calls
    #   0x302020(param, idx, set=1); 0x0D handler @ VA 0x2F3C00 calls 0x302180
    #   (the matching CLEAR).  In 0x302020:
    #       v1 = sext16(param); if (v1 < 0 || v1 >= 13) return;   # param in [0,12]
    #       a0 = idx & 0xFFFF;  if (idx >= 512) return;           # idx is 0..511
    #       table = {0:0x565110, 1:0x5650D0, 2:0x565090, ...}[param]
    #       table[idx >> 5] |= (1 << (idx & 31))                  # SET bit `idx`
    #   i.e. param selects a 512-bit flag/channel register; idx is the BIT to set
    #   or clear.  The per-frame portrait-emit branch reads these channel flags,
    #   so remapping idx (treating it as a glyph offset) corrupts the
    #   speaker->portrait lookup and the portrait stops drawing (v86 regression --
    #   R1251 BITBLT vanished).  v83's incomplete patcher happened to leave the
    #   gating records alone, which is the only reason the portrait survived there.
    #
    # Corpus confirmation: across all 617 type-02 resources, every one of the
    # 3199 0x0C/0x0D records has param in {0,1,2} and idx < 512 -- never a value
    # that could be a Section-2 word offset.  param==121 (the old, mistaken
    # discriminator) NEVER occurs.  Therefore NONE of these idx values are
    # remapped; they are left byte-for-byte identical to the original JP stream.
    #
    # n_name is reported as 0 (none remapped); the records are intentionally
    # preserved.
    n_name = 0

    print(
        "  Section 2: %d -> %d bytes (%+d), %d groups; Section 1: %d walked instrs, "
        "%d/%d DISPLAY_TEXT remapped, %d 0x14 labels, %d name refs"
        % (
            orig_sec2_size,
            pat_sec2_size,
            pat_sec2_size - orig_sec2_size,
            len(old_groups),
            len(instrs),
            n_disp_remapped,
            n_disp,
            n_label,
            n_name,
        )
    )

    # Reassemble: header (with updated sec2_size) + patched Section 1 + new Section 2
    header = bytearray(patched_data[:HEADER_SIZE])
    struct.pack_into("<I", header, 0x14, pat_sec2_size)
    after_sec2 = patched_data[sec2_off + pat_sec2_size :]
    return bytes(header) + bytes(sec1_bytes) + bytes(new_sec2) + bytes(after_sec2)


def patch_file(orig_path, patched_path, output_path=None):
    """
    Patch a single type-02 resource file.

    orig_path:    path to the ORIGINAL (unmodified) resource
    patched_path: path to the PATCHED resource (with injected Section 2)
    output_path:  where to write the result (defaults to overwriting patched_path)
    """
    if output_path is None:
        output_path = patched_path

    orig_data = open(orig_path, "rb").read()
    patched_data = open(patched_path, "rb").read()

    result = patch_section1(orig_data, patched_data, res_name=os.path.basename(orig_path))

    sc = math.ceil(len(result) / SECTOR)
    if len(result) < sc * SECTOR:
        result = result + b"\x00" * (sc * SECTOR - len(result))

    open(output_path, "wb").write(result)
    return output_path


# ===============================================================================
# Injection pipeline
# ===============================================================================
def _strip_trailing_color_controls(trailing):
    """Drop trailing COLOUR-state control words (0xFFD0-0xFFD9) from a group's
    trailing-control list.  A colour-SET sitting right before the FFFF group
    terminator governs NO following glyph (there is none), so removing it is
    visually inert -- but if it is left in place after a left-align-padded
    narration body it lands on the LAST line and inflates ONLY that line's
    engine-counted length (the per-line centring lc array @desc+0x40), breaking
    the equal-count left-align (R1198 g24).  Only the 0xFFD0-0xFFD9 colour family
    is removed; any other trailing control (FFFE line-breaks, FB02, FFE0, FFC*
    choice markers, ...) is preserved verbatim."""
    return [w for w in trailing if not (0xFFD0 <= w <= 0xFFD9)]


def inject_and_patch(res_idx, msg_translations, raw_dir, out_dir,
                     strip_trailing_color_groups=None):
    """
    Full pipeline: inject translations with variable-size, then patch Section 1
    offsets via the byte-stream disassembler.

    res_idx:          resource number (e.g., 1198)
    msg_translations: dict {msg_index: [glyph_list]}
    raw_dir:          directory with original *_type02.raw files
    out_dir:          output directory for patched files
    strip_trailing_color_groups:
                      optional set of msg_indices that received the narration
                      left-align pad; for these, a trailing colour-control word
                      (0xFFD0-0xFFD9) is dropped so it does not inflate the last
                      padded line's engine-counted length (see
                      _strip_trailing_color_controls).  Other groups are
                      untouched.

    Name-island preservation: 0x14 NAME/LABEL prefixes at the head of translated
    groups are rebuilt as English labels (data/name_labels.json) or kept as the
    original JP glyphs, and a name plan is handed to patch_section1 so the 0x14
    records and mid-group DISPLAY_TEXT starts are remapped correctly.

    If the Section-1 walk fails, NOTHING is written and the resource stays
    pristine.

    Returns (output_filename, status_string) or (None, error_string).
    """
    _load_tables()
    strip_color = strip_trailing_color_groups or set()

    raw_path = os.path.join(raw_dir, "{:04d}_type02.raw".format(res_idx))
    if not os.path.isfile(raw_path):
        return (None, "no _type02.raw found")

    raw = bytearray(open(raw_path, "rb").read())
    orig_bytes = bytes(raw)

    if len(raw) < HEADER_SIZE:
        return (None, "file too small")

    sec2_size = struct.unpack_from("<I", raw, 0x14)[0]
    sec2_offset = struct.unpack_from("<I", raw, 0x18)[0]

    if sec2_offset < HEADER_SIZE or sec2_offset >= len(raw):
        return (None, "invalid sec2_offset=0x{:x}".format(sec2_offset))
    if sec2_size < 4:
        return (None, "sec2_size too small")

    sec2_end = sec2_offset + sec2_size

    # --- Walk the original Section 1 first; bail out if it cannot be walked ---
    sec1 = bytes(raw[HEADER_SIZE:sec2_offset])
    ok, instrs = walk(sec1)
    if not ok:
        return (None, "sec1 walk failed -- skipped, resource left pristine")
    recs = extract_records(sec1, instrs)

    # --- Parse Section 2 groups -------------------------------------------------
    sec2_data = raw[sec2_offset:sec2_end]
    n_words = len(sec2_data) // 2
    words = [struct.unpack_from(">H", sec2_data, i * 2)[0] for i in range(n_words)]

    groups = []
    start = 0
    for i in range(n_words):
        if words[i] == 0xFFFF:
            groups.append(words[start:i])
            start = i + 1
    # Preserve trailing data after the last FFFF terminator (e.g. R989, R1034
    # scene/dungeon script data, R1193 narration).  Dropping it causes crashes.
    trailing_words = words[start:] if start < n_words else []

    if not groups:
        return (None, "no FFFF groups in Section 2")

    # Word ranges for label bucketing
    old_group_ranges = []
    pos = 0
    for g in groups:
        old_group_ranges.append((pos, pos + len(g)))
        pos += len(g) + 1
    old_trailing_start = pos

    per_group_labels, _trailing_labels = _bucket_labels(
        recs["label"], old_group_ranges, old_trailing_start
    )

    # Issue #44: island digit-table registrations (see _island_digit_slices).
    # Seed their (0, 11) slice into the label buckets so the ordinary
    # name-prefix path preserves the pristine digit table at the group head and
    # records a name_plan entry -- which in turn lets patch_section1's a3 sweep
    # remap the island 0x14 (plan-matched cnt==11) and land the paired
    # mid-group 0x04 display AFTER the table instead of at the group start.
    # Only groups with NO walked slices are seeded (the walked machinery owns
    # every group it already covers).
    for gi, dslices in _island_digit_slices(
            sec1, instrs, old_group_ranges, words).items():
        if gi not in per_group_labels:
            per_group_labels[gi] = dslices

    # --- Replace translated messages (variable-size, name-island aware) ----------
    replaced = 0
    skipped_label_tables = 0
    name_plan = {}
    for msg_idx, eng_glyphs in sorted(msg_translations.items()):
        if msg_idx < 0 or msg_idx >= len(groups):
            print(
                "    WARNING: R%d msg_index %d out of range (0..%d)"
                % (res_idx, msg_idx, len(groups) - 1)
            )
            continue

        original_group = groups[msg_idx]
        slices = per_group_labels.get(msg_idx)

        # CHOICE-AWARE PATH: if the ORIGINAL group carries option markers
        # (FFC0/FFC1/FFC2...), preserve them and substitute English per segment.
        # This takes precedence over name-island handling: a group that is BOTH
        # a choice and a name-island is treated as a choice (the markers must be
        # preserved verbatim or every option renders as flat, unselectable
        # text).  No name_plan entry is created for the group, so patch_section1
        # falls back to its in-group remapping for any 0x14/0x04 that points at
        # it (choice groups are normally plain dialogue/menu groups, not name
        # islands, so this is the safe default).
        if group_choice_markers(original_group):
            new_group, reason = encode_choice_group(original_group, eng_glyphs)
            if new_group is None:
                print(
                    "    WARNING: R%d group %d choice group kept untranslated -- %s"
                    % (res_idx, msg_idx, reason)
                )
                continue
            groups[msg_idx] = new_group
            replaced += 1
            continue

        if slices:
            prefix_len = _clean_prefix_len(slices)
            if prefix_len is None or prefix_len >= len(original_group):
                # Label-table group (or prefix covers the whole group): leave
                # the original glyphs verbatim so every slice stays valid.
                print(
                    "    NOTE: R%d group %d: 0x14 slices %s are not a clean "
                    "dialogue prefix -- translation skipped, group kept verbatim"
                    % (res_idx, msg_idx, slices[:6])
                )
                skipped_label_tables += 1
                continue

            # Rebuild: [label slice 0][...slice k][English dialogue]
            new_slice_glyphs = []
            new_slices = []
            npos = 0
            active_label_en = None  # English string of the FIRST/active speaker
            override_label = _NAMEPLATE_OVERRIDES.get((res_idx, msg_idx))
            for si, (so, sc) in enumerate(slices):
                old_slice = original_group[so : so + sc]
                jp = _decode_jp(old_slice)
                en = _NAME_LABELS.get(jp) if jp is not None else None
                # Per-(resource,group) override wins for the active speaker slice
                # (the name box) — see _NAMEPLATE_OVERRIDES.
                if si == 0 and override_label is not None:
                    en = override_label
                if si == 0 and en is not None:
                    active_label_en = en
                if en is not None:
                    glyphs = [_enc_char(c) for c in en]
                else:
                    glyphs = list(old_slice)  # keep original JP label verbatim
                new_slices.append((npos, len(glyphs)))
                new_slice_glyphs.extend(glyphs)
                npos += len(glyphs)

            # Strip a redundant "<label>: " speaker prefix that the batch JSON
            # dialogue often duplicates from the 0x14 name-label box header
            # (v85 MINOR-1).  Only the first/active speaker label is matched, and
            # only the dialogue body is shortened -- the label glyphs above are
            # untouched, so new_slices / new_prefix_len stay valid.
            eng_glyphs = _strip_redundant_speaker_prefix(eng_glyphs, active_label_en)

            remainder = original_group[prefix_len:]
            leading, _old_text, trailing = _split_control_and_text(remainder)
            leading = _strip_leading_var_insert(leading)
            leading = _strip_duplicated_fe_controls(leading, eng_glyphs)
            if msg_idx in strip_color:
                trailing = _strip_trailing_color_controls(trailing)
            groups[msg_idx] = new_slice_glyphs + leading + eng_glyphs + trailing
            name_plan[msg_idx] = {
                "old_slices": slices,
                "new_slices": new_slices,
                "old_prefix_len": prefix_len,
                "new_prefix_len": npos,
            }
        else:
            leading, _old_text, trailing = _split_control_and_text(original_group)
            leading = _strip_leading_var_insert(leading)
            leading = _strip_duplicated_fe_controls(leading, eng_glyphs)
            if msg_idx in strip_color:
                trailing = _strip_trailing_color_controls(trailing)
            groups[msg_idx] = leading + eng_glyphs + trailing
        replaced += 1

    # --- Rebuild Section 2 --------------------------------------------------------
    new_sec2 = bytearray()
    for group in groups:
        for g in group:
            new_sec2 += struct.pack(">H", g)
        new_sec2 += struct.pack(">H", 0xFFFF)
    for t in trailing_words:
        new_sec2 += struct.pack(">H", t)

    new_sec2_size = len(new_sec2)

    # Build injected file (Section 1 unchanged, new Section 2)
    section1 = bytearray(raw[:sec2_offset])
    struct.pack_into("<I", section1, 0x14, new_sec2_size)
    after_sec2 = raw[sec2_end:]
    injected = bytes(section1) + bytes(new_sec2) + bytes(after_sec2)

    # Patch Section 1 offsets (walk-based, with the name-island plan)
    result = patch_section1(
        orig_bytes, injected, name_plan=name_plan, res_name=str(res_idx)
    )

    # Pad to sector boundary
    sc = math.ceil(len(result) / SECTOR)
    if len(result) < sc * SECTOR:
        result = result + b"\x00" * (sc * SECTOR - len(result))

    out_name = os.path.basename(raw_path)
    out_path = os.path.join(out_dir, out_name)
    os.makedirs(out_dir, exist_ok=True)
    open(out_path, "wb").write(result)

    size_delta = new_sec2_size - sec2_size
    old_sc = len(raw) // SECTOR if len(raw) >= SECTOR else 1
    status = (
        "replaced %d/%d (%d name-prefix groups, %d label tables kept verbatim), "
        "sec2 %d->%d (%+d bytes), %d->%d sectors, OFFSETS PATCHED (walked)"
        % (
            replaced,
            len(groups),
            len(name_plan),
            skipped_label_tables,
            sec2_size,
            new_sec2_size,
            size_delta,
            old_sc,
            sc,
        )
    )
    return (out_name, status)


def _strip_redundant_speaker_prefix(eng_glyphs, label_en):
    """
    Strip a leading redundant "<label>:<sp>" speaker prefix from an already-
    encoded English dialogue glyph sequence.

    The dialogue text from the batch JSON frequently begins with the speaker's
    name followed by a colon (e.g. "Sister: I've been...") which duplicates the
    0x14 name-label box header.  When the active label is known, that prefix is
    redundant and must be removed so the name renders only once.

    Matching (case-insensitive, glyph level):
        <label glyphs> [space]* ':' [space]*
    Only the EXACT leading run is removed, and only when label_en is non-empty
    and eng_glyphs actually starts with it.  Anything else changes nothing.

    Returns the (possibly shortened) glyph list.
    """
    if not label_en or not eng_glyphs:
        return eng_glyphs

    _load_tables()
    colon = _ENG_TABLE.get(":")
    space = _ENG_TABLE.get(" ")
    if colon is None:
        return eng_glyphs

    # Encode the label the same way the dialogue was encoded, then compare
    # case-insensitively at the glyph level (encoding already folds case via
    # the lower() fallback, but glyph indices differ for cased letters that
    # exist in both forms, so compare on the decoded-lower form instead).
    def _lower_key(glyphs):
        # Map glyph -> its source char (best effort) by reverse lookup, then
        # lowercase.  Falls back to the raw glyph index when unmapped.
        out = []
        for g in glyphs:
            ch = _ENG_REV.get(g)
            out.append(ch.lower() if ch is not None else g)
        return out

    label_glyphs = [_enc_char(c) for c in label_en]
    n = len(label_glyphs)
    if n == 0 or len(eng_glyphs) < n:
        return eng_glyphs

    if _lower_key(eng_glyphs[:n]) != _lower_key(label_glyphs):
        return eng_glyphs  # dialogue does not start with the label

    pos = n
    # optional spaces before the colon
    while pos < len(eng_glyphs) and space is not None and eng_glyphs[pos] == space:
        pos += 1
    if pos >= len(eng_glyphs) or eng_glyphs[pos] != colon:
        return eng_glyphs  # no ':' after the label -- not the redundant prefix
    pos += 1
    # Consume any separators after the colon: spaces AND line/page-break
    # controls.  The batch text often wrote the prefix as "<name>: / text"
    # where the " / " encodes to a 0xFFFE line break; once the redundant name
    # is removed, that break is redundant too -- leaving it would make the
    # DISPLAY_TEXT start point at a 0xFFFE terminator instead of real content.
    while pos < len(eng_glyphs) and (
        eng_glyphs[pos] == space
        or eng_glyphs[pos] == 0xFFFE
        or eng_glyphs[pos] == 0xFFD2
    ):
        pos += 1

    # Never strip the entire body away (would create an empty dialogue group).
    if pos >= len(eng_glyphs):
        return eng_glyphs

    return eng_glyphs[pos:]


# Variable / number-insertion controls (0xFFF0..0xFFF6).  At runtime FFF0 inserts
# a bound variable -- in the R1197 narration groups it is the protagonist/party
# name that originally preceded the JP particle (e.g. "<NAME> went up beside the
# female knight...").  The decoded JP text used for translation deliberately drops
# this control, and the English translations fold the subject into the prose
# ("You went up...", "You handed him...").  Re-emitting the leading FFF0 in front
# of the English body leaves an UNBOUND variable that renders as a stray glyph
# placeholder ("AAA") before the narration.  When such a control sits at the very
# head of a group's leading-control run (with no matching opener inside the group),
# it is dropped during English injection.  Trailing controls, line/page breaks,
# choice markers and FF-range openers are NOT touched.
VAR_INSERT_MIN = 0xFFF0
VAR_INSERT_MAX = 0xFFF6


def _strip_leading_var_insert(leading):
    """Drop a leading variable/number-insertion control (0xFFF0..0xFFF6) from a
    group's leading-control run.  Only a run at the very head is removed; any
    other controls (FF-range color openers, breaks) are preserved verbatim so the
    color/skeleton state stays intact."""
    i = 0
    while i < len(leading) and VAR_INSERT_MIN <= leading[i] <= VAR_INSERT_MAX:
        i += 1
    return leading[i:]


def _strip_duplicated_fe_controls(leading, eng_glyphs):
    """Double-print guard for authored number tokens (issue #44).

    When the translated glyph stream AUTHORS an inline number-insert control
    (0xFE00..0xFE0F, from a "[FE0x]" token), the same control preserved in the
    group's leading run would print the number twice.  Drop exactly the FE
    words the translation authors itself; every other preserved control
    (colours, breaks) stays verbatim.  When the translation authors no FE
    token -- the overwhelmingly common case -- the leading run is returned
    unchanged."""
    authored = {g for g in eng_glyphs if 0xFE00 <= g <= 0xFE0F}
    if not authored:
        return leading
    return [g for g in leading if g not in authored]


def _split_control_and_text(group):
    """Split a group into leading controls, text, trailing controls."""
    if not group:
        return ([], [], [])

    lead_end = 0
    for i, g in enumerate(group):
        if g < 0xFB00:
            lead_end = i
            break
    else:
        return (list(group), [], [])

    trail_start = len(group)
    for i in range(len(group) - 1, lead_end - 1, -1):
        if group[i] < 0xFB00:
            trail_start = i + 1
            break

    return (list(group[:lead_end]), list(group[lead_end:trail_start]), list(group[trail_start:]))


# ===============================================================================
# Choice-group (FFC0/FFC1/FFC2...) support
# ===============================================================================
# The game marks selectable choice options with in-stream control words
# 0xFFC0 (option 1), 0xFFC1 (option 2), 0xFFC2 ... sitting in the MIDDLE of a
# FFFF-group, each immediately preceding its option text.  Example (R1197
# group 63, a Yes/No question):
#     <question glyphs> FFFE FFFE FFC0 <はい> FFFE FFC1 <いいえ>
# The plain leading/trailing control split discards these mid-group markers,
# rendering every choice as flat unselectable text.  encode_choice_group()
# preserves the EXACT original marker words/order and substitutes the injected
# English per segment.  Logic ported from tools/inject_type2_dialogue.py (which
# the build does NOT use), adapted to operate on a pre-encoded glyph list rather
# than a raw English string.
CHOICE_MIN = 0xFFC0
CHOICE_MAX = 0xFFCF  # FFC0..FFCF reserved for option markers
LINE_BREAK = 0xFFFE
PAGE_BREAK = 0xFFD2


def _is_choice_marker(w):
    return CHOICE_MIN <= w <= CHOICE_MAX


def group_choice_markers(group):
    """Ordered list of choice-marker words (FFC0, FFC1, ...) in stream order.
    Empty if this is not a choice group."""
    return [w for w in group if _is_choice_marker(w)]


def split_choice_group(group):
    """Split a choice FFFF-group into (leading_ctrls, question_words, options)
    where options is [(marker, option_words), ...].  Mirrors
    inject_type2_dialogue.split_choice_group():
      * leading = contiguous controls (>= 0xFB00) at the very start
      * question = everything between the leading controls and the first marker
      * each marker owns the words up to the next marker (or end of group)

    NOTE: a leading control run must STOP at the first choice marker.  Choice
    markers (0xFFC0..0xFFCF) are themselves >= 0xFB00, so a group whose VERY
    FIRST word is a marker (e.g. R1347 g5: M0 G8 FFFE M1 ...) would otherwise
    have its M0 swallowed into `leading`, dropping it from the options list and
    making encode_choice_group's marker-set tripwire fail (marker-set-mismatch).
    Excluding markers from the leading run fixes those marker-first groups while
    leaving genuine leading FFFE/colour controls untouched.
    """
    lead_end = 0
    for i, g in enumerate(group):
        if g < 0xFB00 or _is_choice_marker(g):
            lead_end = i
            break
    else:
        lead_end = len(group)
    leading = list(group[:lead_end])
    body = list(group[lead_end:])

    first_marker = None
    for i, g in enumerate(body):
        if _is_choice_marker(g):
            first_marker = i
            break
    if first_marker is None:
        return (leading, list(body), [])

    question = list(body[:first_marker])
    options = []
    i = first_marker
    n = len(body)
    while i < n:
        marker = body[i]
        j = i + 1
        while j < n and not _is_choice_marker(body[j]):
            j += 1
        options.append((marker, list(body[i + 1:j])))
        i = j
    return (leading, question, options)


def encode_choice_group(original_group, eng_glyphs):
    """Rebuild a choice group, preserving the original marker sequence and
    substituting the injected English for the question and each option.

    The English glyph list (already encoded by build_v9 Step 4) uses 0xFFFE as
    the segment separator (and 0xFFD2 for page breaks within the question).  By
    the data contract, the LAST N 0xFFFE-separated segments are the N options
    (one per marker, in order); everything before them is the question (its
    internal 0xFFFE / 0xFFD2 breaks are preserved).

    Returns (new_group, None) on success, or (None, reason) to keep the original
    group untranslated.
    """
    leading, question_old, options_old = split_choice_group(original_group)
    markers = [m for (m, _txt) in options_old]
    n_markers = len(markers)
    if n_markers == 0:
        return (None, "no choice markers in original group")

    def _ctrl_tail(words):
        """Return (body_without_tail, trailing_ctrl_run).  The trailing control
        run is the maximal suffix of words w >= 0xFB00 -- these are the FFFE /
        FFFE-FFFE line-advance separators that originally preceded the NEXT
        marker (split_choice_group hands them to the PREVIOUS segment)."""
        k = len(words)
        while k > 0 and words[k - 1] >= 0xFB00:
            k -= 1
        return (list(words[:k]), list(words[k:]))

    # Capture the original control skeleton: the trailing control run of the
    # question and of every option body EXCEPT the last (the last option's tail,
    # if any, would be trailing slack after the final marker -- not a separator).
    _q_body_old, q_tail = _ctrl_tail(question_old)
    opt_bodies_old = []
    opt_tails = []
    for k, (_m, body) in enumerate(options_old):
        if k < n_markers - 1:
            b, t = _ctrl_tail(body)
        else:
            # Last option: keep its body verbatim (no following marker to feed).
            b, t = list(body), []
        opt_bodies_old.append(b)
        opt_tails.append(t)

    # ------------------------------------------------------------------
    # PORTRAIT-OPTION MODE: every original option body consists SOLELY of control
    # words >= 0xFB00 (e.g. the FFF1..FFF6 portrait selectors of the
    # fortune-reading N=6 groups), so there is no option STRING to substitute.
    # Here the English provides ONLY the question.  Re-emit each marker with its
    # ORIGINAL body verbatim and the captured separators.  Detected BEFORE the
    # segment-count guard so it does NOT require >= n_markers+1 segments.
    # NOTE: tested against the FULL original bodies (not the tail-stripped ones)
    # so the last option -- whose tail we intentionally keep verbatim -- is also
    # recognised as control-only.
    # ------------------------------------------------------------------
    portrait_mode = all(
        all(w >= 0xFB00 for w in body) for (_m, body) in options_old
    )

    # Split the incoming English glyph list on ANY break control (0xFFFE line
    # break OR 0xFFD2 page break).  build_v9 Step 4 auto-promotes every 3rd line
    # break to a 0xFFD2 page break, so a choice's option separators can arrive as
    # FFD2 rather than FFFE; treating both as separators keeps the last-N-segments
    # = options contract robust regardless of where the auto page break lands.
    segments = []
    cur = []
    for g in eng_glyphs:
        if g == LINE_BREAK or g == PAGE_BREAK:
            segments.append(cur)
            cur = []
        else:
            cur.append(g)
    segments.append(cur)

    def _join_question(question_segs):
        """Join question segments with 0xFFFE, trimming dangling breaks.  The
        captured q_tail supplies the separator before the first marker, so we do
        NOT leave a trailing break here (avoids doubling the break)."""
        qg = []
        for si, seg in enumerate(question_segs):
            if si > 0:
                qg.append(LINE_BREAK)
            qg.extend(seg)
        while qg and qg[-1] == LINE_BREAK:
            qg.pop()
        while qg and qg[0] == LINE_BREAK:
            qg.pop(0)
        return qg

    if portrait_mode:
        # ALL English segments are the question; markers + original bodies stay.
        question_glyphs = _join_question(segments)
        new_group = list(leading) + list(question_glyphs) + list(q_tail)
        for idx, marker in enumerate(markers):
            new_group.append(marker)
            new_group.extend(opt_bodies_old[idx])
            new_group.extend(opt_tails[idx])
    else:
        if len(segments) < n_markers + 1:
            return (None,
                    "english has %d 0xFFFE segments, need >= %d "
                    "(question + %d options)"
                    % (len(segments), n_markers + 1, n_markers))

        option_segs = segments[-n_markers:]
        question_segs = segments[:-n_markers]
        question_glyphs = _join_question(question_segs)

        # Re-insert the captured original control run BEFORE each marker: the
        # question's tail before FFC0, option k's tail before FFC(k+1).
        new_group = list(leading) + list(question_glyphs) + list(q_tail)
        for idx, marker in enumerate(markers):
            new_group.append(marker)
            new_group.extend(option_segs[idx])
            new_group.extend(opt_tails[idx])

    # Tripwire: the marker set/order MUST be byte-identical to the original.
    if [w for w in new_group if _is_choice_marker(w)] != markers:
        return (None, "marker-set-mismatch")

    # Tripwire 2: marker-line collision.  Verified via EXE disassembly (FFFE
    # handler 0x304740 increments a line index s1 per 0xFFFE, capped at 0x1f;
    # FFC0/FFC1 arms 0x304948/0x304978 flag the CURRENT line selectable; the
    # selection read loop 0x303AF8 scans for the FIRST flagged line positionally).
    # Yes/No selection therefore depends ONLY on each marker landing on a DISTINCT
    # display line — the question-internal 0xFFFE COUNT is cosmetic (vertical
    # layout) and intentionally NOT pinned to pristine.  The ONLY FFFE condition
    # that can break selection is two markers aliasing onto one line; guard it so
    # any future translation that does so fails the build loudly.
    _s1 = 0
    _mlines = []
    for _w in new_group:
        if _w == LINE_BREAK:
            if (_s1 & 0xFF) < 0x1F:
                _s1 = (_s1 + 1) & 0xFF
        elif _is_choice_marker(_w):
            _mlines.append(_s1 & 0xFF)
    if len(set(_mlines)) != len(_mlines):
        return (None, "marker-line-collision")
    return (new_group, None)


# ---------------------------------------------------------------------------
# Verification / diagnostics
# ---------------------------------------------------------------------------
def verify_patched(orig_path, patched_path):
    """
    Verify a patched file by RE-WALKING its Section 1 with the disassembler and
    checking that every walked Section-2 reference is consistent with the new
    Section 2.  Returns (issues, text_ops, name_ops).
    """
    patched = open(patched_path, "rb").read()

    sec2_size = struct.unpack_from("<I", patched, 0x14)[0]
    sec2_off = struct.unpack_from("<I", patched, 0x18)[0]
    sec2 = patched[sec2_off : sec2_off + sec2_size]
    sec2_words = sec2_size // 2
    words = [struct.unpack_from(">H", sec2, i * 2)[0] for i in range(sec2_words)]

    s1 = patched[HEADER_SIZE:sec2_off]
    issues = []

    ok, instrs = walk(s1)
    if not ok:
        issues.append("Section 1 walk FAILED on the patched file")
    recs = extract_records(s1, instrs)

    text_ops = len(recs["display"])
    name_ops = len(recs["name_ref"]) + len(recs["label"])

    for r in recs["display"]:
        if r["cnt"] == 0:
            continue
        end = r["off"] + r["cnt"]
        if end > sec2_words:
            issues.append(
                "DISPLAY_TEXT at S1+0x%X: range %d..%d exceeds Section 2 (%d words)"
                % (r["pc"], r["off"], end, sec2_words)
            )
        elif words[end - 1] != 0xFFFF:
            issues.append(
                "DISPLAY_TEXT at S1+0x%X: off=%d cnt=%d does not end at FFFF "
                "(word[end-1]=0x%04X)" % (r["pc"], r["off"], r["cnt"], words[end - 1])
            )

    for r in recs["label"]:
        if r["off"] + r["cnt"] > sec2_words:
            issues.append(
                "0x14 at S1+0x%X: off=%d cnt=%d exceeds Section 2 (%d words)"
                % (r["pc"], r["off"], r["cnt"], sec2_words)
            )

    # 0x0C/0x0D `idx` is a speaker/portrait CHANNEL BIT index (0..511), not a
    # Section-2 glyph offset (see the patch loop above), so it has no Section-2
    # bound to validate.  The EXE only accepts param in [0,12] and idx in
    # [0,511]; flag anything outside that as a structural anomaly instead.
    for r in recs["name_ref"]:
        if not (0 <= r["param"] <= 12) or r["idx"] >= 512:
            issues.append(
                "%s at S1+0x%X: channel record param=%d idx=%d outside the "
                "EXE-accepted range (param 0..12, idx 0..511)"
                % (
                    "SET_NAME" if r["op"] == 0x0C else "CLR_NAME",
                    r["pc"],
                    r["param"],
                    r["idx"],
                )
            )

    return issues, text_ops, name_ops


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        # Default: test on R1198
        print("=" * 60)
        print("  SECTION 1 OFFSET PATCHER -- Test Mode (R1198)")
        print("=" * 60)

        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(base)

        from encode_english_text import encode_text

        raw_dir = "extracted/packdata_raw"
        out_dir = "build/patched_type2"
        trans_file = "data/type2_translated/batch_r1198.json"

        if not os.path.isfile(trans_file):
            print("ERROR: Translation file not found:", trans_file)
            sys.exit(1)

        entries = json.load(open(trans_file, encoding="utf-8"))
        print("Loaded %d translation entries for R1198" % len(entries))

        def clean_and_encode(text):
            text = text.strip()
            if not text:
                return []
            if text.endswith(" /"):
                text = text + " "
            if " / " in text:
                parts = text.split(" / ")
                glyphs = []
                for pi, part in enumerate(parts):
                    part = part.strip()
                    if pi > 0:
                        glyphs.append(0xFFFE)
                    if part:
                        glyphs.extend(encode_text(part, max_chars_per_line=18, max_lines_per_page=3))
                return glyphs
            else:
                return encode_text(text, max_chars_per_line=18, max_lines_per_page=3)

        msg_trans = {}
        for entry in entries:
            eng = entry.get("english", "").strip()
            jpn = entry.get("japanese", "").strip()
            if not eng or eng == jpn:
                continue
            msg_idx = int(entry["msg_index"])
            try:
                glyphs = clean_and_encode(eng)
                if glyphs:
                    msg_trans[msg_idx] = glyphs
            except Exception as e:
                print("  ERROR encoding msg %d: %s" % (msg_idx, e))

        print("Encoded %d messages" % len(msg_trans))
        print()

        print("Injecting with VARIABLE-SIZE and patching offsets (walk-based)...")
        out_name, status = inject_and_patch(1198, msg_trans, raw_dir, out_dir)
        if out_name:
            print("  SUCCESS: %s -> %s" % (out_name, status))
        else:
            print("  FAILED:", status)
            sys.exit(1)

        print()
        print("Verifying patched file (re-walk)...")
        orig_path = os.path.join(raw_dir, "1198_type02.raw")
        patched_path = os.path.join(out_dir, "1198_type02.raw")
        issues, text_ops, name_ops = verify_patched(orig_path, patched_path)

        print("  DISPLAY_TEXT opcodes (walked): %d" % text_ops)
        print("  Name/label ref opcodes (walked): %d" % name_ops)
        if issues:
            print("  ISSUES FOUND:")
            for issue in issues:
                print("    - %s" % issue)
        else:
            print("  ALL REFERENCES VALID")

        # Show detailed diff of walked instructions
        print()
        print("Offset mapping details (walked instructions):")
        orig = open(orig_path, "rb").read()
        patched = open(patched_path, "rb").read()
        o_sec2_off = struct.unpack_from("<I", orig, 0x18)[0]
        o_s1 = orig[HEADER_SIZE:o_sec2_off]
        p_s1 = patched[HEADER_SIZE:o_sec2_off]
        _, o_instrs = walk(o_s1)
        o_recs = extract_records(o_s1, o_instrs)
        p_recs = extract_records(p_s1, o_instrs)
        shown = 0
        for o_r, p_r in zip(o_recs["display"], p_recs["display"]):
            if (o_r["off"], o_r["cnt"]) != (p_r["off"], p_r["cnt"]) and shown < 40:
                print(
                    "  S1+0x%05X  DISP off=%d cnt=%d -> off=%d cnt=%d"
                    % (o_r["pc"], o_r["off"], o_r["cnt"], p_r["off"], p_r["cnt"])
                )
                shown += 1
        for o_r, p_r in zip(o_recs["label"], p_recs["label"]):
            if (o_r["off"], o_r["cnt"]) != (p_r["off"], p_r["cnt"]) and shown < 60:
                print(
                    "  S1+0x%05X  0x14 off=%d cnt=%d -> off=%d cnt=%d"
                    % (o_r["pc"], o_r["off"], o_r["cnt"], p_r["off"], p_r["cnt"])
                )
                shown += 1

        o_s2size = struct.unpack_from("<I", orig, 0x14)[0]
        p_s2size = struct.unpack_from("<I", patched, 0x14)[0]
        print()
        print("Original sec2: %d bytes, Patched sec2: %d bytes" % (o_s2size, p_s2size))
        print("Section 1 changed: %s" % (o_s1 != p_s1))

    elif len(sys.argv) >= 3:
        orig_path = sys.argv[1]
        patched_path = sys.argv[2]
        output_path = sys.argv[3] if len(sys.argv) > 3 else patched_path

        print("Patching Section 1 offsets (walk-based):")
        print("  Original: %s" % orig_path)
        print("  Patched:  %s" % patched_path)
        print("  Output:   %s" % output_path)

        patch_file(orig_path, patched_path, output_path)

        print()
        print("Verifying (re-walk)...")
        issues, text_ops, name_ops = verify_patched(orig_path, output_path)
        print("  DISPLAY_TEXT: %d, Name/label refs: %d" % (text_ops, name_ops))
        if issues:
            for issue in issues:
                print("  ISSUE: %s" % issue)
        else:
            print("  ALL REFERENCES VALID")
    else:
        print("Usage: python patch_section1_offsets.py <original.raw> <patched.raw> [output.raw]")
        print("       python patch_section1_offsets.py   (test mode with R1198)")
        sys.exit(1)


if __name__ == "__main__":
    main()
