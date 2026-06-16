#!/usr/bin/env python3
"""Diagnostic: PROPORTIONAL narration spacing Stage 1 + Stage 2 (on top of v101).

Stage 1 (advance LUT): per-glyph advance = clamp(ink_width+GAP, 6, 23), space=9.
  Cave @ VA 0x4C7540, 256-byte ADV table @ VA 0x4C7564 (as in apply_prop_diag.py).
Stage 2 (DRAW-SHIFT): draw each glyph at penX - ink_left[glyph], so its ink starts
  exactly at the pen.  Combined with the ink_width advance this makes EVERY visible
  inter-glyph gap a uniform GAP px (no more f/o collisions, no "h eavy" wobble).
  GS-measured proof of the need: Stage-1-only gaps swing -3px..+14px because
  right-heavy glyphs (f: ink_left=12) stick past their advance.

Stage-2 mechanism (disasm-verified): the narration draw X is built at
  0x309738 lh r7,0x1CE(sp)        ; r7 = penX
  0x309750 addu r12,r7,r12        ; X = penX + field8   <-- HOOK here
  0x30975C addu r12,r12,r10       ; + origin
Hook 0x309750 -> j cave2 (delay slot 0x309754 'addu r10,r10,r8' still runs once);
cave2 subtracts LEFTSHIFT[r17] from r7 (penX register only — does NOT touch the
0x1CE(sp) pen, so the advance is unaffected), redoes addu r12,r7,r12, returns to
0x309758.  Scratch: r1 (AT, dead), r7 (penX, reloaded at 0x309758).  s1=r17=glyph.
cave2 @ VA 0x4C7670, LEFTSHIFT table @ VA 0x4C7690 (same 744B verified-clean pad).

KNOWN: line-start bleed (first glyph of a line draws ink_left px left of origin);
minor for typical leads, flagged for eyeball.  Centering (Stage 3) still pending.

Run after build/BUSIN0_EN_v101.iso exists.  -> v101_propdiag2.iso.
"""
import json, struct, sys
sys.stdout.reconfigure(encoding='utf-8')

SRC='build/BUSIN0_EN_v101.iso'; DST='build/BUSIN0_EN_v101_propdiag2.iso'; GAP=3
m=json.load(open('data/r1188_ascii_metrics.json'))
def met(gid):
    e=m[gid] if isinstance(m,list) else m[str(gid)]
    return e.get('ink_left',0), e.get('ink_width',0)
ADV=[]; LSH=[]
for g in range(95):
    il,iw=met(g)
    if g==0: ADV.append(9); LSH.append(0); continue
    ADV.append(9 if iw==0 else max(6,min(23,iw+GAP)))
    LSH.append(max(0,il))

data=bytearray(open(SRC,'rb').read())
P6=bytes.fromhex('289d8293050001240300411000000000102e0c08000000000800e00300000000')
base=data.find(P6)-0x3B0E50
def off(va): return base+(va-0x100000+0x80)

# ---- Stage 1: advance cave @0x4C7540 + ADV table @0x4C7564 ----
assert struct.unpack_from('<I',data,off(0x3097A0))[0]==0x08131D50,'v101 hook missing'
assert data[off(0x4C7564):off(0x4C7564)+256]==b'\x00'*256,'ADV table region not free'
cave1=[0x3C08004C,0x322300FF,0x01034021,0x91037564,0x87A201CE,0x00431021,0xA7A201CE,0x080C25F8,0x00000000]
for i,w in enumerate(cave1): struct.pack_into('<I',data,off(0x4C7540)+i*4,w)
tbl1=bytearray([0x12])*256
for i,a in enumerate(ADV): tbl1[i]=a&0xFF
data[off(0x4C7564):off(0x4C7564)+256]=tbl1

# ---- 3B per-line centering x24->x18 ----
for va,exp,new in [(0x308364,0x00062040,0x000620C0),(0x30836C,0x000420C0,0x00042040)]:
    o=off(va)
    if struct.unpack_from('<I',data,o)[0]==exp: struct.pack_into('<I',data,o,new)

# ---- Stage 2: draw-shift cave2 @0x4C7670 + LEFTSHIFT table @0x4C7690 ----
assert struct.unpack_from('<I',data,off(0x309750))[0]==0x00EC6021,'draw X site changed'
assert data[off(0x4C7670):off(0x4C7670)+0x120]==b'\x00'*0x120,'cave2/LSH region not free'
cave2=[
    0x3C01004C,  # lui  r1, 0x4C
    0x00310821,  # addu r1, r1, s1(r17)
    0x90217690,  # lbu  r1, 0x7690(r1)   ; LEFTSHIFT[glyph&...]  (table @0x4C7690)
    0x00E13823,  # subu r7, r7, r1       ; penX -= ink_left
    0x00EC6021,  # addu r12, r7, r12     ; (original 0x309750)
    0x080C25D6,  # j    0x309758
    0x00000000,  # nop
]
for i,w in enumerate(cave2): struct.pack_into('<I',data,off(0x4C7670)+i*4,w)
tbl2=bytearray(256)             # 0 default (no shift)
for i,s in enumerate(LSH): tbl2[i]=s&0xFF
data[off(0x4C7690):off(0x4C7690)+256]=tbl2
# hook the draw X site
struct.pack_into('<I',data,off(0x309750),0x08131D9C)  # j 0x4C7670

open(DST,'wb').write(data)
print(f'wrote {DST}')
print(f'  Stage1 advance avg={sum(ADV)/95:.1f}px ; Stage2 draw-shift (LEFTSHIFT) installed')
print(f'  sample: f adv={ADV[70]} lsh={LSH[70]} | A adv={ADV[33]} lsh={LSH[33]} | i adv={ADV[73]} lsh={LSH[73]}')
print('  -> GS-dump "A heavy fog"; expect EVERY inter-letter ink gap == %dpx (uniform), no collisions' % GAP)
