"""Find message display opcodes - where are Section 2 message indices referenced?"""
import struct

data = open('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1198_type02.raw', 'rb').read()
sec2_off = struct.unpack_from('<I', data, 0x18)[0]
s1 = data[28:sec2_off]
words = []
for i in range(0, len(s1)-1, 2):
    words.append(struct.unpack_from('>H', s1, i)[0])

# Key findings so far:
# 0x001A 0x00BD XX = some kind of block/scene marker, XX goes 1,4,5,6,7,8,9,10,11,12,13,14
# 0x0016 0001 0000 XX 0000 ADDR = branch/case with index XX (0-5) and jump target ADDR
# 0x0016 0002 FFFF FFFF 0000 ADDR = default/else branch
# 0x002B XX = some kind of setup, XX is often 0x0005
# 0x0006 PARAM 0040 0000 MASK 0000 ADDR = conditional bit test, 7 words
# 0x0007 PARAM 0040 0000 MASK 0000 ADDR = similar to 0x0006, 7 words
# 0x000B 0000 ADDR = jump/goto, 3 words
# 0x0008 0000 ADDR = similar to 0x000B, 3 words
# 0x000C 0002 ADDR = another jump variant, 3 words

# The PARAM values (0x005B=91, 0x0094=148, 0x00CD=205, 0x0106=262, 0x013F=319, 0x0178=376)
# are spaced 57 apart. Could be character/NPC slot IDs.

# Now: where are message indices 0-87?
# Let me look at the Section 2 message count first
print("=== Section 2 info ===")
# Parse Section 2 header to find message count
s2 = data[sec2_off:]
print(f"Section 2 starts at offset {sec2_off} (0x{sec2_off:04X})")
# Check first few bytes of Section 2
s2_header = struct.unpack_from('>8H', s2, 0)
print(f"Section 2 first 8 words: {' '.join(f'{w:04X}' for w in s2_header)}")

# The message count for R1198 is 88. Let me look for where values
# in the range 0-87 appear in ways that suggest message references.

# Key insight: the 0x001A opcode seems to be a general "set/call" with the
# next word being a function/register ID. Let me look at ALL 0x001A instances.
print("\n=== ALL 0x001A instances ===")
for i, w in enumerate(words):
    if w == 0x001A:
        ctx = words[i:i+6]
        print(f"  @{i*2:04X}: {' '.join(f'{w:04X}' for w in ctx)}")

# Now let me look for opcodes that might reference dialogue
# Check the tail end of the file - event scripts often have dialogue at the end
print("\n=== Last 200 words of Section 1 ===")
start = max(0, len(words) - 200)
for i in range(start, len(words)):
    if i % 10 == start % 10:
        print(f"[{i:4d}] @{i*2:04X}: ", end="")
    print(f"{words[i]:04X} ", end="")
    if (i - start) % 10 == 9:
        print()
print()

# Look at what's around offset 0x2000+ (after the main repeating blocks)
print("\n=== Words from 0x2000 (after repeating blocks) ===")
for i in range(0x2000//2, min(0x2200//2, len(words))):
    print(f"[{i:4d}] @{i*2:04X}: 0x{words[i]:04X} ({words[i]})")
