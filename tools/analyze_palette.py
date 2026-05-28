#!/usr/bin/env python3
import struct, sys, collections
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'C:/Programmieren/wizardrytranslation/build/textures_to_edit'

for fname, w, h in [('R2121_guild_background.raw', 512, 512),
                     ('R2122_guild_buttons.raw', 512, 64),
                     ('R2118_tavern_background.raw', 512, 512)]:
    data = open(f'{BASE}/{fname}', 'rb').read()
    tex = data[16:]
    raw = tex[272:]  # after GIF header
    pc = w * h
    pal_size = 1024

    print(f'\n{"="*60}')
    print(f'{fname}: tex={len(tex)}, raw={len(raw)}, pixels={pc}, pal@{pc}')

    # Palette at expected position (after pixel data)
    pal = raw[pc:pc+pal_size]
    print(f'Palette (first 8 colors):')
    for i in range(min(8, len(pal)//4)):
        r, g, b, a = pal[i*4], pal[i*4+1], pal[i*4+2], pal[i*4+3]
        print(f'  [{i:3d}] R={r:3d} G={g:3d} B={b:3d} A={a:3d}')

    # Palette validity check
    nonzero = sum(1 for i in range(256) if i*4+3 < len(pal) and
                  (pal[i*4] + pal[i*4+1] + pal[i*4+2] + pal[i*4+3]) > 0)
    print(f'Non-zero palette entries: {nonzero}/256')

    # Pixel histogram
    hist = collections.Counter(raw[:pc])
    print(f'Unique pixel values: {len(hist)}')
    print(f'Top 10: {hist.most_common(10)}')

    # First pixel bytes
    print(f'First 32 raw bytes: {raw[:32].hex()}')

    # Extra data after palette
    extra = len(raw) - pc - pal_size
    print(f'Extra bytes after palette: {extra}')
    if extra > 0:
        print(f'Extra data: {raw[pc+pal_size:pc+pal_size+32].hex()}')
