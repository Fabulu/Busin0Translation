#!/usr/bin/env python3
"""Check whether glyph 851 and 766 appear in R1193."""
import struct, sys
sys.stdout.reconfigure(encoding='utf-8')
data = open('C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1193_type02.raw', 'rb').read()

for gid in [851, 766, 1186, 684, 337]:
    target = struct.pack('>H', gid)
    pos = data.find(target)
    positions = []
    while pos >= 0:
        positions.append(pos)
        pos = data.find(target, pos + 1)
    print(f"Glyph {gid} (0x{gid:04X}): found at {len(positions)} positions: {positions[:10]}")

# Also: the byte pair 0x0353 0x02FE
pair = struct.pack('>HH', 851, 766)
pos = data.find(pair)
print(f"\nByte pair 0x0353+0x02FE: {'found at ' + str(pos) if pos >= 0 else 'NOT FOUND'}")
