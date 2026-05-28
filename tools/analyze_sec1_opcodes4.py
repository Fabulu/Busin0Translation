"""Try to correlate Section 1 values with Section 2 message offsets."""
import struct

data = open('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1198_type02.raw', 'rb').read()
sec2_off = struct.unpack_from('<I', data, 0x18)[0]
s1 = data[28:sec2_off]
s2 = data[sec2_off:]

words = []
for i in range(0, len(s1)-1, 2):
    words.append(struct.unpack_from('>H', s1, i)[0])

# Parse Section 2 to understand message structure
# Section 2 starts with: 0377 0088 01C1 009C 03EA 02D5 007B 007F
# The 0x0088 = 136 could be message count * something, or it could be an offset
# Let's parse Section 2 properly

print("=== Section 2 raw header (first 32 bytes) ===")
for i in range(0, 32, 2):
    w = struct.unpack_from('>H', s2, i)[0]
    print(f"  +{i:02X}: 0x{w:04X} ({w})")

# Try reading Section 2 header as little-endian too
print("\n=== Section 2 header as LE words ===")
for i in range(0, 32, 2):
    w = struct.unpack_from('<H', s2, i)[0]
    print(f"  +{i:02X}: 0x{w:04X} ({w})")

# Also try as LE 32-bit values
print("\n=== Section 2 header as LE dwords ===")
for i in range(0, 32, 4):
    w = struct.unpack_from('<I', s2, i)[0]
    print(f"  +{i:02X}: 0x{w:08X} ({w})")

# Let me look at what's in the existing extraction tools for message parsing
# The message count is 88 for R1198.
# How is this stored? Let me check the first 100 bytes of Section 2
print("\n=== Section 2 first 128 bytes hex ===")
for i in range(0, min(128, len(s2)), 16):
    h = ' '.join(f'{s2[i+j]:02X}' for j in range(min(16, len(s2)-i)))
    print(f"  {i:04X}: {h}")

# Now, the key question: the opcode that shows messages.
# Let me look for the opcode 0x000D which appeared in some contexts
print("\n=== Opcode 0x000D instances ===")
for i, w in enumerate(words):
    if w == 0x000D:
        ctx = words[i:i+8]
        print(f"  @{i*2:04X}: {' '.join(f'{w:04X}' for w in ctx)}")

# Maybe the large values like 0x012D, 0x02A3, 0x03B8 etc are
# Section 2 byte offsets. Let me check what's at those offsets in Section 2
print("\n=== Checking if large values are Section 2 offsets ===")
test_offsets = [0x012D, 0x02A3, 0x02A7, 0x02AD, 0x02BB, 0x02D5, 0x03B8, 0x03DF, 0x03F5, 0x03FB, 0x040B]
for off in test_offsets:
    if off < len(s2):
        snippet = ' '.join(f'{s2[off+j]:02X}' for j in range(min(16, len(s2)-off)))
        print(f"  S2[0x{off:04X}]: {snippet}")

# Alternative: maybe they're indices into a message table
# Let me also check the header of the raw file itself
print("\n=== Full file header (first 28 bytes = header before Section 1) ===")
for i in range(0, 28, 4):
    le = struct.unpack_from('<I', data, i)[0]
    be = struct.unpack_from('>I', data, i)[0]
    print(f"  +{i:02X}: LE=0x{le:08X} ({le}), BE=0x{be:08X} ({be})")
