#!/usr/bin/env python3
"""Try various row reordering patterns to fix R2121 display."""
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE = 'C:/Programmieren/wizardrytranslation/build/textures_to_edit'

data = open(f'{BASE}/R2121_guild_background.raw', 'rb').read()
tex = data[16:]
raw = tex[272:]
w, h = 512, 512
pc = w * h

# Palette
pal_bytes = raw[pc:pc+1024]
colors = []
for i in range(256):
    off = i * 4
    r, g, b, a = pal_bytes[off], pal_bytes[off+1], pal_bytes[off+2], pal_bytes[off+3]
    colors.append((r, g, b, min(a * 2, 255)))
for grp in range(8):
    base = grp * 32
    for j in range(8):
        colors[base + 8 + j], colors[base + 16 + j] = \
            colors[base + 16 + j], colors[base + 8 + j]

def render(name, remap_func):
    img = Image.new('RGBA', (w, h))
    px = []
    for y in range(h):
        src_y = remap_func(y)
        src_y = max(0, min(h - 1, src_y))
        for x in range(w):
            idx = src_y * w + x
            if idx < len(raw):
                px.append(colors[raw[idx]])
            else:
                px.append((0, 0, 0, 0))
    img.putdata(px)
    img.save(f'{BASE}/R2121_{name}.png')
    print(f'Saved R2121_{name}.png')

# Within each 4-row group, swap rows 1 and 2: output row order 0,2,1,3
render('swap12_in4', lambda y: (y // 4) * 4 + [0, 2, 1, 3][y % 4])

# Swap pairs: output y gets data from y^1
render('pair_swap', lambda y: y ^ 1)

# Interleave: even rows come from rows 0,2,4,...; odd from 1,3,5,...
render('interleave', lambda y: y * 2 if y < h // 2 else (y - h // 2) * 2 + 1)

# Reverse interleave: output row y comes from source y//2 or h//2 + y//2
render('rev_interleave', lambda y: y // 2 if y % 2 == 0 else h // 2 + y // 2)

# Within each 2-row group: read row 1 then row 0
# (source data has pairs stored in reverse)
render('pair_rev', lambda y: (y // 2) * 2 + (1 - y % 2))

# Within each 16-row block, interleave:
# Read as: 0,8,1,9,2,10,3,11,4,12,5,13,6,14,7,15 within each block
def remap_16(y):
    block = y // 16
    sub = y % 16
    if sub < 8:
        return block * 16 + sub * 2
    else:
        return block * 16 + (sub - 8) * 2 + 1
render('interleave16', remap_16)

# Within each 4-row block, interleave:
# 0,2,1,3 -> straighten to 0,1,2,3
# Source rows 0,1,2,3 map to output rows 0,2,1,3
# So output row 0 <- src 0, output row 1 <- src 2, output row 2 <- src 1, output row 3 <- src 3
render('straighten4', lambda y: (y // 4) * 4 + [0, 2, 1, 3][y % 4])

# 8-row interleave
def remap_8(y):
    block = y // 8
    sub = y % 8
    if sub < 4:
        return block * 8 + sub * 2
    else:
        return block * 8 + (sub - 4) * 2 + 1
render('interleave8', remap_8)

print("Done!")
