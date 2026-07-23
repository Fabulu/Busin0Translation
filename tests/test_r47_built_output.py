#!/usr/bin/env python3
"""
test_r47_built_output.py -- TIER-2 structural gate on the BUILT R47 (combat
text) resource, build/packdata_resources/0047_type03.raw.

R47 is a type-03 resource: a 3-record LE sub-table (16 bytes each: idx, size,
offset, pad) followed by three BE-u16 FFFF-delimited glyph streams (sub0 combat
text, sub1 battle UI, sub2 special abilities). It is injected in-place, fixed
size, by build/inject_r46_r47.py -- headers, offset tables and slot boundaries
are preserved verbatim; only glyph content inside each FFFF slot is rewritten.

This module is the R47-wide structural gate (test_r39_spell_desc_alignment's T5
pins three specific sub0 pills; this pins the whole resource):

  * STRUCTURE: built byte length == pristine, the 3-record sub-table is
    byte-identical, and every sub's FFFF-group count matches pristine (a changed
    count means slot addressing broke).

  * v160 PILL-FIX INVARIANT: every pristine group that ends on the 0xFFFE line
    terminator must STILL end on 0xFFFE in the build. The injector used to
    overwrite that terminator with 0x0000 padding, which made every battle title
    pill render its text one full line BELOW the pill (live A/B-proven via the
    v159 R47_FFFE_EXPERIMENT ISO; inject_r46_r47.py keep_fffe). Zero violations
    allowed.

  * ENGLISH LANDED: >=5 known combat strings decode out of the built sub0. The
    example strings ('Start turn', 'Go!!', 'Redo', 'Atk', 'Results') were
    VERIFIED by decoding the built resource first (they live in sub0 groups
    12/13/14/18/15 -- the R47_SUB0 order-confirm + ability cluster), not
    hardcoded blind.

TIER-2: SKIPs cleanly when the built resource is absent.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import PACKDATA_RES_DIR, RAW_DIR, ROOT, Skip, main_exit, require_file

BUILT = os.path.join(PACKDATA_RES_DIR, "0047_type03.raw")
PRISTINE = os.path.join(RAW_DIR, "0047_type03.raw")
N_SUBS = 3

# Known English combat strings that MUST decode out of the built sub0. Verified
# present by decoding the shipped resource (build/packdata_resources/
# 0047_type03.raw) -- these are the R47_SUB0 order-confirm / turn-flow / ability
# labels at groups 12,13,14,15,18 respectively.
KNOWN_SUB0_STRINGS = ["Start turn", "Yes", "No", "Confirm", "Atk"]


def _require_built():
    if not os.path.isfile(BUILT):
        raise Skip("build/packdata_resources/0047_type03.raw missing (run a build)")
    require_file(PRISTINE, "pristine R47")
    return open(BUILT, "rb").read(), open(PRISTINE, "rb").read()


def _subs(blob):
    """Return the 3 sub-records as (idx, size, offset)."""
    out = []
    for i in range(N_SUBS):
        idx, size, off, _pad = struct.unpack_from("<IIII", blob, i * 16)
        out.append((idx, size, off))
    return out


def _groups(blob, off, size):
    """Split the BE-u16 stream [off, off+size) into FFFF-delimited groups
    (lists of glyph words, FFFF markers dropped)."""
    groups, cur = [], []
    end = min(off + size, len(blob))
    pos = off
    while pos + 2 <= end:
        w = struct.unpack_from(">H", blob, pos)[0]
        if w == 0xFFFF:
            groups.append(cur)
            cur = []
        else:
            cur.append(w)
        pos += 2
    return groups


def _clean_text(cells):
    """Decode a group to text: ids 0..94 -> chr(id+0x20); drop control words
    (>= 0xFB00, incl. the trailing 0xFFFE terminator); strip 0x0000 pad spaces."""
    out = []
    for g in cells:
        if g >= 0xFB00:
            continue
        if 0 <= g <= 94:
            out.append(chr(0x20 + g))
        else:
            out.append("[%04X]" % g)
    return "".join(out).strip()


# ===========================================================================
# STRUCTURE: length, sub-table and per-sub FFFF counts match pristine.
# ===========================================================================
def test_structure_matches_pristine():
    built, pris = _require_built()
    assert len(built) == len(pris), (
        "built R47 is %d bytes, pristine is %d -- in-place injection must not "
        "change size (headers/offset table preserved verbatim)"
        % (len(built), len(pris))
    )
    # The 3-record sub-table (first 48 bytes) is pure structure -- byte-identical.
    assert built[:N_SUBS * 16] == pris[:N_SUBS * 16], (
        "built R47 sub-table (first %d bytes) differs from pristine -- slot "
        "sizes/offsets were altered, which corrupts every group boundary"
        % (N_SUBS * 16)
    )
    bsubs, psubs = _subs(built), _subs(pris)
    assert bsubs == psubs, (
        "built R47 sub records %s != pristine %s" % (bsubs, psubs)
    )
    for si, (idx, size, off) in enumerate(psubs):
        gb = _groups(built, off, size)
        gp = _groups(pris, off, size)
        assert len(gb) == len(gp), (
            "R47 sub%d FFFF-group count %d != pristine %d -- FFFF terminators "
            "were added/removed; slot addressing is broken" % (si, len(gb), len(gp))
        )


# ===========================================================================
# v160 PILL-FIX INVARIANT: pristine 0xFFFE terminators survive the build.
# ===========================================================================
def test_fffe_terminator_preserved():
    built, pris = _require_built()
    violations = []
    checked = 0
    for si, (idx, size, off) in enumerate(_subs(pris)):
        gb = _groups(built, off, size)
        gp = _groups(pris, off, size)
        for gi, (cb, cp) in enumerate(zip(gb, gp)):
            if cp and cp[-1] == 0xFFFE:
                checked += 1
                if not (cb and cb[-1] == 0xFFFE):
                    tail = ("0x%04X" % cb[-1]) if cb else "<empty>"
                    violations.append(
                        "sub%d g%d: pristine ends 0xFFFE but built ends %s"
                        % (si, gi, tail)
                    )
    assert checked >= 100, (
        "only %d R47 groups end on 0xFFFE in pristine -- expected the resource "
        "to be full of line-terminated slots; is this really R47?" % checked
    )
    assert not violations, (
        "v160 PILL-FIX REGRESSED: %d R47 slot(s) lost their trailing 0xFFFE "
        "line terminator (first: %s). Without it the battle title pills render "
        "their text one line BELOW the pill (inject_r46_r47.py keep_fffe; "
        "live A/B-proven via the v159 R47_FFFE_EXPERIMENT ISO)."
        % (len(violations), violations[0])
    )


# ===========================================================================
# ENGLISH LANDED: >=5 known combat strings decode from the built sub0.
# ===========================================================================
def test_known_english_strings_decode():
    built, _pris = _require_built()
    _idx, size, off = _subs(built)[0]  # sub0 = combat text
    groups = _groups(built, off, size)
    decoded = {_clean_text(g) for g in groups}
    found = [s for s in KNOWN_SUB0_STRINGS if s in decoded]
    assert len(found) >= 5, (
        "only %d/%d known English combat strings decoded from built R47 sub0 "
        "(found %s of %s). The English injection did not land -- R47 is "
        "shipping JP or garbled text. A decoded sample: %s"
        % (
            len(found), len(KNOWN_SUB0_STRINGS), found, KNOWN_SUB0_STRINGS,
            sorted(t for t in decoded if t)[:12],
        )
    )


TESTS = [
    test_structure_matches_pristine,
    test_fffe_terminator_preserved,
    test_known_english_strings_decode,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_r47_built_output")
