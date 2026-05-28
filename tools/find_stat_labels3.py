import struct, json

gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# Decode R38 around the stat label area (around offset 0x300)
data = open('extracted/packdata_resources/0038_type01.bin', 'rb').read()

print("=== R38 decoded glyphs around stat label area (0x2F0 - 0x400) ===")
for i in range(0x2F0, min(0x400, len(data)), 2):
    g = struct.unpack('>H', data[i:i+2])[0]
    ch = gmap.get(str(g), None)
    if g == 0xFFFE:
        ch = '[NL]'
    elif g == 0xFFFF:
        ch = '[END]'
    elif ch is None:
        ch = f'[{g:04x}]'
    if i % 32 == 0:
        print(f'\n  {i:04x}: ', end='')
    print(ch, end='')
print()

# Now decode the area around 0x360 where 性別/種族/属性/職業 were found
print("\n=== R38 decoded around 0x340 - 0x3C0 ===")
for i in range(0x340, min(0x3C0, len(data)), 2):
    g = struct.unpack('>H', data[i:i+2])[0]
    ch = gmap.get(str(g), None)
    if g == 0xFFFE:
        ch = '[NL]'
    elif g == 0xFFFF:
        ch = '[END]'
    elif ch is None:
        ch = f'[{g:04x}]'
    if i % 32 == 0:
        print(f'\n  {i:04x}: ', end='')
    print(ch, end='')
print()

# Show the raw hex for 0x300-0x380 to see actual glyph IDs
print("\n=== R38 raw hex 0x300 - 0x380 ===")
for i in range(0x300, 0x380, 2):
    g = struct.unpack('>H', data[i:i+2])[0]
    ch = gmap.get(str(g), f'?{g}')
    print(f"  {i:04x}: {g:04x} ({g:5d}) = {ch}")

# Check: the first search found 信仰心 via context but not via direct search
# Let me check what glyph IDs are actually at the 信仰心 position
print("\n=== Checking what's actually at the area showing 信仰心 ===")
# From context, 知恵 was at 0x312, so 信仰心 should be nearby
pos = 0x312
while pos < 0x360:
    g = struct.unpack('>H', data[pos:pos+2])[0]
    ch = gmap.get(str(g), f'[{g}]')
    print(f"  {pos:04x}: glyph {g} = {ch}")
    pos += 2
