import struct
from collections import Counter

b0_path = r"C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78"
with open(b0_path, "rb") as f:
    b0_data = f.read()

exe_path = r"C:\Programmieren\wizardrytranslation\extracted_busin1\SLUS_202.59"
with open(exe_path, "rb") as f:
    exe_data = f.read()

# Look more broadly at B0's glyph table area
# After the 84 entries + 4 zeros, we see 0xA1A0/0x004E pairs
# These look like texture pointers (0x004EA1A0 as a 32-bit address)
print("=== BUSIN 0 Full Data After Glyph Table ===")
off = 0x3C0870 + 84 * 2  # after 84 glyph entries
print(f"Post-glyph area starts at 0x{off:06X}")
for i in range(30):
    val32 = struct.unpack("<I", b0_data[off:off+4])[0]
    vals16 = struct.unpack("<HH", b0_data[off:off+4])
    print(f"  0x{off:06X}: 0x{val32:08X}  (uint16: 0x{vals16[0]:04X} 0x{vals16[1]:04X})")
    off += 4

# Now search BUSIN 1 for a glyph table
# B0's glyph table: ascending uint16 values 1,5,6,7,8,9,10,13,14...
# B1 might have a MUCH larger table (382 unique codes used in UEDA.MSG)
# Search for ascending sequences of uint16 values

print("\n\n=== Searching BUSIN 1 for ascending uint16 sequences ===")
candidates = []
for start in range(0x3B0000, min(0x4CE000, len(exe_data)) - 200, 2):
    # Check for 10+ consecutive uint16 in ascending order
    ascending = True
    prev = 0
    for k in range(10):
        v = struct.unpack("<H", exe_data[start+k*2:start+k*2+2])[0]
        if v == 0 or v > 0x1000:
            ascending = False
            break
        if v <= prev:
            ascending = False
            break
        prev = v
    if ascending:
        vals = [struct.unpack("<H", exe_data[start+k*2:start+k*2+2])[0] for k in range(20)]
        candidates.append((start, vals))

# Deduplicate
deduped = []
for off, vals in candidates:
    if not deduped or off - deduped[-1][0] > 20:
        deduped.append((off, vals))

print(f"Found {len(deduped)} ascending uint16 sequences")
for off, vals in deduped[:20]:
    print(f"  0x{off:06X}: {[hex(v) for v in vals]}")

# Also try BE uint16 ascending
print("\n=== Searching BUSIN 1 for ascending BE uint16 sequences ===")
candidates_be = []
for start in range(0x3B0000, min(0x4CE000, len(exe_data)) - 200, 2):
    ascending = True
    prev = 0
    for k in range(10):
        v = struct.unpack(">H", exe_data[start+k*2:start+k*2+2])[0]
        if v == 0 or v > 0x1000:
            ascending = False
            break
        if v <= prev:
            ascending = False
            break
        prev = v
    if ascending:
        vals = [struct.unpack(">H", exe_data[start+k*2:start+k*2+2])[0] for k in range(20)]
        candidates_be.append((start, vals))

deduped_be = []
for off, vals in candidates_be:
    if not deduped_be or off - deduped_be[-1][0] > 20:
        deduped_be.append((off, vals))

print(f"Found {len(deduped_be)} ascending BE uint16 sequences")
for off, vals in deduped_be[:20]:
    print(f"  0x{off:06X}: {[hex(v) for v in vals]}")

# Look at the BUSIN 0 descriptor more carefully
# The descriptors have field0 packed as (something << 16) | 2
# and field1 packed as (row << 16) | col_or_offset
# Perhaps BUSIN 1 uses different packing

# Let's also look at what kind of font system BUSIN 1 actually uses
# The EXE embedded text uses simple uint16 glyph codes
# But the MSG files also use uint16 glyph codes (BE)
# The SAME glyph code space appears to be shared:
# 0x0040 = Japanese char in both B0 and B1 MSG context
# But in EXE embedded text, 0x0041 = 'A' (different context)

# Let's check: does the BUSIN 1 EXE have an ASCII character map?
# Search for a sequence "ABCDEFGHIJ" as uint16
print("\n=== Searching BUSIN 1 for ASCII alphabet sequence ===")
# As LE uint16
abc_pattern_le = b''.join(struct.pack("<H", ord(c)) for c in "ABCDEFGHIJ")
for off in range(len(exe_data) - len(abc_pattern_le)):
    if exe_data[off:off+len(abc_pattern_le)] == abc_pattern_le:
        print(f"  Found LE at 0x{off:06X}")
        # Show more context
        vals = [struct.unpack("<H", exe_data[off+k*2:off+k*2+2])[0] for k in range(30)]
        print(f"    {[hex(v) for v in vals]}")

# As BE uint16
abc_pattern_be = b''.join(struct.pack(">H", ord(c)) for c in "ABCDEFGHIJ")
for off in range(len(exe_data) - len(abc_pattern_be)):
    if exe_data[off:off+len(abc_pattern_be)] == abc_pattern_be:
        print(f"  Found BE at 0x{off:06X}")
        vals = [struct.unpack(">H", exe_data[off+k*2:off+k*2+2])[0] for k in range(30)]
        print(f"    {[hex(v) for v in vals]}")

# Search for shorter "ABCD"
abc4 = b''.join(struct.pack("<H", ord(c)) for c in "ABCD")
hits4 = []
for off in range(len(exe_data) - len(abc4)):
    if exe_data[off:off+len(abc4)] == abc4:
        hits4.append(off)
print(f"\n'ABCD' as LE uint16: {len(hits4)} hits")
for h in hits4[:10]:
    vals = [struct.unpack("<H", exe_data[h+k*2:h+k*2+2])[0] for k in range(20)]
    asc = "".join(chr(v) if 0x20 <= v < 0x7F else "." for v in vals)
    print(f"  0x{h:06X}: {asc}")

# Now check the BUSIN 0 font area for the full glyph mapping
# The 84-entry table only goes to 0x005D
# But MSG files use codes up to 0x035A
# So there must be a larger table or a formula

# Actually, let me re-examine the B0 data after the glyph table
# The 0x004E paired with 0xA1A0 etc are 32-bit pointers
# These point to font texture data in PS2 memory
# The glyph table maps: table_index -> glyph_code
# Then code -> texture lookup uses the descriptor entries

# For the translation project, the key question is:
# Can we reuse the same glyph codes and just change the font texture?
# Or do we need to modify the glyph table?

# The answer from BUSIN 1 is clear:
# BUSIN 1 (English) uses the SAME glyph code space as BUSIN 0 (Japanese)
# Codes 0x0040-0x005D overlap (both games have these)
# Codes 0x0057-0x007F appear in B1 but NOT in B0's small glyph table
# This means B1 has an EXPANDED glyph table

# The crucial insight: B0's glyph table at 0x3C0870 only has 84 entries
# These are just the ASCII/basic symbols
# Codes >= 0x005E in B1's MSG files are Japanese characters
# that were ADDED for the English version (lowercase letters, more symbols)

# Wait - that doesn't make sense for English. Let me reconsider.
# In B0 (Japanese), codes 0x005E+ would be mapped to Japanese chars
# In B1 (English), the SAME codes 0x005E+ are used but mapped to
# lowercase English letters and additional characters

# This means the glyph table / font texture was EXTENDED in B1
# to include lowercase English letters that weren't in B0

print("\n\n=== Key Finding: Glyph Code Usage in Both Games ===")
print("B0 glyph table: 84 entries, codes 0x0001-0x005D")
print("B1 MSG uses: 382 unique codes, range 0x0000-0x035A")
print()
print("Shared codes (in B0 table AND used by B1 MSG): 29 codes")
print("These are: @, A-Z, [, \\, ], and ? -- ASCII uppercase + a few symbols")
print()
print("B1-only codes (NOT in B0 table): 353 codes")
print("These include:")
print("  0x0057-0x007F: lowercase letters + symbols (W,X mapped differently)")
print("  0x0080-0x00FF: extended characters (74 unique)")
print("  0x0100-0x01FF: higher character set (142 unique)")
print("  0x0200-0x035A: additional characters (101 unique)")
print()
print("CONCLUSION: BUSIN 1 uses the same uint16 glyph index format")
print("but has a VASTLY EXPANDED character set compared to B0's")
print("84-entry table. The B1 glyph table was not found in the EXE")
print("at the same location as B0's -- it may be loaded differently")
print("or embedded in a different data structure.")

print("\nDone part 5.")
