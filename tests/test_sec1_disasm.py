#!/usr/bin/env python3
"""
test_sec1_disasm.py -- TIER 1: the Section-1 byte-stream disassembler.

Guards the v85 BUG-1 foundation: the BFS walk over the recovered 193-opcode
table must walk every pristine scene script cleanly, and every walked 0x04
DISPLAY_TEXT with cnt>0 in the PRISTINE resources must satisfy the FFFF-end
invariant (the ground truth that separates true displays from the v84
pattern-matching false positives).  Also locks in that R989/R990/R1034
(binary VIF data masquerading as type-02) FAIL the walk, which is what makes
the skip-resource-on-walk-failure safety net ship them pristine.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (
    RAW_DIR,
    Skip,
    display_invariant_issues,
    get_disasm,
    main_exit,
    require_file,
)

# resource name -> (min expected walked instructions, max)
WALK_BOUNDS = {
    "1196_type02.raw": (3000, 20000),   # measured 7294
    "1197_type02.raw": (2000, 15000),   # measured 5097
    "1198_type02.raw": (1000, 8000),    # measured 2610
    "1193_type02.raw": (200, 2000),     # measured 484
}


def _pristine(name):
    return require_file(os.path.join(RAW_DIR, name), "pristine extract")


def _walk_pristine(name):
    sd = get_disasm()
    data = open(_pristine(name), "rb").read()
    ok, instrs, sec1, sec2_off = sd.walk_resource(data)
    assert ok, "%s: pristine Section 1 walk FAILED" % name
    bad_ops = [op for op in instrs.values() if op >= sd.N_OPS]
    assert not bad_ops, "%s: %d invalid opcodes in walk" % (name, len(bad_ops))
    lo, hi = WALK_BOUNDS[name]
    assert lo <= len(instrs) <= hi, (
        "%s: walked %d instructions, expected %d..%d (opcode table drift?)"
        % (name, len(instrs), lo, hi)
    )


def test_walk_pristine_r1196():
    _walk_pristine("1196_type02.raw")


def test_walk_pristine_r1197():
    _walk_pristine("1197_type02.raw")


def test_walk_pristine_r1198():
    _walk_pristine("1198_type02.raw")


def test_walk_pristine_r1193():
    _walk_pristine("1193_type02.raw")


def test_ffff_invariant_pristine():
    """Ground truth: every walked 0x04 cnt>0 span in the PRISTINE resources
    ends exactly on a group's 0xFFFF terminator."""
    total_checked = 0
    for name in sorted(WALK_BOUNDS):
        data = open(_pristine(name), "rb").read()
        issues, checked = display_invariant_issues(data, strict=True)
        assert not issues, "%s: %s" % (name, "; ".join(issues[:5]))
        total_checked += checked
    # all four resources together carry hundreds of true displays
    assert total_checked >= 500, (
        "only %d DISPLAY_TEXT spans checked -- walk regressed" % total_checked
    )


def test_walk_garbage_fails_cleanly():
    """Negative: garbage byte streams must not crash; the walk must fail or
    yield zero usable Section-2 records."""
    sd = get_disasm()
    garbage_streams = [
        struct.pack(">H", 0x4242) * 64,          # opcode 0x4242 >= 193
        bytes(range(256)) * 8,                    # pseudo-random bytes
        b"\x00\x04\x00",                          # truncated / odd length
        b"",                                      # empty
    ]
    for i, g in enumerate(garbage_streams):
        ok, instrs = sd.walk(g)  # must not raise
        recs = sd.extract_records(g, {pc: op for pc, op in instrs.items()
                                      if pc + 14 <= len(g)})
        usable = len(recs["display"]) + len(recs["name_ref"]) + len(recs["label"])
        assert (not ok) or usable == 0, (
            "garbage stream %d: walk ok=%s with %d usable records" % (i, ok, usable)
        )


def test_binary_type02_walks_fail():
    """R989/R990/R1034 are binary VIF data with a type-02 TOC code.  Their
    walks MUST fail so inject_and_patch ships them pristine (v83 VIF crash)."""
    sd = get_disasm()
    for name in ("0989_type02.raw", "0990_type02.raw", "1034_type02.raw"):
        data = open(_pristine(name), "rb").read()
        ok, _instrs, _sec1, _off = sd.walk_resource(data)
        assert not ok, (
            "%s: walk unexpectedly SUCCEEDED -- the skip-on-walk-failure "
            "safety net no longer protects this binary resource" % name
        )


TESTS = [
    test_walk_pristine_r1196,
    test_walk_pristine_r1197,
    test_walk_pristine_r1198,
    test_walk_pristine_r1193,
    test_ffff_invariant_pristine,
    test_walk_garbage_fails_cleanly,
    test_binary_type02_walks_fail,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_sec1_disasm")
