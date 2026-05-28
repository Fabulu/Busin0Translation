import struct, json

gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# Check for duplicate characters in glyph map
dupes = {}
for k, v in gmap.items():
    if v not in dupes:
        dupes[v] = []
    dupes[v].append(int(k))

# Show duplicates for our key characters
key_chars = list('信心力種生命')
for ch in key_chars:
    if ch in dupes and len(dupes[ch]) > 1:
        print(f"  '{ch}' has multiple glyph IDs: {dupes[ch]}")
    elif ch in dupes:
        print(f"  '{ch}' has single glyph ID: {dupes[ch]}")
    else:
        print(f"  '{ch}' NOT in glyph map")

# Now let's verify what we found. R38 has ALL the chargen stat labels.
# Let me decode the full chargen label table
data = open('extracted/packdata_resources/0038_type01.bin', 'rb').read()

print("\n=== Complete chargen label table from R38 (0x2F0 - 0x4E0) ===")
# Parse as string table: each entry is terminated by FFFE FFFF
pos = 0x2F0
idx = 0
while pos < 0x4E0:
    entry = []
    while pos < len(data):
        g = struct.unpack('>H', data[pos:pos+2])[0]
        pos += 2
        if g == 0xFFFE:
            break
        ch = gmap.get(str(g), f'[{g}]')
        entry.append(ch)
    # skip FFFF
    if pos < len(data):
        g2 = struct.unpack('>H', data[pos:pos+2])[0]
        if g2 == 0xFFFF:
            pos += 2
    text = ''.join(entry)
    if text:
        print(f"  [{idx:3d}] {text}")
        idx += 1

# Also check what 果別, 条果, 果性 should be
print("\n=== Glyph map check for suspicious chars ===")
for gid in [511, 512, 515, 516]:
    ch = gmap.get(str(gid), '?')
    print(f"  Glyph {gid} = '{ch}'")

# Check: is 果 really the right mapping for glyph 511?
# 果別 should be 性別 (gender), 条果 should be 属性 (attribute)
# So glyph 511=果 might actually be 性, and 515=条 might be 属
print("\n=== Possible glyph map errors ===")
print("  R38 says glyph 511 + 512 = 果別, but context suggests 性別 (gender)")
print("  R38 says glyph 515 + 511 = 条果, but context suggests 属性 (attribute)")
print("  R38 says glyph 511 + 516 = 果性, but this doesn't make sense")
print("  So glyph 511 mapping might be wrong in the glyph map")
