#!/usr/bin/env python3
import zipfile, numpy as np, sys
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')

z = zipfile.ZipFile('C:/Programmieren/wizardrytranslation/RAMdumps/intro.p2s', 'r')
gs = z.read('GS.bin')
print(f'GS.bin: {len(gs)} bytes')
header = len(gs) - 4*1024*1024
print(f'Header: {header} bytes')
vram = gs[header:]
print(f'VRAM: {len(vram)} bytes')

# Render as 1024x1024 RGBA (standard PS2 VRAM layout for 32bpp)
arr = np.frombuffer(vram[:1024*1024*4], dtype=np.uint8).reshape(1024, 1024, 4)
img = Image.fromarray(arr[:,:,:3], 'RGB')
img.save('C:/Programmieren/wizardrytranslation/dumps/textevent/intro_vram.png')
print('Saved intro_vram.png')

# Also save just alpha channel
alpha = arr[:,:,3]
Image.fromarray(alpha, 'L').save('C:/Programmieren/wizardrytranslation/dumps/textevent/intro_vram_alpha.png')
print('Saved intro_vram_alpha.png')

# Also render sub-regions where text textures might be
# The GS address FB7C from R1192 - convert to VRAM coordinates
# For 32bpp: address in 256-byte units = page * 8192
# FB7C * 256 = 0xFB7C00 = way bigger than 4MB VRAM
# So FB7C is not a 256-byte unit address

# Actually PS2 GS addresses are in 32-bit words (4 bytes)
# So FB7C * 4 = 0x3EDEF0... still too big

# Or FB7C might be a VRAM word address in units of 64 bytes (quadwords)
# FB7C * 64 = 0x3EDEF00... way too big

# The addresses might be page-relative or use a different scale
# Let's just look at the VRAM for text-like regions

# Look for text near VRAM coordinates where intro text would appear
# The screenshot shows text at about 25-75% horizontal, 40-80% vertical
# In 32bpp 1024-wide VRAM, the framebuffer could be at various positions

# Save a few sub-regions
for y_start, y_end, label in [(0, 256, 'top'), (256, 512, 'mid'), (512, 768, 'lower'), (768, 1024, 'bottom')]:
    sub = arr[y_start:y_end, :, :3]
    Image.fromarray(sub, 'RGB').save(f'C:/Programmieren/wizardrytranslation/dumps/textevent/vram_{label}.png')
    print(f'Saved vram_{label}.png')

print('Done')
