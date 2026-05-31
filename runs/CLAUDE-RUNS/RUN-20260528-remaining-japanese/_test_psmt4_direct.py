import sys, os
sys.path.insert(0, "C:/Programmieren/wizardrytranslation/tools")
from psmt4_deswizzle import _psmt4_nibble_addr

ORIG = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources/1272_type01.bin"
orig = open(ORIG, "rb").read()
HEADER = 192
orig_pixels = orig[HEADER:-64]

CELL_W, CELL_H = 12, 12
COLS = 21

print("Testing direct PSMT4 read of original R1272...")
print("(If original is stored as raw PSMT4 VRAM data, this should show correct glyphs)")
print()

for glyph_id in [33, 346]:
    col = glyph_id % COLS
    row = glyph_id // COLS
    x0, y0 = col * CELL_W, row * CELL_H
    print(f"Glyph {glyph_id} at ({x0},{y0}):")
    nt = 0
    for dy in range(CELL_H):
        rp = []
        for dx in range(CELL_W):
            x, y = x0+dx, y0+dy
            nib_addr = _psmt4_nibble_addr(x, y, 256)
            byte_addr = nib_addr // 2
            if byte_addr < len(orig_pixels):
                b = orig_pixels[byte_addr]
                val = (b & 0x0F) if nib_addr & 1 == 0 else ((b >> 4) & 0x0F)
            else:
                val = -1
            rp.append(val)
            if val != 15 and val >= 0:
                nt += 1
        print("  " + " ".join(f"{p:X}" for p in rp))
    print(f"  Non-transparent: {nt}")
    print()

print("=" * 60)
print("Testing PSMCT32 upload interpretation (deswizzle)...")
print("(If original is stored as PSMCT32 host data, this should show correct glyphs)")
print()

from psmt4_deswizzle import deswizzle_psmt4
deswizzled = deswizzle_psmt4(orig_pixels, 256, 512, bw_psmt4=256, dbw_ct32=256)

for glyph_id in [33, 346]:
    col = glyph_id % COLS
    row = glyph_id // COLS
    x0, y0 = col * CELL_W, row * CELL_H
    print(f"Glyph {glyph_id} at ({x0},{y0}):")
    nt = 0
    for dy in range(CELL_H):
        rp = []
        for dx in range(CELL_W):
            val = deswizzled[(y0+dy)*256 + (x0+dx)]
            rp.append(val)
            if val != 15:
                nt += 1
        print("  " + " ".join(f"{p:X}" for p in rp))
    print(f"  Non-transparent: {nt}")
    print()

# Now test our atlas with same approaches
print("=" * 60)
print("Testing OUR ATLAS with direct PSMT4 read...")
print()

ATLAS = "C:/Programmieren/wizardrytranslation/build/english_font_atlas.bin"
atlas = open(ATLAS, "rb").read()
atlas_pixels = atlas[HEADER:-64]

for glyph_id in [33, 346]:
    col = glyph_id % COLS
    row = glyph_id // COLS
    x0, y0 = col * CELL_W, row * CELL_H
    print(f"Glyph {glyph_id} at ({x0},{y0}):")
    nt = 0
    for dy in range(CELL_H):
        rp = []
        for dx in range(CELL_W):
            x, y = x0+dx, y0+dy
            nib_addr = _psmt4_nibble_addr(x, y, 256)
            byte_addr = nib_addr // 2
            if byte_addr < len(atlas_pixels):
                b = atlas_pixels[byte_addr]
                val = (b & 0x0F) if nib_addr & 1 == 0 else ((b >> 4) & 0x0F)
            else:
                val = -1
            rp.append(val)
            if val != 15 and val >= 0:
                nt += 1
        print("  " + " ".join(f"{p:X}" for p in rp))
    print(f"  Non-transparent: {nt}")
    print()

print("=" * 60)
print("Testing OUR ATLAS with PSMCT32 deswizzle...")
print()

atlas_desw = deswizzle_psmt4(atlas_pixels[:65536], 256, 512, bw_psmt4=256, dbw_ct32=256)

for glyph_id in [33, 346]:
    col = glyph_id % COLS
    row = glyph_id // COLS
    x0, y0 = col * CELL_W, row * CELL_H
    print(f"Glyph {glyph_id} at ({x0},{y0}):")
    nt = 0
    for dy in range(CELL_H):
        rp = []
        for dx in range(CELL_W):
            val = atlas_desw[(y0+dy)*256 + (x0+dx)]
            rp.append(val)
            if val != 15:
                nt += 1
        print("  " + " ".join(f"{p:X}" for p in rp))
    print(f"  Non-transparent: {nt}")
    print()
