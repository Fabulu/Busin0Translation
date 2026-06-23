#!/usr/bin/env python3
"""
test_r46_board.py -- R46 bulletin board injection (BUG-8 centering, BUG-9 typo).

TIER 1: imports the padding algorithm (build_symmetric_payload) and the
encoder straight from build/inject_r46_r47.py via AST extraction (the script
runs at import, so only the function defs are executed) and exercises them on
synthetic messages: capacity exactly filled, FFFE count preserved, no
dangling FFFE, uniform leading pad across lines.

TIER 2: checks the built build/packdata_resources/0046_type03.raw against the
pristine extract: byte length unchanged, per-sub FFFF counts unchanged, and
sub0 msg 21 decodes containing "i'll never forget" (the BUG-9 fix).
"""

import ast
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (
    DATA_DIR,
    PACKDATA_RES_DIR,
    RAW_DIR,
    ROOT,
    Skip,
    decode_glyphs,
    main_exit,
    require_file,
)

INJECTOR = os.path.join(ROOT, "build", "inject_r46_r47.py")

_FUNCS = None


def _load_injector_funcs():
    """Extract encode_english/build_symmetric_payload from the injector source
    WITHOUT executing its top-level build code."""
    global _FUNCS
    if _FUNCS is not None:
        return _FUNCS
    require_file(INJECTOR, "R46/R47 injector")
    src = open(INJECTOR, encoding="utf-8").read()
    tree = ast.parse(src)
    wanted = {"encode_english", "build_symmetric_payload"}
    nodes = [
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name in wanted
    ]
    found = {n.name for n in nodes}
    missing = wanted - found
    assert not missing, (
        "build/inject_r46_r47.py lost function(s) %s -- the symmetric "
        "padding fix (BUG-8) appears to be gone" % sorted(missing)
    )
    glyph_table = json.load(
        open(os.path.join(DATA_DIR, "english_glyph_table.json"), encoding="utf-8")
    )
    ns = {"struct": struct, "json": json, "glyph_table": glyph_table}
    mod = ast.Module(body=nodes, type_ignores=[])
    exec(compile(ast.fix_missing_locations(mod), INJECTOR, "exec"), ns)
    _FUNCS = ns
    return ns


def _lines(payload):
    out = [[]]
    for g in payload:
        if g == 0xFFFE:
            out.append([])
        else:
            out[-1].append(g)
    return out


def _leading_zeros(line):
    n = 0
    for g in line:
        if g != 0:
            break
        n += 1
    return n


# Synthetic messages: glyph values deliberately avoid 0 (so leading zeros are
# unambiguously padding) and 0xFFFE marks line breaks.
def _mk(text_lines):
    glyphs = []
    for i, ln in enumerate(text_lines):
        if i > 0:
            glyphs.append(0xFFFE)
        glyphs.extend([0x21 + (ord(c) % 50) for c in ln])
    return glyphs

SYNTH = [
    (_mk(["a board for duhan", "is now set up. to", "post it"]), 60),
    (_mk(["how to learn magic"]), 23),          # one line, small spare
    (_mk(["x"]), 40),                           # one tiny line, huge spare
    (_mk(["abcdefgh", "ab", "abcdefghijklmn"]), 50),
    (_mk(["same", "size", "rows"]), 14),        # exact fit (E == 0)
    (_mk(["one", "two", "three", "four", "five", "six"]), 80),
]


def test_capacity_exactly_filled():
    f = _load_injector_funcs()["build_symmetric_payload"]
    for glyphs, cap in SYNTH:
        payload = f(glyphs, cap)
        assert len(payload) == cap, (
            "payload %d words != capacity %d (input %d glyphs)"
            % (len(payload), cap, len(glyphs))
        )


def test_fffe_count_preserved():
    f = _load_injector_funcs()["build_symmetric_payload"]
    for glyphs, cap in SYNTH:
        payload = f(glyphs, cap)
        n_in = sum(1 for g in glyphs if g == 0xFFFE)
        n_out = sum(1 for g in payload if g == 0xFFFE)
        assert n_in == n_out, "FFFE count changed %d -> %d" % (n_in, n_out)
        assert 0xFFFF not in payload, "stray FFFF inside payload"


def test_no_dangling_fffe():
    f = _load_injector_funcs()["build_symmetric_payload"]
    for glyphs, cap in SYNTH:
        payload = f(glyphs, cap)
        assert payload and payload[-1] != 0xFFFE, "payload ends with dangling FFFE"


def test_uniform_leading_pad():
    """Every line must carry the SAME leading 0x0000 pad (this is what keeps
    the centered block from shifting left -- BUG-8)."""
    f = _load_injector_funcs()["build_symmetric_payload"]
    for glyphs, cap in SYNTH:
        payload = f(glyphs, cap)
        lines = _lines(payload)
        pads = [_leading_zeros(ln) for ln in lines]
        assert len(set(pads)) == 1, (
            "non-uniform leading pad %s (cap=%d, %d lines)"
            % (pads, cap, len(lines))
        )
        # max line width stays near Mtext + 2p (never the v84-style blowup
        # where ALL spare landed on the last line)
        p = pads[0]
        content = [len(ln) - _leading_zeros(ln) for ln in _lines(
            [g for g in glyphs] )]
        m = max(content)
        widths = [len(ln) for ln in lines]
        assert max(widths) <= m + 2 * p + 1, (
            "line width %d exceeds Mtext+2p+1 = %d (p=%d, M=%d)"
            % (max(widths), m + 2 * p + 1, p, m)
        )


def test_exact_fit_passthrough():
    f = _load_injector_funcs()["build_symmetric_payload"]
    glyphs, cap = SYNTH[4]
    assert len(glyphs) == cap, "synthetic exact-fit case is wrong"
    assert f(glyphs, cap) == list(glyphs), "exact-fit message was modified"


def test_built_r46_structure():
    """TIER 2: built R46 keeps size + FFFF structure of the pristine file."""
    built_path = os.path.join(PACKDATA_RES_DIR, "0046_type03.raw")
    if not os.path.isfile(built_path):
        raise Skip("build/packdata_resources/0046_type03.raw missing (run a build)")
    pris_path = require_file(os.path.join(RAW_DIR, "0046_type03.raw"), "pristine")
    built = open(built_path, "rb").read()
    pris = open(pris_path, "rb").read()
    assert len(built) == len(pris), (
        "R46 byte length changed: %d != pristine %d" % (len(built), len(pris))
    )
    for si in range(3):
        _idx, size, off, _pad = struct.unpack_from("<IIII", pris, si * 16)
        nf = sum(1 for j in range(0, size, 2)
                 if struct.unpack_from(">H", built, off + j)[0] == 0xFFFF)
        pf = sum(1 for j in range(0, size, 2)
                 if struct.unpack_from(">H", pris, off + j)[0] == 0xFFFF)
        assert nf == pf, "R46 sub%d FFFF count %d != pristine %d" % (si, nf, pf)


def test_built_r46_msg21_typo_fixed():
    """TIER 2: sub0 msg 21 must decode to \"i'll never forget ...\" (BUG-9)."""
    built_path = os.path.join(PACKDATA_RES_DIR, "0046_type03.raw")
    if not os.path.isfile(built_path):
        raise Skip("build/packdata_resources/0046_type03.raw missing (run a build)")
    built = open(built_path, "rb").read()
    _idx, size, off, _pad = struct.unpack_from("<IIII", built, 0)
    ffff = [j for j in range(0, size, 2)
            if struct.unpack_from(">H", built, off + j)[0] == 0xFFFF]
    msgs = []
    prev = 0
    for fp in ffff:
        msgs.append((prev, fp))
        prev = fp + 2
    assert len(msgs) > 21, "R46 sub0 has only %d messages" % len(msgs)
    s, e = msgs[21]
    glyphs = [struct.unpack_from(">H", built, off + j)[0] for j in range(s, e, 2)]
    text = decode_glyphs([g for g in glyphs if g < 0xFB00], linebreak=" ")
    norm = " ".join(text.split())
    # BUG-9 = the "ill" -> "i'll" apostrophe fix. The bulletin posts were later
    # recapitalized (sentence case), so this asserts the apostrophe fix
    # case-INSENSITIVELY ("I'll" is the intended capitalized form).
    assert "i'll never forget" in norm.lower(), (
        "BUG-9 regressed: sub0 msg 21 decodes to %r (expected \"I'll never "
        "forget ...\")" % norm[:60]
    )


TESTS = [
    test_capacity_exactly_filled,
    test_fffe_count_preserved,
    test_no_dangling_fffe,
    test_uniform_leading_pad,
    test_exact_fit_passthrough,
    test_built_r46_structure,
    test_built_r46_msg21_typo_fixed,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_r46_board")
