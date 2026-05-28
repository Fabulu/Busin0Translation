#!/usr/bin/env python3
"""Create zoomed crops of R2121 to analyze pixel-level patterns."""
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

# Full linear image
img = Image.new('RGBA', (w, h))
img.putdata([colors[raw[j]] for j in range(pc)])

# Crop a 64x64 region from the middle and zoom 4x
for cx, cy, label in [(0, 0, 'topleft'), (256, 256, 'center'), (200, 400, 'lower')]:
    crop = img.crop((cx, cy, cx + 64, cy + 64))
    zoomed = crop.resize((256, 256), Image.NEAREST)
    zoomed.save(f'{BASE}/R2121_zoom_{label}.png')
    print(f'Saved R2121_zoom_{label}.png')

# Save 128x128 region at 2x to see the pattern
crop2 = img.crop((0, 0, 128, 128))
zoomed2 = crop2.resize((512, 512), Image.NEAREST)
zoomed2.save(f'{BASE}/R2121_zoom_topleft128.png')
print(f'Saved R2121_zoom_topleft128.png')

# Save the full image at 1:1
img.save(f'{BASE}/R2121_linear_full.png')
print(f'Saved R2121_linear_full.png')

print('Done!')
