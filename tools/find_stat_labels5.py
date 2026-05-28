import struct, json

gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# The chargen label table has clear context clues for glyph map corrections:
# Entry 11: glyphs 511,512 should be 性別 (gender) -> glyph 511 = 性 (not 果)
# Entry 12: glyphs 515,511 should be 属性 (attribute) -> glyph 515 = 属 (not 条)
# Entry 14: glyphs 511,516 should be 耐性 (resistance) -> glyph 511=耐? No...

# Wait, let me reconsider. The labels are:
# 性別 gender, 種族 race, 属性 attribute, 職業 class
# If glyph 511 maps to both positions 11 (X別) and 12 (属X) and 14 (X性):
# 11: 511+512 = ?+別 -> 性別 -> 511=性
# 12: 515+511 = ?+性 -> 属性 -> 515=属
# 14: 511+516 = 性+? -> this doesn't match a standard label...

# Actually looking at in-game: the chargen screen shows these labels.
# Let me check what glyph 516 currently maps to
print("Current glyph map entries:")
for gid in [504, 511, 512, 513, 514, 515, 516, 517]:
    ch = gmap.get(str(gid), '?')
    print(f"  Glyph {gid} = '{ch}'")

# Let me also decode entry 29 and 39 for more context
# 29: 人壁 - should be 人間 (human)?
# 39: 騎事持 - should be 騎士 (knight)?
# This suggests more glyph map errors
print("\nContext-based corrections needed:")
print("  Entry 29: 人壁 should be 人間 (human) -> glyph for 壁 might be 間")
print("  Entry 39: 騎事持 should be something like 騎士? (knight)")
print("  Entry 15: 騎事持騎法 -> likely 呪文 related")

# Check specific glyphs
for gid in [280, 342, 320, 308, 363, 458]:
    ch = gmap.get(str(gid), '?')
    print(f"  Glyph {gid} = '{ch}'")

# Let's look at the R38 header to understand the string table format
data = open('extracted/packdata_resources/0038_type01.bin', 'rb').read()
print(f"\nR38 header (first 16 entries of offset table):")
for i in range(0, 64, 4):
    offset = struct.unpack('>I', data[i:i+4])[0]
    print(f"  [{i//4:3d}] offset = {hex(offset)}")

# Count total entries in the offset table
# The first offset value tells us where strings start
first_offset = struct.unpack('>I', data[0:4])[0]
num_entries = first_offset // 4
print(f"\nFirst string offset: {hex(first_offset)}")
print(f"Estimated number of entries: {num_entries}")

# Decode ALL entries
print(f"\n=== ALL R38 string entries ===")
offsets = []
for i in range(0, first_offset, 4):
    offsets.append(struct.unpack('>I', data[i:i+4])[0])

for idx, off in enumerate(offsets):
    end = offsets[idx+1] if idx+1 < len(offsets) else len(data)
    entry = []
    pos = off
    while pos < end and pos < len(data) - 1:
        g = struct.unpack('>H', data[pos:pos+2])[0]
        pos += 2
        if g == 0xFFFE or g == 0xFFFF:
            continue
        ch = gmap.get(str(g), f'[{g}]')
        entry.append(ch)
    text = ''.join(entry)
    if idx < 80:  # only show first 80
        print(f"  [{idx:3d}] @{hex(off)}: {text}")
