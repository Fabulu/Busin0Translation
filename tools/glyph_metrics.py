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

# ── SECOND FONT (v158): R2100 sub0 — the UPRIGHT 16x16-cell UI serif ─────────
# The chargen/request renderers (0x307510 / 0x3A2EF0, Patches 26/27/29/31) draw
# the R2100 sub0 ASCII glyphs (upright serif, 16px cells, cell = char-0x20 in a
# 16-column grid), NOT the oblique 24px R1188 font.  Feeding them the R1188
# tables was the root cause of the game-wide "Ge nde r" per-letter unevenness
# (see memory project_chargen_font_r2100_rootcause).  ADV2/LEFTSHIFT2 below are
# the same formulas scaled to the 16px font, sourced from
# data/r2100_ascii_metrics.json (measured offline from the PRISTINE R2100 sub0
# pixels in PACKDATA — R2100 deswizzles cleanly at 256x256 dbw_ct32=128).
GAP2 = 2                      # inter-letter ink gap for the 16px font (R1188=3 @24px)
SPACE_ADV2 = 6                # space advance for the 16px font (R1188=9 @24px)
_METRICS2 = os.path.join(_BASE, 'data', 'r2100_ascii_metrics.json')


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


def _load2():
    m = json.load(open(_METRICS2, encoding='utf-8'))
    adv, lsh = [], []
    for g in range(95):
        e = m[g]
        iw = e['ink_width']
        il = e.get('ink_left', 0)
        adv.append(SPACE_ADV2 if (g == 0 or iw == 0) else max(4, min(15, iw + GAP2)))
        lsh.append(max(0, il))
    return adv, lsh


ADV, LEFTSHIFT = _load()
assert len(ADV) == 95 and ADV[0] == 9

ADV2, LEFTSHIFT2 = _load2()
assert len(ADV2) == 95 and ADV2[0] == SPACE_ADV2
# Space (and any empty glyph) must never draw-shift; several cave designs also
# rely on LEFTSHIFT2[0] == 0.
assert LEFTSHIFT2[0] == 0 and LEFTSHIFT[0] == 0


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


def adv2_table_256():
    """256-byte R2100 advance table (ADV2, legacy 256-byte layout).

    idx 0..94 = ADV2; the 95..255 tail stays 0x12 — byte-identical to the
    canonical table's tail, so non-ASCII glyphs (kanji low-byte reads through
    P27's unguarded `lbu -1(s2)`) keep the exact pre-v158 advance behaviour.

    NOTE (v170 dead-.text relocation): the EXE no longer installs this 256-byte
    table.  Patches 26/27/29/31 now read the RELOCATED 95-byte table
    adv2_table_95() at ADV2_VA=0x4AF338 (dead libgraph trailing pad, below the
    arena, dump-verified-zero) and reconstruct the 0x12 tail from their own
    gid>=95 guards.  This 256-byte builder is retained only for the static
    layout test (test_r2100_metrics_source T3).
    """
    t = bytearray([0x12]) * 256
    for i, a in enumerate(ADV2):
        t[i] = a & 0xFF
    return bytes(t)


def leftshift2_table_256():
    """256-byte R2100 left-shift table (LSH2, legacy 256-byte layout).

    idx 0..94 = LEFTSHIFT2; tail 95..255 = 0 (non-ASCII subtracts nothing),
    matching the canonical table's zero tail.

    NOTE (v170 dead-.text relocation): the EXE no longer installs this 256-byte
    table.  Patches 26/27/29/31 now read the RELOCATED 95-byte table
    leftshift2_table_95() at LSH2_VA=0x4AF398 and reconstruct the zero tail from
    their own gid>=95 guards.  Retained only for the static layout test.
    """
    t = bytearray(256)
    for i, s in enumerate(LEFTSHIFT2):
        t[i] = s & 0xFF
    return bytes(t)


def adv2_table_95():
    """95-byte R2100 advance table (gid 0..94 only) for the RELOCATED cave.

    Patches 26/27/29/31 carry their OWN gid>=95 ASCII guard (ADV2 tail default
    0x12), so this table needs only the 95 real ASCII slots — the old 256-byte
    0x12 tail is reproduced by the caves' guards, byte-for-byte.  Installed at
    ADV2_VA=0x4AF338 (dead libgraph trailing pad, below the arena).
    """
    return bytes((a & 0xFF) for a in ADV2)


def leftshift2_table_95():
    """95-byte R2100 left-shift table (gid 0..94 only) for the RELOCATED cave.

    The relocated caves guard gid>=95 -> default LEFTSHIFT2 0 (subtract nothing),
    matching the old 256-byte table's zero tail exactly.  Installed at
    LSH2_VA=0x4AF398.
    """
    return bytes((s & 0xFF) for s in LEFTSHIFT2)


def px_width2(s, enc):
    """Pixel width of a single-line string in the R2100 (chargen/request) font."""
    return sum(ADV2[enc(c)] if 0 <= enc(c) < 95 else 0x12 for c in s)


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
    print(f'ADV2 (R2100 16px font, gid 0..94), avg {sum(ADV2)/95:.1f}px:')
    print(' ', ADV2)
    print(f'LEFTSHIFT2 (gid 0..94):')
    print(' ', LEFTSHIFT2)
    print(f"sample2: space adv={ADV2[0]} | 'e'(69) adv={ADV2[69]} lsh={LEFTSHIFT2[69]} | "
          f"'f'(70) adv={ADV2[70]} lsh={LEFTSHIFT2[70]} | 'W'(55) adv={ADV2[55]} lsh={LEFTSHIFT2[55]}")
