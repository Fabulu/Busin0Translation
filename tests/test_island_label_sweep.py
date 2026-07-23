#!/usr/bin/env python3
"""
test_island_label_sweep.py -- guard against stale MID-GROUP DISPLAY offsets and
stale 0x14 labels in Section-1 code ISLANDS (issues #27/#30/#31 root cause).

Background
----------
Speaker-labeled dialogue inside an unwalked code island (runtime/indirect
dispatch -- the v171 class) is a 0x14 LABEL (name prefix = the first words of
the group) immediately followed by a 0x04 DISPLAY whose offset points MID-group
(group_start + prefix_len).  patch_section1's pass a2 only remaps an unwalked
0x04 whose offset is EXACTLY a pristine group start, so these island pairs
shipped STALE: once English grew Section 2 the pristine offset landed inside a
DIFFERENT scene's text and the span no longer ended on 0xFFFF -- wrong text +
non-terminated display = infinite loop (B1F shop/orcs #27, B8F dying soldier
#30, B10F Ingo #31).  Island 0x14 labels were never swept at all (pass b
patches WALKED labels only) -> stale nameplates.

The fix is patch_section1's pass a3 (island label-pair sweep): every unwalked
0x04 whose offset lies INSIDE a group and whose pristine span ends exactly on a
group 0xFFFF terminator is remapped through map_rel_offset, hard-asserted to
end on the NEW 0xFFFF; every unwalked SHORT 0x14 (cnt <= 10) inside a group is
remapped through the pass-b plan/clamp/identity logic.

What this test does (TIER 2 -- SKIPs when build outputs are missing)
--------------------------------------------------------------------
For R1203 / R1210 / R1212 it reconstructs the exact input inject_and_patch
feeds patch_section1 (pristine Section 1 + the BUILT Section 2), runs the real
patcher, and asserts:
  1. EVERY unwalked mid-group display satisfying the pristine gate now ends on
     the new 0xFFFF terminator (zero stale island displays), and
  2. the specific loop-bug records (known island pcs from the Jul-23 root-cause
     report) are enumerated, repointed, and their 0x14 labels land inside their
     own group's new bounds.
"""

import contextlib
import io
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import RAW_DIR, PACKDATA_RES_DIR, Skip, get_disasm, main_exit

# Known stale island records per LOOP_FINDINGS (issues #27/#30/#31):
# resource -> ([0x14 label pcs], [0x04 display pcs])
KNOWN_ISLAND_PAIRS = {
    1203: ([0x9DC6, 0x9EF0, 0x447B], [0x9DDC, 0x9F1A, 0x4491]),
    1210: ([0x88F0, 0x894E], [0x8902, 0x8960]),
    1212: ([0x7C96, 0x7CEC, 0x7D80, 0x7E1A, 0x8026],
           [0x7CAE, 0x7D04, 0x7D98, 0x7E2C, 0x8038]),
}


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


def _find_gi(ranges, off):
    for gi, (gs, ge) in enumerate(ranges):
        if gs <= off <= ge:
            return gi
    return None


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


def _island_midgroup_displays(sec1, ranges, instrs):
    """Enumerate (pc, sgi, egi) for every UNWALKED 0x0004 whose offset lies
    INSIDE a group (rel > 0), whose span ends exactly on a group 0xFFFF
    terminator at/after that group, and whose record bytes do not straddle any
    walked instruction.  Mirrors patch_section1 pass a3 part 1."""
    lenb = get_disasm().LENB
    walked_pcs = set(instrs)
    walked_bytes = set()
    for pc, op in instrs.items():
        walked_bytes.update(range(pc, pc + lenb[op]))
    term2gi = {e: gi for gi, (s, e) in enumerate(ranges)}
    out = []
    n = len(sec1)
    i = 0
    while i <= n - 10:
        if struct.unpack_from(">H", sec1, i)[0] != 0x0004 or i in walked_pcs:
            i += 1
            continue
        off = struct.unpack_from(">I", sec1, i + 2)[0]
        cnt = struct.unpack_from(">I", sec1, i + 6)[0]
        if cnt == 0 or not walked_bytes.isdisjoint(range(i, i + 10)):
            i += 1
            continue
        sgi = _find_gi(ranges, off)
        if sgi is None or off - ranges[sgi][0] == 0:
            i += 1
            continue
        egi = term2gi.get(off + cnt - 1)
        if egi is None or egi < sgi:
            i += 1
            continue
        out.append((i, sgi, egi))
        i += 10
    return out


def _run_patcher(res):
    """Returns (pristine, pristine_s1, result_s1, result_ranges, result_words,
    pristine_ranges, instrs) or raises Skip when the resource cannot be
    checked.  `instrs` is the pristine BFS walk {pc: opcode}."""
    disasm = get_disasm()
    from patch_section1_offsets import patch_section1

    pris_path = os.path.join(RAW_DIR, "%d_type02.raw" % res)
    built_path = os.path.join(PACKDATA_RES_DIR, "%d_type02.raw" % res)
    if not os.path.isfile(pris_path) or not os.path.isfile(built_path):
        raise Skip("missing pristine/built pair for R%d (run a build first)" % res)
    pristine = open(pris_path, "rb").read()
    built = open(built_path, "rb").read()

    p_off, _, p_s1, p_s2 = _parts(pristine)
    p_ranges, _p_words = _groups(p_s2)

    ok, instrs = disasm.walk(p_s1)
    assert ok, "R%d: pristine Section 1 walk failed" % res

    injected = _reconstruct_injected(pristine, built)
    # name_plan=None drives the conservative standalone remap; its WARNING
    # chatter (which the real build, with a plan, never emits) is silenced.
    with contextlib.redirect_stdout(io.StringIO()):
        result = patch_section1(pristine, injected, name_plan=None, res_name=str(res))

    _r_off, _, r_s1, r_s2 = _parts(result)
    r_ranges, r_words = _groups(r_s2)
    if len(r_ranges) != len(p_ranges):
        raise Skip("R%d: group count changed pristine vs built" % res)
    return pristine, p_s1, r_s1, r_ranges, r_words, p_ranges, instrs


def test_no_stale_island_displays():
    """After the a3 sweep, EVERY unwalked mid-group DISPLAY satisfying the
    pristine group/terminator gate must end on the NEW 0xFFFF terminator in
    R1203/R1210/R1212 (the #27/#30/#31 loop resources)."""
    for res in sorted(KNOWN_ISLAND_PAIRS):
        (_pristine, p_s1, r_s1, r_ranges, r_words,
         p_ranges, instrs) = _run_patcher(res)
        islands = _island_midgroup_displays(p_s1, p_ranges, instrs)
        assert islands, "R%d: no island mid-group displays enumerated" % res
        stale = []
        for pc, sgi, egi in islands:
            off = struct.unpack_from(">I", r_s1, pc + 2)[0]
            cnt = struct.unpack_from(">I", r_s1, pc + 6)[0]
            end = off + cnt
            if (cnt <= 0 or end > len(r_words)
                    or r_words[end - 1] != 0xFFFF
                    or end - 1 != r_ranges[egi][1]):
                stale.append((pc, sgi, egi, off, cnt))
        assert not stale, (
            "R%d: %d island mid-group displays STALE after pass a3: %s"
            % (res, len(stale), ["pc=0x%X G%d-%d off=%d cnt=%d" % s
                                 for s in stale[:5]])
        )
        print("  R%d: %d island mid-group displays all end on FFFF" % (res, len(islands)))


def test_known_loop_records_fixed():
    """The specific #27/#30/#31 records must be enumerated by the sweep and be
    correctly repointed: displays end on their span's new terminator, labels
    land inside their own group's new bounds."""
    for res, (label_pcs, disp_pcs) in sorted(KNOWN_ISLAND_PAIRS.items()):
        (_pristine, p_s1, r_s1, r_ranges, r_words,
         p_ranges, instrs) = _run_patcher(res)
        enumerated = {pc for pc, _s, _e in
                      _island_midgroup_displays(p_s1, p_ranges, instrs)}
        for pc in disp_pcs:
            assert pc not in instrs, (
                "R%d S1+0x%X unexpectedly WALKED (not an island)" % (res, pc))
            assert struct.unpack_from(">H", p_s1, pc)[0] == 0x0004, (
                "R%d S1+0x%X is not a 0x04 opcode" % (res, pc))
            assert pc in enumerated, (
                "R%d S1+0x%X not enumerated as an island mid-group display -- "
                "the a3 gate no longer covers the known loop record" % (res, pc))
            off = struct.unpack_from(">I", r_s1, pc + 2)[0]
            cnt = struct.unpack_from(">I", r_s1, pc + 6)[0]
            assert cnt > 0 and off + cnt <= len(r_words) and \
                r_words[off + cnt - 1] == 0xFFFF, (
                "R%d S1+0x%X: patched island display off=%d cnt=%d does not "
                "end on FFFF" % (res, pc, off, cnt))
        for pc in label_pcs:
            assert struct.unpack_from(">H", p_s1, pc)[0] == 0x0014, (
                "R%d S1+0x%X is not a 0x14 opcode" % (res, pc))
            p_off = struct.unpack_from(">I", p_s1, pc + 6)[0]
            gi = _find_gi(p_ranges, p_off)
            assert gi is not None, (
                "R%d S1+0x%X: pristine label offset %d outside groups"
                % (res, pc, p_off))
            off = struct.unpack_from(">I", r_s1, pc + 6)[0]
            cnt = struct.unpack_from(">I", r_s1, pc + 10)[0]
            ngs, nge = r_ranges[gi]
            assert ngs <= off and off + cnt <= nge, (
                "R%d S1+0x%X: patched island label off=%d cnt=%d outside its "
                "group's new bounds [%d,%d)" % (res, pc, off, cnt, ngs, nge))
    print("  known #27/#30/#31 island records verified: %s"
          % {r: v for r, v in sorted(KNOWN_ISLAND_PAIRS.items())})


TESTS = [
    test_no_stale_island_displays,
    test_known_loop_records_fixed,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_island_label_sweep")
