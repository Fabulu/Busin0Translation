"""Analyze pristine R39 block2 spell-description cell counts (the box budget)."""
import struct

PRISTINE = 'C:/programmieren/wizardrytranslation/extracted/packdata_raw/0039_type15.raw'
raw = open(PRISTINE, 'rb').read()

# header
header = []
for i in range(15):
    idx, size, off, z = struct.unpack_from('<4I', raw, i*16)
    header.append((idx, size, off, z))
B2_OFF = header[2][2]
B2_SIZE = header[2][1]
block2 = raw[B2_OFF:B2_OFF+B2_SIZE]

# split records on 0xFFFF
recs = []
cur = []
pos = 0
n = len(block2)
while pos+1 < n:
    w = struct.unpack_from('>H', block2, pos)[0]
    if w == 0xFFFF:
        recs.append(cur); cur = []
    else:
        cur.append(w)
    pos += 2

print(f"block2 off={B2_OFF} size={B2_SIZE} records={len(recs)}")
print()
# g# = index+1. spell descriptions g3..g58 = recs[2..57]
# count cells, also count line-break cells 0xFFFE and the per-line max
for g in range(1, len(recs)+1):
    r = recs[g-1]
    cells = len(r)
    # split into lines at 0xFFFE
    lines = []
    cur_line = 0
    for c in r:
        if c == 0xFFFE:
            lines.append(cur_line); cur_line = 0
        else:
            cur_line += 1
    lines.append(cur_line)
    nbreaks = r.count(0xFFFE)
    maxline = max(lines) if lines else 0
    if 3 <= g <= 58:
        print(f"g{g:2d}: cells={cells:3d} lines={len(lines)} maxline={maxline:3d} breaks={nbreaks} per_line={lines}")
