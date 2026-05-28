import struct
from collections import Counter

exe_path = r"C:\Programmieren\wizardrytranslation\extracted_busin1\SLUS_202.59"
with open(exe_path, "rb") as f:
    exe_data = f.read()

b0_path = r"C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78"
with open(b0_path, "rb") as f:
    b0_data = f.read()

msg_path = r"C:\Programmieren\wizardrytranslation\extracted_busin1\IMAGE\EVENT\UEDA.MSG"
with open(msg_path, "rb") as f:
    msg_data = f.read()

# KEY INSIGHT from part 3:
# - The embedded text in EXE (0x3B8900+) uses LE uint16 with glyph codes
#   that ARE ASCII codes (0x41='A', 0x4E='N', etc.)
# - UEDA.MSG uses BE uint16 glyph indices that are NOT direct ASCII
# - Some MSG values happen to fall in ASCII range but the text is clearly Japanese
# - The Japanese game's glyph system was kept; the font texture was changed
# - The MSG format is: glyph indices into a JIS-like character set

# Let's verify: decode the UEDA.MSG using the B0 glyph table as a lookup
# B0 glyph table at 0x3C0870: maps position -> character code
# But wait - B0's table goes: [0]=1, [1]=5, [2]=6 ...
# These are NOT sequential, they skip some values
# This means the table maps SOME index to the actual glyph code

# Actually, looking more carefully at B0's structure:
# - Font descriptors (0x3C0700): 12 entries defining font sizes/textures
# - Entry 12: 0xFFFF terminator
# - Then at 0x3C086C: 4 zero bytes, then glyph table starts
# - The glyph table values are the valid glyph codes

# For BUSIN 1 MSG files, the uint16 values ARE the glyph codes
# The EXE embedded text at 0x3B8900 uses the SAME glyph code space
# where codes 0x0041-0x005D map to ASCII A-Z plus some

# So the glyph codes in UEDA.MSG like 0x026A, 0x0148, 0x0247
# are Japanese characters (hiragana/katakana/kanji)

# Let's verify by looking at what BUSIN 0's glyph table covers
print("=== BUSIN 0 Full Glyph Table (0x3C0870 onwards) ===")
off = 0x3C0870
b0_glyphs = []
while off + 2 <= len(b0_data) and len(b0_glyphs) < 600:
    val = struct.unpack("<H", b0_data[off:off+2])[0]
    b0_glyphs.append(val)
    off += 2

# Count how many before the zeros (actual glyph entries)
actual_count = 0
for i, v in enumerate(b0_glyphs):
    if v == 0 and i > 0 and b0_glyphs[i-1] == 0x005D:
        actual_count = i
        break
    actual_count = i + 1

print(f"B0 glyph count before zeros: {actual_count}")
print(f"Glyph range: 0x{min(b0_glyphs[:actual_count]):04X} - 0x{max(b0_glyphs[:actual_count]):04X}")

# Check what's after the glyph table - pointers
print(f"\nAfter glyph table (offsets 84-100):")
for i in range(84, min(120, len(b0_glyphs))):
    print(f"  [{i:3d}] 0x{b0_glyphs[i]:04X}")

# Now let's search for BUSIN 1's equivalent font descriptor table
# The B0 descriptors had a very specific structure:
# [width_packed:2][height_packed:2][0:4][0x80808080:4][0x01000100:4][0:4][0:4]
# BUSIN 1 does NOT have 0x80808080 in font descriptors - only in a fill block
# This means BUSIN 1 uses a DIFFERENT font descriptor format

# Let's try searching based on the fact that BUSIN 1 has a larger EXE
# and may have the font descriptors near the same relative position

# B0: descriptors at 0x3C0700, glyph table at 0x3C0870
# B0 EXE size: 0x3FDEB0, so relative offset from end: 0x3FDEB0 - 0x3C0700 = 0x3D7B0
# B1 EXE size: 0x4CE1A0, so equivalent in B1: 0x4CE1A0 - 0x3D7B0 = 0x4909F0?
# That's near end of file, let's check

b1_equiv = len(exe_data) - (len(b0_data) - 0x3C0700)
print(f"\nB1 equivalent by offset-from-end: 0x{b1_equiv:06X}")
if b1_equiv + 100 < len(exe_data):
    print("Data at that offset:")
    for i in range(5):
        off2 = b1_equiv + i * 28
        vals = struct.unpack("<7I", exe_data[off2:off2+28])
        print(f"  0x{off2:06X}: {' '.join(f'{v:08X}' for v in vals)}")

# Better approach: Search for the characteristic pattern of the font descriptor
# In B0: the second field's high word cycles through 0x10, 0x20, 0x30, 0x40
# (which are font height values), let's look for something similar in B1

# Actually, let me look at this from a completely different angle.
# The 0x498DC4 area from part 1 had interesting 28-byte structs:
# [0] 00000040 0000000C 00000000 0000003C 00000078 0000007F 00000040
# This has: width=64(0x40), height=12(0x0C), something, index=0x3C,
# x_pos=0x78, y_pos=0x7F, something=64

# Let's examine this area more carefully
print("\n\n=== BUSIN 1 potential font descriptors at 0x498D00 ===")
# First find the start of this array
off = 0x498D00
while off < 0x49A000:
    vals = struct.unpack("<7I", exe_data[off:off+28])
    # Look for the pattern start
    if vals[0] == 0x40 and (vals[1] in range(4, 20)):
        # Found a potential start
        # Back up to find the actual beginning
        test_off = off - 28
        while test_off > 0x498C00:
            tvals = struct.unpack("<7I", exe_data[test_off:test_off+28])
            if tvals[0] != 0x40:
                break
            test_off -= 28
        start_off = test_off + 28
        print(f"Array likely starts at 0x{start_off:06X}")

        # Dump entries
        entry_off = start_off
        for i in range(40):
            if entry_off + 28 > len(exe_data):
                break
            vals = struct.unpack("<7I", exe_data[entry_off:entry_off+28])
            if vals[0] == 0 and vals[1] == 0:
                print(f"  END at entry {i}")
                break
            print(f"  [{i:2d}] 0x{entry_off:06X}: w={vals[0]:3d} h={vals[1]:3d} "
                  f"v2={vals[2]:3d} idx={vals[3]:3d}(0x{vals[3]:02X}) "
                  f"v4={vals[4]:3d} v5={vals[5]:3d} v6={vals[6]:3d}")
            entry_off += 28
        break
    off += 4

# Now look earlier for smaller struct sizes
print("\n=== Search for font descriptor candidates near 0x490000-0x4A0000 ===")
# Font descriptors might be 12, 16, 20, 24, or 28 bytes
# Try different struct sizes
for struct_size in [12, 16, 20, 24, 28]:
    for off in range(0x490000, min(0x4A0000, len(exe_data) - struct_size * 3), 4):
        if struct_size == 28:
            vals = struct.unpack("<7I", exe_data[off:off+struct_size])
            # Font width 8-24 pixels, font height 10-32
            if 8 <= vals[0] <= 24 and 8 <= vals[1] <= 32 and vals[0] != vals[1]:
                vals2 = struct.unpack("<7I", exe_data[off+struct_size:off+struct_size*2])
                if 8 <= vals2[0] <= 24 and 8 <= vals2[1] <= 32:
                    vals3 = struct.unpack("<7I", exe_data[off+struct_size*2:off+struct_size*3])
                    if 8 <= vals3[0] <= 24 and 8 <= vals3[1] <= 32:
                        print(f"  28-byte candidate at 0x{off:06X}:")
                        for j in range(min(5, (len(exe_data) - off) // struct_size)):
                            v = struct.unpack("<7I", exe_data[off+j*struct_size:off+(j+1)*struct_size])
                            print(f"    [{j}] {' '.join(f'{x:08X}' for x in v)}")
                        break

# Let's also search the wider range with the B0-like structure
# B0 descriptors pack values as: (height << 16) | format  and  (row << 16) | col
# For B1, maybe the format is different
print("\n=== BUSIN 1: Looking for the 0x498DA4 area in detail ===")
off = 0x498D50
for i in range(30):
    vals = struct.unpack("<7I", exe_data[off:off+28])
    print(f"  0x{off:06X}: {vals[0]:4d} {vals[1]:4d} {vals[2]:4d} "
          f"{vals[3]:4d} {vals[4]:4d} {vals[5]:4d} {vals[6]:4d}")
    off += 28

# Now the most important question: what do the UEDA.MSG glyph indices mean?
# Are they the same as B0's encoding?
print("\n\n=== Cross-reference: B1 MSG glyph indices vs B0 glyph table ===")

# Parse all UEDA.MSG glyphs
b1_glyphs = []
i = 0
while i + 1 < len(msg_data):
    val = struct.unpack(">H", msg_data[i:i+2])[0]
    if val < 0xFF00:
        b1_glyphs.append(val)
    i += 2

b1_freq = Counter(b1_glyphs)

# Check how many of B1's top glyphs exist in B0's glyph table
b0_glyph_set = set(b0_glyphs[:actual_count])
print(f"B0 glyph table has {len(b0_glyph_set)} unique codes")
print(f"B1 UEDA.MSG uses {len(b1_freq)} unique glyph codes")

in_b0 = sum(1 for g in b1_freq if g in b0_glyph_set)
not_in_b0 = sum(1 for g in b1_freq if g not in b0_glyph_set)
print(f"B1 codes that exist in B0 table: {in_b0}")
print(f"B1 codes NOT in B0 table: {not_in_b0}")

# Show the B1 codes not in B0
print("\nB1 glyph codes NOT in B0 table (first 50):")
not_in_list = sorted(g for g in b1_freq if g not in b0_glyph_set)
for g in not_in_list[:50]:
    print(f"  0x{g:04X} ({g:5d}) count={b1_freq[g]}")

# And B1 codes that ARE in B0 table
print("\nB1 glyph codes that ARE in B0 table (by frequency):")
in_list = [(g, c) for g, c in b1_freq.most_common() if g in b0_glyph_set]
for g, c in in_list[:30]:
    # Find position in B0 table
    pos = b0_glyphs[:actual_count].index(g) if g in b0_glyphs[:actual_count] else -1
    label = ""
    if 0x20 <= g < 0x7F:
        label = f" = ASCII '{chr(g)}'"
    elif g < 0x20:
        label = f" = ctrl"
    print(f"  0x{g:04X} count={c:4d} (B0 table pos {pos:3d}){label}")

# Check: in the EXE embedded text, 0x0000 was used for space
# But in UEDA.MSG, 0x0040 ('@') is most frequent
# 0x0040 in B0's glyph table is at position 56
# In B0, glyph 0x40 = '@', but in the MSG context it might be a Japanese char

# Let's look at glyph codes 0x0100-0x02FF range - these are NOT ASCII
# They must be in a different character set (likely JIS/Shift-JIS derived)
print("\n\n=== Glyph code distribution summary ===")
ranges = [
    (0x0000, 0x001F, "Control/special"),
    (0x0020, 0x003F, "ASCII punctuation/digits"),
    (0x0040, 0x005F, "ASCII uppercase + @[\\]^_"),
    (0x0060, 0x007F, "ASCII lowercase + `{|}~"),
    (0x0080, 0x00FF, "Extended (likely hiragana)"),
    (0x0100, 0x01FF, "High (likely katakana/kanji start)"),
    (0x0200, 0x02FF, "High (likely kanji)"),
    (0x0300, 0x03FF, "High (kanji continued)"),
]
for lo, hi, label in ranges:
    codes = [(g, c) for g, c in b1_freq.items() if lo <= g <= hi]
    total = sum(c for _, c in codes)
    unique = len(codes)
    if unique > 0:
        top3 = sorted(codes, key=lambda x: -x[1])[:3]
        top3_str = ", ".join(f"0x{g:04X}({c})" for g, c in top3)
        print(f"  {label}: {unique} unique, {total} total, top: {top3_str}")

print("\nDone part 4.")
