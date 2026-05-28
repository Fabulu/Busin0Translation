#!/usr/bin/env python3
"""Find all PACKDATA resources with TextEventImage data (magic 13131313)."""
import struct, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'C:/Programmieren/wizardrytranslation'
manifest = json.load(open(f'{BASE}/extracted/packdata_resources/manifest.json'))

# Search for resources whose Section 2 starts with 13131313 (TextEvent marker)
textevent_resources = []

for r in manifest:
    idx = r.get('index', -1)
    tc = r.get('type_code', 0)
    if tc == 0 or idx < 0:
        continue
    rawfile = f"{BASE}/extracted/packdata_raw/{idx}_type{tc:02d}.raw"
    if not os.path.exists(rawfile):
        continue

    data = open(rawfile, 'rb').read()
    if len(data) < 0x20:
        continue

    # Only type-02 has section2
    if tc == 2 and len(data) >= 0x20:
        s2o = struct.unpack_from('<I', data, 24)[0]
        s2t = struct.unpack_from('<I', data, 20)[0]
        if s2o + 4 <= len(data):
            magic = data[s2o:s2o+4]
            if magic == b'\x13\x13\x13\x13':
                count = struct.unpack_from('<H', data, s2o+6)[0]
                textevent_resources.append({
                    'index': idx,
                    'size': len(data),
                    's2_offset': s2o,
                    's2_size': s2t,
                    's1_size': s2o - 0x20,
                    'count': count,
                })

    # Also check first 4 bytes of payload
    if data[0x20:0x24] == b'\x13\x13\x13\x13':
        if idx not in [t['index'] for t in textevent_resources]:
            textevent_resources.append({
                'index': idx,
                'size': len(data),
                's2_offset': 'n/a (in S1)',
                's2_size': 'n/a',
                's1_size': 'n/a',
                'count': struct.unpack_from('<H', data, 0x26)[0] if len(data) > 0x26 else '?',
                'note': 'magic in S1'
            })

print(f"=== Resources with TextEventImage marker (13131313) ===")
print(f"Found: {len(textevent_resources)}")
print()
for t in sorted(textevent_resources, key=lambda x: x['index']):
    print(f"R{t['index']:4d}: total={t['size']:7d}  S1={t.get('s1_size','?'):>7}  S2_off=0x{t['s2_offset']:X}  S2_size={t.get('s2_size','?'):>7}  items={t['count']}")

# Also search all resources for the 13131313 magic anywhere
print()
print("=== Broader search: 13131313 magic at ANY offset ===")
for r in manifest:
    idx = r.get('index', -1)
    tc = r.get('type_code', 0)
    if tc == 0 or idx < 0:
        continue
    rawfile = f"{BASE}/extracted/packdata_raw/{idx}_type{tc:02d}.raw"
    if not os.path.exists(rawfile):
        continue
    data = open(rawfile, 'rb').read()
    positions = []
    for i in range(0, len(data) - 4, 4):
        if data[i:i+4] == b'\x13\x13\x13\x13':
            positions.append(i)
    if positions and idx not in [t['index'] for t in textevent_resources]:
        print(f"R{idx}: magic at offsets {[f'0x{p:X}' for p in positions[:5]]}")
