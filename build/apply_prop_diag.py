#!/usr/bin/env python3
"""Diagnostic: PROPORTIONAL narration advance (Stage 1) on top of v101.

Replaces the fixed 18/9 space cave (PATCH 14) with a per-glyph ADVANCE table
lookup: advance = clamp(ink_width+3, 6, 23), space/blank = 9.  Ink widths are
measured from the LIVE R1188 font in GS-dump VRAM (TBP0=0x3000), verified by
re-rendering 'A'/'a' (data/r1188_ascii_metrics.json).  This fixes the
"after" f/t collisions and most of the inconsistent-gap problem.

NOT included (Stage 2/3, need more authoring):
 - draw-shift (subtract ink_left before draw) for TRUE-uniform side-bearings;
 - summed-width centering (lines still reserve count*18, so proportional advance
   leaves an 11-34px variable left-drift — KNOWN, judge it in the dump).
Included cheap centering fix (3B): the per-line re-center site at VA 0x308364/
0x30836C still multiplied by 24 while PATCH 13 set the origin to *18 -> x24/x18
mismatch; switched to *18 (same idiom as PATCH 13).

Cave @ VA 0x4C7540 (file 0x3C75C0); 256-byte table @ VA 0x4C7564 (file 0x3C75E4),
both inside the verified 744-byte never-written rodata padding.  Hook 0x3097A0
already = j 0x4C7540 in v101.  Run after build/BUSIN0_EN_v101.iso exists.
"""
import json, struct, sys
sys.stdout.reconfigure(encoding='utf-8')

SRC = 'build/BUSIN0_EN_v101.iso'
DST = 'build/BUSIN0_EN_v101_propdiag.iso'
GAP = 3

# advance table from the VERIFIED VRAM ink metrics
m = json.load(open('data/r1188_ascii_metrics.json'))
def ink_w(gid):
    e = m[gid] if isinstance(m, list) else m[str(gid)]
    return e['ink_width'] if isinstance(e, dict) else e
ADV = [9] + [(9 if ink_w(g) == 0 else max(6, min(23, ink_w(g) + GAP))) for g in range(1, 95)]
assert len(ADV) == 95 and ADV[0] == 9

data = bytearray(open(SRC, 'rb').read())
P6 = bytes.fromhex('289d8293050001240300411000000000102e0c08000000000800e00300000000')
base = data.find(P6) - 0x3B0E50
def off(va): return base + (va - 0x100000 + 0x80)

# --- sanity ---
assert struct.unpack_from('<I', data, off(0x3097A0))[0] == 0x08131D50, 'v101 hook missing'
# table region must be free
tbl_off = off(0x4C7564)
assert data[tbl_off:tbl_off + 256] == b'\x00' * 256, 'table region 0x4C7564 not free'

# --- proportional cave (9 words) ---
cave_words = [
    0x3C08004C,   # lui  t0, 0x4C
    0x322300FF,   # andi v1, s1, 0xFF
    0x01034021,   # addu t0, t0, v1
    0x91037564,   # lbu  v1, 0x7564(t0)   ; v1 = ADV[glyph&0xFF]
    0x87A201CE,   # lh   v0, 0x1CE(sp)
    0x00431021,   # addu v0, v0, v1
    0xA7A201CE,   # sh   v0, 0x1CE(sp)
    0x080C25F8,   # j    0x3097E0
    0x00000000,   # nop
]
for i, w in enumerate(cave_words):
    struct.pack_into('<I', data, off(0x4C7540) + i * 4, w)

# --- 256-byte advance table ---
tbl = bytearray([0x12]) * 256
for i, a in enumerate(ADV):
    tbl[i] = a & 0xFF
data[tbl_off:tbl_off + 256] = tbl

# --- 3B: per-line re-center x24 -> x18 (idiom: sll sa 1->3 then 3->1) ---
def patch(va, exp, new, lbl):
    o = off(va); w = struct.unpack_from('<I', data, o)[0]
    if w == exp:
        struct.pack_into('<I', data, o, new); print(f"  3B {va:08X}: {lbl} OK")
    elif w == new:
        print(f"  3B {va:08X}: already")
    else:
        print(f"  3B {va:08X}: WARN exp 0x{exp:08X} got 0x{w:08X}")
patch(0x308364, 0x00062040, 0x000620C0, 'sll r4,r6,1->3')
patch(0x30836C, 0x000420C0, 0x00042040, 'sll r4,r4,3->1')

open(DST, 'wb').write(data)
print(f'wrote {DST}')
print(f'  proportional advance: {len([a for a in ADV if a!=18])} of 95 glyphs != 18; avg {sum(ADV)/95:.1f}px')
print(f'  cave @ 0x4C7540, table @ 0x4C7564, GAP={GAP}')
print('  -> GS-dump "A heavy fog"; expect uniform ~4px inter-letter gaps, no f/t collision')
