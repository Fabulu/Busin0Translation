"""Identify the message display mechanism - trace 0x0004 and the values following 0x0012 patterns."""
import struct

data = open('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1198_type02.raw', 'rb').read()
sec2_off = struct.unpack_from('<I', data, 0x18)[0]
s1 = data[28:sec2_off]
s2 = data[sec2_off:]

words = []
for i in range(0, len(s1)-1, 2):
    words.append(struct.unpack_from('>H', s1, i)[0])

# Look at the "0012 0000 XXXX 0004 0000 YYYY 0000 ZZZZ" pattern
# where XXXX is a register, YYYY is a Section 2 offset, ZZZZ is a length
print("=== Pattern: 0012 0000 XXXX ... 0004 0000 YYYY 0000 ZZZZ ===")
for i in range(len(words)):
    if (words[i] == 0x0004 and i+2 < len(words) and
        words[i+1] == 0x0000 and words[i+2] > 0x100 and words[i+2] < 0x1000):
        # This looks like a text reference
        s2_off_val = words[i+2]
        length = words[i+4] if i+4 < len(words) else 0

        # Get some context before
        ctx_before = words[max(0,i-6):i]
        ctx_after = words[i:i+6]

        # Verify it's a valid S2 offset by checking the data
        if s2_off_val < len(s2):
            s2_snippet = ' '.join(f'{s2[s2_off_val+j]:02X}' for j in range(min(8, len(s2)-s2_off_val)))
        else:
            s2_snippet = "OUT OF RANGE"

        print(f"  @{i*2:04X}: before: {' '.join(f'{w:04X}' for w in ctx_before)}")
        print(f"          0004: {' '.join(f'{w:04X}' for w in ctx_after)}")
        print(f"          S2[0x{s2_off_val:04X}]: {s2_snippet}")
        print()

# Also look at opcodes that directly contain S2 text offsets
# Let me examine: 0x0012 0x0000 0x00B2 ... pattern
# 0x00B2 = 178. What is at S2[178]?
print("\n=== Check specific S2 offsets ===")
for off in [0x00B2, 0x00CE, 0x00DA, 0x00E4, 0x0086, 0x0098, 0x00C2]:
    if off < len(s2):
        snippet = ' '.join(f'{s2[off+j]:02X}' for j in range(min(16, len(s2)-off)))
        print(f"  S2[0x{off:04X}]: {snippet}")

# Now let me look at the full "0012 0000 XXXX 0004 0000 YYYY 0000 ZZZZ" sequences
# to understand the instruction grouping
print("\n=== Full instruction sequences around text displays ===")
print("(Looking for 0x0004 preceded by 0x0012 in broader context)\n")

# Walk through the data from 0x2000 onwards (the non-repeating part)
# and try to identify individual instructions
pos = 0x2000 // 2  # Start at word offset for byte 0x2000
end = len(words)
count = 0
while pos < end and count < 100:
    w = words[pos]
    if w == 0:
        pos += 1
        continue

    # Print current position and next 12 words
    ctx = words[pos:pos+12]
    ctx_str = ' '.join(f'{w:04X}' for w in ctx)

    # Only print non-zero sequences
    if any(x != 0 for x in ctx[:3]):
        print(f"@{pos*2:04X}: {ctx_str}")
        count += 1
    pos += 1
