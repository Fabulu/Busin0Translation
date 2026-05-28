"""BREAKTHROUGH: S2 offsets are GLYPH indices (half of byte offsets).
Verify this by checking all 0004 references with offset*2."""
import struct

data = open('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1198_type02.raw', 'rb').read()
sec2_off = struct.unpack_from('<I', data, 0x18)[0]
s1 = data[28:sec2_off]
s2 = data[sec2_off:]

words = []
for i in range(0, len(s1)-1, 2):
    words.append(struct.unpack_from('>H', s1, i)[0])

# Find message boundaries
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

def s2_off_to_msg(byte_off):
    for idx in range(len(msg_starts)-1):
        if msg_starts[idx] <= byte_off < msg_starts[idx+1]:
            return idx
    return len(msg_starts)-1

print("=== ALL 0004 0000 S2_GLYPH_OFF 0000 GLYPH_LEN references ===")
print(f"(interpreting offsets and lengths as glyph counts, *2 for bytes)")
print()

for i in range(len(words) - 4):
    if words[i] == 0x0004 and words[i+1] == 0x0000:
        glyph_off = words[i+2]
        byte_off = glyph_off * 2
        if byte_off >= len(s2) or byte_off < 0:
            continue
        if words[i+3] != 0x0000:
            continue
        glyph_len = words[i+4] if i+4 < len(words) else 0
        byte_len = glyph_len * 2

        # Read first glyph at this position
        first_glyph = struct.unpack_from('>H', s2, byte_off)[0]

        # Check what's at the end
        end_byte = byte_off + byte_len
        end_glyph = 0
        if end_byte < len(s2) - 1:
            end_glyph = struct.unpack_from('>H', s2, end_byte)[0]

        msg_idx = s2_off_to_msg(byte_off)
        end_msg = s2_off_to_msg(min(end_byte - 2, len(s2)-2)) if byte_len > 0 else msg_idx

        # Check if the span ends at a 0xFFFF terminator
        last_glyph = 0
        if end_byte >= 2:
            last_glyph = struct.unpack_from('>H', s2, end_byte - 2)[0]

        print(f"  @S1+{i*2:04X}: glyph_off={glyph_off}, glyph_len={glyph_len}")
        print(f"    byte_off=0x{byte_off:04X}, byte_len={byte_len}")
        print(f"    msg[{msg_idx}]{'->msg['+str(end_msg)+']' if end_msg != msg_idx else ''}")
        print(f"    first=0x{first_glyph:04X}, last=0x{last_glyph:04X}, next=0x{end_glyph:04X}")

        # Check if it ends at or near 0xFFFF
        terminator_ok = (last_glyph == 0xFFFF or
                        (end_byte < len(s2)-1 and struct.unpack_from('>H', s2, end_byte)[0] == 0xFFFF) or
                        last_glyph >= 0xFF00)
        if not terminator_ok:
            print(f"    WARNING: does not end at terminator")
        print()

# Now verify the 000C pattern too
print("\n=== 000C 0002 as glyph index ===")
for i in range(len(words) - 2):
    if words[i] == 0x000C and words[i+1] == 0x0002 and i < 100:
        glyph_idx = words[i+2]
        byte_off = glyph_idx * 2
        if byte_off < len(s2):
            glyph_at = struct.unpack_from('>H', s2, byte_off)[0]
            msg_idx = s2_off_to_msg(byte_off)
            print(f"  @S1+{i*2:04X}: glyph_idx={glyph_idx}, byte=0x{byte_off:04X}, msg[{msg_idx}], glyph=0x{glyph_at:04X}")

# Now verify the 000D pattern
print("\n=== 000D 0002 as glyph index ===")
for i in range(len(words) - 2):
    if words[i] == 0x000D and words[i+1] == 0x0002:
        glyph_idx = words[i+2]
        byte_off = glyph_idx * 2
        if byte_off < len(s2):
            glyph_at = struct.unpack_from('>H', s2, byte_off)[0]
            msg_idx = s2_off_to_msg(byte_off)
            print(f"  @S1+{i*2:04X}: glyph_idx={glyph_idx}, byte=0x{byte_off:04X}, msg[{msg_idx}], glyph=0x{glyph_at:04X}")

# Also check the 0012 0000 REG values as glyph indices
print("\n=== 0012 0000 values as glyph indices ===")
for val in sorted([0x86, 0x98, 0xB2, 0xC2, 0xCE, 0xDA, 0xE4]):
    byte_off = val * 2
    if byte_off < len(s2):
        glyph_at = struct.unpack_from('>H', s2, byte_off)[0]
        msg_idx = s2_off_to_msg(byte_off)
        print(f"  val=0x{val:04X}, byte=0x{byte_off:04X}, msg[{msg_idx}], glyph=0x{glyph_at:04X}")
