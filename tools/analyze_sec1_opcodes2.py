"""Deeper analysis of Section 1 event script format."""
import struct

data = open('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1198_type02.raw', 'rb').read()
sec2_off = struct.unpack_from('<I', data, 0x18)[0]
s1 = data[28:sec2_off]
words = []
for i in range(0, len(s1)-1, 2):
    words.append(struct.unpack_from('>H', s1, i)[0])

# Key insight from the data:
# 0x000B always followed by 0x0000 then a value that looks like an offset
# 0x0008 always followed by 0x0000 then a value that looks like an offset
# 0x000C always followed by 0x0002 then a value 0x012D
# These look like 3-word (6-byte) instructions

# 0x0006 appears to take 6 parameters (7 words total)
# 0x0007 appears to take 6 parameters (7 words total)
# 0x0016 appears to take 5 parameters (6 words total)

# Let me verify by trying to decode a known block
# Block at 0x0190 (word 200):
# 000C 0002 012D  -- opcode 0C, 2 params
# 0006 0016 0001 0000 0001 0000 01F6  -- opcode 06 with param 0016, then 5 more
# 0006 0094 0040 0000 2000 0000 01B4  -- opcode 06 with different params
# 000B 0000 01F6  -- opcode 0B
# 0007 0094 0040 0000 4000 0000 01C8  -- opcode 07
# 000B 0000 01F6  -- opcode 0B

# Wait, there are TWO types of 0x0006:
# Type A: 0006 0016 0001 ... (7 words) - starts with 0016
# Type B: 0006 005B 0040 ... (7 words) - starts with 005B/0094/00CD/0106/013F/0178

# Actually maybe opcode 0x0006 always takes 6 params (7 words)?
# Let me check: 0006 0008 0002 0001 0006 0000 0040 -- no that's only reading first occurrence at 0x12

# Let me re-examine. The very first instruction might be different.
# Let me try walking through from the start with hypothesized instruction lengths.

# Try approach: assume small values (0x00-0x20 or so) are opcodes
# and try to figure out instruction length from context

print("=== Attempting instruction decode from start ===")
print("Looking at opcode 0x0016 pattern more carefully:")
print()

# 0x0016 instances:
for i, w in enumerate(words):
    if w == 0x0016:
        ctx = words[i:i+10]
        print(f"  @{i*2:04X}: {' '.join(f'{w:04X}' for w in ctx)}")
        if len([x for x in ctx[:6] if x > 0x1000]) > 0:
            first_big = next(j for j, x in enumerate(ctx[:8]) if x > 0x100)
            print(f"    -> first large value at offset +{first_big}: 0x{ctx[first_big]:04X}")

print()
print("=== Opcode 0x002B instances ===")
for i, w in enumerate(words):
    if w == 0x002B:
        ctx = words[i:i+10]
        print(f"  @{i*2:04X}: {' '.join(f'{w:04X}' for w in ctx)}")

print()
print("=== Opcode 0x0017 instances ===")
for i, w in enumerate(words):
    if w == 0x0017:
        ctx = words[i:i+10]
        print(f"  @{i*2:04X}: {' '.join(f'{w:04X}' for w in ctx)}")

print()
# The value 0x012D appears after every opcode 0x000C 0x0002.
# 0x012D = 301. Let me check if this is a Section 2 message count or index
print("=== Opcode 0x000C context (first 20) ===")
for i, w in enumerate(words):
    if w == 0x000C and i < len(words) - 3:
        ctx = words[i:i+6]
        print(f"  @{i*2:04X}: {' '.join(f'{w:04X}' for w in ctx)}")
        if len([x for x in [i for i,w2 in enumerate(words) if w2 == 0x000C]]) > 20:
            break

print()
# Look at larger offsets - where the dialogue might be referenced
# Opcode 0x001A with 0x00BD:
print("=== Opcode 0x001A + 0x00BD instances (all) ===")
for i, w in enumerate(words):
    if w == 0x001A and i+1 < len(words) and words[i+1] == 0x00BD:
        ctx = words[i:i+8]
        print(f"  @{i*2:04X}: {' '.join(f'{w:04X}' for w in ctx)}")
        # The 3rd value (words[i+2]) goes 1,4,5,6,7,8,9,10,11,12,13,14
        # Could be message group/character index

print()
# What follows each 0x001A 0x00BD block?
# Look at what comes after 001A 00BD XXXX YYYY
print("=== Context AFTER each 001A 00BD block (8 words after) ===")
for i, w in enumerate(words):
    if w == 0x001A and i+1 < len(words) and words[i+1] == 0x00BD:
        ctx = words[i:i+12]
        print(f"  @{i*2:04X}: {' '.join(f'{w:04X}' for w in ctx)}")
