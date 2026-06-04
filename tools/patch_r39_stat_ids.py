#!/usr/bin/env python3
"""
Patch R39 stat label glyph IDs from Japanese kanji to ASCII.

Runs AFTER inject_r39_v2.py (reads from build/packdata_resources/0039_type15.raw).
inject_r39_v2.py replaces these messages with pure ASCII text but destroys the
suffix glyphs and FFFE line-break markers that the game engine expects. This
script restores the correct structure.

R39 glyph stream (bytes 632-2702) contains 97 FFFF-delimited messages.
Messages 56-62 are "full" stat labels:  [space] [stat] [133] [652] [855] [FFFE]
Messages 63-69 are "short" stat labels: [stat] [158] [FFFE]

The suffix glyphs (133/652/855 and 158) are kanji-page glyphs that render
specific decorative elements after the stat name. The FFFE is a line-break
marker. Both must be preserved for correct rendering.

Stat mapping (JP kanji -> English):
  力      (glyph 346)              -> Str (S=51, t=84, r=82)
  知恵    (glyphs 535, 717)        -> Int (I=41, n=78, t=84)
  信仰心  (glyphs 308, 354, 320)   -> Pie (P=48, i=73, e=69)
  生命力  (glyphs 718, 696, 346)   -> Vit (V=54, i=73, t=84)
  敏捷度  (glyphs 582, 719, 590)   -> Agi (A=33, g=71, i=73)
  幸運度  (glyphs 720, 721, 590)   -> Lck (L=44, c=67, k=75)

Capacity constraints:
  MSG 64 (short Str): only 3 slots total [kanji, 158, FFFE].
    "Str" = 3 glyphs. Must sacrifice both suffix 158 AND FFFE.
    Result: [S, t, r] -- suffix and line break dropped.
  MSG 65 (short Int): 4 slots [chi, e, 158, FFFE].
    "Int" = 3 glyphs + FFFE. Suffix 158 dropped, FFFE kept.
    Result: [I, n, t, FFFE]
  MSG 66-69 (short Pie/Vit/Agi/Lck): 5 slots [k1, k2, k3, 158, FFFE].
    3 letters + suffix 158 + FFFE = 5. Perfect fit.
    Result: [letter, letter, letter, 158, FFFE]

  MSG 57 (full Str): 6 slots [space, kanji, 133, 652, 855, FFFE].
    "Str" = 3 letters. [space, S, t, r, 0, FFFE] -- drop all 3 suffixes.
    Result: [0, S, t, r, 0, FFFE]
  MSG 58 (full Int): 7 slots [space, k1, k2, 133, 652, 855, FFFE].
    [space, I, n, t, 0, 0, FFFE] -- drop all 3 suffixes.
    Result: [0, I, n, t, 0, 0, FFFE]
  MSG 59-62 (full Pie/Vit/Agi/Lck): 8 slots.
    [space, L1, L2, L3, 0, 0, 0, FFFE] -- drop all 3 suffixes.
    Result: [0, letter, letter, letter, 0, 0, 0, FFFE]
"""

import struct, os, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = 'C:/Programmieren/wizardrytranslation'
os.chdir(BASE)

# ---------------------------------------------------------------------------
# ASCII glyph IDs (R2100 sub-block 0): glyph_id = ord(char) - 32
# ---------------------------------------------------------------------------
S, t, r = 51, 84, 82   # Str
I, n    = 41, 78        # Int (t=84 reused)
P, i, e = 48, 73, 69   # Pie
V       = 54            # Vit (i=73, t=84 reused)
A, g    = 33, 71        # Agi (i=73 reused)
L, c, k = 44, 67, 75   # Lck
M, H    = 45, 40        # MHP (P=48 reused)

SPACE   = 0
FFFE    = 0xFFFE
FFFF    = 0xFFFF
SUFFIX_SHORT = 158      # suffix glyph for short stat labels
SUFFIX_A     = 133      # suffix glyph 1 for full stat labels
SUFFIX_B     = 652      # suffix glyph 2 for full stat labels
SUFFIX_C     = 855      # suffix glyph 3 for full stat labels

# ---------------------------------------------------------------------------
# Patch table: (msg_index, byte_offset, slot_count, new_glyphs)
#
# Each entry specifies the COMPLETE content of the message slot
# (everything between start and FFFF, NOT including the FFFF itself).
# The slot_count must match the original slot count exactly.
# ---------------------------------------------------------------------------
PATCHES = [
    # --- Full stat labels (MSG 56-62) ---
    # Format: [space] [stat letters] [padding...] [FFFE]
    # MHP: already English in original, but inject_r39_v2 may have broken it
    (56, 1744, 8, [SPACE, M, H, P, 0, 0, 0, FFFE]),
    # Str: 6 slots, was [space, kanji346, 133, 652, 855, FFFE]
    (57, 1762, 6, [SPACE, S, t, r, 0, FFFE]),
    # Int: 7 slots, was [space, kanji535, kanji717, 133, 652, 855, FFFE]
    (58, 1776, 7, [SPACE, I, n, t, 0, 0, FFFE]),
    # Pie: 8 slots, was [space, k308, k354, k320, 133, 652, 855, FFFE]
    (59, 1792, 8, [SPACE, P, i, e, 0, 0, 0, FFFE]),
    # Vit: 8 slots
    (60, 1810, 8, [SPACE, V, i, t, 0, 0, 0, FFFE]),
    # Agi: 8 slots
    (61, 1828, 8, [SPACE, A, g, i, 0, 0, 0, FFFE]),
    # Lck: 8 slots
    (62, 1846, 8, [SPACE, L, c, k, 0, 0, 0, FFFE]),

    # --- Short stat labels (MSG 63-69) ---
    # Format: [stat letters] [suffix_158?] [FFFE?]
    # MHP: 5 slots, was [M, H, P, 158, FFFE] -> keep suffix + FFFE
    (63, 1864, 5, [M, H, P, SUFFIX_SHORT, FFFE]),
    # Str: 3 slots ONLY [kanji346, 158, FFFE] -> must use all 3 for letters
    (64, 1876, 3, [S, t, r]),
    # Int: 4 slots [k535, k717, 158, FFFE] -> 3 letters + FFFE, drop suffix
    (65, 1884, 4, [I, n, t, FFFE]),
    # Pie: 5 slots [k308, k354, k320, 158, FFFE] -> 3 letters + suffix + FFFE
    (66, 1894, 5, [P, i, e, SUFFIX_SHORT, FFFE]),
    # Vit: 5 slots
    (67, 1906, 5, [V, i, t, SUFFIX_SHORT, FFFE]),
    # Agi: 5 slots
    (68, 1918, 5, [A, g, i, SUFFIX_SHORT, FFFE]),
    # Lck: 5 slots
    (69, 1930, 5, [L, c, k, SUFFIX_SHORT, FFFE]),
]

# ---------------------------------------------------------------------------
# Load the binary (after inject_r39_v2.py has run)
# ---------------------------------------------------------------------------
input_path = 'build/packdata_resources/0039_type15.raw'
if not os.path.exists(input_path):
    print(f"ERROR: {input_path} not found. Run inject_r39_v2.py first.")
    sys.exit(1)

raw = bytearray(open(input_path, 'rb').read())
base_size = 26624
print(f"R39 loaded: {len(raw)} bytes (base {base_size})")

# ---------------------------------------------------------------------------
# Verify original FFFF positions are intact
# ---------------------------------------------------------------------------
GLYPH_STREAM_START = 632
GLYPH_STREAM_END = 2702

for msg_idx, offset, slot_count, new_glyphs in PATCHES:
    # The FFFF terminator should be at offset + slot_count * 2
    ffff_pos = offset + slot_count * 2
    ffff_val = struct.unpack_from('>H', raw, ffff_pos)[0]
    if ffff_val != FFFF:
        print(f"  ERROR: MSG {msg_idx} @{offset}: expected FFFF at {ffff_pos}, "
              f"got 0x{ffff_val:04X}")
        sys.exit(1)

print("FFFF positions verified for all target messages")

# ---------------------------------------------------------------------------
# Apply patches
# ---------------------------------------------------------------------------
out = bytearray(raw)
patched = 0

for msg_idx, offset, slot_count, new_glyphs in PATCHES:
    assert len(new_glyphs) == slot_count, \
        f"MSG {msg_idx}: glyph count {len(new_glyphs)} != slot count {slot_count}"

    # Read current values for logging
    current = []
    for j in range(slot_count):
        current.append(struct.unpack_from('>H', out, offset + j * 2)[0])

    # Write new values
    for j, glyph_id in enumerate(new_glyphs):
        struct.pack_into('>H', out, offset + j * 2, glyph_id)

    # Decode for display
    def decode(glyphs):
        parts = []
        for g in glyphs:
            if g == FFFE:
                parts.append("FFFE")
            elif g == FFFF:
                parts.append("FFFF")
            elif g == 0:
                parts.append("_")
            elif 1 <= g <= 94:
                parts.append(chr(g + 32))
            else:
                parts.append(f"[{g}]")
        return " ".join(parts)

    print(f"  MSG {msg_idx:2d} @{offset}: {decode(current)} -> {decode(new_glyphs)}")
    patched += 1

print(f"\nPatched {patched} stat label messages")

# ---------------------------------------------------------------------------
# Sanity checks
# ---------------------------------------------------------------------------
# 1. FFFF count in glyph stream must be exactly 97
ffff_count = 0
for j in range(GLYPH_STREAM_START, GLYPH_STREAM_END, 2):
    if struct.unpack_from('>H', out, j)[0] == FFFF:
        ffff_count += 1
assert ffff_count == 97, f"FFFF count in glyph stream changed! Expected 97, got {ffff_count}"

# 2. Bytes outside glyph stream unchanged
assert out[:GLYPH_STREAM_START] == raw[:GLYPH_STREAM_START], \
    "Pre-stream bytes changed!"
assert out[GLYPH_STREAM_END:] == raw[GLYPH_STREAM_END:], \
    "Post-stream bytes changed!"

# 3. Only our target messages were modified
for j in range(GLYPH_STREAM_START, GLYPH_STREAM_END, 2):
    if out[j:j+2] != raw[j:j+2]:
        # Check this offset belongs to one of our patches
        in_patch = False
        for msg_idx, offset, slot_count, _ in PATCHES:
            if offset <= j < offset + slot_count * 2:
                in_patch = True
                break
        if not in_patch:
            old_val = struct.unpack_from('>H', raw, j)[0]
            new_val = struct.unpack_from('>H', out, j)[0]
            print(f"  WARNING: unexpected change at offset {j}: "
                  f"0x{old_val:04X} -> 0x{new_val:04X}")

print("Sanity checks passed")

# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------
with open(input_path, 'wb') as f:
    f.write(bytes(out))
print(f"Written {len(out)} bytes to {input_path}")
print("R39 stat label patch complete")
