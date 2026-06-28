#!/usr/bin/env python3
"""Single source of truth for R1188 proportional glyph metrics.

EVERYTHING that needs per-glyph widths — the in-EXE advance/leftshift cave tables
(build/patch_exe.py), the future pixel-aware line wrap (build/build_v9.py), the
summed-width centering, and the test gates — MUST import from here.  If any of
them recomputes widths independently they silently desync (this project's #1
failure mode).

Source: data/r1188_ascii_metrics.json (byte-identical recon copy) — a 95-element list, gid 0..94,
each {gid, char, ink_left, ink_right, ink_width}, measured from the LIVE R1188
font in GS-dump VRAM (TBP0=0x3000) and verified by re-rendering 'A'/'a'.

gid = char - 32 (space=0, '!'=1, 'A'=33, 'a'=65) == enc(ch) in build_v9.py ==
the in-game ADV table index (s1 register).  So no remapping anywhere.

Formulas (byte-identical to the GS-dump-confirmed diagnostic apply_prop_diag2.py):
  ADV[g]       = 9 if g==0 else clamp(ink_width + GAP, 6, 23)   ; GAP=3
  LEFTSHIFT[g] = max(0, ink_left)
A glyph's pixel width on screen = ADV[g]; a string's width = sum of ADV.
The draw-shift subtracts LEFTSHIFT[g] from the pen so each glyph's ink starts at
the pen -> uniform GAP-px inter-letter gaps.
"""
import json
import os

GAP = 3
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_METRICS = os.path.join(_BASE, 'data', 'r1188_ascii_metrics.json')


def _load():
    m = json.load(open(_METRICS, encoding='utf-8'))
    adv, lsh = [], []
    for g in range(95):
        e = m[g] if isinstance(m, list) else m[str(g)]
        iw = e['ink_width'] if isinstance(e, dict) else e
        il = (e.get('ink_left', 0) if isinstance(e, dict) else 0)
        adv.append(9 if (g == 0 or iw == 0) else max(6, min(23, iw + GAP)))
        lsh.append(max(0, il))
    return adv, lsh


ADV, LEFTSHIFT = _load()
assert len(ADV) == 95 and ADV[0] == 9


def adv_table_256():
    """256-byte advance table for the EXE cave (idx 0..94 = ADV, 95..255 = 0x12)."""
    t = bytearray([0x12]) * 256
    for i, a in enumerate(ADV):
        t[i] = a & 0xFF
    return bytes(t)


def leftshift_table_256():
    """256-byte left-shift table for the EXE draw-shift cave (idx 0..94, rest 0)."""
    t = bytearray(256)
    for i, s in enumerate(LEFTSHIFT):
        t[i] = s & 0xFF
    return bytes(t)


def adv_table_95():
    """95-byte advance table (gid 0..94 only) for the RELOCATED battle-safe cave.

    The relocated P14/P27 caves carry their own ASCII guard (gid>=95 -> default
    ADV 18), so this table needs only the 95 real ASCII slots — the old 256-byte
    0x12 tail is reproduced by the guard, byte-for-byte.
    """
    return bytes((a & 0xFF) for a in ADV)


def leftshift_table_95():
    """95-byte left-shift table (gid 0..94 only) for the RELOCATED draw-shift cave.

    The relocated cave guards gid>=95 -> default LEFTSHIFT 0 (subtract nothing),
    matching the old 256-byte table's zero tail exactly.
    """
    return bytes((s & 0xFF) for s in LEFTSHIFT)


def px_width(s, enc):
    """Pixel width of a single-line string. enc(ch)->glyph id (char-32 family)."""
    return sum(ADV[enc(c)] if 0 <= enc(c) < 95 else 18 for c in s)


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(f'ADV (gid 0..94), avg {sum(ADV)/95:.1f}px:')
    print(' ', ADV)
    print(f'LEFTSHIFT (gid 0..94):')
    print(' ', LEFTSHIFT)
    print(f"sample: space adv={ADV[0]} | 'i'(73) adv={ADV[73]} lsh={LEFTSHIFT[73]} | "
          f"'m'(77) adv={ADV[77]} lsh={LEFTSHIFT[77]} | 'f'(70) adv={ADV[70]} lsh={LEFTSHIFT[70]}")
