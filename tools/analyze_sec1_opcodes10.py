"""Check if S2 offsets are byte offsets (some are ODD) or if something else is going on.
Many offsets like 0x0017, 0x008D, 0x0113, 0x02AD are ODD - not word-aligned.
This could mean:
1. The S2 data is byte-addressed (not glyph-addressed)
2. The offsets need adjustment (e.g., multiply by 2, or add a base)
3. The format uses byte-level addressing for some reason

Let me check if multiplying by 2 or adding 1 fixes alignment.
"""
import struct

data = open('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1198_type02.raw', 'rb').read()
sec2_off = struct.unpack_from('<I', data, 0x18)[0]
s1 = data[28:sec2_off]
s2 = data[sec2_off:]

words = []
for i in range(0, len(s1)-1, 2):
    words.append(struct.unpack_from('>H', s1, i)[0])

# Collect all "0004 0000 OFF" pattern offsets
offsets_0004 = []
for i in range(len(words) - 2):
    if words[i] == 0x0004 and words[i+1] == 0x0000 and words[i+2] > 0:
        off = words[i+2]
        if off < len(s2):
            offsets_0004.append(off)

print("=== Check alignment of 0004 S2 offsets ===")
even = sum(1 for o in offsets_0004 if o % 2 == 0)
odd = sum(1 for o in offsets_0004 if o % 2 == 1)
print(f"Even: {even}, Odd: {odd}")
print(f"All offsets: {[f'0x{o:04X}' for o in offsets_0004]}")

# What if these are NOT S2 offsets but rather something else?
# Let me reconsider. The word before 0x0004 (i.e., the word at position i-1)
# might be relevant.
print("\n=== Word immediately before 0004 ===")
from collections import Counter
before_0004 = Counter()
for i in range(len(words) - 2):
    if words[i] == 0x0004 and words[i+1] == 0x0000:
        if i > 0:
            before_0004[words[i-1]] += 1

for w, c in before_0004.most_common():
    print(f"  0x{w:04X} ({w}): {c} times")

# Let me rethink. What if the "0004" I'm seeing is NOT an opcode but part
# of the previous instruction? Let me look at what CONSISTENTLY appears
# in the text display context.
#
# From the hex dump at 0x2054:
# 0012 0000 00B2 0004 0000 0017 0000 0076 0062 0000
# Maybe "0012 0000 00B2" is instruction 1, then "0004 0000 0017 0000 0076" is instruction 2.
#
# But 0x00B2 + 0x0004 = 0x00B6? That doesn't help.
# What if 0x0012 takes 2 params: 0000 and 00B2, making it 3 words?
# Then the next instruction starts at 0004.
# Or what if 0x0012 0x0000 is the opcode, and 00B2 is a register ID?
# Then the instruction is "0012 0000 00B2" = "load register 0xB2 with 0"?

# Wait - let me look at this differently. The pattern consistently appears as:
# 0012 0000 REG
# 0004 0000 S2OFF 0000 VALUE
# where REG is 0x86, 0x98, 0xB2, 0xC2, 0xCE, 0xDA, 0xE4

# What if opcode 0x0012 is "SET_TEXT_POINTER register, value"?
# And opcode 0x0004 is "DISPLAY_TEXT S2offset, someParam"?

# Actually wait. Let me look at the value AFTER S2OFF in the 0004 pattern.
# Pattern: 0004 0000 S2OFF 0000 VALUE
# The VALUE could be the text LENGTH (in bytes).

# Let me verify: S2OFF=0x0017, VALUE=0x0076 (118)
# Text from S2[0x17] for 118 bytes = S2[0x17:0x8D]
# S2[0x8D-2:0x8D] should be near the end of a text segment

print("\n=== Verify text lengths ===")
test_cases = [
    (0x0017, 0x0076),  # 118
    (0x008D, 0x0086),  # 134
    (0x0113, 0x001B),  # 27
    (0x012E, 0x00B8),  # 184
    (0x01E6, 0x0058),  # 88
    (0x023E, 0x0065),  # 101
]

for s2off, length in test_cases:
    end = s2off + length
    if end <= len(s2) and end >= 2:
        last_word = struct.unpack_from('>H', s2, end-2)[0]
        at_end = struct.unpack_from('>H', s2, end)[0] if end < len(s2)-1 else 0
        aligned = "ALIGNED" if s2off % 2 == 0 else "ODD"
        end_aligned = "ALIGNED" if end % 2 == 0 else "ODD"
        print(f"  S2[0x{s2off:04X}:{s2off+length}] len={length} ({aligned}->end {end_aligned})")
        print(f"    last word at end-2: 0x{last_word:04X}, word at end: 0x{at_end:04X}")

        # Check if the end lands on or near a 0xFFFF terminator
        # Search for nearest FFFF
        nearest_ff = -1
        for j in range(max(0, end-10), min(len(s2)-1, end+10), 2):
            w = struct.unpack_from('>H', s2, j)[0]
            if w == 0xFFFF:
                nearest_ff = j
                break
        if nearest_ff >= 0:
            print(f"    nearest 0xFFFF at S2+0x{nearest_ff:04X} (delta={nearest_ff-end})")
        print()

# Let me also check: do these lengths represent glyph counts (multiply by 2)?
print("=== Try lengths as glyph counts ===")
for s2off, length in test_cases:
    end = s2off + length * 2  # if length is glyph count
    if end <= len(s2) and end >= 2:
        last_word = struct.unpack_from('>H', s2, end-2)[0]
        print(f"  S2[0x{s2off:04X}+{length}*2=0x{end:04X}]: last_word=0x{last_word:04X}")

# Hmm, let me check if the S2 offsets should be doubled
print("\n=== Try S2 offsets * 2 ===")
for s2off, length in test_cases:
    real_off = s2off * 2
    if real_off < len(s2):
        first = struct.unpack_from('>H', s2, real_off)[0]
        print(f"  S2[0x{s2off:04X}*2=0x{real_off:04X}]: first glyph=0x{first:04X}")
