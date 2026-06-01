"""
R1188 Fill Test: Fill the ENTIRE atlas pixel area with 0x88 (solid blocks).

If chargen stat labels become solid blocks -> R1188 IS the source.
If they still show normally -> R1188 is NOT the source.

R1188 layout:
  - 3072-byte header (0x000 - 0xBFF)
  - 524,288 bytes of 4bpp pixel data (0xC00 - 0x80BFF)
  - Total: 528,384 bytes -> 258 sectors (528,384 bytes)

We fill all pixel bytes with 0x88 so every nibble = 8 (mid-gray solid).
"""

import os, math

SECTOR = 2048
SRC = 'C:/Programmieren/wizardrytranslation/extracted/packdata_raw/1188_type01.raw'
DST = 'C:/Programmieren/wizardrytranslation/build/packdata_resources/1188_type01.raw'

data = bytearray(open(SRC, 'rb').read())
print(f'Read {len(data)} bytes from R1188')

HEADER_SIZE = 3072  # 0xC00
PIXEL_SIZE = 524288  # 0x80000 = 512 KiB

assert len(data) >= HEADER_SIZE + PIXEL_SIZE, f'File too small: {len(data)}'

# Preserve header, fill all pixels with 0x88
header = data[:HEADER_SIZE]
pixels = b'\x88' * PIXEL_SIZE

result = bytearray(header + pixels)

# Pad to sector boundary
sc = math.ceil(len(result) / SECTOR)
if len(result) < sc * SECTOR:
    result += b'\x00' * (sc * SECTOR - len(result))

os.makedirs(os.path.dirname(DST), exist_ok=True)
open(DST, 'wb').write(result)

print(f'Wrote {len(result)} bytes to {DST}')
print(f'Header: {HEADER_SIZE} bytes preserved')
print(f'Pixels: {PIXEL_SIZE} bytes filled with 0x88')
print(f'Sectors: {sc}')
print()
print('Next: run rebuild_packdata.py then build ISO')
