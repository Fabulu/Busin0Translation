#!/usr/bin/env python3
"""
sec1_disasm.py -- Byte-stream disassembler for type-02 Section 1 opcode streams
================================================================================

The SLPM_653.78 scene-script interpreter (dispatcher at VA 0x2F3230) reads each
opcode as a big-endian u16 from a BYTE-addressed stream and jumps through a
193-entry handler table.  Per-opcode BYTE lengths (several are odd -- the
stream is NOT word-aligned) were recovered by static analysis of the EXE and
validated by walking every pristine type-02 resource with 0 invalid opcodes
(see build/recon_v85/exe-interpreter/corpus_validate.py).

This module provides:
  walk(sec1_bytes)            -> (ok, instrs)  BFS reachability walk
  extract_records(sec1, instrs) -> dict with all walked 0x04/0x0C/0x0D/0x14
                                   records and their operand values

Section 1 = file offset 0x20 .. sec2_offset of a type-02 resource.
All jump targets are BYTE offsets relative to the Section-1 base.
"""

import json
import os
import struct

N_OPS = 193

# Control-flow opcode classes (byte lengths come from the recovered table)
JUMP_OPS = {0x08, 0x0B, 0x11}    # unconditional jump, NO fallthrough
GOSUB_OPS = {0x12}               # call: follows target AND falls through
COND_OPS = {0x06, 0x07}          # conditional jump: target @+10, falls through

_TABLE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "build", "recon_v85", "exe-interpreter", "opcode_table_v85.json",
)


def _load_lengths():
    """Load per-opcode byte lengths from the recovered v85 opcode table."""
    with open(_TABLE_PATH, encoding="utf-8") as f:
        table = json.load(f)
    lens = {}
    for key, info in table["opcodes"].items():
        lens[int(key, 16)] = info["bytes"]
    if len(lens) != N_OPS:
        raise RuntimeError(
            "opcode_table_v85.json has %d opcodes, expected %d" % (len(lens), N_OPS)
        )
    return lens


LENB = _load_lengths()


def walk(sec1):
    """
    BFS-walk a Section 1 byte stream from pc=0, following all jump / gosub /
    conditional-jump targets (exactly the corpus_validate.py walk).

    Returns (ok, instrs):
      ok     -- False if any reachable opcode is >= 193 (not in the handler
                table) or any control-flow target is out of range.  A walk
                that fails must NOT be used for patching.
      instrs -- dict {pc (byte offset, sec1-relative): opcode} for every
                reachable instruction (best effort even when ok is False).
    """
    n = len(sec1)

    def beu16(o):
        return struct.unpack_from(">H", sec1, o)[0]

    def beu32(o):
        return struct.unpack_from(">I", sec1, o)[0]

    instrs = {}
    ok = True
    work = [0]
    while work:
        pc = work.pop()
        if pc < 0 or pc >= n:
            ok = False  # control-flow target out of range
            continue
        while pc not in instrs:
            if pc < 0 or pc + 2 > n:
                # Fallthrough ran off the end of Section 1.  Zero padding is
                # executable (2-byte NOPs), so paths routinely walk to the
                # exact end of the section -- this is a normal path stop,
                # NOT a failure (matches corpus_validate.py behavior).
                break
            opc = beu16(pc)
            if opc >= N_OPS:
                ok = False
                break
            instrs[pc] = opc
            ln = LENB[opc]
            if opc in JUMP_OPS:
                if pc + 6 > n:
                    ok = False
                    break
                t = beu32(pc + 2)
                if t >= n:
                    ok = False
                    break
                pc = t
                continue
            if opc in GOSUB_OPS:
                if pc + 6 > n:
                    ok = False
                    break
                t = beu32(pc + 2)
                if t >= n:
                    ok = False
                elif t not in instrs:
                    work.append(t)
            if opc in COND_OPS:
                if pc + 14 > n:
                    ok = False
                    break
                t = beu32(pc + 10)
                if t >= n:
                    ok = False
                elif t not in instrs:
                    work.append(t)
            pc += ln
    return ok, instrs


def extract_records(sec1, instrs):
    """
    Extract operand values of all walked Section-2-referencing instructions.

    Returns dict:
      'display'  -- list of {'pc', 'off', 'cnt'} for 0x04 DISPLAY_TEXT
                    (u32 glyph word offset @pc+2, u32 glyph word count @pc+6)
      'name_ref' -- list of {'pc', 'op', 'param', 'idx'} for 0x0C SET_NAME_REF
                    and 0x0D CLEAR_NAME_REF (u16 param @pc+2, u16 idx @pc+4)
      'label'    -- list of {'pc', 'param', 'off', 'cnt'} for 0x14 NAME/LABEL
                    REF (u16 param @pc+2, s16 @pc+4 [always 0xFFFF],
                    u32 NAME_OFF @pc+6, u32 NAME_CNT @pc+10)
    """

    def beu16(o):
        return struct.unpack_from(">H", sec1, o)[0]

    def beu32(o):
        return struct.unpack_from(">I", sec1, o)[0]

    recs = {"display": [], "name_ref": [], "label": []}
    for pc in sorted(instrs):
        op = instrs[pc]
        if op == 0x04:
            recs["display"].append(
                {"pc": pc, "off": beu32(pc + 2), "cnt": beu32(pc + 6)}
            )
        elif op in (0x0C, 0x0D):
            recs["name_ref"].append(
                {"pc": pc, "op": op, "param": beu16(pc + 2), "idx": beu16(pc + 4)}
            )
        elif op == 0x14:
            recs["label"].append(
                {
                    "pc": pc,
                    "param": beu16(pc + 2),
                    "off": beu32(pc + 6),
                    "cnt": beu32(pc + 10),
                }
            )
    return recs


def walk_resource(data):
    """
    Convenience: walk the Section 1 of a full type-02 resource blob.

    Returns (ok, instrs, sec1_bytes, sec2_offset).
    """
    if len(data) < 0x20:
        raise ValueError("file too small to be a type-02 resource")
    sec2_off = struct.unpack_from("<I", data, 0x18)[0]
    if sec2_off <= 0x20 or sec2_off > len(data):
        raise ValueError("invalid sec2_offset=0x%x" % sec2_off)
    sec1 = data[0x20:sec2_off]
    ok, instrs = walk(sec1)
    return ok, instrs, sec1, sec2_off


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python sec1_disasm.py <resource.raw> [...]")
        sys.exit(1)
    for path in sys.argv[1:]:
        data = open(path, "rb").read()
        ok, instrs, sec1, sec2_off = walk_resource(data)
        recs = extract_records(sec1, instrs)
        print(
            "%s: sec1=%d bytes, walk %s, %d instrs, %d DISPLAY_TEXT, "
            "%d name refs (0C/0D), %d 0x14 labels"
            % (
                os.path.basename(path),
                len(sec1),
                "OK" if ok else "FAILED",
                len(instrs),
                len(recs["display"]),
                len(recs["name_ref"]),
                len(recs["label"]),
            )
        )
