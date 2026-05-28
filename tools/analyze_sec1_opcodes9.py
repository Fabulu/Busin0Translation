"""Final analysis: understand the 000C pattern and build instruction format table.

The 000C 0002 offsets 0x012D-0x013A are spaced 1 byte apart (not 2).
0x012D, 0x0130, 0x0131, 0x0132, 0x0133, 0x0134, 0x0135, 0x0136, 0x0137, 0x0138, 0x0139, 0x013A
Gaps: 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1

Wait: 0x012D=301, 0x0130=304 -- that's a gap of 3, then all gaps of 1.
But glyph indices are 2 bytes each. So these are NOT byte offsets.
Unless 000C 0002 doesn't reference S2 at all?

Let me reconsider: maybe 0x000C 0x0002 XXXX means something different.
The values 0x012D, 0x0130-0x013A could be item IDs, character names, or
something else entirely.

For the 0004 pattern, the "length" field doesn't always match byte boundaries either.
Let me check if the lengths are byte counts or glyph counts.
"""
import struct

data = open('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1198_type02.raw', 'rb').read()
sec2_off = struct.unpack_from('<I', data, 0x18)[0]
s1 = data[28:sec2_off]
s2 = data[sec2_off:]

words = []
for i in range(0, len(s1)-1, 2):
    words.append(struct.unpack_from('>H', s1, i)[0])

# For the 0004 pattern, check if the "length" field is byte count or glyph count
# S2[0x0017], len=118: 0x0017 + 118 = 0x008D. But S2[0x008D] = 0xAB (not 0xFFFF)
# If it were 118 glyphs (236 bytes), 0x0017 + 236 = 0x0103. S2[0x0103] = ?
# If it were glyph count, next text at 0x0017+118*2 = 0x0017+236 = 0x0103

# Actually wait -- maybe it's not a length at all. Let me look at the full pattern
# more carefully for 0x0004.

# Let me re-examine: the pattern is 0004 0000 XXXX where XXXX could be the S2 offset
# but maybe I'm wrong about the instruction boundary.

# Let me look at the word BEFORE 0004 and AFTER the S2 offset more carefully
print("=== Full context around '0004' opcode (10 words before + 10 after) ===")
for i in range(len(words)):
    if words[i] == 0x0004 and i+1 < len(words):
        before = words[max(0,i-10):i]
        after = words[i:i+10]
        print(f"@{i*2:04X}: ...{' '.join(f'{w:04X}' for w in before)} | {' '.join(f'{w:04X}' for w in after)}")
        if i*2 > 0x2600:
            break

# Now check: the 0012 0000 XXXX pattern.
# XXXX values were: 134, 152, 178, 194, 206, 218, 228
# hex: 0x86, 0x98, 0xB2, 0xC2, 0xCE, 0xDA, 0xE4
# These are all within S2 too. But they DON'T cross message boundaries like the 0004 refs.
# Let me check what's at those S2 offsets:
print("\n=== S2 data at 0012-referenced offsets ===")
for off in [0x86, 0x98, 0xB2, 0xC2, 0xCE, 0xDA, 0xE4]:
    snippet = ' '.join(f'{s2[off+j]:02X}' for j in range(min(20, len(s2)-off)))
    # Also check what message this falls in
    msg_idx = -1
    msg_starts = [0]
    ii = 0
    while ii < len(s2) - 1:
        w = struct.unpack_from('>H', s2, ii)[0]
        if w == 0xFFFF:
            if ii + 2 < len(s2):
                msg_starts.append(ii + 2)
            ii += 2
        else:
            ii += 2

    for idx in range(len(msg_starts)-1):
        if msg_starts[idx] <= off < msg_starts[idx+1]:
            msg_idx = idx
            break

    print(f"  S2[0x{off:04X}] (msg[{msg_idx}]+{off-msg_starts[msg_idx]}): {snippet}")

# Let me look at the 000C values differently.
# 000C 0002 0x012D: what if 0x0002 is a "type" and 0x012D is a global ID (not S2 offset)?
# The values 0x012D=301, 0x0130-0x013A = 304-314
# These could be character name indices in a global name table.
# In fact, for a game with character creation, 301-314 could be
# party member name slots (14 possible characters).

print("\n=== Analyzing the 000C second parameter ===")
from collections import Counter
c_params = Counter()
for i in range(len(words) - 2):
    if words[i] == 0x000C:
        c_params[words[i+1]] += 1

print("000C second parameter distribution:")
for param, count in c_params.most_common():
    print(f"  param=0x{param:04X} ({param}): {count} times")

# And the 000D second parameter
d_params = Counter()
for i in range(len(words) - 2):
    if words[i] == 0x000D:
        d_params[words[i+1]] += 1

print("\n000D second parameter distribution:")
for param, count in d_params.most_common():
    print(f"  param=0x{param:04X} ({param}): {count} times")

# Let me also verify: do the 0x0004 0x0000 references consistently point to
# S2 data that starts with valid glyph indices?
print("\n=== Verifying 0004 S2 offset data ===")
for i in range(len(words) - 4):
    if (words[i] == 0x0004 and words[i+1] == 0x0000 and
        words[i+2] > 0 and words[i+2] < len(s2)):
        s2off = words[i+2]
        # Read first glyph at this offset
        if s2off + 1 < len(s2):
            first_glyph = struct.unpack_from('>H', s2, s2off)[0]
            # Check if it looks like a valid glyph (not 0x0000, in reasonable range)
            valid = 0x0001 <= first_glyph <= 0x0600 or 0xFF00 <= first_glyph <= 0xFFFF
            print(f"  @S1+{i*2:04X}: S2[0x{s2off:04X}] first glyph=0x{first_glyph:04X} valid={valid}")
