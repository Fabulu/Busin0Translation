#!/usr/bin/env python3
"""
test_stale_display_offsets.py -- guard against stale DISPLAY_TEXT offsets in
Section-1 code ISLANDS the BFS walk cannot reach (issue #9 root cause).

Background
----------
patch_section1() re-points 0x04 DISPLAY_TEXT operands after English injection
grows/shrinks Section 2.  Historically it re-pointed ONLY opcodes reached by the
static BFS walk from pc=0.  But some scene "events" (the resurrection ceremony
in R1200, the R1204 gambling game's "Hand over Cursed Armor and play? Yes/No",
R1208 "lend your strength?", R1210 "Fight/Flee", ...) live in code ISLANDS
entered only by runtime/indirect dispatch, so their DISPLAY_TEXT opcodes are
never walked.  Their offsets kept the PRISTINE value; once Section 2 resized
they pointed at the WRONG group -- a choice rendered as a flat continue-arrow,
narration showed a different group's text.

The fix is patch_section1's group-anchored linear sweep (pass a2): every
UNWALKED 0x0004 whose offset is exactly a pristine group-start AND whose span
ends exactly on that group's 0xFFFF terminator is remapped too.

What this test does
-------------------
For every translated type-02 resource it enumerates -- from the PRISTINE
Section 1 -- every "whole-group" DISPLAY_TEXT (offset == a group start, span
ends on that group's FFFF), WALKED OR NOT.  It then reconstructs the exact input
inject_and_patch feeds patch_section1 (pristine Section 1 + the built Section 2),
runs the real patcher, and asserts EVERY such opcode now points at that same
logical group's NEW bounds (span ends on the NEW 0xFFFF).  Zero stale offsets
allowed.  R1200/R1204/R1208/R1210 must be present and clean, and their known
choice groups must still carry FFC0.. markers.
"""

import contextlib
import glob
import io
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import RAW_DIR, PACKDATA_RES_DIR, Skip, get_disasm, main_exit

CHOICE_MIN, CHOICE_MAX = 0xFFC0, 0xFFCF

# (resource, group index) of choice displays that regressed to a continue-arrow
# in issue #9.  Each must be enumerated as a whole-group display, be fixed, and
# still carry option markers.
KNOWN_CHOICE_EVENTS = [
    (1200, 137), (1200, 169), (1204, 169), (1204, 178),
    (1208, 804), (1210, 710),
]


def _parts(data):
    sec2_size = struct.unpack_from("<I", data, 0x14)[0]
    sec2_off = struct.unpack_from("<I", data, 0x18)[0]
    return sec2_off, sec2_size, data[0x20:sec2_off], data[sec2_off:sec2_off + sec2_size]


def _groups(sec2):
    n = len(sec2) // 2
    words = [struct.unpack_from(">H", sec2, i * 2)[0] for i in range(n)]
    ranges, start = [], 0
    for i, w in enumerate(words):
        if w == 0xFFFF:
            ranges.append((start, i))
            start = i + 1
    return ranges, words


def _reconstruct_injected(pristine, built):
    """Exactly what inject_and_patch hands patch_section1: pristine Section 1
    (offsets still pristine) + the built (resized) Section 2."""
    p_off, _, p_s1, _ = _parts(pristine)
    b_off, b_sz, _, b_s2 = _parts(built)
    if p_off != b_off:
        raise Skip("Section-1 length differs pristine vs built (%d/%d)" % (p_off, b_off))
    b_after = built[b_off + b_sz:]
    hdr = bytearray(pristine[:0x20])
    struct.pack_into("<I", hdr, 0x14, b_sz)
    return bytes(hdr) + p_s1 + b_s2 + b_after


def _whole_group_displays(sec1, ranges, walked_pcs):
    """Enumerate (pc, sgi, egi, walked) for every 0x0004 whose offset is a group
    start and whose span ends exactly on a group FFFF terminator at or after the
    start group -- single-group (sgi==egi) OR multi-group narration runs
    (egi>sgi).  Mirrors the patch_section1 island-sweep gate, including its
    exclusion of the degenerate offset-0 multi-group binary false positive."""
    start2gi = {s: gi for gi, (s, e) in enumerate(ranges)}
    term2gi = {e: gi for gi, (s, e) in enumerate(ranges)}
    out = []
    n = len(sec1)
    i = 0
    while i <= n - 10:
        if struct.unpack_from(">H", sec1, i)[0] == 0x0004:
            off = struct.unpack_from(">I", sec1, i + 2)[0]
            cnt = struct.unpack_from(">I", sec1, i + 6)[0]
            sgi = start2gi.get(off)
            egi = term2gi.get(off + cnt - 1) if cnt > 0 else None
            if sgi is not None and egi is not None and egi >= sgi \
                    and not (egi > sgi and off == 0):
                out.append((i, sgi, egi, i in walked_pcs))
        i += 1
    return out


def _load_pair(res):
    pris_path = os.path.join(RAW_DIR, "%d_type02.raw" % res)
    built_path = os.path.join(PACKDATA_RES_DIR, "%d_type02.raw" % res)
    if not os.path.isfile(pris_path) or not os.path.isfile(built_path):
        return None
    return open(pris_path, "rb").read(), open(built_path, "rb").read()


def _check_resource(res):
    """Return (checked, stale_list, choice_gis).  Skips (returns None) resources
    that ship pristine (walk-failed Section 1) or whose group count changed."""
    disasm = get_disasm()
    walk = disasm.walk
    from patch_section1_offsets import patch_section1

    pair = _load_pair(res)
    if pair is None:
        return None
    pristine, built = pair

    p_off, _, p_s1, p_s2 = _parts(pristine)
    p_ranges, p_words = _groups(p_s2)

    ok, instrs = walk(p_s1)
    if not ok:
        return None  # walk-failed resource -> ships pristine, patcher not run
    walked = set(instrs)

    whole = _whole_group_displays(p_s1, p_ranges, walked)
    if not whole:
        return None  # nothing to check

    injected = _reconstruct_injected(pristine, built)
    # name_plan=None drives the conservative standalone 0x14 remap (noisy WARNINGs
    # that the real build, which supplies a plan, never emits).  Its label
    # clamping does not affect the whole-group DISPLAY_TEXT offsets checked here
    # (offset==group-start -> rel 0 -> new group-start, plan-independent), so we
    # silence the chatter to keep the gate output focused.
    with contextlib.redirect_stdout(io.StringIO()):
        result = patch_section1(pristine, injected, name_plan=None, res_name=str(res))

    r_off, _, r_s1, r_s2 = _parts(result)
    r_ranges, r_words = _groups(r_s2)
    if len(r_ranges) != len(p_ranges):
        return None  # group count changed -> different handling upstream

    stale = []
    choice_gis = []
    for pc, sgi, egi, was_walked in whole:
        off = struct.unpack_from(">I", r_s1, pc + 2)[0]
        cnt = struct.unpack_from(">I", r_s1, pc + 6)[0]
        ngs = r_ranges[sgi][0]
        nge = r_ranges[egi][1]  # terminator of the (last) group in the span
        good = (off == ngs and cnt > 0 and off + cnt - 1 == nge
                and r_words[nge] == 0xFFFF)
        if not good:
            stale.append((pc, sgi, egi, was_walked, off, cnt, ngs, nge))
        # a choice display is single-group with FFC0.. markers in it
        if sgi == egi and any(CHOICE_MIN <= w <= CHOICE_MAX
                              for w in r_words[ngs:nge]):
            choice_gis.append(sgi)
    return whole, stale, choice_gis


def test_no_stale_display_offsets_corpus():
    """No translated type-02 resource may retain a stale whole-group DISPLAY_TEXT
    offset after patch_section1 -- walked OR in an unreachable code island."""
    get_disasm()  # Skip cleanly if the opcode table is unavailable
    built = sorted(glob.glob(os.path.join(PACKDATA_RES_DIR, "*_type02.raw")))
    if not built:
        raise Skip("no build/packdata_resources/*_type02.raw (run a build first)")

    checked = 0
    failures = []
    for path in built:
        res = int(os.path.basename(path).split("_")[0])
        try:
            r = _check_resource(res)
        except Skip:
            continue
        if r is None:
            continue
        whole, stale, _ = r
        checked += 1
        if stale:
            failures.append(
                "R%d: %d/%d whole-group displays STALE (e.g. %s)"
                % (res, len(stale), len(whole),
                   ["pc=0x%X G%d-%d walked=%s off=%d" % (s[0], s[1], s[2], s[3], s[4])
                    for s in stale[:4]])
            )
    assert checked > 0, "no resources were actually checked -- harness broken"
    assert not failures, "STALE display offsets remain:\n  " + "\n  ".join(failures)
    print("  %d translated type-02 resources: 0 stale whole-group displays" % checked)


def test_known_choice_events_fixed():
    """The specific issue-#9 choice events (R1200/R1204/R1208/R1210) must be
    enumerated as whole-group displays, be repointed correctly, and their target
    groups must still carry FFC0.. option markers (i.e. render as a menu)."""
    get_disasm()
    by_res = {}
    for res, gi in KNOWN_CHOICE_EVENTS:
        by_res.setdefault(res, []).append(gi)

    for res, gis in sorted(by_res.items()):
        r = _check_resource(res)
        assert r is not None, (
            "R%d could not be checked (missing build artifact / walk-failed) -- "
            "this test needs a build present" % res
        )
        whole, stale, choice_gis = r
        enumerated = {sgi for _pc, sgi, _egi, _w in whole}
        assert not stale, (
            "R%d has %d stale display offsets after the fix: %s"
            % (res, len(stale), stale[:3])
        )
        for gi in gis:
            assert gi in enumerated, (
                "R%d G%d is not enumerated as a whole-group display" % (res, gi)
            )
            assert gi in choice_gis, (
                "R%d G%d target group lost its FFC0.. option markers" % (res, gi)
            )
    print("  issue-#9 choice events verified: %s" % KNOWN_CHOICE_EVENTS)


TESTS = [
    test_no_stale_display_offsets_corpus,
    test_known_choice_events_fixed,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_stale_display_offsets")
