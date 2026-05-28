"""Map all S2 offsets to message indices and build instruction format hypothesis."""
import struct

data = open('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1198_type02.raw', 'rb').read()
sec2_off = struct.unpack_from('<I', data, 0x18)[0]
s1 = data[28:sec2_off]
s2 = data[sec2_off:]

words = []
for i in range(0, len(s1)-1, 2):
    words.append(struct.unpack_from('>H', s1, i)[0])

# Find all message boundaries
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

def s2_off_to_msg(off):
    for idx in range(len(msg_starts)-1):
        if msg_starts[idx] <= off < msg_starts[idx+1]:
            return idx, off - msg_starts[idx]
    if off >= msg_starts[-1]:
        return len(msg_starts)-1, off - msg_starts[-1]
    return -1, 0

# The 000C 0002 offsets: 301-314 = individual byte offsets within message 4
# msg[4] starts at 282 (0x011A) and msg[5] starts at 318 (0x013E)
# So 301-314 all fall within msg[4] which spans 282-317 (36 bytes = 18 glyphs)
# 301 = msg[4]+19, 304 = msg[4]+22, ...
# These are BYTE offsets pointing to individual glyph positions within msg[4]!

print("=== S2 offsets 301-314 mapped to messages ===")
for off in range(301, 315):
    msg_idx, msg_off = s2_off_to_msg(off)
    print(f"  S2[{off}] = msg[{msg_idx}] + {msg_off} bytes, byte: 0x{s2[off]:02X}")

print()
# msg[4] text data:
msg4_start = msg_starts[4]
msg5_start = msg_starts[5]
msg4_data = s2[msg4_start:msg5_start]
print(f"msg[4] full data ({msg5_start-msg4_start} bytes):")
print(' '.join(f'{b:02X}' for b in msg4_data))

# Now decode msg[4] as glyph indices
print("\nmsg[4] as glyph indices:")
for j in range(0, len(msg4_data)-1, 2):
    gi = struct.unpack_from('>H', msg4_data, j)[0]
    off_in_s2 = msg4_start + j
    ref_mark = " <-- ref'd by 000C 0002" if off_in_s2 in range(301, 315) else ""
    print(f"  S2+{off_in_s2:04X} (byte {off_in_s2}): glyph 0x{gi:04X}{ref_mark}")

# Now map ALL collected S2 offsets to messages
print("\n=== All S2 text offsets mapped to messages ===")

# Collect all references
all_refs = []

# Method 1: 0004 0000 OFF 0000 LEN
for i in range(len(words) - 4):
    if (words[i] == 0x0004 and words[i+1] == 0x0000 and
        words[i+2] > 0 and words[i+2] < len(s2) and
        words[i+3] == 0x0000):
        all_refs.append(('0004', i*2, words[i+2], words[i+4] if i+4 < len(words) else 0))

# Method 2: 000C 0002 OFF
for i in range(len(words) - 2):
    if words[i] == 0x000C and words[i+1] == 0x0002:
        all_refs.append(('000C_2', i*2, words[i+2], 0))

# Method 3: 000C 0000 OFF
for i in range(len(words) - 2):
    if words[i] == 0x000C and words[i+1] == 0x0000:
        all_refs.append(('000C_0', i*2, words[i+2], 0))

# Sort by S2 offset
all_refs.sort(key=lambda x: x[2])

print(f"Total text references: {len(all_refs)}")
print()

# Group by message
from collections import defaultdict
by_msg = defaultdict(list)
for optype, s1off, s2off, length in all_refs:
    msg_idx, msg_off = s2_off_to_msg(s2off)
    by_msg[msg_idx].append((optype, s1off, s2off, msg_off, length))

print("References grouped by message:")
for msg_idx in sorted(by_msg.keys()):
    refs = by_msg[msg_idx]
    msg_start = msg_starts[msg_idx] if msg_idx < len(msg_starts) else -1
    msg_end = msg_starts[msg_idx+1] if msg_idx+1 < len(msg_starts) else len(s2)
    msg_size = msg_end - msg_start
    print(f"\n  msg[{msg_idx}] (S2+{msg_start:04X}, {msg_size} bytes):")
    for optype, s1off, s2off, msg_off, length in refs:
        end_off = s2off + length if length > 0 else 0
        if length > 0:
            end_msg, end_moff = s2_off_to_msg(s2off + length - 1)
            span = f", spans to msg[{end_msg}]+{end_moff}" if end_msg != msg_idx else ""
            print(f"    {optype} @S1+{s1off:04X}: S2+{s2off:04X} (msg+{msg_off}), len={length}{span}")
        else:
            print(f"    {optype} @S1+{s1off:04X}: S2+{s2off:04X} (msg+{msg_off})")
