#!/usr/bin/env python3
"""Split R2121 into even and odd rows to analyze the interleaving pattern."""
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE = 'C:/Programmieren/wizardrytranslation/build/textures_to_edit'
data = open(f'{BASE}/R2121_guild_background.raw', 'rb').read()
tex = data[16:]
raw = tex[272:]
w, h = 512, 512
pc = w * h

pal_bytes = raw[pc:pc + 1024]
colors = []
for i in range(256):
    off = i * 4
    r, g, b, a = pal_bytes[off], pal_bytes[off + 1], pal_bytes[off + 2], pal_bytes[off + 3]
    colors.append((r, g, b, min(a * 2, 255)))
for grp in range(8):
    base = grp * 32
    for j in range(8):
        colors[base + 8 + j], colors[base + 16 + j] = \
            colors[base + 16 + j], colors[base + 8 + j]

# Even rows only (stretched to full height)
even_img = Image.new('RGBA', (w, h // 2))
even_px = []
for y in range(0, h, 2):
    for x in range(w):
        even_px.append(colors[raw[y * w + x]])
even_img.putdata(even_px)
even_img.save(f'{BASE}/R2121_even_rows.png')
print('Saved R2121_even_rows.png')

# Odd rows only
odd_img = Image.new('RGBA', (w, h // 2))
odd_px = []
for y in range(1, h, 2):
    for x in range(w):
        odd_px.append(colors[raw[y * w + x]])
odd_img.putdata(odd_px)
odd_img.save(f'{BASE}/R2121_odd_rows.png')
print('Saved R2121_odd_rows.png')

# Also do R2122
data2 = open(f'{BASE}/R2122_guild_buttons.raw', 'rb').read()
tex2 = data2[16:]
raw2 = tex2[272:]
w2, h2 = 512, 64
pc2 = w2 * h2
pal2 = raw2[pc2:pc2 + 1024]
colors2 = []
for i in range(256):
    off = i * 4
    r, g, b, a = pal2[off], pal2[off + 1], pal2[off + 2], pal2[off + 3]
    colors2.append((r, g, b, min(a * 2, 255)))
for grp in range(8):
    base = grp * 32
    for j in range(8):
        colors2[base + 8 + j], colors2[base + 16 + j] = \
            colors2[base + 16 + j], colors2[base + 8 + j]

even2 = Image.new('RGBA', (w2, h2 // 2))
ep2 = []
for y in range(0, h2, 2):
    for x in range(w2):
        ep2.append(colors2[raw2[y * w2 + x]])
even2.putdata(ep2)
even2.save(f'{BASE}/R2122_even_rows.png')
print('Saved R2122_even_rows.png')

odd2 = Image.new('RGBA', (w2, h2 // 2))
op2 = []
for y in range(1, h2, 2):
    for x in range(w2):
        op2.append(colors2[raw2[y * w2 + x]])
odd2.putdata(op2)
odd2.save(f'{BASE}/R2122_odd_rows.png')
print('Saved R2122_odd_rows.png')

print('Done!')
