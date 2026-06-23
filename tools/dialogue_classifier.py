#!/usr/bin/env python3
"""dialogue_classifier.py — reproduce the ENGINE'S OWN render-mode decision for
every type-02 display group: BOXED DIALOGUE (wide box, nameplate) vs CENTERED
NARRATION.  This is NOT a heuristic — it is the mechanism the interpreter uses.

THE MECHANISM (discovered 2026-06-20, build/recon box-mode sweep; validated 19/19
on ground truth + grounded in a traced EXE write):
  Every 0x04 DISPLAY_TEXT block is preceded, in control-flow execution order, by a
  0x12 GOSUB to a short "mode-config" helper subroutine whose FIRST opcode is 0x63
  (the text align/justify setter).  The 0x63 operand-0 IS the render mode:
      0x63 op0 == 0  -> DIALOGUE  (boxed, left margin 30; align==0)
      0x63 op0 >= 1  -> NARRATION (centered; align!=0 -> bw=313 centered geometry)
  Proof chain: opcode 0x63 handler (EXE 0x2FA520) stores op0 to ctx+0x2a7 (align);
  the universal R1188 renderer 0x307DA0 branches on EXACTLY ctx+0x2a7 at 0x307E48
  (align!=0 -> centered/bw=313 narration; align==0 -> boxed dialogue).  This is the
  script-side source of the live descriptor tell (narration boxX==0/bw==313 vs
  dialogue boxX==-1/bw==0).  Because the helper sets PERSISTENT interpreter state,
  the rule is control-flow based, NOT block-local 0x14 adjacency — which is why a
  cutscene line with no local name-island (e.g. R1197 g4 barkeep, nameplate
  inherited from an earlier 0x60 speaker op) is still correctly DIALOGUE: its mode
  comes from the GOSUB-config immediately before its 0x04.

Earlier rules and why they FAIL: the old "0x04 block headed by a 0x14 name-island"
heuristic inverts every cutscene case (~4/19); 0x48-window-b&0x80 = 16/19 (false-
positive on the narration interludes g7/g13/g926/g575 that SHARE the dialogue
window); 0x60-speaker = 13-15/19 (sticky speaker over-floods D).  Only the 0x63
helper distinguishes a narration interlude embedded in a dialogue scene.

API (unchanged): build_dialogue_map(res) / build_narration_map(res) — now an exact
PARTITION of the groups covered by a walked 0x04 block.  Resources whose Section 1
fails the BFS walk (R35/989/990/1034 + the ~552 binary type-02) yield EMPTY maps
(ship pristine), matching inject_and_patch.
"""
import os
import struct
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from sec1_disasm import walk, extract_records, LENB  # noqa: E402
from patch_section1_offsets import parse_sec2_group_offsets  # noqa: E402

# Per-opcode byte lengths for the linear helper decode.  LENB (the walk's table)
# already covers the 193 handler opcodes; 0x1a (helper RETURN) and 0x4e are not in
# opcode_table_v85.json so supply them here (corpus-walk-consistent: 0x1a=2, 0x4e=6).
_LEN = dict(LENB)
_LEN.setdefault(0x1A, 2)
_LEN.setdefault(0x4E, 6)

# Control-flow opcodes that terminate a linear helper decode.
_JUMP_OPS = {0x08, 0x0B, 0x11}   # unconditional jump (no fallthrough)
_RETURN_OP = 0x1A                # helper return (pops ctx call stack)
_ALIGN_OP = 0x63                 # text align/justify setter — op0 is the mode
_GOSUB_OP = 0x12


def _b16(b, o):
    return struct.unpack_from(">H", b, o)[0]


def _b32(b, o):
    return struct.unpack_from(">I", b, o)[0]


def _helper_mode(sec1, tgt, depth=0):
    """Decode a GOSUB target linearly; return operand-0 of the FIRST 0x63 align
    opcode reached (the render mode), recursing into a nested 0x12, stopping at a
    return / unconditional jump / bad opcode.  None if no 0x63 governs this helper."""
    if depth > 4:
        return None
    pc = tgt
    n = len(sec1)
    steps = 0
    while pc + 2 <= n and steps < 64:
        op = _b16(sec1, pc)
        if op >= 193:
            return None
        if op == _ALIGN_OP:
            if pc + 4 > n:
                return None
            return _b16(sec1, pc + 2)          # 0x63 operand-0 = mode
        if op == _GOSUB_OP:
            if pc + 6 > n:
                return None
            m = _helper_mode(sec1, _b32(sec1, pc + 2), depth + 1)
            if m is not None:
                return m
        if op == _RETURN_OP or op in _JUMP_OPS:
            return None
        pc += _LEN.get(op, 2)
        steps += 1
    return None


def _classify(res_idx, raw_dir=None):
    """Return {group_index: 'D'|'N'} for every group covered by a walked 0x04
    block in resource `res_idx`, using the 0x63-helper rule.  Empty dict on any
    failure / non-type-02 / binary Section 1 (ship pristine)."""
    raw_dir = raw_dir or os.path.join(BASE, "extracted", "packdata_raw")
    path = os.path.join(raw_dir, f"{res_idx:04d}_type02.raw")
    if not os.path.isfile(path):
        return {}
    try:
        raw = open(path, "rb").read()
        sec2_off = struct.unpack_from("<I", raw, 0x18)[0]
        sec2_size = struct.unpack_from("<I", raw, 0x14)[0]
        sec1 = raw[0x20:sec2_off]
        sec2 = raw[sec2_off:sec2_off + sec2_size]
        groups, _trailing = parse_sec2_group_offsets(sec2)
        ok, instrs = walk(sec1)
        if not ok:
            return {}
        recs = extract_records(sec1, instrs)
    except Exception:
        return {}

    # 0x14 NAME-ISLAND glyph target groups.  Whether one is a "nameplate to skip"
    # depends on the RENDER MODE of its covering block, not on the ref position:
    #  * NARRATION context — the verbatim name glyphs glue to the body and no wrap
    #    can fit them in the 360 box ("Melanie, Milly, Kunnar:", "Part-timer ...").
    #    Exclude -> default char-wrap; the engine draws the name as a separate
    #    nameplate anyway.
    #  * DIALOGUE context — the engine draws the name as a separate nameplate and the
    #    480 box holds the body (R1197 g903 Lady Knight "I must know...", g577 Shady
    #    Man).  KEEP it, or it falls to the narrow default wrap and cramps to 4 lines.
    name_groups = set()
    for L in recs["label"]:
        off = L["off"]
        for gi, (gs, ge) in enumerate(groups):
            if gs <= off <= ge:
                name_groups.add(gi)
                break

    pcs = sorted(instrs)
    # mode of each 0x12 GOSUB (None if its helper has no 0x63)
    gosub_mode = {pc: _helper_mode(sec1, _b32(sec1, pc + 2))
                  for pc in pcs if instrs[pc] == _GOSUB_OP}
    gosub_pcs = sorted(p for p in gosub_mode if gosub_mode[p] is not None)
    displays = [(pc, _b32(sec1, pc + 2), _b32(sec1, pc + 6))
                for pc in pcs if instrs[pc] == 0x04]

    out = {}
    prev_mode = None
    import bisect
    for pc, off, cnt in sorted(displays):
        # nearest preceding config GOSUB (pc order; the interpreter emits the
        # mode-config GOSUB immediately before the 0x04 it governs)
        i = bisect.bisect_left(gosub_pcs, pc) - 1
        m = gosub_mode[gosub_pcs[i]] if i >= 0 else None
        if m is None:
            m = prev_mode                       # continuation block inherits mode
        # conservative default: a block before any 0x63 -> NARRATION (never-paginate)
        mode = "N" if m is None else ("D" if m == 0 else "N")
        if m is not None:
            prev_mode = m
        end = off + cnt
        for gi, (gs, ge) in enumerate(groups):
            if not (ge < off or gs >= end):
                if gi in name_groups and mode == "N":
                    continue                    # nameplate in narration -> default
                out[gi] = mode                  # last covering block (pc order) wins
    return out


def build_dialogue_map(res_idx, raw_dir=None):
    """Groups the engine renders as BOXED DIALOGUE (safe to wrap at the wide box /
    auto-paginate).  Empty set on walk failure / non-type-02."""
    return {gi for gi, m in _classify(res_idx, raw_dir).items() if m == "D"}


def build_narration_map(res_idx, raw_dir=None):
    """Groups the engine renders as CENTERED NARRATION.  Exact complement of
    build_dialogue_map over the covered groups.  Empty set on walk failure."""
    return {gi for gi, m in _classify(res_idx, raw_dir).items() if m == "N"}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    d1196 = build_dialogue_map(1196)
    d1197 = build_dialogue_map(1197)
    n1196 = build_narration_map(1196)
    n1197 = build_narration_map(1197)
    # GROUND TRUTH (19 cases, on-screen verified): the 0x63-helper rule reproduces
    # the engine's render mode, INCLUDING the cutscene cases that defeat every other
    # rule (g4 inherited nameplate; g7/g13/g926/g575 narration interludes inside a
    # dialogue scene sharing its window/speaker).
    GT_DIALOGUE = [(1197, 4), (1197, 9), (1197, 10), (1197, 904), (1197, 922),
                   (1197, 925), (1197, 927), (1197, 929), (1196, 577), (1197, 905)]
    GT_NARRATION = [(1197, 3), (1197, 7), (1197, 13), (1197, 926),
                    (1196, 568), (1196, 569), (1196, 570), (1196, 575),
                    (1196, 615), (1196, 616)]
    dmaps = {1196: d1196, 1197: d1197}
    nmaps = {1196: n1196, 1197: n1197}
    checks = []
    for r, g in GT_DIALOGUE:
        checks.append((f"R{r} g{g} IS dialogue", g in dmaps[r]))
    for r, g in GT_NARRATION:
        checks.append((f"R{r} g{g} IS narration", g in nmaps[r] and g not in dmaps[r]))
    checks.append(("R35 walk-fail -> empty dialogue", build_dialogue_map(35) == set()))
    checks.append(("R35 walk-fail -> empty narration", build_narration_map(35) == set()))
    checks.append(("dialogue/narration disjoint (R1196)", not (d1196 & n1196)))
    checks.append(("dialogue/narration disjoint (R1197)", not (d1197 & n1197)))
    ok = True
    for name, cond in checks:
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
        ok = ok and cond
    print(f"R1196 D:{len(d1196)} N:{len(n1196)} | R1197 D:{len(d1197)} N:{len(n1197)}")
    sys.exit(0 if ok else 1)
