"""Decode the instruction stream with hypothesized opcode lengths.
Focus on the message-reference mechanism."""
import struct

data = open('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1198_type02.raw', 'rb').read()
sec2_off = struct.unpack_from('<I', data, 0x18)[0]
s1 = data[28:sec2_off]

words = []
for i in range(0, len(s1)-1, 2):
    words.append(struct.unpack_from('>H', s1, i)[0])

# The Section 2 contains message text. The values seen in Section 1 (0x012D, 0x02A3, etc.)
# are byte offsets into Section 2.
#
# Section 1 is 12836 bytes. The data ends with a large zero-padding region
# starting around offset 0x2500.
#
# Let me focus on what opcodes reference Section 2 offsets.
# I know Section 2 is at file offset 0x3240 and has data starting at byte 0.
# Values in the range say 0x0000 - 0x1000 could be Section 2 offsets.
#
# But we also saw values like 0x012D appearing consistently after opcode 0x000C 0x0002.
# And values like 0x02A3, 0x02BB, 0x02D5 etc. appearing after 0x0012 0x0000 ... 0x0004 0x0000
#
# Let me trace the opcode patterns more carefully.

# First: the 0x012D value. It always follows "000C 0002".
# 0x012D = 301 decimal. Section 2 at offset 301 shows text-like data.
# This might be a "display message starting at S2 offset 0x012D"

# The repeating structure has:
# Block template (for each of 6 character slots 0-5):
#   0006 0016 0001 0000 SLOT_IDX 0000 BLOCK_END_ADDR
#   0006 CHAR_ID 0040 0000 2000 0000 JMP1
#   000B 0000 BLOCK_END_ADDR
#   0007 CHAR_ID 0040 0000 4000 0000 JMP2
#   000B 0000 BLOCK_END_ADDR
#   0007 CHAR_ID 0040 0000 1000 0000 JMP3
#   000B 0000 BLOCK_END_ADDR
#   0007 CHAR_ID 0040 0000 0800 0000 JMP4
#   0008 0000 BLOCK_END_ADDR
#   000C 0002 MSG_OFFSET
# Where CHAR_IDs are 0x005B, 0x0094, 0x00CD, 0x0106, 0x013F, 0x0178

# So opcode 0x000C with param 0x0002 followed by a Section 2 text offset
# is likely the MESSAGE DISPLAY opcode!

# Let me collect all opcode 0x000C instances
print("=== ALL opcode 0x000C instances ===")
for i, w in enumerate(words):
    if w == 0x000C:
        ctx = words[i:i+6]
        print(f"  @{i*2:04X}: {' '.join(f'{w:04X}' for w in ctx)}")

# Count unique values after 000C
print()
msg_offsets_000c = set()
for i, w in enumerate(words):
    if w == 0x000C and i+2 < len(words):
        msg_offsets_000c.add(words[i+2])
print(f"Unique Section 2 offsets via opcode 0x000C: {len(msg_offsets_000c)}")
print(f"Values: {sorted(msg_offsets_000c)}")

# Now let me find opcode 0x000D instances and check their pattern
print("\n=== ALL opcode 0x000D instances ===")
msg_offsets_000d = set()
for i, w in enumerate(words):
    if w == 0x000D:
        ctx = words[i:i+6]
        print(f"  @{i*2:04X}: {' '.join(f'{w:04X}' for w in ctx)}")
        if i+2 < len(words):
            msg_offsets_000d.add(words[i+2])
print(f"\nUnique values after 0x000D: {len(msg_offsets_000d)}")
print(f"Values: {sorted(msg_offsets_000d)}")

# Now let me look for ALL Section 2 offsets that appear in Section 1
# Section 2 is 5874 bytes (from header: 0x16F2).
# Values in range 0-5874 could be Section 2 offsets.
# But we need to distinguish from Section 1 jump addresses (which are also in a similar range).
# Section 1 is 12836 bytes, so S1 jump targets would be 0-12836 (0x3224).

# Let me check the patterns around opcode 0x0012
print("\n=== Opcode 0x0012 instances (all) ===")
for i, w in enumerate(words):
    if w == 0x0012:
        ctx = words[i:i+8]
        print(f"  @{i*2:04X}: {' '.join(f'{w:04X}' for w in ctx)}")

# The pattern 0012 0000 XXXX seems common. What are the XXXX values?
print("\n=== Values after '0012 0000' pattern ===")
vals_after_0012 = []
for i, w in enumerate(words):
    if w == 0x0012 and i+2 < len(words) and words[i+1] == 0x0000:
        vals_after_0012.append(words[i+2])
print(f"Count: {len(vals_after_0012)}")
print(f"Unique: {sorted(set(vals_after_0012))}")

# 0x0004 often follows the 0x0012 pattern. Check what follows 0x0004
print("\n=== Opcode 0x0004 pattern ===")
for i, w in enumerate(words):
    if w == 0x0004 and i > 0 and i+3 < len(words):
        # Check if preceded by 0012 0000 XXXX
        ctx_before = words[max(0,i-4):i]
        ctx_after = words[i:i+6]
        print(f"  @{i*2:04X}: before={' '.join(f'{w:04X}' for w in ctx_before)} | {' '.join(f'{w:04X}' for w in ctx_after)}")
        if len([x for x in [i for i2,w2 in enumerate(words) if w2 == 0x0004]]) > 30:
            break
