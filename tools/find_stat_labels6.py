import struct, json

gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
data = open('extracted/packdata_resources/0038_type01.bin', 'rb').read()

# Header is little-endian uint32 offsets
print(f"R38 size: {len(data)} bytes")
print(f"R38 header (LE uint32 offsets):")
for i in range(0, 64, 4):
    offset = struct.unpack('<I', data[i:i+4])[0]
    print(f"  [{i//4:3d}] offset = {hex(offset)} ({offset})")

first_offset = struct.unpack('<I', data[0:4])[0]
num_entries = first_offset // 4
print(f"\nFirst string offset: {hex(first_offset)} = {first_offset}")
print(f"Number of entries: {num_entries}")

# Read all offsets
offsets = []
for i in range(0, first_offset, 4):
    offsets.append(struct.unpack('<I', data[i:i+4])[0])

# Decode all entries
print(f"\n=== ALL R38 string entries ({len(offsets)} total) ===")
for idx in range(len(offsets)):
    off = offsets[idx]
    # Find end: next offset or end of file
    end = offsets[idx+1] if idx+1 < len(offsets) else len(data)
    entry = []
    pos = off
    while pos < end and pos < len(data) - 1:
        g = struct.unpack('>H', data[pos:pos+2])[0]
        pos += 2
        if g == 0xFFFE:
            entry.append('[NL]')
        elif g == 0xFFFF:
            entry.append('[END]')
        else:
            ch = gmap.get(str(g), f'[{g}]')
            entry.append(ch)
    text = ''.join(entry)
    print(f"  [{idx:3d}] @{hex(off)}: {text}")
