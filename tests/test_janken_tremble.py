#!/usr/bin/env python3
"""test_janken_tremble.py -- regression gate for the Janken Man "trembling tell"
(issue #26).

The Janken minigame reveals its throw via three visually distinct chant groups in
R1204: G185 (FB03 chant), G186 and G187 (reveal variants B/C). Pristine
distinguishes 186 from 187 by ONE embedded control token before the last glyph --
G186 carries FB04, G187 carries FB05 -- which drives the on-screen tremble the
player reads as the tell. Our English injection dropped those interior tokens,
collapsing G186 == G187 (both "FB03 + Shoooot + !") so the tell was unreadable.
tools/patch_r1204_janken.py restores them (size-neutral, in place).

This gate pins the restored state on the BUILT resource: G186 must contain FB04,
G187 must contain FB05, the two groups must differ, and G185 must keep its FB03
chant token. TIER-2: SKIPs cleanly when the built resource is absent.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import PACKDATA_RES_DIR, Skip, main_exit

BUILT = os.path.join(PACKDATA_RES_DIR, "1204_type02.raw")
G_CHANT, G_VAR_B, G_VAR_C = 185, 186, 187


def _groups(blob):
    sec2_size = struct.unpack_from("<I", blob, 0x14)[0]
    sec2_off = struct.unpack_from("<I", blob, 0x18)[0]
    end = min(sec2_off + sec2_size, len(blob))
    out, cur, pos = [], [], sec2_off
    while pos + 2 <= end:
        w = struct.unpack_from(">H", blob, pos)[0]
        if w == 0xFFFF:
            out.append(cur)
            cur = []
        else:
            cur.append(w)
        pos += 2
    return out


def _load():
    if not os.path.isfile(BUILT):
        raise Skip("build/packdata_resources/1204_type02.raw missing (run a build)")
    return _groups(open(BUILT, "rb").read())


def test_reveal_groups_distinct():
    g = _load()
    assert len(g) > G_VAR_C, "R1204 has too few Section-2 groups -- layout changed"
    g185, g186, g187 = g[G_CHANT], g[G_VAR_B], g[G_VAR_C]
    assert 0xFB03 in g185, "R1204 G185 lost its FB03 chant token"
    assert 0xFB04 in g186, (
        "R1204 G186 lost FB04 -- Janken tremble tell broken (issue #26); "
        "tools/patch_r1204_janken.py must run in build Step 6.5"
    )
    assert 0xFB05 in g187, (
        "R1204 G187 lost FB05 -- Janken tremble tell broken (issue #26); "
        "tools/patch_r1204_janken.py must run in build Step 6.5"
    )
    assert g186 != g187, (
        "R1204 G186 == G187 -- the two reveal variants collapsed to identical "
        "bytes, so the tremble tell is unreadable (issue #26)"
    )


TESTS = [test_reveal_groups_distinct]

if __name__ == "__main__":
    main_exit(TESTS, "test_janken_tremble")
