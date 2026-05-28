"""Proper instruction decoder for Section 1 event script.

Key findings so far:
- Data is big-endian 16-bit words
- Instructions are variable-length
- Section 2 text offsets appear after specific patterns like "0004 0000 OFFSET 0000 LEN"

Hypothesized opcode table (all lengths include opcode word):
- 0x0003: 3 words (opcode, param, ??)  -- or maybe 2 words?
- 0x0004: 3 words (opcode, 0x0000, S2_offset) -- TEXT DISPLAY
- 0x0006: 7 words (opcode, target, mask_hi, mask_lo, bitmask_hi, bitmask_lo, jmp_addr)
- 0x0007: 7 words (same as 0x0006)
- 0x0008: 3 words (opcode, 0x0000, jmp_addr) -- JUMP
- 0x000B: 3 words (opcode, 0x0000, jmp_addr) -- JUMP
- 0x000C: 3 words (opcode, param, S2_offset_or_value)
- 0x000D: 3 words (opcode, param, S2_offset)
- 0x0010: 2 words (opcode, param)
- 0x0012: 3 words (opcode, 0x0000, register_id)
- 0x0014: 3 words (opcode, param, value)
- 0x0016: 6 words (opcode, type, p1, p2, p3, jmp_addr)
- 0x0017: 5 words (opcode, param1, param2, param3, param4)
- 0x001A: 3 words (opcode, register, value)
- 0x001B: 2 words (opcode, param)
- 0x002B: 2 words (opcode, param)
- 0x002C: 2 words (opcode, param)
- 0x003C: 1 word (opcode/NOP?)
- 0x0021: 4 words?
- 0x0022: 3 words?
- 0x0027: 1 word?
- 0x0043: 2 words (opcode, param)
- 0x0045: 3 words (opcode, param, value)
- 0x0047: 3 words (opcode, param, value)
- 0x0048: 3 words (opcode, param, value)
- 0x004E: 2 words (opcode, param)
- 0x005A: 1 word
- 0x0060: 2 words
- 0x0062: 2 words (opcode, param)
- 0x0063: 2 words
- 0x0065: 2 words
- 0x006D: 2 words
- 0x0076: 1 word?
- 0x0079: 2 words
- 0x0080: 1 word?
- 0x0086: 1 word?
- 0x0098: 1 word?
- 0x0099: 1 word?
- 0x00B2: 1 word?
- 0x00B4: 2 words
- 0x00B8: 1 word?
- 0x00BD: 2 words (opcode, section_id)
- 0x00BE: 1 word?
- 0xFFFF: 3 words (opcode, 0x0000, jmp_addr)

The problem is I can't easily determine instruction lengths without the opcode table.
Let me try a different approach: find the patterns that ALWAYS lead to text display.
"""
import struct

data = open('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1198_type02.raw', 'rb').read()
sec2_off = struct.unpack_from('<I', data, 0x18)[0]
s1 = data[28:sec2_off]
s2 = data[sec2_off:]

words = []
for i in range(0, len(s1)-1, 2):
    words.append(struct.unpack_from('>H', s1, i)[0])

# The clearest text display pattern is:
# 0012 0000 REG 0004 0000 S2_OFF 0000 MSGLEN
#
# But there's also:
# 000C 0002 S2_OFF  (message reference in the repeating blocks)
# 000D 0002 S2_OFF  (cleanup/dealloc of message?)
#
# Let me collect ALL S2 text references by looking for the pattern:
# XXXX 0000 S2_OFF where S2_OFF is followed by 0000 MSGLEN
# and S2_OFF is in the valid range for Section 2

print("=== Collecting all Section 2 text offset references ===")
print(f"Section 2 size: {len(s2)} bytes")
print()

# Method 1: Find "0004 0000 S2OFF 0000 LEN" pattern
text_refs = []
for i in range(len(words) - 4):
    if (words[i] == 0x0004 and words[i+1] == 0x0000 and
        words[i+2] > 0 and words[i+2] < len(s2) and
        words[i+3] == 0x0000):
        s2_off_val = words[i+2]
        msg_len = words[i+4] if i+4 < len(words) else 0
        text_refs.append((i*2, s2_off_val, msg_len))

print(f"Method 1 (0004 0000 OFF 0000 LEN): {len(text_refs)} references")
for byte_off, s2off, mlen in text_refs:
    print(f"  @{byte_off:04X}: S2[0x{s2off:04X}], len={mlen}")

# Method 2: "000C 0002 S2OFF" pattern
print()
text_refs_c = []
for i in range(len(words) - 2):
    if words[i] == 0x000C and words[i+1] == 0x0002:
        s2off = words[i+2]
        text_refs_c.append((i*2, s2off))

print(f"Method 2 (000C 0002 OFF): {len(text_refs_c)} references")
unique_c = sorted(set(off for _, off in text_refs_c))
print(f"  Unique S2 offsets: {unique_c}")
print(f"  Decimal: {[f'0x{x:04X}={x}' for x in unique_c]}")

# Method 3: "000C 0000 S2OFF" pattern
print()
text_refs_c0 = []
for i in range(len(words) - 2):
    if words[i] == 0x000C and words[i+1] == 0x0000:
        s2off = words[i+2]
        text_refs_c0.append((i*2, s2off))

print(f"Method 3 (000C 0000 OFF): {len(text_refs_c0)} references")
for byte_off, s2off in text_refs_c0:
    print(f"  @{byte_off:04X}: S2 offset = 0x{s2off:04X} ({s2off})")

# Now let me collect ALL unique S2 offsets from all methods
all_s2_offsets = set()
for _, off, _ in text_refs:
    all_s2_offsets.add(off)
for _, off in text_refs_c:
    all_s2_offsets.add(off)
for _, off in text_refs_c0:
    all_s2_offsets.add(off)

print(f"\n=== Total unique S2 text offsets referenced: {len(all_s2_offsets)} ===")
for off in sorted(all_s2_offsets):
    # Read a few bytes of text at this offset
    if off < len(s2):
        snippet = ' '.join(f'{s2[off+j]:02X}' for j in range(min(8, len(s2)-off)))
    else:
        snippet = "OUT OF RANGE"
    print(f"  0x{off:04X} ({off:5d}): {snippet}")

# Now: how does this relate to the 88 messages?
# Let me check the existing dialogue extraction to understand message boundaries
# The Section 2 glyph data starts at offset 0. Each message is a variable-length
# sequence of 16-bit glyph indices terminated by 0xFFFF.

print(f"\n=== Section 2 message boundary scan ===")
msg_starts = [0]
i = 0
while i < len(s2) - 1:
    w = struct.unpack_from('>H', s2, i)[0]
    if w == 0xFFFF:
        if i + 2 < len(s2):
            msg_starts.append(i + 2)
        i += 2
    else:
        i += 2

print(f"Found {len(msg_starts)} messages (terminated by 0xFFFF)")
print("First 100 message start offsets:")
for idx, off in enumerate(msg_starts[:100]):
    marker = " <-- REFERENCED" if off in all_s2_offsets else ""
    print(f"  msg[{idx:3d}] @ S2+0x{off:04X} ({off:5d}){marker}")
