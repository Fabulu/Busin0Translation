import struct
from collections import Counter

exe_path = r"C:\Programmieren\wizardrytranslation\extracted_busin1\SLUS_202.59"
with open(exe_path, "rb") as f:
    exe_data = f.read()

b0_path = r"C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78"
with open(b0_path, "rb") as f:
    b0_data = f.read()

# The area at 0x3B8A44 has English text as uint16 values!
# This is NOT the MSG format (which uses BE uint16). This is LE uint16.
# Let's dump more of this area to understand the format

print("=== BUSIN 1 Embedded Text Area (LE uint16 ASCII) ===")
print("Starting scan from 0x3B8A00...")

off = 0x3B8900
end = 0x3B9000
while off < end:
    vals = []
    text = ""
    for j in range(20):
        if off + j*2 + 2 <= len(exe_data):
            v = struct.unpack("<H", exe_data[off + j*2 : off + j*2 + 2])[0]
            vals.append(v)
            if 0x20 <= v < 0x7F:
                text += chr(v)
            elif v == 0:
                text += " "
            elif v == 0x001D:
                text += "["
            elif v == 0x0001:
                text += "|"
            else:
                text += f"<{v:04X}>"
    print(f"  0x{off:06X}: {text}")
    off += 40

# Now let's understand the BUSIN 1 MSG format by examining UEDA.MSG more carefully
print("\n\n=== BUSIN 1 UEDA.MSG deep analysis ===")
msg_path = r"C:\Programmieren\wizardrytranslation\extracted_busin1\IMAGE\EVENT\UEDA.MSG"
with open(msg_path, "rb") as f:
    msg_data = f.read()

# The first Read showed the text had recognizable patterns but NOT ASCII
# The glyph index 0x0040 (64) was most common at 3.32%
# In ASCII, 0x40 = '@', but in the MSG context, BUSIN 1 uses BE uint16

# Let's look at the raw bytes and try to decode with ASCII interpretation
print("First 200 bytes as BE uint16:")
for i in range(0, min(400, len(msg_data)), 2):
    val = struct.unpack(">H", msg_data[i:i+2])[0]
    if i % 40 == 0:
        print()
        print(f"  0x{i:04X}: ", end="")
    if 0x20 <= val < 0x7F:
        print(f" {chr(val)}", end="")
    elif val == 0xFFFF:
        print(" \\n", end="")
    elif val == 0xFFFE:
        print(" \\0", end="")
    elif val < 0x100:
        print(f" [{val:02X}]", end="")
    else:
        print(f" <{val:04X}>", end="")
print()

# Now check: do the MSG glyph indices correspond to the embedded text's uint16 values?
# In the embedded text, space = 0x0000, 'A' = 0x0041, etc.
# In UEDA.MSG (BE), the top glyph is 0x0040 = '@' in ASCII...
# But the frequency doesn't match space (3.32% vs expected 18%)
# Let's see if these are glyph table indices rather than direct codes

# Check if BUSIN 0 has the same glyphs
print("\n\n=== BUSIN 0 Glyph Table Analysis ===")
# The glyph table at 0x3C0870 maps index -> glyph_code
# It goes: 1, 5, 6, 7, 8, 9, 10, 13, 14, ... (skipping some)
# Entry 84 onwards is 0x0000 (terminator?)
# This is a mapping: position in table -> actual glyph code

# Build the B0 glyph map
b0_glyph_map = []
off = 0x3C0870
while True:
    if off + 2 > len(b0_data):
        break
    val = struct.unpack("<H", b0_data[off:off+2])[0]
    b0_glyph_map.append(val)
    off += 2
    if len(b0_glyph_map) > 600:
        break

# Find actual glyph entries (non-zero, before the pointer area)
print(f"B0 glyph table entries (first 90):")
for i, v in enumerate(b0_glyph_map[:90]):
    label = ""
    if 0x20 <= v < 0x7F:
        label = f" = ASCII '{chr(v)}'"
    elif v == 0:
        label = " = NULL/SPACE"
    print(f"  [{i:3d}] 0x{v:04X}{label}")

# The MSG files use indices into this glyph table
# So in UEDA.MSG (BUSIN 1), glyph index 0x0040 (=64) maps to...
# what position in the glyph table?
# OR: the MSG uint16 IS the glyph code directly, and the glyph table
# maps glyph_code -> texture position

# Let's check: in B0's glyph table, position 56 has value 0x0040
# So if UEDA.MSG has code 0x0040, it could mean:
# "render the glyph at texture position for code 0x0040"

# For BUSIN 1, we need to find ITS glyph table
# The embedded text at 0x3B8A44 uses uint16 that look like direct glyph codes
# where 0x0041='A', 0x004E='N', etc.

# Let's search for a glyph table in BUSIN 1 similar to B0's
# B0's glyph table starts with: 01 00 05 00 06 00 07 00 08 00
b0_pattern = b0_data[0x3C0870:0x3C0870+10]
print(f"\nB0 glyph table start pattern: {b0_pattern.hex()}")

# Search BUSIN 1 for this pattern
for off in range(0, len(exe_data) - 10):
    if exe_data[off:off+10] == b0_pattern:
        print(f"  Found at 0x{off:06X}")
        # Dump surrounding area
        for i in range(20):
            v = struct.unpack("<H", exe_data[off+i*2:off+i*2+2])[0]
            print(f"    [{i}] 0x{v:04X}")

# Alternative: search for the font descriptor structure
# B0 has 12 font entries at 0x3C0700, each 28 bytes
# B1 might have the same but the values differ

# Look for the 0xFFFF terminator pattern that ends B0's font descriptors
# Entry 12 in B0: [0000:FFFF] [0000:0000] [00000000] [80808080] [01000100] [00000000] [00000000]
# The unique pattern is FFFF followed by specific values
print("\n=== Searching BUSIN 1 for FFFF0000 + 00000000 + 80808080 pattern ===")
for off in range(0, len(exe_data) - 20, 4):
    val0 = struct.unpack("<I", exe_data[off:off+4])[0]
    val1 = struct.unpack("<I", exe_data[off+4:off+8])[0]
    val2 = struct.unpack("<I", exe_data[off+8:off+12])[0]
    val3 = struct.unpack("<I", exe_data[off+12:off+16])[0]
    if val0 == 0x0000FFFF and val1 == 0x00000000 and val2 == 0x00000000 and val3 == 0x80808080:
        print(f"  Found at 0x{off:06X}")
        # Dump context before (potential descriptor entries)
        for i in range(-12, 3):
            e_off = off + i * 28
            if 0 <= e_off < len(exe_data) - 28:
                vals = struct.unpack("<7I", exe_data[e_off:e_off+28])
                print(f"    Entry at 0x{e_off:06X}: {' '.join(f'{v:08X}' for v in vals)}")

# Now try a completely different approach - the BUSIN 1 font system may be
# reorganized. Search for 01000100 pattern (from B0 descriptor field 4)
print("\n=== Searching for 0x01000100 pattern ===")
pattern_0100 = struct.pack("<I", 0x01000100)
hits = []
for off in range(0, len(exe_data) - 4):
    if exe_data[off:off+4] == pattern_0100:
        hits.append(off)
print(f"Found {len(hits)} occurrences of 01000100")
for h in hits[:20]:
    ctx = exe_data[max(0,h-16):h+16]
    print(f"  0x{h:06X}: {ctx.hex()}")

# Now analyze the UEDA.MSG glyph codes as potential ASCII
print("\n\n=== UEDA.MSG: Attempting ASCII decode ===")
# Read first message (until first FFFE)
decoded = []
i = 0
while i + 1 < len(msg_data):
    val = struct.unpack(">H", msg_data[i:i+2])[0]
    if val == 0xFFFE:
        decoded.append("\\n[MSG_END]\\n")
        break
    elif val == 0xFFFF:
        decoded.append("\\n")
    elif 0x20 <= val < 0x7F:
        decoded.append(chr(val))
    elif val == 0:
        decoded.append(" ")
    else:
        decoded.append(f"[{val:04X}]")
    i += 2

first_msg = "".join(decoded)
print(f"First message attempt (ASCII):\n{first_msg}")

# Try interpreting the glyph codes differently
# Maybe there's an offset or the high byte means something
print("\n=== First 100 uint16 values from UEDA.MSG ===")
for i in range(min(100, len(msg_data)//2)):
    val = struct.unpack(">H", msg_data[i*2:i*2+2])[0]
    ch = ""
    if 0x20 <= val < 0x7F:
        ch = f" = '{chr(val)}'"
    print(f"  [{i:3d}] 0x{val:04X} ({val:5d}){ch}")

print("\nDone part 3.")
