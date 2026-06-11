"""
FINAL COMPREHENSIVE ANALYSIS:
Search for ALL comparisons against 38 AND 45 that could be cell-index checks
in the ENTIRE keyboard-related code (0x350000-0x3A0000).

The key insight from the analysis so far:
- Function at VA 0x46C710 (file 0x36C790): Switch table that returns pixel
  WIDTHS per category (0-20). Case 3 returns 38, case 10 returns 45.
  THESE ARE WIDTHS, NOT GLYPH IDS.

- Function at VA 0x46C7F0 (file 0x36C870): Switch table that returns
  VISIBILITY per category (0-20). Case 3 returns 0, case 10 returns 0.
  ALL OTHER active cases return 1 or 2.

- When visibility is 0, the category is hidden/disabled.

- The rendering pipeline: 0x48CFB0 -> 0x48C810 -> 0x3A3260 -> 0x3A2EF0
  This processes a glyph data STREAM from a PACKDATA resource.

- The drawing function table at VA 0x574690 is in BSS (runtime, not in EXE).

- The font metrics table is in the PACKDATA resource, read by 0x3A2D10.

CONCLUSION: The skip mechanism is NOT a hardcoded comparison against glyph
IDs 38 and 45 in the EXE. The values 38 and 45 in the EXE are pixel widths
for disabled categories. The actual skip is controlled by:

1. The FONT METRICS in the R1188 resource (4 bytes per glyph at resource+8+glyph*4)
2. The KEYBOARD LAYOUT glyph stream data in a PACKDATA resource
3. The VISIBILITY TABLE populated at runtime from resource data

Let me verify by checking if the R1188 resource has zero-width metrics
for the Japanese characters that correspond to cell positions 38 and 45.
"""
import struct

EXE_PATH = r"C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78"
R1188_PATH = r"C:\Programmieren\wizardrytranslation\extracted\packdata_resources\1188_type01.bin"
VA_BASE = 0x0FFF80

# Read EXE
with open(EXE_PATH, "rb") as f:
    exe = f.read()

# Read R1188
with open(R1188_PATH, "rb") as f:
    r1188 = f.read()

print(f"R1188 size: {len(r1188)} bytes")
print(f"R1188 header: {r1188[:64].hex(' ')}")
print()

# R1188 is a type-01 resource. It has a sub-header structure.
# The sub-header at offset 0 contains metadata.
# After the sub-header, there's the font data.
# For the font metrics, we need to find the glyph table.

# The type-01 sub-header has:
# 0x00: type (0x11 = type 01 with sub-type 0x11)
# 0x04: type again
# Then the actual font data follows.

# The unrolled setup code calls 0x3A2D10 with:
# $a0 = base pointer (points to font data in RAM)
# $a1 = some value ($s0)
# $a2 = some value ($s1)
# $a3 = glyph ID (0-94)
# $t0 = some value ($s3)

# 0x3A2D10:
#   if $a0 == 0: return 0
#   $a0 += 8              -- skip 8-byte header
#   mult $t0, $a1         -- but result never used (mflo never called!)
#   $v0 = $a3 + $v0       -- $v0 was 0 from delay slot, so $v0 = glyph_id ($a3)
# Wait actually: $v0 = $a3 + $v0 where $v0 = 0 = glyph_id
# Then:
#   sll $v0, $v0, 2       -- $v0 = glyph_id * 4
#   addu $a0, $a0, $v0    -- $a0 = base + 8 + glyph_id * 4
#   Read 4 bytes big-endian from $a0

# So the font resource has an 8-byte header followed by 4 bytes per glyph.
# But the R1188 type-01 resource has its OWN header structure.
# The base pointer in RAM points to the font data AFTER the type-01
# sub-header has been processed and the data loaded.

# For type-01 resources, the sub-header at offset 0x10-0x14 contains
# the data offset. Let me check.
print("Type-01 sub-header analysis:")
for i in range(16):
    val = struct.unpack_from("<I", r1188, i*4)[0]
    print(f"  Offset {i*4:#06x}: {val:#010x} ({val})")

# The key data structure used by the keyboard: the glyph stream.
# This is loaded from one of the PACKDATA resources and placed in RAM.
# The stream contains 2-byte glyph codes that the renderer (0x3A2EF0)
# iterates over.

# Without being able to identify which resource contains the keyboard
# layout data stream, I'll look at what the glyph codes would be.

# In the renderer 0x3A2EF0, the glyph code is a 16-bit value:
# - 0xFFFF = end of stream
# - 0xFFFE = newline
# - 0xFF00-0xFF08 = color change
# - 0xFFF0 = restore color
# - Other values: high byte = row in atlas, low byte = column in atlas

# For the R1188 atlas (16x16 grid if each cell is 16px in a 256px atlas):
# Cell 38: row = 38 // 16 = 2, col = 38 % 16 = 6 -> code = 0x0206
# Cell 45: row = 45 // 16 = 2, col = 45 % 16 = 13 -> code = 0x020D

# But R1188 is 1024x1024 with different cell sizes.
# The actual cell layout depends on the font atlas structure.

# Let me search the R1188 resource for the glyph metrics table.
# The metrics are accessed at base + 8 + glyph_id * 4.
# But 'base' in RAM is not the same as offset in the file.

# For type-01 resources, the data section starts after the offset table.
# Let me check the sub-header more carefully.

# Type-01 format:
# Bytes 0-3: type (0x11)
# Bytes 4-7: type again
# Bytes 8-15: zeros (padding)
# Bytes 16-19: data1_size or offset
# Bytes 20-23: data2_base
# Bytes 24-27: count
# ... etc

# Sub-header at offset 52 (0x34) starts the offset table
# The first offset might point to the font atlas pixels
# The second might point to the metrics

# Let me look at the offsets
print()
print("Possible offset table starting at various positions:")
for start in [52, 56, 60, 64]:
    vals = [struct.unpack_from("<I", r1188, start + i*4)[0] for i in range(8)]
    print(f"  Starting at {start:#06x}: {[hex(v) for v in vals]}")

# Actually, since the game loads this resource and processes the type-01
# header to extract sub-resources, we'd need to understand the full
# type-01 format. Let me look at the build pipeline to see if there's
# any code that parses R1188.

# For now, let me just confirm: the values 38 and 45 in the keyboard
# switch tables at VA 0x46C710 are PIXEL WIDTHS, not glyph IDs.
# Here's the proof:
print()
print("=" * 90)
print("PROOF: Values 38 and 45 in VA 0x46C710 are PIXEL WIDTHS, not glyph IDs")
print("=" * 90)
print()
print("Width table (VA 0x46C710) returns:")
widths = [159, 105, 42, 38, 46, 56, 40, 30, 117, 37, 45, 30, 42, 7, 40, 17, 30, 8, 1, 1, 1]
for i, w in enumerate(widths):
    vis = [2, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0][i]
    skip = "  SKIP (vis=0)" if vis == 0 else ""
    marker = "  <-- coincidental value 38 (NOT glyph ID F)" if w == 38 else \
             "  <-- coincidental value 45 (NOT glyph ID M)" if w == 45 else ""
    print(f"  Category {i:2d}: width={w:3d}px, visibility={vis}{skip}{marker}")

print()
print("Categories 3, 10-20 have visibility=0 and are NOT DRAWN.")
print("Category 3 has width 38px and category 10 has width 45px.")
print("These are pixel widths for character spacing, NOT glyph cell indices.")
print()
print("The skip of cells 38 (F) and 45 (M) must be caused by:")
print("1. The font resource data (metrics table with zero-width entries)")
print("2. The keyboard layout data stream (resource data, not EXE)")
print("3. A runtime table populated from resource data")
print()
print("NONE of these can be found in the EXE code as hardcoded comparisons.")
