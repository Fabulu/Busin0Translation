#!/usr/bin/env python3
"""Diagnostic: narrow the SPACE glyph in narration to 9px (letters stay 18px).

Installs a code-cave trampoline (architect-designed, recon-verified mechanism)
that, per glyph in the narration renderer (func 0x307da0), checks the glyph id
and advances the pen by 9px for the SPACE (glyph 0) and 18px for everything
else.  Hooks the integer advance site VA 0x3097A0 (narration takes the
metric==100 integer path; GS-dump proven).  The cave lives at VA 0x4B0DF0
(file 0x3B0E70), the all-zero region immediately AFTER the 32-byte Patch-6
trampoline at file 0x3B0E50 — verified non-overlapping.

ROOT CAUSE OF THE v100 'lol' (advance==0 pile), now FIXED:
 The old cave read the glyph via `lhu v0,2(s5)`.  s5 (r21) is NOT a glyph
 pointer on the PATH-B default-char path that narration takes — its only writes
 in this function are in setup / control-code / debug-grid branches, none of
 which run for a plain glyph, so s5 was STALE.  The read returned garbage (and
 on the gp&1 debug path s5 is a tiny int {0,1,2,3} -> an unmapped 2(s5) load),
 which broke the pen advance -> every glyph drew at one X.

 FIX (disasm-verified): the current glyph id is already live in register s1
 (r17).  It is assembled at the dispatcher 0x3084F8 (`andi s1,v0,0xFFFF`),
 tested directly at the PATH-B draw site 0x3096B4 (`slt at,s1,at` / `beq` skip),
 and passed to the drawer at 0x309724 (`sd s1,0x10(sp)`).  No s1 write occurs
 between 0x3084F8 and the hook on a normal glyph (the 0x308748 `beq zero,zero,
 0x3096B0` falls straight through to PATH-B).  So read s1 directly — no memory
 access, no endianness/off-by-one risk.

 SPACE ENCODING: narration glyphs are stored as glyph INDICES (not ASCII).
 data/english_glyph_table.json maps ' ' -> 0, and patch_r1193_narration.py
 emits the space as glyph id 0 (decode is chr(g+0x20), so space 0x20 -> id 0).
 Therefore the space test is `s1 == 0`.  v0 and v1 are both DEAD at the hook
 (return path writes v0@0x3097E0, v1@0x3097EC before any read), so the cave is
 free to use them as scratch.  The r3-clobber theory from the prompt is FALSE:
 the draw-position add at 0x309770 uses v1 freshly loaded at 0x309740
 (`lh v1,0x3E(s0)`), reloaded every iteration BEFORE the draw, and the cave is
 entered AFTER the draw — clobbering v1 cannot reach the next draw.

 SAFE-DEGRADATION: if the space code were ever NOT 0 for some line, the worst
 case is that the space simply renders at the full 18px (same as letters) — the
 advance is always a correct nonzero value, so this can never re-pile ('lol').

 REMAINING (cosmetic only): narration centering reserves count*18 per line, so a
 9px space sits (18-9)/2 = 4.5px left of true centre per space.  Judge visually.

Run AFTER build/BUSIN0_EN_v100.iso exists.  Produces v100_spacediag.iso.
"""
import struct, sys
sys.stdout.reconfigure(encoding='utf-8')

SRC = 'build/BUSIN0_EN_v100.iso'
DST = 'build/BUSIN0_EN_v100_spacediag2.iso'
SPACE_ADV = 0x09   # tunable: pen advance for the space glyph (letters = 0x12 = 18px)

data = bytearray(open(SRC, 'rb').read())

# Locate the EXE inside the ISO via the Patch-6 trampoline signature.
P6 = bytes.fromhex('289d8293' '05000124' '03004110' '00000000'
                   '102e0c08' '00000000' '0800e003' '00000000')
hit = data.find(P6)
assert hit != -1, 'Patch-6 trampoline not found — is this a built v100 ISO?'
base = hit - 0x3B0E50          # EXE file offset 0 -> ISO offset `base`

HOOK = base + 0x209820         # VA 0x3097A0
# CAVE RELOCATED (v2): the old cave VA 0x4B0DF0 (file 0x3B0E70) is NOT free at
# runtime — the game uses 0x4B0DD0-0x4B0E0C as a DATA buffer DURING text rendering
# (live RAM in ramdumps/text.p2s shows a {count,self-ptr,ptr,val} struct there),
# which overwrote the cave's tail (the j-back) mid-render -> EE ran off -> HANG
# ("text didn't draw, got stuck").  This is why BOTH prior attempts failed; the
# s5->s1 read fix was correct but masked by the cave self-destructing.
# NEW CAVE VA 0x4C7540 (file 0x3C75C0): zero in the EXE AND verified never-written
# across 30 captured scenes (May23..Jun16: town/battle/dungeon/menu/text/requests).
CAVE = base + 0x3C75C0         # VA 0x4C7540 (rodata padding near handler table 0x4C9360)

# --- sanity: hook site must be the narration advance pre-amble ---
w_a0 = struct.unpack_from('<I', data, HOOK)[0]       # lh v0,0x1CE(sp)
w_a4 = struct.unpack_from('<I', data, HOOK + 4)[0]    # addiu v0,v0,0x12 (18px, baked by Patch 13)
assert w_a0 == 0x87A201CE, f'hook+0 = 0x{w_a0:08X}, expected lh v0,0x1CE(sp)'
assert w_a4 in (0x24420012, 0x24420018), f'hook+4 = 0x{w_a4:08X}, expected addiu v0,v0,0x12/0x18'
# --- sanity: cave must be free (all zero) ---
cave_now = bytes(data[CAVE:CAVE + 36])
assert cave_now == b'\x00' * 36, 'cave at 0x3B0E70 is not all-zero — refusing to clobber'

# --- write the trampoline cave (9 words / 36 bytes) ---
#  addiu v1, zero, 0x12      ; default advance = 18px (letter)
#  bne  s1, zero, +2         ; glyph (s1) != 0 -> keep 18
#  nop
#  addiu v1, zero, SPACE_ADV ; glyph == 0 (space) -> 9px
#  lh   v0, 0x1CE(sp)        ; pen-X
#  addu v0, v0, v1
#  sh   v0, 0x1CE(sp)
#  j    0x3097E0             ; rejoin after the original store
#  nop
# s1 (r17) holds the CURRENT glyph id (assembled @0x3084F8, tested @0x3096B4,
# passed to drawer @0x309724); both v0 and v1 are dead at the hook.
cave_words = [
    0x24030012,                       # addiu v1, zero, 0x12
    0x16200002,                       # bne s1, zero, +2
    0x00000000,                       # nop
    0x24030000 | (SPACE_ADV & 0xFFFF),# addiu v1, zero, SPACE_ADV
    0x87A201CE,                       # lh v0, 0x1CE(sp)
    0x00431021,                       # addu v0, v0, v1
    0xA7A201CE,                       # sh v0, 0x1CE(sp)
    0x080C25F8,                       # j 0x3097E0
    0x00000000,                       # nop
]
for i, word in enumerate(cave_words):
    struct.pack_into('<I', data, CAVE + i * 4, word)

# --- install the hook ---
# j 0x4C7540  =  0x08000000 | (0x4C7540 >> 2)  =  0x08131D50
struct.pack_into('<I', data, HOOK,     0x08131D50)   # j 0x4C7540
struct.pack_into('<I', data, HOOK + 4, 0x00000000)   # nop (delay slot)

open(DST, 'wb').write(data)
print(f'wrote {DST}')
print(f'  EXE base in ISO = 0x{base:X}')
print(f'  hook @ ISO 0x{HOOK:X} (VA 0x3097A0): j 0x4C7540 ; nop')
print(f'  cave @ ISO 0x{CAVE:X} (VA 0x4C7540): space={SPACE_ADV}px, letter=18px')
print('  -> GS-dump a narration line WITH spaces; measure space-step (want 9px) vs letter-step (18px)')
